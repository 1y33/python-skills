"""Lexicon sentiment with negation, intensifier, and contrast handling."""

import math
from typing import ClassVar

from mlpipe.contracts import Algorithm
from mlpipe.ml.outputs import EngineOutput
from mlpipe.ml.outputs import SentenceScore, SentimentOutput, TermHit
from mlpipe.ml.text import CONTRAST_MARKERS, tokenize

from .registry import Engine

LEXICON: dict[str, float] = {
    "love": 3.0, "loved": 3.0, "loves": 2.8, "adore": 3.1, "amazing": 2.9, "awesome": 2.8,
    "excellent": 3.0, "fantastic": 2.9, "great": 2.4, "good": 1.8, "nice": 1.5, "best": 2.9,
    "brilliant": 2.8, "perfect": 2.9, "perfectly": 2.4, "wonderful": 2.9, "superb": 3.0,
    "happy": 2.2, "glad": 1.7, "pleased": 1.9, "delightful": 2.6, "impressive": 2.2,
    "smooth": 1.5, "smoothly": 1.4, "fast": 1.3, "quick": 1.2, "reliable": 2.0, "stable": 1.7,
    "helpful": 2.0, "friendly": 2.0, "clear": 1.5, "clean": 1.5, "easy": 1.4, "useful": 1.9,
    "works": 1.4, "worked": 1.4, "working": 1.2, "fix": 1.0, "fixed": 1.7, "solved": 1.9,
    "thanks": 1.9, "thank": 1.8, "appreciate": 2.1, "recommend": 2.0, "worth": 1.4,
    "goodness": 1.0, "fine": 0.9, "okay": 0.5, "ok": 0.5, "solid": 1.6, "robust": 1.8,
    "scalable": 1.6, "efficient": 1.7, "accurate": 1.6, "improved": 1.9, "improvement": 1.7,
    "win": 1.9, "winning": 1.5, "success": 2.2, "successful": 2.1, "successfully": 1.9,
    "surprised": 0.9, "excited": 2.1, "enjoy": 1.9, "enjoyed": 1.9, "enjoying": 1.9,
    "bad": -2.2, "terrible": -3.0, "awful": -2.9, "horrible": -3.0, "worst": -3.1, "worse": -2.4,
    "poor": -2.0, "poorly": -1.9, "broken": -2.5, "break": -1.5, "breaks": -1.8, "breaking": -1.9,
    "bug": -1.8, "bugs": -1.8, "buggy": -2.4, "crash": -2.7, "crashes": -2.7, "crashing": -2.6,
    "crashed": -2.6, "fail": -2.3, "fails": -2.2, "failed": -2.4, "failing": -2.3, "failure": -2.5,
    "error": -1.6, "errors": -1.7, "exception": -1.4, "timeout": -1.7, "lag": -1.6, "laggy": -2.2,
    "slow": -1.9, "slower": -1.9, "slowest": -2.1, "sluggish": -2.2, "stuck": -2.1, "hangs": -2.1,
    "hang": -2.0, "freeze": -2.0, "frozen": -1.9, "dead": -2.2, "down": -2.1, "outage": -2.9,
    "outages": -2.8, "unusable": -2.9, "useless": -2.8, "brokenly": -2.6, "wrong": -1.9,
    "incorrect": -1.9, "missing": -1.7, "confusing": -1.8, "confused": -1.5, "frustrating": -2.4,
    "frustrated": -2.2, "frustration": -2.2, "annoying": -2.1, "annoyed": -1.9, "angry": -2.3,
    "disappointed": -2.4, "disappointing": -2.4, "disappointment": -2.5, "hate": -2.9,
    "hated": -2.8, "dislike": -1.8, "ugly": -2.0, "clunky": -2.0, "unreliable": -2.4,
    "inconsistent": -1.9, "flaky": -2.0, "noisy": -1.4, "leak": -2.1, "leaks": -2.1, "leaking": -2.0,
    "leak memory": -2.5, "crashloop": -2.8, "crashloops": -2.8, "degraded": -2.0, "degradation": -2.0,
    "blocked": -1.8, "blocking": -1.8, "waiting": -1.0, "expensive": -1.4, "duplicate": -1.5,
    "duplicated": -1.6, "lost": -2.0, "losing": -1.9, "drop": -1.4, "dropped": -1.5, "dropping": -1.5,
    "delayed": -1.6, "delay": -1.4, "delays": -1.5, "stale": -1.7, "silent": -1.3, "silently": -1.4,
    "fails": -2.2, "fixable": 0.8, "painful": -2.4, "pain": -2.0, "mess": -2.1, "messy": -2.0,
    "complicated": -1.2, "hard": -1.1, "difficult": -1.2, "impossible": -2.3, "never": -1.6,
    "not": -1.0, "no": -0.9, "unfortunately": -1.5, "sadly": -1.5, "concern": -1.2, "concerned": -1.4,
    "worried": -1.6, "risk": -1.2, "risky": -1.5, "problem": -1.8, "problems": -1.8, "issue": -1.3,
    "issues": -1.4, "support": 0.4, "responsive": 1.6, "polite": 1.5, "professional": 1.5,
    "recommended": 1.8, "seamless": 2.0, "seamlessly": 1.8, "intuitive": 1.9, "beautiful": 2.2,
    "gorgeous": 2.3, "brilliantly": 2.5, "flawless": 2.6, "flawlessly": 2.4, "super": 1.8,
    "excitedly": 1.9, "improve": 1.4, "improves": 1.5, "fastest": 1.8, "stable-ish": 0.8,
}

