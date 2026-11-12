"""Bot sozlamalari. Barcha maxfiy qiymatlar .env faylidan o'qiladi."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _parse_ids(raw: str) -> set[int]:
    ids: set[int] = set()
    for chunk in raw.replace(";", ",").split(","):
        chunk = chunk.strip()
        if chunk.lstrip("-").isdigit():
            ids.add(int(chunk))
    return ids


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()
ADMIN_IDS: frozenset[int] = frozenset(_parse_ids(os.getenv("ADMIN_IDS", "")))

_db_path = Path(os.getenv("DB_PATH", "data/bot.db")).expanduser()
DB_PATH: Path = _db_path if _db_path.is_absolute() else BASE_DIR / _db_path

REQUEST_TIMEOUT: float = _env_float("REQUEST_TIMEOUT", 20.0)
BROADCAST_DELAY: float = _env_float("BROADCAST_DELAY", 0.05)
