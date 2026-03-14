from __future__ import annotations

import os
from pathlib import Path

_data_root: Path | None = None


def configure(data_root: Path) -> None:
    global _data_root
    _data_root = data_root
    os.environ["PPX_DATA_DIR"] = str(data_root)


def get_data_root() -> Path:
    if _data_root is not None:
        return _data_root
    env = os.environ.get("PPX_DATA_DIR")
    if env:
        return Path(env)
    raise RuntimeError("Data root not configured; call configure() or set PPX_DATA_DIR")
