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

    def start_span(self, **kwargs: Any) -> FakeObservation:
        self.last_observation = FakeObservation(kwargs["name"])
        return self.last_observation

    def start_as_current_span(self, **kwargs: Any) -> FakeContextManager:
        self.last_observation = FakeObservation(kwargs["name"])
        return FakeContextManager(self.last_observation)

    def update_current_trace(self, **kwargs: Any) -> None:
        self.update_current_trace_kwargs = kwargs


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
