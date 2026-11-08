"""Algorithm registry: the single place a new consumer/worker is registered.

Adding an algorithm means one new ``Engine`` subclass, one ``EngineOutput`` model,
and one entry in ``build_registry``; topics, the API, the UI legend, and the
worker entrypoint all read from here.
"""

from abc import ABC, abstractmethod
from typing import ClassVar

from mlpipe.contracts import Algorithm
from mlpipe.ml.outputs import EngineOutput


class Engine(ABC):
    """One algorithm behind one Kafka consumer group."""

    algorithm: ClassVar[Algorithm]
    label: ClassVar[str]
    description: ClassVar[str]
    model: ClassVar[str]
    version: ClassVar[str]
    accent: ClassVar[str]

    @abstractmethod
    def run(self, text: str) -> EngineOutput:
        """Pure function: same text in, same output out, no I/O."""


def build_registry() -> dict[Algorithm, Engine]:
    from mlpipe.ml.classify import ClassifyEngine
    from mlpipe.ml.embedding import EmbeddingEngine
    from mlpipe.ml.sentiment import SentimentEngine
    from mlpipe.ml.summarize import SummaryEngine

    engines: tuple[Engine, ...] = (
        SentimentEngine(),
        ClassifyEngine(),
        SummaryEngine(),
        EmbeddingEngine(),
    )
    return {engine.algorithm: engine for engine in engines}


ENGINES: dict[Algorithm, Engine] = build_registry()


def get_engine(algorithm: Algorithm) -> Engine:
    return ENGINES[algorithm]
