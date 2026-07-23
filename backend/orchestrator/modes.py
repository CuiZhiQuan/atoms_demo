"""
Orchestrator modes — Engineer, Team, and Race execution.
"""

import json
import asyncio
import uuid
from typing import AsyncGenerator, Optional
from backend.agents.registry import get_agent
from backend.orchestrator.runner import run_agent_react
from backend.sse import session_start, session_end, message_event, error_event, done_event
from backend.config import LLM_MODEL, LLM_RACE_MODELS
from backend.memory import load_messages, save_message
from backend.db import update_race_session


def _save_in_background(project_id: str, prompt: str, final_response: str):
    """Save conversation turn to history without blocking the SSE stream."""
    async def _save():
        try:
            await save_message(project_id, "user", prompt)
            if final_response:
                await save_message(project_id, "agent", final_response[:2000])
        except Exception:
            pass  # Never let history save failures affect the user
    asyncio.create_task(_save())


async def engineer_mode(
    prompt: str,
    project_id: str,
    session_id: str,
    model: Optional[str] = None,
) -> AsyncGenerator[dict, None]:
    """
    Engineer mode: single agent (Alex) directly generates code.
    Loads previous conversation history for cross-turn context.
    """
    # Send session_start IMMEDIATELY so the SSE connection is established
    # before any potentially slow I/O (like load_messages on cold disks)
    yield session_start(session_id, project_id, "engineer")
    yield message_event(f"🚀 Engineer Mode: Alex is coding...")

    # Load conversation history for context
    history = await load_messages(project_id, limit=20)

    agent = get_agent("engineer")
    final_response = ""
    async for event in run_agent_react(agent, prompt, project_id, model=model, history=history):
        if isinstance(event, str):
            final_response = event
        yield event  # Forward all events to keep SSE connection alive

    yield done_event(project_id)
    yield session_end(session_id)

    _save_in_background(project_id, prompt, final_response)


async def team_mode(
    prompt: str,
    project_id: str,
    session_id: str,
    model: Optional[str] = None,
) -> AsyncGenerator[dict, None]:
    """
    Team mode: 4-agent pipeline (team_lead → pm → architect → engineer).
    Loads previous conversation history for cross-turn context.
    """
    # Send session_start IMMEDIATELY so the SSE connection is established
    yield session_start(session_id, project_id, "team")
    yield message_event("🤝 Team Mode: 4 agents collaborating...")

    # Load conversation history for context
    history = await load_messages(project_id, limit=20)

    pipeline = ["team_lead", "pm", "architect", "engineer"]
    context = ""
    final_result = ""

    for agent_name in pipeline:
        agent = get_agent(agent_name)
        yield message_event(f"👤 {agent.role} is working...", agent_name)

        # Build agent-specific prompt
        if agent_name == "team_lead":
            task_prompt = f"Analyze this user requirement and create a task plan:\n{prompt}"
        elif agent_name == "pm":
            task_prompt = f"Based on the team lead's analysis, create a PRD for:\n{prompt}\n\nTeam Lead Analysis:\n{context}"
        elif agent_name == "architect":
            task_prompt = f"Based on the PRD, design the architecture:\n{context}"
        else:  # engineer
            task_prompt = f"Based on the architecture and PRD, implement the complete application:\n\nUser Request: {prompt}\n\nDesign Context:\n{context}"

        # Only pass history to the first agent to avoid redundancy
        agent_history = history if agent_name == "team_lead" else None
        async for event in run_agent_react(agent, task_prompt, project_id, context=context, model=model, history=agent_history):
            if isinstance(event, str):
                context = event
                if agent_name == "engineer":
                    final_result = event
            yield event  # Forward all events to keep SSE connection alive

    yield done_event(project_id)
    yield session_end(session_id)

    _save_in_background(project_id, prompt, final_result)


async def race_mode(
    prompt: str,
    project_id: str,
    session_id: str,
    race_id: str,
    model: Optional[str] = None,
) -> AsyncGenerator[dict, None]:
    """
    Race mode: parallel execution with multiple LLMs, user picks the best result.
    Loads previous conversation history for cross-turn context.
    """
    # Send session_start IMMEDIATELY so the SSE connection is established
    yield session_start(session_id, project_id, "race")
    yield message_event("🏁 Race Mode: 3 AI models competing...")

    # Load conversation history for context
    history = await load_messages(project_id, limit=20)

    # Determine race models
    race_models = [LLM_MODEL]
    if LLM_RACE_MODELS:
        extra = [m.strip() for m in LLM_RACE_MODELS.split(",") if m.strip()]
        race_models.extend(extra)
    race_models = race_models[:3]  # Max 3 lanes

    async def run_lane(lane_model: str, lane_idx: int):
        """Run one race lane and collect all events."""
        lane_events = []
        lane_project_id = f"{project_id}_race_{lane_idx}"
        agent = get_agent("engineer")

        async for event in run_agent_react(agent, prompt, lane_project_id, model=lane_model, history=history):
            if isinstance(event, str):
                lane_events.append({"type": "final_result", "content": event})
            else:
                lane_events.append(event)

        return {
            "lane_idx": lane_idx,
            "model": lane_model,
            "project_id": lane_project_id,
            "events": lane_events,
        }

    # Run all lanes in parallel
    yield message_event(f"🏃 Starting {len(race_models)} race lanes: {', '.join(race_models)}")

    tasks = [run_lane(model, i) for i, model in enumerate(race_models)]
    results = await asyncio.gather(*tasks)

    # Emit race results
    race_results = []
    for r in results:
        lane_events = r["events"]
        final_content = ""
        for evt in lane_events:
            if evt.get("type") == "final_result":
                final_content = evt["content"]
            elif evt.get("type") == "agent_thought":
                yield {
                    "type": "agent_thought",
                    "payload": {
                        "agent": f"race_lane_{r['lane_idx']}",
                        "model": r["model"],
                        "thought": evt["payload"]["thought"],
                    },
                    "timestamp": evt["timestamp"],
                }

        race_results.append({
            "lane_idx": r["lane_idx"],
            "model": r["model"],
            "project_id": r["project_id"],
            "summary": final_content[:200] if final_content else "",
            "full_content": final_content[:2000] if final_content else "",
        })

    yield {
        "type": "race_complete",
        "payload": {"race_id": race_id, "results": race_results},
        "timestamp": 0,
    }

    # Persist race results so select_race_result can access them
    await update_race_session(race_id, results=json.dumps(race_results))

    yield done_event(project_id)
    yield session_end(session_id)

    _save_in_background(project_id, prompt, "")