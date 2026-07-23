"""
LLM client using LiteLLM with OpenAI-compatible protocol.
Supports streaming, non-streaming, retry with exponential backoff.
"""

import asyncio
import litellm
from typing import Optional, AsyncGenerator
from backend.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

# Configure LiteLLM globals
litellm.drop_params = True
litellm.telemetry = False

MAX_RETRIES = 3
RETRY_BASE_DELAY = 2.0  # seconds
TIMEOUT = 120.0  # seconds


def _resolve_model(model: str) -> str:
    """Auto-prefix model with 'openai/' if no provider prefix is given."""
    if "/" not in model:
        return f"openai/{model}"
    return model


def _build_kwargs(model: str, messages: list, tools: Optional[list] = None):
    kwargs = {
        "model": _resolve_model(model),
        "messages": messages,
        "api_key": LLM_API_KEY,
        "api_base": LLM_BASE_URL,
        "timeout": TIMEOUT,
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"
    return kwargs


async def chat_complete(
    messages: list,
    tools: Optional[list] = None,
    model: Optional[str] = None,
) -> dict:
    """Non-streaming chat completion with retry."""
    model = model or LLM_MODEL
    kwargs = _build_kwargs(model, messages, tools)

    for attempt in range(MAX_RETRIES):
        try:
            response = await litellm.acompletion(**kwargs)
            return response
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                raise
            delay = RETRY_BASE_DELAY * (2**attempt)
            await asyncio.sleep(delay)

    raise RuntimeError("Unexpected: all retries exhausted")


async def chat_stream(
    messages: list,
    tools: Optional[list] = None,
    model: Optional[str] = None,
) -> AsyncGenerator[dict, None]:
    """Streaming chat completion with retry."""
    model = model or LLM_MODEL
    kwargs = _build_kwargs(model, messages, tools)
    kwargs["stream"] = True

    for attempt in range(MAX_RETRIES):
        try:
            response = await litellm.acompletion(**kwargs)
            async for chunk in response:
                yield chunk
            return
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                raise
            delay = RETRY_BASE_DELAY * (2**attempt)
            await asyncio.sleep(delay)