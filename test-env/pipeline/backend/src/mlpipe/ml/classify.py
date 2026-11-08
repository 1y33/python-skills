"""Multinomial Naive Bayes over a small embedded support-ticket corpus.

The vocabulary is part of the source, so the same message always gets the same
label on every worker: no training state, no model download, no drift.
"""

import math
from collections import Counter
from typing import ClassVar

from mlpipe.contracts import Algorithm
from mlpipe.ml.outputs import ClassLabel, ClassifyOutput, EngineOutput
from mlpipe.ml.text import content_tokens

from .registry import Engine

ALPHA = 0.35
TEMPERATURE = 1.7
TOP_LABELS = 5
TOP_EVIDENCE = 5
LOW_CONFIDENCE_BELOW = 0.42

CORPUS: dict[str, tuple[str, ...]] = {
    "incident": (
        "everything is down right now production is unreachable",
        "the whole pipeline stopped no messages are processed at all",
        "urgent outage all consumers offline since the deploy",
        "we are losing data every minute the brokers are failing",
        "on call page firing the service is unavailable and requests are timing out",
        "cluster is red replicas are down nothing is being consumed",
        "total outage in production consumers keep dying and lag explodes",
        "data is missing from the last hour and nothing is being written",
        "critical the api returns 503 for every request and the dashboard is blank",
        "broker unreachable and workers are offline the incident is ongoing",
        "everything froze and no jobs are completed at all",
        "severe degradation requests are timing out across the board",
    ),
    "bug_report": (
        "there is an error when i click submit it throws an exception",
        "the page renders blank after opening the results tab",
        "i can reproduce the bug with a small text it crashes the worker",
        "the retry button does nothing and the status stays running forever",
        "error message shows undefined instead of the failure reason",
        "a bug in the form validation accepts empty input and fails later",
        "it fails only when the text contains an emoji and the worker crashes",
        "the timeline is broken and shows negative durations",
        "exception traceback in the console when i refresh the page twice",
        "the ui shows the wrong algorithm result on the card",
        "this is broken after the update the table is empty but errors exist",
        "reproduce by sending the same request twice the second one fails",
    ),
    "feature_request": (
        "please add dark mode to the dashboard",
        "it would be great to export the results as csv",
        "can you support batch upload of multiple requests",
        "add a filter for the consumer lag columns please",
        "we would like a way to compare two algorithms side by side",
        "could you add a webhook when a job completes",
        "feature request a shortcut to resend the last request",
        "i would love a diff view of the summary before and after",
        "support for markdown in the text input would be nice",
        "add an option to pin a favorite prompt template",
        "request to add per algorithm timeouts in settings",
        "would be great to see token counts next to each result",
    ),
    "billing": (
        "i was charged twice for the pro plan this month",
        "my invoice shows a duplicate payment and the total is wrong",
        "the subscription renewed but the card was declined how do i update it",
        "please send me a receipt for the last billing period",
        "we need to cancel the annual plan and get a refund",
        "billing address is outdated on the invoice",
        "why did the price increase on my invoice",
        "i want to switch to the monthly plan and pay by transfer",
        "the payment failed twice and the account is now locked",
        "invoice vat number is missing from the receipt",
        "charged for seats we removed last week",
        "refund request for the unused annual subscription",
    ),
    "praise": (
        "love the new latency chart it is beautiful and so fast",
        "great work the dashboard is clear and the results are excellent",
        "thank you the summary feature is really useful and smooth",
        "this is the best release so far the pipeline is stable and reliable",
        "awesome experience everything worked flawlessly on the first try",
        "the ui is gorgeous and the documentation is helpful",
        "impressive improvement please keep it up",
        "works perfectly for us the team is very happy",
        "nice job the retry handling is smooth and easy to understand",
        "i appreciate the clear errors they make debugging simple",
        "the new cards are great and load fast",
        "excellent support response time thank you for the fix",
    ),
    "question": (
        "how do i increase the partition count for a topic",
        "what does the lag column mean on the pipeline panel",
        "is there a way to reset the offset for a consumer group",
        "where can i find the api key settings",
        "how long are results retained before cleanup",
        "what happened to the retry count in the status view",
        "can someone explain the difference between partial and failed",
        "does the worker need access to the database",
        "which port exposes the metrics endpoint",
        "how do i run the pipeline locally with docker compose",
        "what is the default timeout for a request",
        "where is the documentation for the classify labels",
    ),
    "out_of_scope": (
        "the weather tomorrow will be sunny with a light breeze",
        "my favorite pasta recipe needs more garlic and olive oil",
        "the football team won the match in the last minute",
        "please translate this poem into french",
        "i am going to the store to buy milk and bread",
        "the museum opens at ten on sunday morning",
        "my cat is sleeping on the keyboard again",
        "the train leaves from platform three at noon",
        "hello is anyone there",
        "asdfghjkl qwertyuiop",
        "the novel has a slow beginning but a strong ending",
        "let me know when you are free for lunch",
    ),
}

