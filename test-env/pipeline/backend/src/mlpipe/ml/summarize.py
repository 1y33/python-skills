"""Extractive summariser: TF-IDF sentence centrality, MMR de-duplication."""

import math
from collections import Counter

from mlpipe.contracts import Algorithm
from mlpipe.ml.engine import Engine
from mlpipe.ml.outputs import EngineOutput, SummaryOutput, SummarySentence, TermHit
from mlpipe.ml.text import clamp, split_sentences, tokenize

MAX_SENTENCES = 80
MAX_WORDS_PER_SENTENCE = 60
MAX_KEYWORDS = 8
CENTRALITY_WEIGHT = 0.62
POSITION_WEIGHT = 0.22
DENSITY_WEIGHT = 0.16
REDUNDANCY_WEIGHT = 0.35
STOPWORDS = frozenset(
    "a an and are as at be been but by can could did do does for from had has have he her his how i if in into is it its "
    "just me more my no not of on or our out she so some such than that the their them then there these they this to was "
    "we were what when where which while who will with would you your also about above after again all any because "
    "before below between both during each few further here once only other over own same too under until very via".split()
)


def _words(text: str) -> list[str]:
    return [token for token in tokenize(text) if token not in STOPWORDS and len(token) > 2]


def _cosine(left: dict[str, float], right: dict[str, float]) -> float:
    if not left or not right:
        return 0.0
    shared = set(left) & set(right)
    numerator = sum(left[token] * right[token] for token in shared)
    if numerator == 0.0:
        return 0.0
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    return numerator / (left_norm * right_norm)


class SummaryEngine(Engine):
    algorithm = Algorithm.SUMMARY
    label = "Summarise"
    description = "TF-IDF centrality plus MMR diversity; extracts sentences, not paraphrases."
    model = "tfidf-textrank"
    version = "1.2.0"
    accent = "#5eead4"

    def run(self, text: str) -> EngineOutput:
        sentences = split_sentences(text)[:MAX_SENTENCES]
        if not sentences:
            sentences = [text.strip()]
        tokens_by_sentence = [tokenize(sentence)[:MAX_WORDS_PER_SENTENCE] for sentence in sentences]
        document_frequency: Counter[str] = Counter()
        for tokens in tokens_by_sentence:
            document_frequency.update(set(tokens))
        total = len(sentences)

        vectors: list[dict[str, float]] = []
        for tokens in tokens_by_sentence:
            counts = Counter(token for token in tokens if token not in STOPWORDS and len(token) > 2)
            peak = max(counts.values(), default=1)
            vectors.append(
                {
                    token: (0.5 + 0.5 * count / peak) * math.log((total + 1) / (document_frequency[token] + 1))
                    for token, count in counts.items()
                }
            )

        centrality: list[float] = []
        for index, vector in enumerate(vectors):
            similarities = [
                _cosine(vector, other) if other_index != index else 0.0
                for other_index, other in enumerate(vectors)
            ]
            strongest = sorted(similarities, reverse=True)[:3]
            centrality.append(sum(strongest) / len(strongest) if strongest else 0.0)

        peak_centrality = max(centrality, default=0.0) or 1.0
        candidates: list[tuple[int, float]] = []
        for index, sentence in enumerate(sentences):
            position_bias = math.exp(-index / max(total * 0.55, 1.0))
            density = len(vectors[index]) / max(len(tokenize(sentence)), 1)
            score = (
                CENTRALITY_WEIGHT * centrality[index] / peak_centrality
                + POSITION_WEIGHT * position_bias
                + DENSITY_WEIGHT * clamp(density, 0.0, 1.0)
            )
            candidates.append((index, round(score, 4)))

        target = int(clamp(round(total * 0.28), 1, 4)) if total > 1 else 1
        selected: list[int] = []
        remaining = sorted(candidates, key=lambda item: (-item[1], item[0]))
        while remaining and len(selected) < target:
            best_index, best_score = remaining[0]
            redundancy = max((_cosine(vectors[best_index], vectors[chosen]) for chosen in selected), default=0.0)
            if selected and redundancy > 0.82:
                remaining.pop(0)
                continue
            selected.append(best_index)
            remaining.pop(0)
            remaining = [
                (index, round(score * (1.0 - REDUNDANCY_WEIGHT * _cosine(vectors[index], vectors[best_index])), 4))
                for index, score in remaining
            ]
            remaining.sort(key=lambda item: (-item[1], item[0]))
        selected_set = set(selected)

        word_frequencies: Counter[str] = Counter()
        for tokens in tokens_by_sentence:
            word_frequencies.update(token for token in tokens if token not in STOPWORDS and len(token) > 2 and token.isalpha())
        keyword_scores: dict[str, float] = {}
        for term, count in word_frequencies.items():
            specificity = math.log((total + 1) / (document_frequency[term] + 1))
            keyword_scores[term] = (1.0 + math.log(count)) * (1.0 + specificity) * (1.0 + 0.1 * min(len(term), 12))
        scores_by_index = dict(candidates)
        for index in selected_set:
            for token in set(tokens_by_sentence[index]):
                if token in keyword_scores:
                    keyword_scores[token] += 0.35 * scores_by_index[index]

        ranked_keywords = sorted(keyword_scores.items(), key=lambda item: (-item[1], item[0]))[:MAX_KEYWORDS]
        peak_keyword = ranked_keywords[0][1] if ranked_keywords else 1.0
        summary_sentences = [sentences[index] for index in sorted(selected_set)]
        summary = " ".join(summary_sentences)
        source_words = len(tokenize(text))
        summary_words = len(tokenize(summary))
        reading_saved = max(0, round((source_words - summary_words) / 200 * 60))

        return SummaryOutput(
            model=self.model,
            version=self.version,
            summary=summary,
            sentences=tuple(
                SummarySentence(
                    index=index,
                    text=sentences[index][:400],
                    score=score,
                    selected=index in selected_set,
                )
                for index, score in candidates
            ),
            keywords=tuple(
                TermHit(term=term, weight=round(score / peak_keyword, 3), count=word_frequencies[term])
                for term, score in ranked_keywords
            ),
            source_words=source_words,
            summary_words=summary_words,
            compression=round(summary_words / source_words, 3) if source_words else 0.0,
            reading_seconds_saved=reading_saved,
        )
