# Traceparent Context Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add traceparent-only extract and inject helpers to `WindLangfuse`.

**Architecture:** Keep propagation logic inside the thin wrapper and translate W3C `traceparent` to Langfuse's existing `trace_context` shape. Do not add `baggage` support or new runtime dependencies.

**Tech Stack:** Python 3.10+, Langfuse 3.15.0, pytest, ruff, build.

---

### Task 1: Add Failing Extract Tests

**Files:**
- Modify: `tests/test_wind_langfuse.py`

**Step 1: Add tests**

Append tests for valid, missing, and invalid `traceparent` extraction:

```python
def test_extract_trace_context_from_traceparent(monkeypatch: Any) -> None:
    monkeypatch.setattr("wind_langfuse.client.Langfuse", FakeLangfuse)
    client = create_test_client()

    trace_context = client.extract_trace_context(
        {
            "traceparent": (
                "00-4bf92f3577b34da6a3ce929d0e0e4736-"
                "00f067aa0ba902b7-01"
            )
        }
    )

    assert trace_context == {
        "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
        "parent_span_id": "00f067aa0ba902b7",
    }
```

Also add:

- missing header returns `None`
- malformed header returns `None`
- case-insensitive header name works

**Step 2: Run tests to verify failure**

Run:

```bash
.venv/bin/python -m pytest tests/test_wind_langfuse.py -q
```

Expected: FAIL because `WindLangfuse.extract_trace_context` does not exist.

**Step 3: Commit tests**

```bash
git add tests/test_wind_langfuse.py
git commit -m "test: cover traceparent extraction"
```

### Task 2: Implement Extract

**Files:**
- Modify: `wind_langfuse/client.py`
- Test: `tests/test_wind_langfuse.py`

**Step 1: Implement helper**

Add `TRACEPARENT_HEADER = "traceparent"` and a regex for:

```text
version-trace_id-parent_span_id-flags
```

Implement:

```python
def extract_trace_context(self, headers: Mapping[str, str]) -> Optional[Dict[str, str]]:
    traceparent = _get_header(headers, TRACEPARENT_HEADER)
    if traceparent is None:
        return None

    match = TRACEPARENT_PATTERN.fullmatch(traceparent.strip())
    if match is None:
        return None

    return {
        "trace_id": match.group("trace_id"),
        "parent_span_id": match.group("parent_span_id"),
    }
```

Use a small `_get_header` helper for case-insensitive lookup.

**Step 2: Run tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_wind_langfuse.py -q
```

Expected: PASS for extraction tests and existing wrapper tests.

**Step 3: Commit**

```bash
git add wind_langfuse/client.py
git commit -m "feat: extract trace context from traceparent"
```

### Task 3: Add Failing Inject Tests

**Files:**
- Modify: `tests/test_wind_langfuse.py`

**Step 1: Extend fake client**

Add fields and methods to `FakeLangfuse`:

```python
self.current_trace_id: Optional[str] = None
self.current_observation_id: Optional[str] = None

def get_current_trace_id(self) -> Optional[str]:
    return self.current_trace_id

def get_current_observation_id(self) -> Optional[str]:
    return self.current_observation_id
```

**Step 2: Add tests**

Add tests that verify:

- empty headers get `traceparent`
- existing headers are preserved
- existing `traceparent` is overwritten
- no active context leaves headers unchanged

**Step 3: Run tests to verify failure**

Run:

```bash
.venv/bin/python -m pytest tests/test_wind_langfuse.py -q
```

Expected: FAIL because `WindLangfuse.inject_trace_context` does not exist.

**Step 4: Commit tests**

```bash
git add tests/test_wind_langfuse.py
git commit -m "test: cover traceparent injection"
```

### Task 4: Implement Inject

**Files:**
- Modify: `wind_langfuse/client.py`
- Test: `tests/test_wind_langfuse.py`

**Step 1: Implement inject**

Add:

```python
def inject_trace_context(
    self, headers: Optional[MutableMapping[str, str]] = None
) -> Dict[str, str]:
    output_headers = dict(headers or {})
    trace_id = self._client.get_current_trace_id()
    parent_span_id = self._client.get_current_observation_id()
    if trace_id is None or parent_span_id is None:
        return output_headers

    output_headers[TRACEPARENT_HEADER] = f"00-{trace_id}-{parent_span_id}-01"
    return output_headers
```

**Step 2: Run tests**

Run:

```bash
.venv/bin/python -m pytest tests/test_wind_langfuse.py -q
```

Expected: PASS.

**Step 3: Commit**

```bash
git add wind_langfuse/client.py
git commit -m "feat: inject current trace context into traceparent"
```

### Task 5: Document Traceparent Usage

**Files:**
- Modify: `README.md`
- Modify: `WIND_SDK_USAGE.md`

**Step 1: Add docs**

Document:

```python
trace_context = client.extract_trace_context(request.headers)
with client.start_as_current_span(name="handler", trace_context=trace_context):
    ...
```

and:

```python
headers = client.inject_trace_context({"content-type": "application/json"})
```

**Step 2: Commit docs**

```bash
git add README.md WIND_SDK_USAGE.md
git commit -m "docs: add traceparent context usage"
```

### Task 6: Verify Package

**Files:**
- Verify: `wind_langfuse/client.py`
- Verify: `tests/test_wind_langfuse.py`
- Verify: `README.md`
- Verify: `WIND_SDK_USAGE.md`

**Step 1: Run tests**

```bash
.venv/bin/python -m pytest tests/test_wind_langfuse.py -q
```

Expected: all tests pass.

**Step 2: Run lint**

```bash
.venv/bin/python -m ruff check wind_langfuse tests
```

Expected: no lint errors.

**Step 3: Run build**

```bash
.venv/bin/python -m build
```

Expected: sdist and wheel build successfully.
