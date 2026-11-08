"""Domain contracts shared by the API, the Kafka services, and the browser.

Every boundary in the pipeline is a pydantic model here: the browser posts a
``JobCreate``, the API publishes a ``JobRequest``, the dispatcher fans it out into
``TaskMessage`` envelopes, workers report ``TaskEvent`` phases, and the sink turns
those phases into the ``JobView`` the UI renders. Field names and enum values are
mirrored 1:1 in ``web/src/lib/types.ts``.
"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Any, Literal, Self
from uuid import UUID

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    TypeAdapter,
    computed_field,
    field_validator,
    model_validator,
)

MAX_TEXT_CHARS = 8000
MIN_TEXT_CHARS = 1
MAX_ERROR_CHARS = 600


def utc_now() -> datetime:
    return datetime.now(UTC)


class Algorithm(StrEnum):
    SENTIMENT = "sentiment"
    CLASSIFY = "classify"
    SUMMARY = "summary"
    EMBEDDING = "embedding"


ALGORITHMS: tuple[Algorithm, ...] = tuple(Algorithm)


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    PARTIAL = "partial"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


TERMINAL_JOB_STATUSES = frozenset({JobStatus.PARTIAL, JobStatus.SUCCEEDED, JobStatus.FAILED})


class TaskStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    DEAD = "dead"


TERMINAL_TASK_STATUSES = frozenset({TaskStatus.SUCCEEDED, TaskStatus.FAILED, TaskStatus.DEAD})
PENDING_TASK_STATUSES = frozenset({TaskStatus.QUEUED, TaskStatus.RUNNING})


class TaskPhase(StrEnum):
    """What a worker reports on ``ml.results``."""

    STARTED = "started"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    RETRYING = "retrying"
    DEAD = "dead"


PHASE_TO_STATUS: dict[TaskPhase, TaskStatus] = {
    TaskPhase.STARTED: TaskStatus.RUNNING,
    TaskPhase.SUCCEEDED: TaskStatus.SUCCEEDED,
    TaskPhase.FAILED: TaskStatus.FAILED,
    TaskPhase.RETRYING: TaskStatus.QUEUED,
    TaskPhase.DEAD: TaskStatus.DEAD,
}

FAILURE_PHASES = frozenset({TaskPhase.FAILED, TaskPhase.RETRYING, TaskPhase.DEAD})


def derive_job_status(statuses: tuple[TaskStatus, ...] | list[TaskStatus]) -> JobStatus:
    """A job's status is a pure rollup of its task statuses."""
    if not statuses:
        return JobStatus.QUEUED
    pending = [status for status in statuses if status in PENDING_TASK_STATUSES]
    succeeded = sum(1 for status in statuses if status is TaskStatus.SUCCEEDED)
    if pending:
        return JobStatus.QUEUED if len(pending) == len(statuses) else JobStatus.RUNNING
    if succeeded == len(statuses):
        return JobStatus.SUCCEEDED
    if succeeded == 0:
        return JobStatus.FAILED
    return JobStatus.PARTIAL


class WireModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class JobCreate(WireModel):
    text: str = Field(min_length=MIN_TEXT_CHARS, max_length=MAX_TEXT_CHARS)
    algorithms: tuple[Algorithm, ...] | None = None

    @field_validator("text")
    @classmethod
    def _strip_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("text must contain non-whitespace characters")
        return cleaned

    @field_validator("algorithms")
    @classmethod
    def _dedupe_algorithms(cls, value: tuple[Algorithm, ...] | None) -> tuple[Algorithm, ...] | None:
        if value is None:
            return None
        unique = tuple(dict.fromkeys(value))
        if not unique:
            raise ValueError("select at least one algorithm")
        return unique


class QueuedTask(WireModel):
    task_id: UUID
    algorithm: Algorithm


class JobRequest(WireModel):
    """Produced by the API to ``ml.requests``; consumed by the dispatcher."""

    job_id: UUID
    text: str = Field(min_length=MIN_TEXT_CHARS, max_length=MAX_TEXT_CHARS)
    tasks: tuple[QueuedTask, ...] = Field(min_length=1)
    source: str = "web"
    created_at: AwareDatetime


class TaskMessage(WireModel):
    """One algorithm's unit of work, on ``ml.tasks.<algorithm>``."""

    task_id: UUID
    job_id: UUID
    algorithm: Algorithm
    text: str = Field(min_length=MIN_TEXT_CHARS, max_length=MAX_TEXT_CHARS)
    attempt: int = Field(default=1, ge=1, le=100)
    created_at: AwareDatetime


