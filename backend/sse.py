"""
SSE event protocol definitions and helpers.
"""

import json
import time
from typing import AsyncGenerator


def _event(type: str, payload: dict) -> str:
    """Format an SSE event as a JSON string."""
    return json.dumps({
        "type": type,
        "payload": payload,
        "timestamp": time.time(),
    }, ensure_ascii=False)


async def sse_event_stream(generator: AsyncGenerator) -> AsyncGenerator[str, None]:
    """Wrap an async generator of event dicts into SSE format."""
    async for event_data in generator:
        yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"


def session_start(session_id: str, project_id: str, mode: str):
    return _event("session_start", {"session_id": session_id, "project_id": project_id, "mode": mode})


def session_end(session_id: str):
    return _event("session_end", {"session_id": session_id})


def agent_start(agent_name: str, message: str = ""):
    return _event("agent_start", {"agent": agent_name, "message": message})


def agent_thought(agent_name: str, thought: str):
    return _event("agent_thought", {"agent": agent_name, "thought": thought})


def agent_end(agent_name: str, result: str = ""):
    return _event("agent_end", {"agent": agent_name, "result": result})


def tool_call(agent_name: str, tool_name: str, arguments: dict):
    return _event("tool_call", {"agent": agent_name, "tool": tool_name, "arguments": arguments})


def tool_result(agent_name: str, tool_name: str, result: dict):
    return _event("tool_result", {"agent": agent_name, "tool": tool_name, "result": result})


def file_created(path: str, size: int):
    return _event("file_created", {"path": path, "size": size})


def file_updated(path: str, size: int):
    return _event("file_updated", {"path": path, "size": size})


def message_event(text: str, agent_name: str = ""):
    return _event("message", {"text": text, "agent": agent_name})


def error_event(message: str, agent_name: str = ""):
    return _event("error", {"message": message, "agent": agent_name})


def done_event(project_id: str):
    return _event("done", {"project_id": project_id})