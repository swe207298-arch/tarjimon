"""SQLite ma'lumotlar bazasi bilan ishlash."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import aiosqlite

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id         INTEGER PRIMARY KEY,
    username   TEXT,
    full_name  TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS translations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    text        TEXT NOT NULL,
    source_lang TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_translations_user ON translations(user_id);
CREATE INDEX IF NOT EXISTS idx_translations_created ON translations(created_at);

CREATE TABLE IF NOT EXISTS channels (
    chat_id     INTEGER PRIMARY KEY,
    title       TEXT NOT NULL,
    username    TEXT,
    invite_link TEXT,
    added_by    INTEGER,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._conn: aiosqlite.Connection | None = None
        self._lock = asyncio.Lock()

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("Ma'lumotlar bazasi hali ulanmagan")
        return self._conn

    async def connect(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self.path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA journal_mode=WAL")
        await self._conn.executescript(SCHEMA)
        await self._conn.commit()

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    async def _scalar(self, query: str, params: tuple[Any, ...] = ()) -> int:
        async with self._lock:
            cursor = await self.conn.execute(query, params)
            row = await cursor.fetchone()
            await cursor.close()
        return int(row[0]) if row else 0

    # ------------------------------------------------------------------ users

    async def add_user(self, user_id: int, username: str | None, full_name: str | None) -> None:
        async with self._lock:
            await self.conn.execute(
                """
                INSERT INTO users (id, username, full_name) VALUES (?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    username = excluded.username,
                    full_name = excluded.full_name
                """,
                (user_id, username, full_name),
            )
            await self.conn.commit()

    async def count_users(self) -> int:
        return await self._scalar("SELECT COUNT(*) FROM users")

    async def count_new_users_today(self) -> int:
        return await self._scalar("SELECT COUNT(*) FROM users WHERE date(created_at) = date('now')")

    async def all_user_ids(self) -> list[int]:
        async with self._lock:
            cursor = await self.conn.execute("SELECT id FROM users")
            rows = await cursor.fetchall()
            await cursor.close()
        return [int(row["id"]) for row in rows]

    # ----------------------------------------------------------- translations

    async def save_text(self, user_id: int, text: str, source_lang: str | None) -> int:
        """Matnni vaqtincha saqlaydi (2 kun) va uning ID sini qaytaradi."""
        async with self._lock:
            cursor = await self.conn.execute(
                "INSERT INTO translations (user_id, text, source_lang) VALUES (?, ?, ?)",
                (user_id, text, source_lang),
            )
            text_id = int(cursor.lastrowid or 0)
            await self.conn.execute(
                "DELETE FROM translations WHERE created_at < datetime('now', '-2 days')"
            )
            await self.conn.commit()
            await cursor.close()
        return text_id

    async def get_text(self, text_id: int) -> dict[str, Any] | None:
        async with self._lock:
            cursor = await self.conn.execute(
                "SELECT * FROM translations WHERE id = ?", (text_id,)
            )
            row = await cursor.fetchone()
            await cursor.close()
        return dict(row) if row else None

    async def count_translations(self) -> int:
        return await self._scalar("SELECT COUNT(*) FROM translations")

    # --------------------------------------------------------------- channels

    async def add_channel(
        self,
        chat_id: int,
        title: str,
        username: str | None,
        invite_link: str | None,
        added_by: int | None = None,
    ) -> None:
        async with self._lock:
            await self.conn.execute(
                """
                INSERT INTO channels (chat_id, title, username, invite_link, added_by)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(chat_id) DO UPDATE SET
                    title = excluded.title,
                    username = excluded.username,
                    invite_link = excluded.invite_link,
                    added_by = excluded.added_by
                """,
                (chat_id, title, username, invite_link, added_by),
            )
            await self.conn.commit()

    async def get_channels(self) -> list[dict[str, Any]]:
        async with self._lock:
            cursor = await self.conn.execute("SELECT * FROM channels ORDER BY created_at")
            rows = await cursor.fetchall()
            await cursor.close()
        return [dict(row) for row in rows]

    async def delete_channel(self, chat_id: int) -> None:
        async with self._lock:
            await self.conn.execute("DELETE FROM channels WHERE chat_id = ?", (chat_id,))
            await self.conn.commit()