class TaskEvent(WireModel):
    """Worker progress, on ``ml.results``; the sink is the only writer."""

    task_id: UUID
    job_id: UUID
    algorithm: Algorithm
    phase: TaskPhase
    attempt: int = Field(ge=1, le=100)
    worker_id: str = Field(min_length=1, max_length=120)
    occurred_at: AwareDatetime
    duration_ms: int | None = Field(default=None, ge=0)
    output: dict[str, Any] | None = None
    error: str | None = Field(default=None, max_length=MAX_ERROR_CHARS)
    retry_in_ms: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _phase_invariants(self) -> Self:
        if self.phase is TaskPhase.SUCCEEDED:
            if self.output is None:
                raise ValueError("succeeded events must carry output")
            if self.error is not None:
                raise ValueError("succeeded events must not carry an error")
        elif self.phase is TaskPhase.STARTED:
            if self.output is not None or self.error is not None:
                raise ValueError("started events carry neither output nor error")
        elif not self.error:
            raise ValueError(f"{self.phase} events must carry an error")
        return self


class TaskView(WireModel):
    id: UUID
    algorithm: Algorithm
    status: TaskStatus
    attempt: int
    output: dict[str, Any] | None = None
    error: str | None = None
    duration_ms: int | None = None
    worker_id: str | None = None
    created_at: AwareDatetime
    dispatched_at: AwareDatetime | None = None
    started_at: AwareDatetime | None = None
    finished_at: AwareDatetime | None = None

    @computed_field
    @property
    def retrying(self) -> bool:
        return self.status is TaskStatus.QUEUED and self.attempt > 0


class JobView(WireModel):
    id: UUID
    text: str
    status: JobStatus
    source: str
    created_at: AwareDatetime
    updated_at: AwareDatetime
    completed_at: AwareDatetime | None = None
    tasks: tuple[TaskView, ...] = ()

    @computed_field
    @property
    def duration_ms(self) -> int | None:
        stamps = [task.finished_at for task in self.tasks if task.finished_at is not None]
        if not stamps:
            return None
        return max(0, int((max(stamps) - self.created_at).total_seconds() * 1000))

    @computed_field
    @property
    def failed_tasks(self) -> int:
        return sum(1 for task in self.tasks if task.status in {TaskStatus.FAILED, TaskStatus.DEAD})


class JobPage(WireModel):
    items: tuple[JobView, ...]
    next_cursor: str | None = None


class ThroughputPoint(WireModel):
    minute: AwareDatetime
    jobs: int


class AlgorithmStats(WireModel):
    algorithm: Algorithm
    total: int
    succeeded: int
    failed: int
    dead: int
    p50_ms: float | None = None
    p95_ms: float | None = None


class StatsView(WireModel):
    jobs_total: int
    jobs_active: int
    jobs_succeeded: int
    jobs_partial: int
    jobs_failed: int
    tasks_total: int
    tasks_failed: int
    success_rate: float
    jobs_per_minute: float
    p50_ms: float | None = None
    p95_ms: float | None = None
    throughput: tuple[ThroughputPoint, ...] = ()
    algorithms: tuple[AlgorithmStats, ...] = ()


class BacklogCounts(WireModel):
    pending: int = 0
    running: int = 0
    undelivered: int = 0
    dead: int = 0


class AlgorithmPipeline(WireModel):
    algorithm: Algorithm
    label: str
    accent: str
    topic: str
    group: str
    model: str
    workers: int
    alive: int
    lag: int
    rate_per_min: float
    inflight: int
    p50_ms: float | None = None
    p95_ms: float | None = None
    backlog: int
    running: int
    dead: int
    history: tuple[float, ...] = ()


class PipelineView(WireModel):
    algorithms: tuple[AlgorithmPipeline, ...]
    total_lag: int
    total_rate_per_min: float
    updated_at: AwareDatetime


class DeadLetter(WireModel):
    task_id: UUID
    job_id: UUID
    algorithm: Algorithm
    attempt: int
    error: str
    preview: str
    occurred_at: AwareDatetime


class DeadLetterPage(WireModel):
    items: tuple[DeadLetter, ...]
    total: int


class AlgorithmInfo(WireModel):
    algorithm: Algorithm
    label: str
    description: str
    accent: str
    model: str
    version: str
    topic: str
    group: str


class JobEvent(WireModel):
    type: Literal["job"] = "job"
    job: JobView


class PipelineEvent(WireModel):
    type: Literal["pipeline"] = "pipeline"
    pipeline: PipelineView


class DeadLetterEvent(WireModel):
    type: Literal["dead_letter"] = "dead_letter"
    dead_letter: DeadLetter


StreamEvent = Annotated[JobEvent | PipelineEvent | DeadLetterEvent, Field(discriminator="type")]
STREAM_EVENT_ADAPTER: TypeAdapter[JobEvent | PipelineEvent | DeadLetterEvent] = TypeAdapter(StreamEvent)


class HealthView(WireModel):
    status: Literal["ok", "degraded"]
    version: str
    postgres: bool
    redis: bool
    kafka_bootstrap: str
    uptime_s: float
    subscribers: int
