import socket
from types import TracebackType
from typing import Any, Dict, Optional, Type

from langfuse import Langfuse
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

from wind_langfuse._version import __version__

WIND_SDK_LANGUAGE = "python"
WIND_SDK_NAME = "wind-langfuse-sdk"


class WindLangfuse:
    """Thin Wind wrapper around the Langfuse Python SDK."""

    def __init__(
        self,
        *,
        product_name: str,
        app_name: str,
        app_class_id: str,
        version: str,
        environment: str,
        tracer_provider: Optional[TracerProvider] = None,
        sample_rate: Optional[float] = None,
        **langfuse_kwargs: Any,
    ) -> None:
        self.product_name = product_name
        self.app_name = app_name
        self.app_class_id = app_class_id
        self.version = version
        self.environment = environment
        self._observation_attributes = {
            "service.product.name": product_name,
            "service.name": app_name,
            "wind.app.class_id": app_class_id,
            "wind.app.version": version,
            "wind.app.environment": environment,
        }

        if tracer_provider is None:
            tracer_provider = self._create_tracer_provider(sample_rate=sample_rate)

        self._client = Langfuse(
            environment=environment,
            release=version,
            tracer_provider=tracer_provider,
            sample_rate=sample_rate,
            **langfuse_kwargs,
        )

    def start_observation(self, **kwargs: Any) -> "WindObservation":
        kwargs["name"] = self._format_observation_name(kwargs["name"])
        return self._wrap_observation(self._client.start_observation(**kwargs))

    def start_as_current_observation(self, **kwargs: Any) -> "WindContextManager":
        kwargs["name"] = self._format_observation_name(kwargs["name"])
        return WindContextManager(
            self._client.start_as_current_observation(**kwargs),
            owner=self,
        )

    def start_span(self, **kwargs: Any) -> "WindObservation":
        kwargs["name"] = self._format_observation_name(kwargs["name"])
        return self._wrap_observation(self._client.start_span(**kwargs))

    def start_as_current_span(self, **kwargs: Any) -> "WindContextManager":
        kwargs["name"] = self._format_observation_name(kwargs["name"])
        return WindContextManager(self._client.start_as_current_span(**kwargs), owner=self)

    def start_generation(self, **kwargs: Any) -> "WindObservation":
        kwargs["name"] = self._format_observation_name(kwargs["name"])
        return self._wrap_observation(self._client.start_generation(**kwargs))

    def start_as_current_generation(self, **kwargs: Any) -> "WindContextManager":
        kwargs["name"] = self._format_observation_name(kwargs["name"])
        return WindContextManager(
            self._client.start_as_current_generation(**kwargs),
            owner=self,
        )

    def create_event(self, **kwargs: Any) -> "WindObservation":
        kwargs["name"] = self._format_observation_name(kwargs["name"])
        return self._wrap_observation(self._client.create_event(**kwargs))

    def update_current_trace(self, **kwargs: Any) -> Any:
        kwargs.pop("name", None)
        return self._client.update_current_trace(**kwargs)

    def flush(self) -> Any:
        return self._client.flush()

    def shutdown(self) -> Any:
        return self._client.shutdown()

    def auth_check(self) -> Any:
        return self._client.auth_check()

    @property
    def api(self) -> Any:
        return self._client.api

    @property
    def async_api(self) -> Any:
        return self._client.async_api

    @property
    def native_client(self) -> Langfuse:
        return self._client

    def _wrap_observation(self, observation: Any) -> "WindObservation":
        wrapped = WindObservation(observation=observation, owner=self)
        wrapped._apply_wind_attributes()
        return wrapped

    def _format_observation_name(self, name: str) -> str:
        prefix = f"{self.app_name}:"
        if name.startswith(prefix):
            return name

        return f"{prefix}{name}"

    def _create_tracer_provider(
        self, *, sample_rate: Optional[float]
    ) -> TracerProvider:
        sampler = (
            TraceIdRatioBased(sample_rate)
            if sample_rate is not None and sample_rate < 1
            else None
        )

        return TracerProvider(
            resource=Resource.create(self._resource_attributes()),
            sampler=sampler,
        )

    def _resource_attributes(self) -> Dict[str, str]:
        return {
            "resource.host.ip": _get_host_ip(),
            "resource.host.name": socket.gethostname(),
            "service.product.name": self.product_name,
            "service.name": self.app_name,
            "wind.sdk.language": WIND_SDK_LANGUAGE,
            "wind.sdk.name": WIND_SDK_NAME,
            "wind.sdk.version": __version__,
        }

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)