_NEGATION_WINDOW = 3
_NEGATION_FLIP = -0.85
_CONTRAST_BOOST = 1.35
_CONTRAST_DAMP = 0.8


def _label_for(score: float) -> str:
    if score >= 0.15:
        return "positive"
    if score <= -0.15:
        return "negative"
    return "neutral"


def _score_tokens(tokens: list[str], contrast_at: int | None) -> tuple[float, list[tuple[str, float]], int]:
    raw = 0.0
    weighted: list[tuple[str, float]] = []
    negations = 0
    for index, token in enumerate(tokens):
        base = LEXICON.get(token)
        if base is None:
            continue
        multiplier = 1.0
        negated = False
        for back in range(1, _NEGATION_WINDOW + 1):
            position = index - back
            if position < 0:
                break
            previous = tokens[position]
            if previous in INTENSIFIER_TABLE:
                multiplier *= INTENSIFIER_TABLE[previous]
            if previous in NEGATION_WORDS:
                negated = True
                negations += 1
                break
        if negated:
            multiplier *= _NEGATION_FLIP * math.sqrt(max(multiplier, 0.25))
        if contrast_at is not None:
            multiplier *= _CONTRAST_BOOST if index > contrast_at else _CONTRAST_DAMP
        raw += base * multiplier
        weighted.append((token, round(base * multiplier, 3)))
    return raw, weighted, negations


NEGATION_WORDS = frozenset(
    "not no never none nobody nothing neither nor cannot cant dont doesnt didnt isnt wasnt werent wont "
    "wouldnt shouldnt couldnt hardly barely without".split()
)
INTENSIFIER_TABLE = {
    "very": 1.55, "extremely": 1.9, "incredibly": 1.85, "really": 1.4, "truly": 1.45,
    "absolutely": 1.8, "completely": 1.65, "totally": 1.6, "utterly": 1.85, "highly": 1.45,
    "super": 1.5, "especially": 1.35, "particularly": 1.3, "so": 1.35, "quite": 1.3,
    "rather": 1.25, "somewhat": 0.65, "slightly": 0.5, "barely": 0.4, "mostly": 0.85,
}


def _normalize(raw: float, hits: int) -> float:
    if hits == 0:
        return 0.0
    damped = raw / (1.0 + 0.55 * math.sqrt(hits))
    return round(math.tanh(damped / 2.6), 4)


class SentimentEngine(Engine):
    algorithm = Algorithm.SENTIMENT
    label = "Sentiment"
    description = "Lexicon polarity with negation, intensifier, and contrast handling."
    model = "lexicon-polarity"
    version = "1.4.0"
    accent = "#f0b46a"

    def run(self, text: str) -> EngineOutput:
        sentences: list[SentenceScore] = []
        terms: dict[str, tuple[float, int]] = {}
        total_hits = 0
        total_negations = 0
        all_tokens = tokenize(text)

        for index, sentence in enumerate(split_sentences(text) or [text]):
            tokens = tokenize(sentence)
            contrast_at = next((i for i, t in enumerate(tokens) if t in CONTRAST_MARKERS), None)
            raw, weighted, negations = _score_tokens(tokens, contrast_at)
            hits = len(weighted)
            total_hits += hits
            total_negations += negations
            score = _normalize(raw, hits)
            highlights = tuple(dict.fromkeys(token for token, weight in sorted(weighted, key=lambda p: -abs(p[1])) if abs(weight) >= 1.0))[:6]
            for token, weight in weighted:
                previous_weight, previous_count = terms.get(token, (0.0, 0))
                terms[token] = (previous_weight + weight, previous_count + 1)
            sentences.append(
                SentenceScore(
                    index=index,
                    text=sentence[:320],
                    score=score,
                    label=_label_for(score),  # type: ignore[arg-type]
                    highlights=highlights,
                )
            )

        overall = _normalize(sum(weight for weight, _count in terms.values()), total_hits)
        confidence = min(0.99, abs(overall) * 0.85 + 0.25 * min(total_hits, 8) / 8) if total_hits else 0.12
        ranked_terms = sorted(terms.items(), key=lambda item: (-abs(item[1][0]), item[0].lower()))[:12]
        return SentimentOutput(
            model=self.model,
            version=self.version,
            score=overall,
            label=_label_for(overall),  # type: ignore[arg-type]
            confidence=round(confidence, 3),
            positive_terms=sum(1 for weight, _count in terms.values() if weight > 0),
            negative_terms=sum(1 for weight, _count in terms.values() if weight < 0),
            negations=total_negations,
            token_count=len(all_tokens),
            terms=tuple(TermHit(term=term, weight=round(weight, 2), count=count) for term, (weight, count) in ranked_terms),
            sentences=tuple(sentences[:16]),
        )
