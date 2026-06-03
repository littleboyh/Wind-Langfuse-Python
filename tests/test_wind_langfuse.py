from typing import Any, Dict, Optional, Type, cast

from wind_langfuse.client import WindLangfuse


class FakeOtelSpan:
    def __init__(self) -> None:
        self.attributes: Dict[str, str] = {}

    def set_attributes(self, attributes: Dict[str, str]) -> None:
        self.attributes.update(attributes)


class FakeObservation:
    def __init__(self, name: str) -> None:
        self.name = name
        self._otel_span = FakeOtelSpan()
        self.update_trace_kwargs: Optional[Dict[str, Any]] = None
        self.update_kwargs: Optional[Dict[str, Any]] = None

    def start_span(self, **kwargs: Any) -> "FakeObservation":
        return FakeObservation(kwargs["name"])

    def update(self, **kwargs: Any) -> "FakeObservation":
        self.update_kwargs = kwargs
        return self

    def update_trace(self, **kwargs: Any) -> "FakeObservation":
        self.update_trace_kwargs = kwargs
        return self

    def end(self, **kwargs: Any) -> "FakeObservation":
        return self


class FakeContextManager:
    def __init__(self, observation: FakeObservation) -> None:
        self.observation = observation

    def __enter__(self) -> FakeObservation:
        return self.observation

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Any,
    ) -> None:
        return None


class FakeLangfuse:
    def __init__(self, **kwargs: Any) -> None:
        self.init_kwargs = kwargs
        self.update_current_trace_kwargs: Optional[Dict[str, Any]] = None
        self.last_observation: Optional[FakeObservation] = None
        self.current_trace_id: Optional[str] = None
        self.current_observation_id: Optional[str] = None

    def start_span(self, **kwargs: Any) -> FakeObservation:
        self.last_observation = FakeObservation(kwargs["name"])
        return self.last_observation

    def start_as_current_span(self, **kwargs: Any) -> FakeContextManager:
        self.last_observation = FakeObservation(kwargs["name"])
        return FakeContextManager(self.last_observation)

    def update_current_trace(self, **kwargs: Any) -> None:
        self.update_current_trace_kwargs = kwargs

    def get_current_trace_id(self) -> Optional[str]:
        return self.current_trace_id

    def get_current_observation_id(self) -> Optional[str]:
        return self.current_observation_id


def create_test_client() -> WindLangfuse:
    return WindLangfuse(
        product_name="risk",
        app_name="quote-service",
        app_class_id="app-1",
        version="1.2.3",
        environment="prod",
        public_key="pk",
        secret_key="sk",
    )


def test_wind_client_prefixes_observation_names_and_sets_attributes(
    monkeypatch: Any,
) -> None:
    created_clients = []

    def create_fake_client(**kwargs: Any) -> FakeLangfuse:
        client = FakeLangfuse(**kwargs)
        created_clients.append(client)
        return client

    monkeypatch.setattr("wind_langfuse.client.Langfuse", create_fake_client)

    client = WindLangfuse(
        product_name="risk",
        app_name="quote-service",
        app_class_id="app-1",
        version="1.2.3",
        environment="prod",
        public_key="pk",
        secret_key="sk",
    )

    span = client.start_span(name="llm-call")

    assert span.native_observation.name == "quote-service:llm-call"
    assert span.native_observation._otel_span.attributes == {
        "service.product.name": "risk",
        "service.name": "quote-service",
        "wind.app.class_id": "app-1",
        "wind.app.version": "1.2.3",
        "wind.app.environment": "prod",
    }
    assert created_clients[0].init_kwargs["environment"] == "prod"
    assert created_clients[0].init_kwargs["release"] == "1.2.3"
    assert "tracer_provider" in created_clients[0].init_kwargs


def test_wind_observation_prefixes_nested_observations(monkeypatch: Any) -> None:
    monkeypatch.setattr("wind_langfuse.client.Langfuse", FakeLangfuse)

    client = WindLangfuse(
        product_name="risk",
        app_name="quote-service",
        app_class_id="app-1",
        version="1.2.3",
        environment="prod",
        public_key="pk",
        secret_key="sk",
    )

    parent = client.start_span(name="parent")
    child = parent.start_span(name="child")

    assert child.native_observation.name == "quote-service:child"