class WindObservation:
    """Wrapper for Langfuse observations returned by WindLangfuse."""

    def __init__(self, *, observation: Any, owner: WindLangfuse) -> None:
        self._observation = observation
        self._owner = owner

    def start_observation(self, **kwargs: Any) -> "WindObservation":
        kwargs["name"] = self._owner._format_observation_name(kwargs["name"])
        return self._owner._wrap_observation(self._observation.start_observation(**kwargs))

    def start_as_current_observation(self, **kwargs: Any) -> "WindContextManager":
        kwargs["name"] = self._owner._format_observation_name(kwargs["name"])
        return WindContextManager(
            self._observation.start_as_current_observation(**kwargs),
            owner=self._owner,
        )

    def start_span(self, **kwargs: Any) -> "WindObservation":
        kwargs["name"] = self._owner._format_observation_name(kwargs["name"])
        return self._owner._wrap_observation(self._observation.start_span(**kwargs))

    def start_as_current_span(self, **kwargs: Any) -> "WindContextManager":
        kwargs["name"] = self._owner._format_observation_name(kwargs["name"])
        return WindContextManager(
            self._observation.start_as_current_span(**kwargs),
            owner=self._owner,
        )

    def start_generation(self, **kwargs: Any) -> "WindObservation":
        kwargs["name"] = self._owner._format_observation_name(kwargs["name"])
        return self._owner._wrap_observation(self._observation.start_generation(**kwargs))

    def start_as_current_generation(self, **kwargs: Any) -> "WindContextManager":
        kwargs["name"] = self._owner._format_observation_name(kwargs["name"])
        return WindContextManager(
            self._observation.start_as_current_generation(**kwargs),
            owner=self._owner,
        )

    def create_event(self, **kwargs: Any) -> "WindObservation":
        kwargs["name"] = self._owner._format_observation_name(kwargs["name"])
        return self._owner._wrap_observation(self._observation.create_event(**kwargs))

    def update(self, **kwargs: Any) -> Any:
        if kwargs.get("name") is not None:
            kwargs["name"] = self._owner._format_observation_name(kwargs["name"])

        result = self._observation.update(**kwargs)
        self._apply_wind_attributes()

        return self if result is self._observation else result

    def update_trace(self, **kwargs: Any) -> Any:
        kwargs.pop("name", None)
        return self._observation.update_trace(**kwargs)

    def end(self, **kwargs: Any) -> "WindObservation":
        self._observation.end(**kwargs)
        return self

    @property
    def native_observation(self) -> Any:
        return self._observation

    def _apply_wind_attributes(self) -> None:
        otel_span = getattr(self._observation, "_otel_span", None)
        if otel_span is None:
            return

        otel_span.set_attributes(self._owner._observation_attributes)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._observation, name)


class WindContextManager:
    def __init__(self, native_context_manager: Any, *, owner: WindLangfuse) -> None:
        self._native_context_manager = native_context_manager
        self._owner = owner
        self._wrapped_observation: Optional[WindObservation] = None

    def __enter__(self) -> WindObservation:
        observation = self._native_context_manager.__enter__()
        self._wrapped_observation = self._owner._wrap_observation(observation)

        return self._wrapped_observation

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Any:
        return self._native_context_manager.__exit__(exc_type, exc_value, traceback)


def _get_host_ip() -> str:
    try:
        return socket.gethostbyname(socket.gethostname())
    except OSError:
        return "127.0.0.1"
