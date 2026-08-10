"""
SEAM Base Agent

Defines the common interface for all six SEAM agents.
"""

from abc import ABC, abstractmethod
from typing import Protocol

from backend.schemas import AgentInput, AgentOutput


class RAGService(Protocol):
    """
    Dummy protocol for RAGService dependency (to be implemented in later phases).
    """
    async def query_knowledge(self, query: str) -> list[dict]:
        ...


class BaseAgent(ABC):
    """
    Abstract base class for all SEAM agents.
    
    All agents must implement the execute() method to process AgentInput
    and return AgentOutput.
    """

    def __init__(self, agent_id: str, rag_service: RAGService | None = None):
        """
        Initialize the agent.

        Args:
            agent_id: The unique identifier/role of the agent.
            rag_service: Optional shared RAG infrastructure (implemented later).
        """
        self.agent_id = agent_id
        self.rag_service = rag_service

    @abstractmethod
    async def execute(self, input: AgentInput) -> AgentOutput:
        """
        Execute the agent's primary task.

        Args:
            input: Standard AgentInput contract containing context and instructions.

        Returns:
            Standard AgentOutput contract containing the results or failure feedback.
        """
        ...