LABELS: tuple[str, ...] = tuple(CORPUS)


class NaiveBayesModel:
    """Fixed-vocabulary multinomial NB, trained once at import from ``CORPUS``."""

    def __init__(self, corpus: dict[str, tuple[str, ...]]) -> None:
        self.label_tokens: dict[str, Counter[str]] = {}
        self.label_total: dict[str, int] = {}
        self.vocabulary: set[str] = set()
        document_tokens: dict[str, list[list[str]]] = {}
        for label, documents in corpus.items():
            token_lists = [content_tokens(document) for document in documents]
            document_tokens[label] = token_lists
            self.label_tokens[label] = Counter(token for tokens in token_lists for token in tokens)
            self.label_total[label] = sum(sum(counts.values()) for counts in (Counter(tokens) for tokens in token_lists))
            self.vocabulary.update(token for tokens in token_lists for token in tokens)
        self.vocabulary_size: int = len(self.vocabulary)
        self.class_count: int = len(corpus)
        self.documents: int = sum(len(documents) for documents in corpus.values())

    def log_likelihood(self, tokens: list[str]) -> dict[str, float]:
        known = [token for token in tokens if token in self.vocabulary]
        denominator_constant = self.vocabulary_size + ALPHA
        scores: dict[str, float] = {}
        for label, counts in self.label_tokens.items():
            denominator = self.label_total[label] + ALPHA * denominator_constant
            total = 0.0
            for token in known:
                total += math.log((counts[token] + ALPHA) / denominator)
            scores[label] = total / max(len(known), 1)
        return scores

    def contributions(self, tokens: list[str], label: str) -> list[tuple[str, float]]:
        counts = self.label_tokens[label]
        denominator = self.label_total[label] + ALPHA * (self.vocabulary_size + ALPHA)
        priors = {other: (self.label_total[other] + ALPHA) / (self.documents + ALPHA) for other in self.label_tokens}
        seen: Counter[str] = Counter(token for token in tokens if token in self.vocabulary)
        scored: list[tuple[str, float]] = []
        for token, count in seen.items():
            own = math.log((counts[token] + ALPHA) / denominator)
            baseline = sum(math.log((prior + ALPHA) / (self.documents + ALPHA)) for prior in priors.values()) / len(priors)
            scored.append((token, (own - baseline) * count))
        scored.sort(key=lambda item: (-item[1], item[0]))
        return scored


_MODEL = NaiveBayesModel(CORPUS)


def _softmax(scores: dict[str, float]) -> dict[str, float]:
    values = {label: value * TEMPERATURE for label, value in scores.items()}
    peak = max(values.values())
    exponentiated = {label: math.exp(value - peak) for label, value in values.items()}
    total = sum(exponentiated.values())
    return {label: value / total for label, value in exponentiated.items()}


class ClassifyEngine(Engine):
    algorithm = Algorithm.CLASSIFY
    label = "Classify"
    description = "Multinomial Naive Bayes ticket triage over an embedded corpus."
    model = "nb-support-ticket"
    version = "2.1.0"
    accent = "#a78bfa"
    unknown_terms: ClassVar[tuple[str, ...]] = ("the",)

    def run(self, text: str) -> EngineOutput:
        tokens = content_tokens(text)
        known_tokens = sum(1 for token in tokens if token in _MODEL.vocabulary)
        if known_tokens == 0:
            labels = (
                ClassLabel(label="out_of_scope", probability=1.0, evidence=()),
                *tuple(ClassLabel(label=name, probability=0.0) for name in LABELS if name != "out_of_scope"),
            )
            return ClassifyOutput(
                model=self.model,
                version=self.version,
                predicted="out_of_scope",
                labels=labels,
                margin=1.0,
                low_confidence=True,
                known_tokens=0,
                unknown_tokens=len(tokens),
                vocabulary=_MODEL.vocabulary_size,
            )

        scores = _MODEL.log_likelihood(tokens)
        probabilities = _softmax(scores)
        ranked = sorted(probabilities.items(), key=lambda item: (-item[1], item[0]))
        predicted, top_probability = ranked[0]
        second_probability = ranked[1][1] if len(ranked) > 1 else 0.0
        evidence = tuple(token for token, _score in _MODEL.contributions(tokens, predicted) if token in _MODEL.vocabulary)[:TOP_EVIDENCE]
        labels = tuple(
            ClassLabel(
                label=label,
                probability=round(probability, 4),
                evidence=evidence if label == predicted else (),
            )
            for label, probability in ranked[:TOP_LABELS]
        )
        return ClassifyOutput(
            model=self.model,
            version=self.version,
            predicted=predicted,
            labels=labels,
            margin=round(top_probability - second_probability, 4),
            low_confidence=top_probability < LOW_CONFIDENCE_BELOW,
            known_tokens=known_tokens,
            unknown_tokens=len(tokens) - known_tokens,
            vocabulary=_MODEL.vocabulary_size,
        )
