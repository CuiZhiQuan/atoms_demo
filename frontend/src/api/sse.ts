/**
 * SSE client for streaming agent events from the backend.
 * All requests include the JWT token from localStorage.
 */

import { getToken } from '../store/authStore';

export interface SSEEvent {
  type: string;
  payload: Record<string, unknown>;
  timestamp: number;
}

// Dev: proxied by Vite to localhost:8000
// Prod: set VITE_API_URL in Vercel dashboard to https://your-backend.onrender.com
const API_BASE = (import.meta.env.VITE_API_URL || '') + '/api';

function authHeaders(): Record<string, string> {
  const token = getToken();
  return token
    ? { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }
    : { 'Content-Type': 'application/json' };
}

export async function runStream(
  prompt: string,
  mode: string,
  projectId: string | null,
  onEvent: (event: SSEEvent) => void,
  signal?: AbortSignal
): Promise<void> {
  const body = JSON.stringify({
    prompt,
    mode,
    project_id: projectId,
  });

  // Wake up Render (free tier sleeps after 15 min inactivity, cold start takes ~50s)
  try {
    await fetch(`${API_BASE}/health`, {
      method: 'GET',
      signal: AbortSignal.timeout(60000),
    });
  } catch {
    // Backend still waking up, but we've already triggered the wake-up cycle
  }

  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: authHeaders(),
    body,
    signal,
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error('No response body');

  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const event: SSEEvent = JSON.parse(line.slice(6));
          onEvent(event);
        } catch {
          // Skip malformed events
        }
      }
    }
  }
}

export async function fetchProjects(): Promise<Array<{
  id: string; name: string; mode: string; created_at: string; updated_at: string;
}>> {
  const res = await fetch(`${API_BASE}/projects`, { headers: authHeaders() });
  const data = await res.json();
  return data.projects || [];
}

export async function createProject(name: string, mode: string): Promise<{
  id: string; name: string; mode: string;
}> {
  const res = await fetch(`${API_BASE}/projects`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({ name, mode }),
  });
  const data = await res.json();
  return data.project;
}

export async function deleteProject(id: string): Promise<void> {
  await fetch(`${API_BASE}/projects/${id}`, {
    method: 'DELETE',
    headers: authHeaders(),
  });
}

export async function getRaceResults(raceId: string): Promise<unknown> {
  const res = await fetch(`${API_BASE}/race/${raceId}/results`, { headers: authHeaders() });
  return res.json();
}

export async function selectRaceResult(raceId: string, selectedIdx: number): Promise<unknown> {
  const res = await fetch(`${API_BASE}/race/${raceId}/select`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({ selected_idx: selectedIdx }),
  });
  return res.json();
}

// ── Auth API ────────────────────────────────────────────────────────────────────

export async function register(username: string, password: string): Promise<{
  user: { id: string; username: string }; token: string;
}> {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Registration failed');
  }
  return res.json();
}

export async function login(username: string, password: string): Promise<{
  user: { id: string; username: string }; token: string;
}> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Login failed');
  }
  return res.json();
}

export async function getMe(): Promise<{ user: { id: string; username: string } }> {
  const res = await fetch(`${API_BASE}/auth/me`, { headers: authHeaders() });
  if (!res.ok) throw new Error('Not authenticated');
  return res.json();
}

// ── Deploy ──────────────────────────────────────────────────────────────────────

export async function deployProject(projectId: string): Promise<{
  status: string; deployment: { url: string; deployment_id: string; ready_state: string; name: string };
}> {
  const res = await fetch(`${API_BASE}/projects/${projectId}/deploy`, {
    method: 'POST',
    headers: authHeaders(),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Deploy failed');
  }
  return res.json();
}

// ── Source Code ──────────────────────────────────────────────────────────────────

export interface ProjectFile {
  path: string;
  content: string;
  binary: boolean;
  size: number;
}

export async function fetchProjectFiles(projectId: string): Promise<ProjectFile[]> {
  const res = await fetch(`${API_BASE}/projects/${projectId}/files`, {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error('Failed to fetch project files');
  const data = await res.json();
  return data.files || [];
}