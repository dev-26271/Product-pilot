import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Type
from backend.workspace_context import WorkspaceContext

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Abstract Base Class for all specialized agents in the ProductPilot ecosystem."""
    
    @abstractmethod
    def execute(self, context: WorkspaceContext, **kwargs) -> WorkspaceContext:
        """Executes the agent's logic on the workspace context, returning an updated context.
        
        Adheres to immutability: returns a NEW WorkspaceContext instance.
        """
        pass


class AgentRegistry:
    """Production-grade registry holding instances of all registered BaseAgent subclasses."""
    
    def __init__(self):
        self._registry: Dict[str, BaseAgent] = {}

    def register(self, name: str, agent: BaseAgent) -> None:
        """Registers an agent instance under a unique identifier string."""
        if name in self._registry:
            logger.warning(f"Agent '{name}' is already registered. Overwriting...")
        self._registry[name] = agent
        logger.info(f"Registered agent: '{name}' ({agent.__class__.__name__})")

    def get(self, name: str) -> BaseAgent:
        """Retrieves a registered agent instance. Raises ValueError if not found."""
        if name not in self._registry:
            raise ValueError(f"Agent '{name}' is not registered in the agent registry.")
        return self._registry[name]

    def list_agents(self) -> Dict[str, str]:
        """Returns a mapping of registered agent keys to their class names."""
        return {k: v.__class__.__name__ for k, v in self._registry.items()}


# Global registry singleton
registry = AgentRegistry()
