"""
Deploy generated projects to Vercel.
Uses Vercel REST API to create a deployment with static files.
Requires VERCEL_TOKEN environment variable.
"""

import os
import base64
import httpx
from backend.config import PROJECTS_DIR, VERCEL_TOKEN

VERCEL_API = "https://api.vercel.com"


async def deploy_to_vercel(project_id: str, project_name: str) -> dict:
    """Deploy a project's static files to Vercel.

    Returns:
        dict with keys: url, deployment_id, ready_state
    """
    if not VERCEL_TOKEN:
        raise ValueError("VERCEL_TOKEN is not configured. Add it to your environment variables.")

    project_dir = os.path.join(PROJECTS_DIR, project_id)
    if not os.path.isdir(project_dir):
        raise FileNotFoundError(f"Project directory not found: {project_dir}")

    # Collect all files and encode as base64
    files = []
    for root, _dirs, filenames in os.walk(project_dir):
        for filename in filenames:
            filepath = os.path.join(root, filename)
            relpath = os.path.relpath(filepath, project_dir)
            with open(filepath, "rb") as f:
                content = base64.b64encode(f.read()).decode()
            files.append({"file": relpath, "data": content})

    if not files:
        raise ValueError("Project has no files to deploy")

    # Sanitize project name for Vercel (lowercase, alphanumeric + hyphens)
    safe_name = "".join(c if c.isalnum() or c == "-" else "-" for c in project_name.lower())
    safe_name = safe_name.strip("-")[:64] or "atoms-app"

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Step 1: Create deployment
        resp = await client.post(
            f"{VERCEL_API}/v13/deployments",
            headers={
                "Authorization": f"Bearer {VERCEL_TOKEN}",
                "Content-Type": "application/json",
            },
            json={
                "name": safe_name,
                "files": files,
                "projectSettings": {"framework": None},
                "target": "production",
            },
        )

        if resp.status_code >= 400:
            detail = ""
            try:
                detail = resp.json().get("error", {}).get("message", resp.text)
            except Exception:
                detail = resp.text
            raise Exception(f"Vercel API error ({resp.status_code}): {detail}")

        data = resp.json()

        # Vercel returns the deployment with a URL (no need to wait for aliasing)
        vercel_url = data.get("url")
        if vercel_url and not vercel_url.startswith("http"):
            vercel_url = f"https://{vercel_url}"

        return {
            "url": vercel_url or f"https://{safe_name}.vercel.app",
            "deployment_id": data.get("id", ""),
            "ready_state": data.get("readyState", "READY"),
            "name": safe_name,
        }


async def get_deployment_status(deployment_id: str) -> dict:
    """Check the status of a Vercel deployment."""
    if not VERCEL_TOKEN:
        raise ValueError("VERCEL_TOKEN is not configured")

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{VERCEL_API}/v13/deployments/{deployment_id}",
            headers={"Authorization": f"Bearer {VERCEL_TOKEN}"},
        )

        if resp.status_code >= 400:
            raise Exception(f"Vercel API error: {resp.text}")

        data = resp.json()
        return {
            "url": f"https://{data['url']}" if not data["url"].startswith("http") else data["url"],
            "ready_state": data.get("readyState", "UNKNOWN"),
            "deployment_id": data["id"],
        }