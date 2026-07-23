"""
API routes — SSE streaming endpoint + project CRUD + race management + auth.
"""

import json
import uuid
import os
import shutil
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.sse import sse_event_stream, error_event
from backend.orchestrator.modes import engineer_mode, team_mode, race_mode
from backend.db import (
    create_project, get_project, list_projects, delete_project,
    create_race_session, get_race_session, update_race_session,
    create_user, get_user_by_username, get_user_by_id,
)
from backend.config import PROJECTS_DIR
from backend.auth import hash_password, verify_password, create_token, get_current_user
from backend.deploy import deploy_to_cloudflare
from backend.memory import save_message

router = APIRouter(prefix="/api")


# ── Request Models ──────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    prompt: str
    mode: str = "engineer"  # engineer | team | race
    project_id: Optional[str] = None


class CreateProjectRequest(BaseModel):
    name: str
    mode: str = "engineer"


class SelectRaceRequest(BaseModel):
    selected_idx: int


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


# ── Auth Routes ─────────────────────────────────────────────────────────────────

@router.post("/auth/register")
async def register(req: RegisterRequest):
    """Register a new user account."""
    if len(req.username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    existing = await get_user_by_username(req.username)
    if existing:
        raise HTTPException(status_code=409, detail="Username already exists")

    user_id = str(uuid.uuid4())
    password_hash = hash_password(req.password)
    user = await create_user(user_id, req.username, password_hash)
    token = create_token(user_id)

    return {"user": user, "token": token}


@router.post("/auth/login")
async def login(req: LoginRequest):
    """Login and receive a JWT token."""
    user = await get_user_by_username(req.username)
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_token(user["id"])
    return {
        "user": {"id": user["id"], "username": user["username"]},
        "token": token,
    }


@router.get("/auth/me")
async def me(user_id: str = Depends(get_current_user)):
    """Get current user info from token."""
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user": {"id": user["id"], "username": user["username"]}}


# ── Chat (SSE) ──────────────────────────────────────────────────────────────────

@router.post("/chat")
async def chat(req: ChatRequest, request: Request, user_id: str = Depends(get_current_user)):
    """SSE streaming endpoint for agent chat."""
    mode = req.mode
    if mode not in ("engineer", "team", "race"):
        raise HTTPException(status_code=400, detail=f"Invalid mode: {mode}")

    # Create or get project
    project_id = req.project_id
    if not project_id:
        project_id = str(uuid.uuid4())
        project_name = req.prompt[:50].strip()
        file_path = os.path.join(PROJECTS_DIR, project_id)
        os.makedirs(file_path, exist_ok=True)
        await create_project(project_id, project_name, mode, file_path, user_id)

    session_id = str(uuid.uuid4())

    async def event_generator():
        try:
            if mode == "engineer":
                gen = engineer_mode(req.prompt, project_id, session_id)
            elif mode == "team":
                gen = team_mode(req.prompt, project_id, session_id)
            else:  # race
                race_id = str(uuid.uuid4())
                await create_race_session(race_id, project_id, req.prompt)
                gen = race_mode(req.prompt, project_id, session_id, race_id)

            async for event in gen:
                # Check for client disconnect
                if await request.is_disconnected():
                    break
                yield f"data: {event}\n\n"
        except Exception as e:
            yield f"data: {error_event(str(e))}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── Projects ────────────────────────────────────────────────────────────────────

@router.get("/projects")
async def get_projects(user_id: str = Depends(get_current_user)):
    """List projects for the current user."""
    projects = await list_projects(user_id)
    return {"projects": projects}


@router.post("/projects")
async def create_new_project(req: CreateProjectRequest, user_id: str = Depends(get_current_user)):
    """Create a new project."""
    project_id = str(uuid.uuid4())
    file_path = os.path.join(PROJECTS_DIR, project_id)
    os.makedirs(file_path, exist_ok=True)
    project = await create_project(project_id, req.name, req.mode, file_path, user_id)
    return {"project": project}


@router.delete("/projects/{project_id}")
async def delete_existing_project(project_id: str, user_id: str = Depends(get_current_user)):
    """Delete a project and its files."""
    project = await get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Only allow deletion of own projects
    if project.get("user_id") and project["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this project")

    # Delete files
    file_path = project.get("file_path", "")
    if file_path and os.path.exists(file_path):
        shutil.rmtree(file_path, ignore_errors=True)

    await delete_project(project_id)
    return {"status": "ok"}


# ── Race ────────────────────────────────────────────────────────────────────────

@router.get("/race/{race_id}/results")
async def get_race_results(race_id: str, user_id: str = Depends(get_current_user)):
    """Get race session results."""
    session = await get_race_session(race_id)
    if not session:
        raise HTTPException(status_code=404, detail="Race session not found")
    return {"race": session}


@router.post("/race/{race_id}/select")
async def select_race_result(race_id: str, req: SelectRaceRequest, user_id: str = Depends(get_current_user)):
    """Select a race result and clean up others."""
    session = await get_race_session(race_id)
    if not session:
        raise HTTPException(status_code=404, detail="Race session not found")

    results = json.loads(session.get("results", "[]"))
    selected = None
    for r in results:
        if r.get("lane_idx") == req.selected_idx:
            selected = r
            # Update project_id to the selected result
            project_id = session["project_id"]
            file_path = os.path.join(PROJECTS_DIR, project_id)
            src_path = os.path.join(PROJECTS_DIR, r["project_id"])
            if os.path.exists(src_path):
                # Move selected files to main project
                if os.path.exists(file_path):
                    shutil.rmtree(file_path, ignore_errors=True)
                shutil.move(src_path, file_path)
            break

    # Clean up unselected race projects
    for r in results:
        if r.get("lane_idx") != req.selected_idx:
            race_path = os.path.join(PROJECTS_DIR, r["project_id"])
            if os.path.exists(race_path):
                shutil.rmtree(race_path, ignore_errors=True)

    await update_race_session(race_id, selected_id=str(req.selected_idx))

    # Save the selected agent response to conversation history
    if selected and selected.get("full_content"):
        await save_message(session["project_id"], "agent", selected["full_content"])

    return {"status": "ok", "selected": selected}


# ── Deploy ──────────────────────────────────────────────────────────────────────

@router.post("/projects/{project_id}/deploy")
async def deploy_project(project_id: str, user_id: str = Depends(get_current_user)):
    """Deploy a project's generated app to Cloudflare Pages."""
    project = await get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.get("user_id") and project["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        result = await deploy_to_cloudflare(project_id, project["name"])
        return {"status": "ok", "deployment": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deploy failed: {str(e)}")


@router.get("/projects/{project_id}/deploy")
async def get_deploy_status(project_id: str, user_id: str = Depends(get_current_user)):
    """Get deployment status for a project (placeholder for future use)."""
    project = await get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"status": "ok", "deployment": None}


# ── Source Code ──────────────────────────────────────────────────────────────────

@router.get("/projects/{project_id}/files")
async def get_project_files(
    project_id: str,
    path: str = "",
    user_id: str = Depends(get_current_user),
):
    """Get source files of a project. Returns file tree + contents."""
    project = await get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.get("user_id") and project["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    project_dir = project.get("file_path", "")
    if not project_dir or not os.path.isdir(project_dir):
        raise HTTPException(status_code=404, detail="Project files not found")

    # If path is specified, return content of a single file
    if path:
        full_path = os.path.normpath(os.path.join(project_dir, path))
        # Security: ensure path is within project directory
        if not full_path.startswith(os.path.normpath(project_dir)):
            raise HTTPException(status_code=403, detail="Path traversal not allowed")
        if not os.path.isfile(full_path):
            raise HTTPException(status_code=404, detail=f"File not found: {path}")
        try:
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            return {"path": path, "content": content}
        except Exception:
            # Binary file — return base64
            import base64
            with open(full_path, "rb") as f:
                content = base64.b64encode(f.read()).decode()
            return {"path": path, "content": content, "binary": True}

    # Otherwise, return the file tree with contents
    files = []
    for root, _dirs, filenames in os.walk(project_dir):
        for filename in filenames:
            filepath = os.path.join(root, filename)
            relpath = os.path.relpath(filepath, project_dir)
            try:
                with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                binary = False
            except Exception:
                content = "[binary file]"
                binary = True
            files.append({
                "path": relpath,
                "content": content,
                "binary": binary,
                "size": os.path.getsize(filepath),
            })

    return {"files": files}