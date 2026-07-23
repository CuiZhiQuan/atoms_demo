"""
Session memory: JSONL-based conversation history persistence.
"""

import json
import os
import aiofiles
from typing import Optional
from backend.config import PROJECTS_DIR


def _session_path(project_id: str) -> str:
    """Get the session file path for a project."""
    atoms_dir = os.path.join(PROJECTS_DIR, project_id, ".atoms")
    os.makedirs(atoms_dir, exist_ok=True)
    return os.path.join(atoms_dir, "session.jsonl")


async def save_message(project_id: str, role: str, content: str, metadata: Optional[dict] = None):
    """Append a message to the session JSONL file."""
    entry = {
        "role": role,
        "content": content,
        "metadata": metadata or {},
    }
    async with aiofiles.open(_session_path(project_id), "a", encoding="utf-8") as f:
        await f.write(json.dumps(entry, ensure_ascii=False) + "\n")


async def load_messages(project_id: str, limit: int = 50) -> list[dict]:
    """Load the most recent messages from the session JSONL file."""
    path = _session_path(project_id)
    if not os.path.exists(path):
        return []

    messages = []
    async with aiofiles.open(path, "r", encoding="utf-8") as f:
        async for line in f:
            line = line.strip()
            if line:
                try:
                    messages.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    return messages[-limit:]


async def clear_session(project_id: str):
    """Clear the session file for a project."""
    path = _session_path(project_id)
    if os.path.exists(path):
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write("")