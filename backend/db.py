"""
SQLite database layer for project metadata persistence.
"""

import aiosqlite
from typing import Optional
from backend.config import DB_PATH


async def init_db():
    """Initialize the database schema."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                mode TEXT NOT NULL DEFAULT 'team',
                user_id TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                file_path TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS race_sessions (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                prompt TEXT NOT NULL,
                results TEXT DEFAULT '[]',
                selected_id TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        """)
        await db.commit()


async def create_project(id: str, name: str, mode: str, file_path: str, user_id: str = "") -> dict:
    """Create a new project record."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO projects (id, name, mode, file_path, user_id) VALUES (?, ?, ?, ?, ?)",
            (id, name, mode, file_path, user_id),
        )
        await db.commit()
    return {"id": id, "name": name, "mode": mode, "file_path": file_path, "user_id": user_id}


async def get_project(id: str) -> Optional[dict]:
    """Get a project by ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM projects WHERE id = ?", (id,))
        row = await cursor.fetchone()
        if row is None:
            return None
        return dict(row)


async def list_projects(user_id: Optional[str] = None) -> list[dict]:
    """List all projects, optionally filtered by user_id."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if user_id:
            cursor = await db.execute(
                "SELECT * FROM projects WHERE user_id = ? ORDER BY updated_at DESC",
                (user_id,),
            )
        else:
            cursor = await db.execute("SELECT * FROM projects ORDER BY updated_at DESC")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def update_project(id: str, **kwargs) -> Optional[dict]:
    """Update project metadata."""
    if not kwargs:
        return await get_project(id)

    set_clause = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [id]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"UPDATE projects SET {set_clause}, updated_at = datetime('now') WHERE id = ?",
            values,
        )
        await db.commit()
    return await get_project(id)


async def delete_project(id: str) -> bool:
    """Delete a project record."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("DELETE FROM projects WHERE id = ?", (id,))
        await db.commit()
        return cursor.rowcount > 0


async def create_race_session(id: str, project_id: str, prompt: str) -> dict:
    """Create a race session record."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO race_sessions (id, project_id, prompt) VALUES (?, ?, ?)",
            (id, project_id, prompt),
        )
        await db.commit()
    return {"id": id, "project_id": project_id, "prompt": prompt}


async def get_race_session(id: str) -> Optional[dict]:
    """Get race session by ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM race_sessions WHERE id = ?", (id,))
        row = await cursor.fetchone()
        if row is None:
            return None
        return dict(row)


async def update_race_session(id: str, **kwargs) -> Optional[dict]:
    """Update race session."""
    if not kwargs:
        return await get_race_session(id)

    set_clause = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [id]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE race_sessions SET {set_clause} WHERE id = ?", values)
        await db.commit()
    return await get_race_session(id)


# ── User CRUD ──────────────────────────────────────────────────────────────────

async def create_user(id: str, username: str, password_hash: str) -> dict:
    """Create a new user."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO users (id, username, password_hash) VALUES (?, ?, ?)",
            (id, username, password_hash),
        )
        await db.commit()
    return {"id": id, "username": username}


async def get_user_by_username(username: str) -> Optional[dict]:
    """Get user by username."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_user_by_id(id: str) -> Optional[dict]:
    """Get user by ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE id = ?", (id,))
        row = await cursor.fetchone()
        return dict(row) if row else None