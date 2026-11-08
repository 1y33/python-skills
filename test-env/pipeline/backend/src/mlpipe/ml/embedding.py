"""Hashed TF-IDF embedding with a few handcrafted discourse features."""

import hashlib
import math
from collections import Counter

from mlpipe.contracts import Algorithm
from mlpipe.ml.engine import Engine
from mlpipe.ml.outputs import EmbeddingOutput, EngineOutput, Neighbor
from mlpipe.ml.text import split_sentences, tokenize

DIM = 192
HASHED_DIMS = 188
SEED_CORPUS: dict[str, tuple[str, ...]] = {
    "incident": (
        "the pipeline is down and no messages are being processed at all",
        "urgent production outage all consumers offline since the deploy",
    ),
    "bug_report": (
        "i can reproduce this error every time i click submit",
        "the page renders blank and the console shows an exception",
    ),
    "feature_request": (
        "please add an option to export the results as csv",
        "it would be great to add a dark mode to the dashboard",
    ),
    "billing": (
        "i was charged twice for the pro plan this month",
        "the invoice total is wrong and i need a refund",
    ),
    "praise": (
        "great work the dashboard is fast and the results are excellent",
        "love the new charts thank you for the quick fix",
    ),
    "question": (
        "how do i increase the partition count for a topic",
        "where can i find the documentation for the api key",
    ),
    "summary": (
        "summarise the following text into the key points",
        "the main idea is that retries need a deadline and a bound",
    ),
}


def _digest(token: str) -> int:
    return int.from_bytes(hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest(), "big")


def _bucket(token: str) -> tuple[int, float]:
    value = _digest(token)
    return value % HASHED_DIMS, 1.0 if (value >> 8) & 1 else -1.0


def _vector(text: str) -> list[float]:
    tokens = tokenize(text)
    unigrams = [token for token in tokens if len(token) > 2]
    bigrams = [f"{first} {second}" for first, second in zip(unigrams, unigrams[1:], strict=False)]
    counts = Counter(unigrams)
    counts.update(bigrams)
    vector = [0.0] * HASHED_DIMS
    peak = max(counts.values(), default=1)
    for token, count in counts.items():
        bucket, sign = _bucket(token)
        weight = (0.5 + 0.5 * count / peak) * (1.0 + min(len(token), 12) / 12)
        vector[bucket] += sign * weight

    lower = text.lower()
    features = (
        2.2 * min(lower.count("?"), 3),
        1.6 * min(lower.count("!"), 3),
        1.2 * ("```" in text or "error" in lower),
        2.4 * (len(split_sentences(text)) > 1),
    )
    return vector + list(features)


def _l2(vector: list[float]) -> float:
    return math.sqrt(sum(value * value for value in vector))


def _unit(vector: list[float]) -> list[float]:
    norm = _l2(vector)
    if norm == 0.0:
        return vector
    return [value / norm for value in vector]


SEED_VECTORS: dict[str, list[tuple[str, list[float]]]] = {
    label: [(text, _unit(_vector(text))) for text in texts] for label, texts in SEED_CORPUS.items()
}


class EmbeddingEngine(Engine):
    algorithm = Algorithm.EMBEDDING
    label = "Embed"
    description = "192-d hashed bag of unigrams and bigrams, L2-normalised, with seed neighbours."
    model = "hashed-tfidf"
    version = "1.1.0"
    accent = "#60a5fa"

    def run(self, text: str) -> EngineOutput:
        raw = _vector(text)
        norm = _l2(raw)
        unit = _unit(raw)
        ranked: list[tuple[str, str, float]] = []
        for label, seeds in SEED_VECTORS.items():
            for seed_text, seed_vector in seeds:
                similarity = sum(
                    left * right
                    for left, right in zip(unit, seed_vector, strict=True)
                )
                ranked.append((label, seed_text, round(similarity, 4)))
        ranked.sort(key=lambda item: (-item[2], item[0]))
        bucket, bucket_similarity = ranked[0][0], ranked[0][2]
        return EmbeddingOutput(
            model=self.model,
            version=self.version,
            dim=DIM,
            vector=tuple(round(value, 4) for value in unit),
            norm=round(norm, 4),
            bucket=bucket,
            bucket_similarity=bucket_similarity,
            neighbors=tuple(Neighbor(text=neighbor, similarity=similarity) for _label, neighbor, similarity in ranked[:3]),
            sparsity=round(sum(1 for value in unit if abs(value) > 1e-6) / DIM, 4),
        )
