"""Deterministic text primitives shared by the engines.

No model downloads, no tokenizer dependency, no network: every algorithm in this
pipeline is standard library only so a worker container starts in ~1s.
"""

import re
from collections import Counter

SENTENCE_BREAK = re.compile(r"(?<=[.!?…])[ \t]+|\n+")
WORD = re.compile(r"[a-z0-9][a-z0-9'’-]*")

STOPWORDS = frozenset(
    """
    a about above after again against all am an and any are aren't as at be because been before being below
    between both but by can can't cannot could couldn't did didn't do does doesn't doing don't down during each
    few for from further had hadn't has hasn't have haven't having he her here hers herself him himself his how
    i if in into is isn't it it's its itself just let's me more most mustn't my myself no nor not of off on once
    only or other ought our ours ourselves out over own same shan't she should shouldn't so some such than that
    the their theirs them themselves then there these they this those through to too under until up very was
    wasn't we were weren't what when where which while who whom why will with won't would wouldn't you your yours
    yourself yourselves also get got make makes made use used using via does etc into from would could should
    """.split()
)

NEGATORS = frozenset(
    "not no never none nobody nothing neither nor cannot cant dont doesnt didnt isnt wasnt werent wont wouldnt "
    "shouldnt couldnt hardly barely without lacking fails failed worse terrible awful".split()
)

INTENSIFIERS: dict[str, float] = {
    "very": 1.55,
    "extremely": 1.9,
    "incredibly": 1.85,
    "really": 1.4,
    "truly": 1.45,
    "absolutely": 1.8,
    "completely": 1.65,
    "totally": 1.6,
    "utterly": 1.85,
    "highly": 1.45,
    "super": 1.5,
    "especially": 1.35,
    "particularly": 1.3,
    "so": 1.35,
    "quite": 1.3,
    "rather": 1.25,
    "somewhat": 0.65,
    "slightly": 0.5,
    "barely": 0.4,
    "kinda": 0.6,
    "sorta": 0.6,
    "mostly": 0.85,
}

CONTRAST_MARKERS = frozenset({"but", "however", "although", "though", "yet", "unfortunately", "still"})

SENTIMENT_LABELS = {"positive", "negative", "neutral"}


def tokenize(text: str) -> list[str]:
    """Lowercase word tokens; digits kept, apostrophes kept, everything else splits."""
    return WORD.findall(text.lower())


def split_sentences(text: str) -> list[str]:
    stripped = text.strip()
    if not stripped:
        return []
    parts = [part.strip() for part in SENTENCE_BREAK.split(stripped)]
    sentences = [part for part in parts if part]
    return sentences[:200]


def stem(token: str) -> str:
    """Tiny suffix stripper; applied identically to corpus and query so drift is symmetric."""
    for suffix in ("ing", "edly", "ed", "es", "ly", "s", "'s"):
        if token.endswith(suffix) and len(token) - len(suffix) >= 4:
            return token[: -len(suffix)]
    return token


def content_tokens(text: str) -> list[str]:
    return [stem(token) for token in tokenize(text) if token not in STOPWORDS and len(token) > 2]


def term_frequencies(text: str) -> Counter[str]:
    return Counter(content_tokens(text))


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def round_floats(values: list[float], digits: int = 4) -> list[float]:
    return [round(value, digits) for value in values]
