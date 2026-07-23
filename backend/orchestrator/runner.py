"""
Orchestrator — ReAct loop runner for a single agent execution.
"""

import json
import uuid
import asyncio
from typing import AsyncGenerator, Optional
from backend.llm import chat_complete, chat_stream
from backend.tools import execute_tool_call, get_tool_definitions
from backend.agents.base import Agent
from backend.sse import (
    agent_start, agent_thought, agent_end,
    tool_call as sse_tool_call, tool_result as sse_tool_result,
    file_created, file_updated, message_event, error_event,
)

MAX_STEPS = 15


async def run_agent_react(
    agent: Agent,
    user_message: str,
    project_id: str,
    context: str = "",
    model: Optional[str] = None,
    history: Optional[list[dict]] = None,
) -> AsyncGenerator[dict, None]:
    """
    Run the ReAct loop for a single agent.
    Yields SSE event dicts as the agent thinks and acts.

    Args:
        history: previous conversation messages from session.jsonl,
                 used to provide cross-turn context to the LLM.
    """
    yield agent_start(agent.name, f"Starting {agent.role}...")

    # Build messages
    messages = [agent.get_system_message()]

    # Inject previous conversation history (cross-turn memory)
    if history:
        for msg in history:
            role = msg.get("role", "")
            if role == "user":
                messages.append({"role": "user", "content": msg["content"]})
            elif role == "agent":
                messages.append({"role": "assistant", "content": msg["content"]})
            # Skip system messages — they're informational, not useful as context

    if context:
        messages.append({"role": "user", "content": f"Context from previous steps:\n{context}\n\nNow, please work on the following task:\n{user_message}"})
    else:
        messages.append({"role": "user", "content": user_message})

    tools = agent.tools
    final_response = ""

    for step in range(MAX_STEPS):
        try:
            # Stream LLM response
            content_parts = []
            tool_calls_buffer: list = []
            current_tool_call = None

            async for chunk in chat_stream(messages, tools, model):
                delta = chunk.get("choices", [{}])[0].get("delta", {})

                # Handle text content
                if "content" in delta and delta["content"]:
                    content_parts.append(delta["content"])
                    yield agent_thought(agent.name, delta["content"])

                # Handle tool calls
                if "tool_calls" in delta and delta["tool_calls"]:
                    for tc in delta["tool_calls"]:
                        idx = tc.get("index", 0)
                        # Ensure buffer has enough slots
                        while len(tool_calls_buffer) <= idx:
                            tool_calls_buffer.append({
                                "id": "", "function": {"name": "", "arguments": ""}
                            })

                        if "id" in tc and tc["id"]:
                            tool_calls_buffer[idx]["id"] = tc["id"]
                        if "function" in tc:
                            if "name" in tc["function"] and tc["function"]["name"]:
                                tool_calls_buffer[idx]["function"]["name"] = tc["function"]["name"]
                            if "arguments" in tc["function"]:
                                tool_calls_buffer[idx]["function"]["arguments"] += tc["function"]["arguments"]

            content = "".join(content_parts)

            # If no tool calls, agent is done
            if not tool_calls_buffer:
                final_response = content
                break

            # Execute tool calls
            # Ensure each tool call has an id (fallback for streams that don't provide one)
            for tc in tool_calls_buffer:
                if not tc["id"]:
                    tc["id"] = f"call_{uuid.uuid4().hex[:12]}"

            assistant_msg = {"role": "assistant", "content": content or None}
            if tool_calls_buffer:
                assistant_msg["tool_calls"] = tool_calls_buffer

            messages.append(assistant_msg)

            for tc in tool_calls_buffer:
                fn_name = tc["function"]["name"]
                try:
                    fn_args = json.loads(tc["function"]["arguments"])
                except json.JSONDecodeError:
                    fn_args = {}

                yield sse_tool_call(agent.name, fn_name, fn_args)

                result = await execute_tool_call(project_id, fn_name, fn_args)
                yield sse_tool_result(agent.name, fn_name, result)

                # Emit file events
                if fn_name == "write_file" and result.get("status") == "ok":
                    yield file_created(result["path"], result["size"])
                elif fn_name == "write_file" and result.get("status") != "ok":
                    yield file_updated(result["path"], result.get("size", 0))

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": json.dumps(result, ensure_ascii=False),
                })

        except Exception as e:
            yield error_event(str(e), agent.name)
            break

    yield agent_end(agent.name, final_response)
    yield final_response