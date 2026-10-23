# Observability

Read when adding or changing logging, tracing, metrics, or diagnostics for production behavior. Emit what an operator needs to answer "what failed, for whom, and since when", not everything available.

## Logs

- Configure handlers and format once at the entrypoint through one `configure_logging()`; modules only call `logging.getLogger(__name__)` at module level. Do not inject loggers or wrap logging in a custom class; add request context with a ContextVar filter or structlog binding. Use the existing stack (stdlib, structlog, loguru); do not add one for a few calls.
- Use structured fields with stable names (`order_id`, `duration_ms`, `status`) rather than values interpolated into prose. Production output is one JSON object per line when logs are collected by machines.
- Levels have meaning: ERROR needs action, WARNING is degraded but handled, INFO marks lifecycle and state transitions, DEBUG is off in production. Log an exception once at the boundary that handles it, with `exc_info`.
- Never log secrets, tokens, full request or response bodies, or personal data; redact at the logging boundary, not per call.

## Correlation

Assign a request or job id at the entrypoint, store it in a ContextVar, and include it in every log record and outgoing call header. Background tasks inherit or receive the id explicitly. With OpenTelemetry already present, use its trace and span ids instead of a second scheme and correlate logs to them.

## Metrics

For long-running services, cover the four golden signals per service and external dependency: latency (histograms, not averages), traffic, errors, and saturation (queue depth, pool usage). Label values come from small closed sets: never ids, URLs with parameters, user input, or error messages. Name units in metric names (`_seconds`, `_bytes`). Derive rates with the metrics backend's rate functions where one exists; hand-written aggregation uses deltas between samples and handles counter resets. Record each request's real outcome.

## Health

Liveness reports whether the process should be restarted; readiness reports whether it can serve now. Keep both cheap, bounded by a timeout, and free of infrastructure details in the response.

## Checklist

- [ ] Logging is configured only at entrypoints; records carry stable fields and a correlation id.
- [ ] Errors are logged once, with context, without secrets or bodies.
- [ ] For long-running services, latency, traffic, errors, and saturation exist for the changed path; label cardinality is bounded.
- [ ] Tests or a local run show the expected records and metrics for one success and one failure.
