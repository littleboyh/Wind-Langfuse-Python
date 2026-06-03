from importlib.metadata import PackageNotFoundError, version

PACKAGE_NAME = "wind-langfuse-sdk"
DEFAULT_VERSION = "0.1.0"


def get_wind_sdk_version() -> str:
    try:
        return version(PACKAGE_NAME)
    except PackageNotFoundError:
        return DEFAULT_VERSION


__version__ = get_wind_sdk_version()

