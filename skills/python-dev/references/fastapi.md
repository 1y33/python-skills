# HTTP applications

Read when changing HTTP contracts, handlers, or application lifecycle. Preserve the framework already used. FastAPI is suitable for typed new APIs, not a reason to migrate an existing application.

## Boundaries and composition

Keep transport parsing, status mapping, and authentication distinguishable from reusable business rules. Simple handlers may call concrete collaborators directly. Extract services for cohesive behavior and repositories for persistence policy; do not mandate pass-through layers or duplicate every schema.

Let the schema reject invalid input before handlers branch: closed path and query values are Literal or Enum parameters, and bodies whose fields depend on a kind are discriminated unions. Separate public schemas from storage/internal models where exposure, compatibility, or validation differs. Declare response contracts so internal fields cannot leak. Specify missing versus null, unknown fields, pagination bounds, error shape, and backward compatibility.

Provide discoverable application assembly and injectable configuration. Use an application factory when multiple configurations or isolated tests need it. Own long-lived clients and pools in lifespan contexts; never create operational resources at import time. Request-scoped resources must outlive all consumers, including streaming responses.

## Execution and failure

Routes match in declaration order; constrain path parameters with Literal rather than catch-all parameters. Use async handlers with nonblocking dependencies. Shared state across awaits and per-worker background loops follow the async reference. FastAPI runs synchronous handlers in a thread pool; calling a blocking helper from an async handler does not offload it. Bound both concurrency and body/response sizes. Propagate request deadlines and account for client disconnection and cancellation.

Translate expected failures consistently at the HTTP boundary: map domain exceptions to statuses once with exception handlers, not per-route try/except. Unexpected failures return safe generic responses with correlation identifiers; log details once without secrets. Do not expose upstream response bodies, internal validation inputs, or chained sensitive exceptions.

Work requiring durable completion belongs in durable storage/queues, not process-local background tasks. Define idempotency for repeatable state-changing requests. Health and readiness checks follow the observability reference.

## Security and operations

Use centralized authentication with explicit public exceptions; enforce authorization on the specific resource and tenant inside the operation. Do not equate successful authentication with permission. Host-header allowlisting follows the security reference. Apply CSRF protection to cookie-authenticated browser writes, explicit credentialed CORS origins, trusted-proxy rules, and bounded uploads. Read the security reference when changing these boundaries.

Version public contracts deliberately. Trace request flow with safe identifiers and timing; keep high-cardinality or sensitive data out of metric labels. Shutdown stops admission and allows bounded completion before releasing shared resources.

## Checklist

- [ ] Normal usage, schemas, failure mapping, and resource ownership are explicit.
- [ ] Handlers do not block the event loop or leak internals; durable work survives restart.
- [ ] No handler or service re-checks what the schema already guarantees.
- [ ] Every route with its own validation, auth, streaming, or failure mapping has a test through the HTTP client.
- [ ] Tests exercise the HTTP entrypoint, validation, resource authorization, and failure mapping.
- [ ] Test setup runs lifespan; ASGITransport alone does not trigger it. Dependencies/configuration can be replaced without global-state leakage.
