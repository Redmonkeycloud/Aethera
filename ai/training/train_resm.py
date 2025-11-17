"""Placeholder training script for RESM."""

from __future__ import annotations

from pathlib import Path

import yaml


def load_config(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main() -> None:
    config = load_config(Path(__file__).parent.parent / "config" / "resm_config.yaml")
    print("Loaded RESM config:", config)  # noqa: T201
    # TODO: implement actual training logic


if __name__ == "__main__":
    main()

