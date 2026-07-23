"""
Agent base class — defines the common interface for all agents.
"""

from abc import ABC, abstractmethod
from typing import Optional


class Agent(ABC):
    """Base agent class."""

    def __init__(self, name: str, role: str, system_prompt: str):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt

    @property
    @abstractmethod
    def tools(self) -> Optional[list]:
        """Return the tools available to this agent (OpenAI function calling schema)."""
        ...

    def get_system_message(self) -> dict:
        """Get the system message for LLM context."""
        return {"role": "system", "content": self.system_prompt}

    def description(self) -> str:
        return f"{self.name} ({self.role})"