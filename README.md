# Wind Langfuse SDK

Wind Langfuse SDK is a thin company wrapper around `langfuse==3.15.0`.

It keeps the upstream Langfuse Python SDK unchanged and adds Wind-specific
initialization, resource attributes, observation naming, and trace update rules.

## Installation

Install from the Wind Python package repository:

```bash
pip install wind-langfuse-sdk
```

## Basic Usage

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

with client.start_as_current_span(name="llm-call") as span:
    span.update(output={"status": "ok"})

client.flush()
```

The observation above is reported to Langfuse with the name:

```text
quote-service:llm-call
```

## Wind Rules

- The published package name is `wind-langfuse-sdk`; the import package is `wind_langfuse`.
- The upstream `langfuse` package is used as a dependency and is not modified.
- Every observation name is prefixed as `<app_name>:<observation_name>`.
- Every observation includes:
  - `service.product.name`
  - `service.name`
  - `wind.app.class_id`
  - `wind.app.version`
  - `wind.app.environment`
- Resource attributes include:
  - `resource.host.ip`
  - `resource.host.name`
  - `service.product.name`
  - `service.name`
  - `wind.sdk.language`
  - `wind.sdk.name`
  - `wind.sdk.version`
- Trace name updates are disabled by the wrapper. Other trace fields can still be updated.

## More Docs

See [WIND_SDK_USAGE.md](WIND_SDK_USAGE.md) for detailed usage and release instructions.
