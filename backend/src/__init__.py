"""Backend package for AETHERA."""

from importlib.metadata import version, PackageNotFoundError


def get_version() -> str:
    try:
        return version("aethera-backend")
    except PackageNotFoundError:
        return "0.0.0"


__all__ = ["get_version"]

