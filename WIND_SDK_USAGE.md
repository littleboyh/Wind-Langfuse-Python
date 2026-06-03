# Wind Langfuse SDK Usage Guide

## Overview

`wind-langfuse-sdk` is a thin wrapper around `langfuse==3.15.0`.

The wrapper gives Wind applications a consistent SDK entry point without modifying
the upstream Langfuse Python SDK source code.

## Install

```bash
pip install wind-langfuse-sdk
```

If installing from a private package index:

```bash
pip install wind-langfuse-sdk --index-url https://<your-private-pypi>/simple
```

## Initialize The Client

```python
from wind_langfuse import WindLangfuse

client = WindLangfuse(
    product_name="risk",
    app_name="quote-service",
    app_class_id="app-1",
    version="1.2.3",
    environment="prod",
    public_key="pk-lf-...",
    secret_key="sk-lf-...",
    base_url="https://langfuse.example.com",
)
```

Wind-required parameters:

| Parameter | Description |
| --- | --- |
| `product_name` | Product name, reported as `service.product.name`. |
| `app_name` | Application name, reported as `service.name` and used as the observation name prefix. |
| `app_class_id` | Wind application class identifier. |
| `version` | Application version. It is also passed to Langfuse as `release`. |
| `environment` | Runtime environment. It is also passed to Langfuse as `environment`. |

Common Langfuse parameters are passed through:

```python
client = WindLangfuse(
    product_name="risk",
    app_name="quote-service",
    app_class_id="app-1",
    version="1.2.3",
    environment="prod",
    public_key="pk-lf-...",
    secret_key="sk-lf-...",
    base_url="https://langfuse.example.com",
    timeout=10,
    flush_at=100,
    flush_interval=5,
    sample_rate=1.0,
    debug=False,
)
```

## Create Spans

```python
with client.start_as_current_span(name="request") as span:
    span.update(input={"query": "hello"})

    with span.start_as_current_span(name="validate") as child:
        child.update(output={"valid": True})

    span.update(output={"status": "done"})
```

Reported observation names:

```text
quote-service:request
quote-service:validate
```

If a name already starts with `app_name:`, the wrapper does not add the prefix again.

## Create Generations

```python
with client.start_as_current_generation(
    name="answer",
    model="gpt-4",
    input={"prompt": "Explain VaR"},
) as generation:
    generation.update(
        output="Value at Risk ...",
        usage_details={
            "prompt_tokens": 10,
            "completion_tokens": 20,
        },
    )
```

Reported observation name:

```text
quote-service:answer
```

## Create Events

```python
event = client.create_event(
    name="cache-hit",
    metadata={"cache": "pricing"},
)
```

Reported observation name:

```text
quote-service:cache-hit
```

## Update Trace Fields

Trace name updates are intentionally disabled by the Wind wrapper:

```python
client.update_current_trace(
    name="ignored",
    user_id="u-1",
    session_id="s-1",
    tags=["prod"],
)
```

The `name` field is dropped. Other trace fields are forwarded to Langfuse.

The same rule applies to observations:

```python
with client.start_as_current_span(name="request") as span:
    span.update_trace(
        name="ignored",
        user_id="u-1",
        metadata={"desk": "fx"},
    )
```

## Wind Attributes

Every observation gets these attributes:

| Attribute | Value |
| --- | --- |
| `service.product.name` | `product_name` |
| `service.name` | `app_name` |
| `wind.app.class_id` | `app_class_id` |
| `wind.app.version` | `version` |
| `wind.app.environment` | `environment` |

The OpenTelemetry resource includes:

| Attribute | Value |
| --- | --- |
| `resource.host.ip` | Local host IP detected by the SDK. |
| `resource.host.name` | Local host name. |
| `service.product.name` | `product_name` |
| `service.name` | `app_name` |
| `wind.sdk.language` | `python` |
| `wind.sdk.name` | `wind-langfuse-sdk` |
| `wind.sdk.version` | Installed Wind SDK package version. |

## Access The Native Langfuse Client

Use `native_client` only when a Langfuse API is not wrapped yet:

```python
native = client.native_client
```

Prefer wrapper methods for observation creation so Wind naming and attributes stay consistent.

## Build

```bash
uv build --no-sources
```

Expected artifacts:

```text
dist/wind_langfuse_sdk-<version>.tar.gz
dist/wind_langfuse_sdk-<version>-py3-none-any.whl
```

## Publish

Publish to a private package repository with Twine:

```bash
uvx twine upload --repository-url https://<your-private-pypi>/ dist/*
```

For PyPI-compatible repositories, credentials can be provided by environment variables.

PowerShell:

```powershell
$env:TWINE_USERNAME="<username>"
$env:TWINE_PASSWORD="<password-or-token>"
uvx twine upload --repository-url https://<your-private-pypi>/ dist/*
```

## Verification

Recommended checks before release:

```bash
uv venv --python 3.12 .venv
uv pip install -e . pytest ruff build
.venv/bin/python -m pytest tests/test_wind_langfuse.py
.venv/bin/python -m ruff check wind_langfuse tests
.venv/bin/python -m build
```
