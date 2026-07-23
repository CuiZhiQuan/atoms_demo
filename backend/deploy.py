"""
Deploy generated projects to Cloudflare Pages.
Uses Cloudflare REST API to create a Pages project and deploy static files.
Requires CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID environment variables.
"""

import os
import io
import re
import uuid
import zipfile
import httpx
from backend.config import PROJECTS_DIR, CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID

CLOUDFLARE_API = "https://api.cloudflare.com/client/v4"


async def deploy_to_cloudflare(project_id: str, project_name: str) -> dict:
    """Deploy a project's static files to Cloudflare Pages.

    Returns:
        dict with keys: url, project_name, deploy_id
    """
    if not CLOUDFLARE_API_TOKEN:
        raise ValueError(
            "CLOUDFLARE_API_TOKEN is not configured. "
            "Get one at https://dash.cloudflare.com/profile/api-tokens"
        )
    if not CLOUDFLARE_ACCOUNT_ID:
        raise ValueError(
            "CLOUDFLARE_ACCOUNT_ID is not configured. "
            "Find it at https://dash.cloudflare.com → select your account → copy Account ID"
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

    # Sanitize project name + random suffix to avoid collisions
    # Cloudflare Pages: 1-58 lowercase chars + dashes, no leading/trailing dash
    safe_name = re.sub(r'[^a-z0-9-]', '-', project_name.lower())  # replace non-[a-z0-9-] with dash
    safe_name = re.sub(r'-+', '-', safe_name)                      # collapse consecutive dashes
    safe_name = safe_name.strip('-')                                # remove leading/trailing dashes
    safe_name = safe_name[:51] or "atoms-app"                       # max 51 (leaving 7 for -{uuid})
    safe_name = f"{safe_name}-{uuid.uuid4().hex[:6]}"

    # Create zip in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for filepath, relpath in file_list:
            zf.write(filepath, relpath)
        # Inject Cloudflare Pages _headers for proper content types
        zf.writestr("_headers", """/*.html
  Content-Type: text/html; charset=utf-8
/*.css
  Content-Type: text/css; charset=utf-8
/*.js
  Content-Type: application/javascript; charset=utf-8
""")
        # Inject _redirects for SPA fallback (in case the generated app is an SPA)
        if not any(rel == "_redirects" for _, rel in file_list):
            zf.writestr("_redirects", "/*    /index.html   200")
    zip_buffer.seek(0)

    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Step 1: Create a Cloudflare Pages project
        resp = await client.post(
            f"{CLOUDFLARE_API}/accounts/{CLOUDFLARE_ACCOUNT_ID}/pages/projects",
            headers={**headers, "Content-Type": "application/json"},
            json={
                "name": safe_name,
                "production_branch": "main",
            },
        )

        if resp.status_code >= 400:
            detail = _extract_error(resp)
            raise Exception(f"Cloudflare API error ({resp.status_code}): {detail}")

        project_data = resp.json()
        cf_project_name = project_data["result"]["name"]

        # Step 2: Deploy via direct upload (multipart form)
        # Cloudflare Pages supports direct upload deployments
        zip_buffer.seek(0)
        resp = await client.post(
            f"{CLOUDFLARE_API}/accounts/{CLOUDFLARE_ACCOUNT_ID}/pages/projects/{cf_project_name}/deployments",
            headers={**headers},
            files={"file": ("deploy.zip", zip_buffer, "application/zip")},
        )

        if resp.status_code >= 400:
            detail = _extract_error(resp)
            raise Exception(f"Cloudflare deploy error ({resp.status_code}): {detail}")

        deploy_data = resp.json()
        result = deploy_data.get("result", {})
        deploy_url = result.get("url", "")
        if not deploy_url:
            subdomain = result.get("subdomain", cf_project_name)
            deploy_url = f"https://{subdomain}.pages.dev"

        return {
            "url": deploy_url,
            "project_name": cf_project_name,
            "deploy_id": result.get("id", ""),
            "ready_state": result.get("latest_stage", {}).get("name", "deploying"),
        }


async def get_deployment_status(deploy_id: str, project_name: str) -> dict:
    """Check the status of a Cloudflare Pages deploy."""
    if not CLOUDFLARE_API_TOKEN or not CLOUDFLARE_ACCOUNT_ID:
        raise ValueError("CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID are required")

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{CLOUDFLARE_API}/accounts/{CLOUDFLARE_ACCOUNT_ID}/pages/projects/{project_name}/deployments/{deploy_id}",
            headers={"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}"},
        )

        if resp.status_code >= 400:
            raise Exception(f"Cloudflare API error: {resp.text}")

        data = resp.json()
        result = data.get("result", {})
        deploy_url = result.get("url", "")
        if not deploy_url:
            subdomain = result.get("subdomain", project_name)
            deploy_url = f"https://{subdomain}.pages.dev"

        return {
            "url": deploy_url,
            "state": result.get("latest_stage", {}).get("status", "unknown"),
            "deploy_id": result.get("id", ""),
        }


def _extract_error(resp: httpx.Response) -> str:
    """Extract error message from Cloudflare API response."""
    try:
        body = resp.json()
        errors = body.get("errors", [])
        if errors:
            return errors[0].get("message", resp.text)
        return body.get("message", resp.text)
    except Exception:
        return resp.text