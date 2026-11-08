"""The four algorithm result schemas. Each is versioned by its engine."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class EngineOutput(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    algorithm: str
    model: str
    version: str


class TermHit(BaseModel):
    term: str
    weight: float
    count: int = 1


class SentenceScore(BaseModel):
    index: int
    text: str
    score: float
    label: Literal["positive", "negative", "neutral"]
    highlights: tuple[str, ...] = ()


class SentimentOutput(EngineOutput):
    algorithm: Literal["sentiment"] = "sentiment"
    score: float = Field(ge=-1.0, le=1.0)
    label: Literal["positive", "negative", "neutral"]
    confidence: float = Field(ge=0.0, le=1.0)
    positive_terms: int
    negative_terms: int
    negations: int
    token_count: int
    terms: tuple[TermHit, ...]
    sentences: tuple[SentenceScore, ...]


class ClassLabel(BaseModel):
    label: str
    probability: float = Field(ge=0.0, le=1.0)
    evidence: tuple[str, ...] = ()


class ClassifyOutput(EngineOutput):
    algorithm: Literal["classify"] = "classify"
    predicted: str
    labels: tuple[ClassLabel, ...]
    margin: float
    low_confidence: bool
    known_tokens: int
    unknown_tokens: int
    vocabulary: int


class SummarySentence(BaseModel):
    index: int
    text: str
    score: float
    selected: bool


class SummaryOutput(EngineOutput):
    algorithm: Literal["summary"] = "summary"
    summary: str
    sentences: tuple[SummarySentence, ...]
    keywords: tuple[TermHit, ...]
    source_words: int
    summary_words: int
    compression: float = Field(ge=0.0, le=1.0)
    reading_seconds_saved: int


class Neighbor(BaseModel):
    text: str
    similarity: float


class EmbeddingOutput(EngineOutput):
    algorithm: Literal["embedding"] = "embedding"
    dim: int
    vector: tuple[float, ...]
    norm: float
    bucket: str
    bucket_similarity: float
    neighbors: tuple[Neighbor, ...]
    sparsity: float
