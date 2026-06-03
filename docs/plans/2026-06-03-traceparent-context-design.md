# Traceparent Context Design

Date: 2026-06-03

## Context

`WindLangfuse` currently supports Langfuse's `trace_context` parameter, but users
must manually pass `trace_id` and `parent_span_id` between upstream and
downstream services. This makes request chaining harder at the application
layer.

The first version will support only the W3C `traceparent` header. It will not
support `baggage`.

## API

Add two methods to `WindLangfuse`:

```python
def extract_trace_context(self, headers: Mapping[str, str]) -> Optional[Dict[str, str]]:
    ...

def inject_trace_context(
    self, headers: Optional[MutableMapping[str, str]] = None
) -> Dict[str, str]:
    ...
```

## Extract Behavior

`extract_trace_context` reads the `traceparent` header from request headers.

Expected format:

```text
00-<32 lowercase hex trace_id>-<16 lowercase hex parent_span_id>-<2 hex flags>
```

If the header is valid, return:

```python
{
    "trace_id": trace_id,
    "parent_span_id": parent_span_id,
}
```

If the header is missing or invalid, return `None`. The method should not raise
for malformed propagation headers.

Header lookup should be case-insensitive enough for common HTTP header mappings.

## Inject Behavior

`inject_trace_context` reads the current active Langfuse/OpenTelemetry context
from the native client:

- `get_current_trace_id()`
- `get_current_observation_id()`

If both values are present, write:

```text
traceparent: 00-<trace_id>-<parent_span_id>-01
```

If no active context exists, return the provided headers unchanged, or an empty
dict when no headers were provided.

If headers are provided, the method preserves existing header values and
adds or overwrites `traceparent`.

## Testing

Add fake-client unit tests for:

- valid `traceparent` extraction
- missing `traceparent`
- malformed `traceparent`
- injection from active context into empty headers
- injection preserves existing headers and overwrites existing `traceparent`
- no active context leaves headers unchanged

Run:

```bash
.venv/bin/python -m pytest tests/test_wind_langfuse.py -q
.venv/bin/python -m ruff check wind_langfuse tests
.venv/bin/python -m build
```
