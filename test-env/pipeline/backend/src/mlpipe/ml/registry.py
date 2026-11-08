"""Algorithm registry: the single place a new consumer/worker is registered.

Adding an algorithm means one new ``Engine`` subclass, one ``EngineOutput`` model,
and one entry in ``build_registry``; Kafka topics, the API, the UI legend, and the
worker entrypoint all read from here.
"""

from mlpipe.contracts import Algorithm
from mlpipe.ml.engine import Engine

ALGORITHM_TOPIC_PREFIX = "ml.tasks"


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


def registry_is_complete() -> bool:
    return set(ENGINES) == set(Algorithm) and len(ENGINES) == len(Algorithm)
