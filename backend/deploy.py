"""
Deploy generated projects to Netlify.
Uses Netlify REST API to create a site and deploy static files.
Requires NETLIFY_TOKEN environment variable.
"""

import os
import io
import zipfile
import httpx
from backend.config import PROJECTS_DIR, NETLIFY_TOKEN

NETLIFY_API = "https://api.netlify.com/api/v1"


async def deploy_to_netlify(project_id: str, project_name: str) -> dict:
    """Deploy a project's static files to Netlify.

    Returns:
        dict with keys: url, site_id, deploy_id
    """
    if not NETLIFY_TOKEN:
        raise ValueError(
            "NETLIFY_TOKEN is not configured. "
            "Get one at https://app.netlify.com/user/applications/personal"
        )

    project_dir = os.path.join(PROJECTS_DIR, project_id)
    if not os.path.isdir(project_dir):
        raise FileNotFoundError(f"Project directory not found: {project_dir}")

    # Collect files
    file_list = []
    for root, _dirs, filenames in os.walk(project_dir):
        for filename in filenames:
            filepath = os.path.join(root, filename)
            relpath = os.path.relpath(filepath, project_dir)
            file_list.append((filepath, relpath))

    if not file_list:
        raise ValueError("Project has no files to deploy")

    # Sanitize project name
    safe_name = "".join(c if c.isalnum() or c == "-" else "-" for c in project_name.lower())
    safe_name = safe_name.strip("-")[:64] or "atoms-app"

    # Create zip in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for filepath, relpath in file_list:
            zf.write(filepath, relpath)
        # Inject Netlify config to ensure proper content types
        zf.writestr("netlify.toml", """
[[headers]]
  for = "/*.html"
  [headers.values]
    Content-Type = "text/html; charset=utf-8"
[[headers]]
  for = "/*.css"
  [headers.values]
    Content-Type = "text/css; charset=utf-8"
[[headers]]
  for = "/*.js"
  [headers.values]
    Content-Type = "application/javascript; charset=utf-8"
""")
    zip_buffer.seek(0)

    headers = {
        "Authorization": f"Bearer {NETLIFY_TOKEN}",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Step 1: Create a new site
        resp = await client.post(
            f"{NETLIFY_API}/sites",
            headers={**headers, "Content-Type": "application/json"},
            json={"name": safe_name},
        )

        if resp.status_code >= 400:
            detail = ""
            try:
                detail = resp.json().get("message", resp.text)
            except Exception:
                detail = resp.text
            raise Exception(f"Netlify API error ({resp.status_code}): {detail}")

        site_data = resp.json()
        site_id = site_data["id"]

        # Step 2: Deploy the zip file
        resp = await client.post(
            f"{NETLIFY_API}/sites/{site_id}/deploys",
            headers={
                **headers,
                "Content-Type": "application/zip",
            },
            content=zip_buffer.read(),
        )

        if resp.status_code >= 400:
            detail = ""
            try:
                detail = resp.json().get("message", resp.text)
            except Exception:
                detail = resp.text
            raise Exception(f"Netlify deploy error ({resp.status_code}): {detail}")

        deploy_data = resp.json()
        deploy_url = deploy_data.get("ssl_url") or deploy_data.get("url", "")
        if not deploy_url:
            deploy_url = f"https://{safe_name}.netlify.app"

        return {
            "url": deploy_url,
            "site_id": site_id,
            "deploy_id": deploy_data.get("id", ""),
            "name": safe_name,
        }


async def get_deployment_status(deploy_id: str) -> dict:
    """Check the status of a Netlify deploy."""
    if not NETLIFY_TOKEN:
        raise ValueError("NETLIFY_TOKEN is not configured")

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{NETLIFY_API}/deploys/{deploy_id}",
            headers={"Authorization": f"Bearer {NETLIFY_TOKEN}"},
        )

        if resp.status_code >= 400:
            raise Exception(f"Netlify API error: {resp.text}")

        data = resp.json()
        return {
            "url": data.get("ssl_url") or data.get("url", ""),
            "state": data.get("state", "unknown"),
            "deploy_id": data["id"],
        }