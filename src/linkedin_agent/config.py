import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(path: Path | None = None) -> dict:
    with open(path or ROOT / "config" / "icps.toml", "rb") as f:
        return tomllib.load(f)
