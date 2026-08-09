"""
SEAM Backend Schemas — Agent Input/Output

Standard data contracts accepted and returned by all agents via
BaseAgent.execute(). These are the primary communication schemas
between the Supervisor and worker agents.

Source: docs/04_agent_specifications.md §2, docs/09_data_models.md §2.3
Traceability: FR-1.2, FR-1.3
"""

from typing import Any

from pydantic import BaseModel, Field

from backend.schemas.enums import AgentRole, AgentStatus, TaskType
from backend.schemas.artifacts import Artifact
from backend.schemas.knowledge import KnowledgeContext
from backend.schemas.qa import ReworkFeedback


class AgentInput(BaseModel):
    """
    Standard input contract for all SEAM agents.

    Dispatched by the Supervisor/Orchestrator to a worker agent.
    Contains the task specification, contextual information, and
    optional rework feedback / pre-fetched knowledge.
    """

    task_id: str
    task_type: TaskType
    context: dict[str, Any]
    instructions: str = Field(..., min_length=1)
    dependencies: list[str] = []
    rework_feedback: ReworkFeedback | None = None
    knowledge_context: KnowledgeContext | None = None
    metadata: dict[str, Any] = {}


class AgentOutput(BaseModel):
    """
    Standard output contract returned by all SEAM agents.

    Returned to the Supervisor/Orchestrator after task execution.
    Contains results, generated artifacts, confidence score, and
    execution metrics.
    """

    task_id: str
    agent_id: AgentRole
    status: AgentStatus
    result: dict[str, Any]
    artifacts: list[Artifact] = []
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    feedback: str = ""
    execution_time_ms: int = Field(default=0, ge=0)
    metadata: dict[str, Any] = {}