def test_wind_trace_name_updates_are_dropped(monkeypatch: Any) -> None:
    monkeypatch.setattr("wind_langfuse.client.Langfuse", FakeLangfuse)

    client = WindLangfuse(
        product_name="risk",
        app_name="quote-service",
        app_class_id="app-1",
        version="1.2.3",
        environment="prod",
        public_key="pk",
        secret_key="sk",
    )

    client.update_current_trace(name="ignored", user_id="u1")
    native_client = cast(FakeLangfuse, client.native_client)

    assert native_client.update_current_trace_kwargs == {"user_id": "u1"}

    span = client.start_span(name="span")
    span.update_trace(name="ignored", session_id="s1")

    assert span.native_observation.update_trace_kwargs == {"session_id": "s1"}


def test_wind_observation_update_prefixes_name(monkeypatch: Any) -> None:
    monkeypatch.setattr("wind_langfuse.client.Langfuse", FakeLangfuse)

    client = WindLangfuse(
        product_name="risk",
        app_name="quote-service",
        app_class_id="app-1",
        version="1.2.3",
        environment="prod",
        public_key="pk",
        secret_key="sk",
    )

    span = client.start_span(name="span")
    span.update(name="renamed")

    assert span.native_observation.update_kwargs == {"name": "quote-service:renamed"}


def test_wind_resource_attributes(monkeypatch: Any) -> None:
    monkeypatch.setattr("wind_langfuse.client.Langfuse", FakeLangfuse)

    client = WindLangfuse(
        product_name="risk",
        app_name="quote-service",
        app_class_id="app-1",
        version="1.2.3",
        environment="prod",
        public_key="pk",
        secret_key="sk",
    )

    native_client = cast(FakeLangfuse, client.native_client)
    resource_attributes = native_client.init_kwargs[
        "tracer_provider"
    ].resource.attributes

    assert resource_attributes["service.product.name"] == "risk"
    assert resource_attributes["service.name"] == "quote-service"
    assert resource_attributes["wind.sdk.language"] == "python"
    assert resource_attributes["wind.sdk.name"] == "wind-langfuse-sdk"
    assert "wind.sdk.version" in resource_attributes
    assert "resource.host.ip" in resource_attributes
    assert "resource.host.name" in resource_attributes


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


def test_extract_trace_context_uses_case_insensitive_header_name(
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr("wind_langfuse.client.Langfuse", FakeLangfuse)
    client = create_test_client()

    trace_context = client.extract_trace_context(
        {
            "TraceParent": (
                "00-4bf92f3577b34da6a3ce929d0e0e4736-"
                "00f067aa0ba902b7-01"
            )
        }
    )

    assert trace_context == {
        "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
        "parent_span_id": "00f067aa0ba902b7",
    }


def test_extract_trace_context_returns_none_when_traceparent_missing(
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr("wind_langfuse.client.Langfuse", FakeLangfuse)
    client = create_test_client()

    assert client.extract_trace_context({"x-request-id": "req-1"}) is None


def test_extract_trace_context_returns_none_when_traceparent_invalid(
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr("wind_langfuse.client.Langfuse", FakeLangfuse)
    client = create_test_client()

    assert client.extract_trace_context({"traceparent": "invalid"}) is None


def test_inject_trace_context_writes_traceparent_from_current_context(
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr("wind_langfuse.client.Langfuse", FakeLangfuse)
    client = create_test_client()
    native_client = cast(FakeLangfuse, client.native_client)
    native_client.current_trace_id = "4bf92f3577b34da6a3ce929d0e0e4736"
    native_client.current_observation_id = "00f067aa0ba902b7"

    headers = client.inject_trace_context()

    assert headers == {
        "traceparent": (
            "00-4bf92f3577b34da6a3ce929d0e0e4736-"
            "00f067aa0ba902b7-01"
        )
    }


def test_inject_trace_context_preserves_headers_and_overwrites_traceparent(
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr("wind_langfuse.client.Langfuse", FakeLangfuse)
    client = create_test_client()
    native_client = cast(FakeLangfuse, client.native_client)
    native_client.current_trace_id = "4bf92f3577b34da6a3ce929d0e0e4736"
    native_client.current_observation_id = "00f067aa0ba902b7"

    headers = client.inject_trace_context(
        {
            "content-type": "application/json",
            "traceparent": "00-00000000000000000000000000000000-0000000000000000-00",
        }
    )

    assert headers == {
        "content-type": "application/json",
        "traceparent": (
            "00-4bf92f3577b34da6a3ce929d0e0e4736-"
            "00f067aa0ba902b7-01"
        ),
    }


def test_inject_trace_context_returns_headers_when_current_context_missing(
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr("wind_langfuse.client.Langfuse", FakeLangfuse)
    client = create_test_client()

    headers = client.inject_trace_context({"content-type": "application/json"})

    assert headers == {"content-type": "application/json"}
