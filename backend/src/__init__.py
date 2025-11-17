"""Backend package for AETHERA."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version


def get_version() -> str:
    try:
        return version("aethera-backend")
    except PackageNotFoundError:
        return "0.0.0"


__all__ = ["get_version"]

