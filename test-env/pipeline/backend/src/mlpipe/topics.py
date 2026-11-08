from mlpipe.contracts import Algorithm

REQUESTS = "ml.requests"
RESULTS = "ml.results"
RETRY = "ml.tasks.retry"
DEAD_LETTERS = "ml.dead_letters"


def task_topic(algorithm: Algorithm) -> str:
    return f"ml.tasks.{algorithm.value}"


TASK_TOPICS: tuple[str, ...] = tuple(task_topic(algorithm) for algorithm in Algorithm)
PIPELINE_TOPICS: tuple[str, ...] = (REQUESTS, RESULTS, RETRY, DEAD_LETTERS, *TASK_TOPICS)

DISPATCHER_GROUP = "dispatcher"
SINK_GROUP = "results-sink"
RETRY_GROUP = "retry-router"


def worker_group(algorithm: Algorithm) -> str:
    return f"worker-{algorithm.value}"
