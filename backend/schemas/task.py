"""
SEAM Backend Schemas — Task

A discrete unit of work assigned by the Supervisor to an agent.
Tracks status, dependencies, assignment, and quality metrics.

Source: docs/09_data_models.md §2.2
Traceability: FR-2.1, FR-2.2
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from backend.schemas.enums import AgentRole, TaskStatus, TaskType


class Task(BaseModel):
    """
    A task within the SEAM workflow.

    Tasks are created by the Planning & Design Agent, managed by the
    Supervisor, and executed by worker agents. Each task tracks its
    dependencies, assignment, and quality outcome.
    """

    id: str
    project_id: str
    title: str
    description: str
    type: TaskType
    status: TaskStatus = TaskStatus.PENDING
    priority: int = Field(default=0, ge=0, le=10)
    dependencies: list[str] = []  # IDs of prerequisite tasks
    assigned_agent: AgentRole | None = None
    input_data: dict[str, Any] = {}
    output_data: dict[str, Any] = {}
    rework_count: int = Field(default=0, ge=0)
    quality_score: float | None = Field(default=None, ge=0.0, le=1.0)
    created_at: datetime
    completed_at: datetime | None = None
