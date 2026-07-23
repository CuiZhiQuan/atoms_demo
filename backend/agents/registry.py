"""
Agent registry — manages agent instances and lookup.
"""

from typing import Optional
from backend.agents.base import Agent
from backend.agents.engineer import EngineerAgent
from backend.agents.pm import PMAgent
from backend.agents.architect import ArchitectAgent
from backend.agents.team_lead import TeamLeadAgent

_registry: dict[str, Agent] = {}


def _init_registry():
    """Initialize the agent registry."""
    global _registry
    if _registry:
        return

    agents = [
        TeamLeadAgent(),
        PMAgent(),
        ArchitectAgent(),
        EngineerAgent(),
    ]
    for agent in agents:
        _registry[agent.name] = agent


def get_agent(name: str) -> Optional[Agent]:
    """Get an agent by name."""
    _init_registry()
    return _registry.get(name)


def list_agents() -> list:
    """List all registered agents."""
    _init_registry()
    return list(_registry.values())


def get_agent_names() -> list:
    """Get all agent names."""
    _init_registry()
    return list(_registry.keys())