"""
Tool definitions for Agents: file operations + shell commands.
Uses OpenAI function calling schema.
"""

import os
import asyncio
import subprocess
import shlex
from backend.config import PROJECTS_DIR

# Whitelist of allowed shell commands (prefix match)
SHELL_WHITELIST = ["npm", "npx", "node", "ls", "cat", "mkdir", "cd", "echo", "pwd"]

# Max shell execution timeout
SHELL_TIMEOUT = 60


def _resolve_path(project_id: str, path: str) -> str:
    """Resolve path relative to project directory, prevent path traversal."""
    project_dir = os.path.join(PROJECTS_DIR, project_id)
    os.makedirs(project_dir, exist_ok=True)

    # Normalize and check for traversal
    full_path = os.path.normpath(os.path.join(project_dir, path))
    if not full_path.startswith(os.path.normpath(project_dir)):
        raise PermissionError(f"Path traversal detected: {path}")
    return full_path


async def write_file(project_id: str, path: str, content: str) -> dict:
    """Write content to a file in the project directory."""
    full_path = _resolve_path(project_id, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    async with __import__("aiofiles").open(full_path, "w", encoding="utf-8") as f:
        await f.write(content)

    return {"status": "ok", "path": path, "size": len(content)}


async def read_file(project_id: str, path: str) -> dict:
    """Read a file from the project directory."""
    full_path = _resolve_path(project_id, path)
    if not os.path.exists(full_path):
        return {"status": "error", "message": f"File not found: {path}"}

    async with __import__("aiofiles").open(full_path, "r", encoding="utf-8") as f:
        content = await f.read()

    return {"status": "ok", "path": path, "content": content}


async def list_dir(project_id: str, path: str = ".") -> dict:
    """List files and directories in the project directory."""
    full_path = _resolve_path(project_id, path)
    if not os.path.exists(full_path):
        return {"status": "error", "message": f"Directory not found: {path}"}

    entries = []
    for entry in os.listdir(full_path):
        entry_path = os.path.join(full_path, entry)
        entries.append({
            "name": entry,
            "type": "directory" if os.path.isdir(entry_path) else "file",
        })

    return {"status": "ok", "path": path, "entries": entries}


async def run_shell(project_id: str, command: str, cwd: str = ".") -> dict:
    """Execute a shell command with whitelist and path restrictions."""
    # Parse command to check whitelist
    parts = shlex.split(command)
    if not parts:
        return {"status": "error", "message": "Empty command"}

    cmd_name = parts[0]
    if cmd_name not in SHELL_WHITELIST:
        return {
            "status": "error",
            "message": f"Command '{cmd_name}' not in whitelist. Allowed: {SHELL_WHITELIST}",
        }

    # Resolve working directory
    project_dir = os.path.join(PROJECTS_DIR, project_id)
    work_dir = os.path.normpath(os.path.join(project_dir, cwd))
    if not work_dir.startswith(os.path.normpath(project_dir)):
        return {"status": "error", "message": f"Path traversal in cwd: {cwd}"}

    try:
        process = await asyncio.create_subprocess_exec(
            *parts,
            cwd=work_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            process.communicate(), timeout=SHELL_TIMEOUT
        )
        return {
            "status": "ok",
            "command": command,
            "exit_code": process.returncode,
            "stdout": stdout.decode("utf-8", errors="replace")[:5000],
            "stderr": stderr.decode("utf-8", errors="replace")[:5000],
        }
    except asyncio.TimeoutError:
        return {"status": "error", "message": f"Command timed out after {SHELL_TIMEOUT}s"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_tool_definitions() -> list:
    """Return OpenAI function calling tool definitions."""
    return [
        {
            "type": "function",
            "function": {
                "name": "write_file",
                "description": "Write content to a file in the project. Use this to create or update code files.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Relative path to the file, e.g. 'index.html' or 'src/App.tsx'",
                        },
                        "content": {
                            "type": "string",
                            "description": "The full content to write to the file",
                        },
                    },
                    "required": ["path", "content"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read the contents of a file in the project.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Relative path to the file to read",
                        },
                    },
                    "required": ["path"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "list_dir",
                "description": "List files and directories in the project.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Relative path to list, defaults to '.' for root",
                        },
                    },
                    "required": ["path"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "run_shell",
                "description": "Execute a shell command. Only npm/npx/node/ls/cat/mkdir/cd/echo/pwd are allowed.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The shell command to execute, e.g. 'npm install'",
                        },
                        "cwd": {
                            "type": "string",
                            "description": "Working directory relative to project root, defaults to '.'",
                        },
                    },
                    "required": ["command"],
                },
            },
        },
    ]


async def execute_tool_call(project_id: str, tool_name: str, arguments: dict) -> dict:
    """Execute a tool call by name and return the result."""
    tool_map = {
        "write_file": write_file,
        "read_file": read_file,
        "list_dir": list_dir,
        "run_shell": run_shell,
    }

    fn = tool_map.get(tool_name)
    if not fn:
        return {"status": "error", "message": f"Unknown tool: {tool_name}"}

    return await fn(project_id, **arguments)