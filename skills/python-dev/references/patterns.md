# Pattern snippets

Read when applying a pattern from the extension check. Snippets show shape, not required code; adapt names and types to the domain.

## Where a branch belongs

- Shape and cross-field rules of one payload: the Pydantic model (Field bounds, Literal, discriminated union, AfterValidator).
- External JSON: a model at the adapter, parsed once.
- The same discriminator (`kind`, `source`, `backend is not None`) branching in 3+ places: one implementation per variant, chosen once at assembly.
- Pydantic strictness differs between Python and JSON input, so test the real ingestion path; `model_copy(update=...)` skips validation.
- Runtime state (credentials configured, resource not created yet, lookup results): a guard clause where it is used.

Smells: `assert isinstance` on your own data (the upstream type is too loose); `getattr(obj, action)` on a string (use a Literal and explicit calls); `**fields: object` update bags (use typed parameters or a dataclass); an if/elif chain over a closed set (use `match` ending in `assert_never`).

### Examples

Payload shape: discriminated union instead of service checks and asserts.

```python
# before: flat model; service does `if method == "bank": if not iban: raise` then asserts
class BankTransfer(BaseModel):
    method: Literal["bank"]
    iban: Annotated[str, AfterValidator(normalize_iban)]  # required, never None

Payment = Annotated[CardPayment | BankTransfer, Field(discriminator="method")]
```

External JSON: one model instead of isinstance chains repeated per call site.

```python
class UserPage(BaseModel):
    users: list[UserEntry] = Field(default_factory=list)

def first_user_id(response: httpx.Response) -> str | None:
    response.raise_for_status()
    page = UserPage.model_validate_json(response.content)  # ValidationError propagates
    return page.users[0].id if page.users else None  # None means "no users", nothing else
```

Repeated discriminator: variants chosen once instead of `if self.backend is not None` in every method.

```python
class EventStore(ABC):
    @abstractmethod
    def append(self, event: Event) -> None: ...

url = settings.database_url
store = PostgresEventStore(url) if url is not None else SqliteEventStore(db_path)
```

Closed set: Literal plus match instead of `getattr(self.runner, action)`.

```python
Action = Literal["pause", "resume", "cancel"]

async def apply(self, action: Action, job: Job) -> None:
    match action:
        case "pause":
            await self.runner.pause(job)
        case "resume":
            await self.runner.resume(job)
        case "cancel":
            await self.runner.cancel(job)
        case _:
            assert_never(action)
```

## State machine

Entities with a lifecycle (job, order, subscription). Every status write goes through one function that checks the allowed transition and writes conditionally on the current status, instead of status assignments scattered through the service.

```python
Status = Literal["pending", "paid", "shipped", "cancelled"]

ALLOWED: dict[Status, frozenset[Status]] = {
    "pending": frozenset({"paid", "cancelled"}),
    "paid": frozenset({"shipped", "cancelled"}),
    "shipped": frozenset(),
    "cancelled": frozenset(),
}

def transition(store: Store, item_id: str, current: Status, new: Status) -> None:
    if new not in ALLOWED[current]:
        raise InvalidTransition(f"{current} -> {new}")
    if not store.update_status(item_id, expected=current, new=new):  # UPDATE ... WHERE status = ?
        raise ConcurrentChange(item_id)
```

## Callable parameter

The cheapest seam: one varying step, no state.

```python
def export(rows: list[Row], *, encode: Callable[[Row], bytes] = encode_json) -> bytes:
    return b"\n".join(encode(r) for r in rows)
```

## ABC strategy plus explicit composition

Variants with state or several methods.

```python
class Exporter(ABC):
    @abstractmethod
    def write(self, rows: Sequence[Row], dest: BinaryIO) -> None: ...

EXPORTERS: dict[str, type[Exporter]] = {"csv": CsvExporter, "json": JsonExporter}  # classes, not shared instances
```

## Decorator registry (same module as the contract)

Many small variants selected by key.

```python
_PARSERS: dict[str, Callable[[bytes], Doc]] = {}

def parser(fmt: str) -> Callable[[Callable[[bytes], Doc]], Callable[[bytes], Doc]]:
    def register(fn: Callable[[bytes], Doc]) -> Callable[[bytes], Doc]:
        if fmt in _PARSERS:
            raise ValueError(f"duplicate parser: {fmt}")
        _PARSERS[fmt] = fn
        return fn
    return register

@parser("csv")
def parse_csv(data: bytes) -> Doc: ...
```

Keep every registered function importable from one visible place; unknown keys raise with the list of known ones.

## Typed cross-cutting decorator

The same wrapper behavior around many functions.

```python
def timed[**P, R](fn: Callable[P, R]) -> Callable[P, R]:
    @functools.wraps(fn)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start = time.perf_counter()
        try:
            return fn(*args, **kwargs)
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            log.info("timed", extra={"fn": fn.__qualname__, "duration_ms": duration_ms})
    return wrapper
```

PEP 695 syntax needs 3.12+; earlier versions declare `ParamSpec` and `TypeVar`. Async functions need an async wrapper. `functools.cache` on a method keeps `self` alive; cache a module-level function or use a bounded per-instance cache.

## Context manager

Setup and teardown shared by several call sites.

```python
@contextlib.contextmanager
def staged_dir(root: Path) -> Iterator[Path]:
    tmp = Path(tempfile.mkdtemp(dir=root))
    try:
        yield tmp
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
```

## Template method

A fixed run loop where variants differ only in steps.

```python
class Job(ABC):
    def run(self) -> Report:
        items = self.load()
        return Report([self.process(i) for i in items])

    @abstractmethod
    def load(self) -> list[Item]: ...
    @abstractmethod
    def process(self, item: Item) -> Result: ...
```

## singledispatch

Behavior chosen by input type, instead of an if-chain spread across modules.

```python
@functools.singledispatch
def render(node: Node) -> str:
    raise TypeError(f"no renderer for {type(node).__name__}")

@render.register
def _(node: Text) -> str: return node.value
```

## Adapter at a boundary

A third-party client behind your own small interface at transport or storage edges.

```python
class BlobStore(ABC):
    @abstractmethod
    def put(self, key: str, data: bytes) -> None: ...

class S3BlobStore(BlobStore):
    def __init__(self, client: S3Client, bucket: str) -> None:
        self._client, self._bucket = client, bucket
    def put(self, key: str, data: bytes) -> None:
        self._client.put_object(Bucket=self._bucket, Key=key, Body=data)
```

## Checklist

- [ ] Each branch sits where it belongs: schema, adapter model, one variant per class, or a runtime guard.
- [ ] The chosen pattern matches its fit line above; no pattern was added without a named variant or repeated behavior.
- [ ] Lifecycle status changes go through one transition function with conditional writes.
