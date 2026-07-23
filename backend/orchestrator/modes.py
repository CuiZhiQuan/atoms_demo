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


async def engineer_mode(
    prompt: str,
    project_id: str,
    session_id: str,
    model: Optional[str] = None,
) -> AsyncGenerator[dict, None]:
    """
    Engineer mode: single agent (Alex) directly generates code.
    """
    yield session_start(session_id, project_id, "engineer")
    yield message_event(f"🚀 Engineer Mode: Alex is coding...")

    agent = get_agent("engineer")
    async for event in run_agent_react(agent, prompt, project_id, model=model):
        if isinstance(event, str):
            final_response = event
        else:
            yield event

    yield done_event(project_id)
    yield session_end(session_id)


async def team_mode(
    prompt: str,
    project_id: str,
    session_id: str,
    model: Optional[str] = None,
) -> AsyncGenerator[dict, None]:
    """
    Team mode: 4-agent pipeline (team_lead → pm → architect → engineer).
    """
    yield session_start(session_id, project_id, "team")
    yield message_event("🤝 Team Mode: 4 agents collaborating...")

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

        async for event in run_agent_react(agent, task_prompt, project_id, context=context, model=model):
            if isinstance(event, str):
                context = event
                if agent_name == "engineer":
                    final_result = event
            else:
                yield event

    yield done_event(project_id)
    yield session_end(session_id)


async def race_mode(
    prompt: str,
    project_id: str,
    session_id: str,
    race_id: str,
    model: Optional[str] = None,
) -> AsyncGenerator[dict, None]:
    """
    Race mode: parallel execution with multiple LLMs, user picks the best result.
    """
    yield session_start(session_id, project_id, "race")
    yield message_event("🏁 Race Mode: 3 AI models competing...")

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

        async for event in run_agent_react(agent, prompt, lane_project_id, model=lane_model):
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
        })

    yield {
        "type": "race_complete",
        "payload": {"race_id": race_id, "results": race_results},
        "timestamp": 0,
    }

    yield done_event(project_id)
    yield session_end(session_id)