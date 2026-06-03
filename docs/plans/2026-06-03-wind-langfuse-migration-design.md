# Wind Langfuse Migration Design

Date: 2026-06-03

## Context

The Wind Langfuse wrapper currently lives inside the local `langfuse-python`
fork at `/Users/hqhe/git/langfuse-python`. The upstream fork should remain
unchanged for now. This repository, `Wind-Langfuse-Python`, will become the
independent thin wrapper package.

## Selected Approach

Use a minimal standalone Python package.

The new repository will contain only the Wind wrapper code, wrapper tests,
package metadata, and usage documentation. It will not vendor or copy the
upstream Langfuse SDK source. Instead, it will depend on `langfuse==3.15.0`.

## Package Contract

- Published package name: `wind-langfuse-sdk`
- Import package name: `wind_langfuse`
- Python support: `>=3.10,<4.0`
- Runtime dependencies:
  - `langfuse==3.15.0`
  - `opentelemetry-sdk`

## Repository Layout

```text
Wind-Langfuse-Python/
  pyproject.toml
  README.md
  WIND_SDK_USAGE.md
  wind_langfuse/
    __init__.py
    _version.py
    client.py
  tests/
    test_wind_langfuse.py
```

## Wrapper Behavior

The wrapper keeps the existing behavior from the fork:

- `WindLangfuse` wraps the native `langfuse.Langfuse` client.
- Wind-required initialization fields are `product_name`, `app_name`,
  `app_class_id`, `version`, and `environment`.
- `version` is forwarded to Langfuse as `release`.
- `environment` is forwarded to Langfuse as `environment`.
- Observation names are prefixed as `<app_name>:<name>`.
- Names already starting with `<app_name>:` are not double-prefixed.
- Observations receive Wind attributes:
  - `service.product.name`
  - `service.name`
  - `wind.app.class_id`
  - `wind.app.version`
  - `wind.app.environment`
- OpenTelemetry resource attributes include host data and Wind SDK metadata.
- Trace name updates are dropped by the wrapper while other trace fields are
  forwarded.
- Native Langfuse APIs remain available through pass-through methods,
  `native_client`, `api`, `async_api`, and `__getattr__`.

## Testing

Migrate the existing fake-based unit tests from `tests/test_wind_langfuse.py`.
They verify wrapper behavior without requiring a live Langfuse server.

Primary checks:

```bash
python -m pytest tests/test_wind_langfuse.py
python -m ruff check wind_langfuse tests
python -m build
```

If local tooling is missing, install project dependencies with the repository's
chosen package manager and rerun the checks.
