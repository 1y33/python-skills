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
