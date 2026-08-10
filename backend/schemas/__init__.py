"""
SEAM Backend Schemas Package

Common data contracts used by all six agents, the Supervisor/Orchestrator,
and the backend API. All schemas are Pydantic v2 models (except
WorkflowState, which is a TypedDict for LangGraph compatibility).

Usage:
    from backend.schemas import AgentInput, AgentOutput, Task, QAResult
"""

# Enumerations
from backend.schemas.enums import (
    AgentRole,
    AgentStatus,
    ArtifactType,
    FindingSeverity,
    QAVerdict,
    TaskStatus,
    TaskType,
    KnowledgeType,
)

# Core schemas
from backend.schemas.artifacts import Artifact
from backend.schemas.knowledge import KnowledgeChunk, KnowledgeContext, KnowledgeEntry
from backend.schemas.task import Task

# QA schemas
from backend.schemas.qa import QAFinding, QAResult, ReworkFeedback

# Agent I/O schemas
from backend.schemas.agent_io import AgentInput, AgentOutput

# Agent-specific output schemas
from backend.schemas.analysis import RequirementItem, RequirementSpec
from backend.schemas.planning import ComponentSpec, ProjectPlan

# Orchestration
from backend.schemas.workflow import WorkflowState

__all__ = [
    # Enums
    "AgentRole",
    "AgentStatus",
    "ArtifactType",
    "FindingSeverity",
    "QAVerdict",
    "TaskStatus",
    "TaskType",
    # Core
    "Artifact",
    "KnowledgeChunk",
    "KnowledgeContext",
    "Task",
    # QA
    "QAFinding",
    "QAResult",
    "ReworkFeedback",
    # Agent I/O
    "AgentInput",
    "AgentOutput",
    # Analysis
    "RequirementItem",
    "RequirementSpec",
    # Planning
    "ComponentSpec",
    "ProjectPlan",
    # Orchestration
    "WorkflowState",
]
