"""
SEAM Backend Schemas — Workflow State

LangGraph-compatible state object tracking the overall orchestration.
Uses TypedDict (not BaseModel) because LangGraph requires TypedDict
for its state machine.

Source: docs/09_data_models.md §3.1 (SupervisorState)
Traceability: FR-2.5
"""

from typing import Any, TypedDict

from backend.schemas.agent_io import AgentOutput
from backend.schemas.artifacts import Artifact
from backend.schemas.task import Task


class WorkflowState(TypedDict):
    """
    LangGraph state for the Supervisor/Orchestrator.

    Tracks the full workflow: task graph, task status lists,
    agent outputs, quality scores, and final artifacts.

    Supports pending, running, completed, and failed task tracking
    as required by the workflow state specification.
    """

    project_id: str
    current_phase: str
    tasks: dict[str, Task]  # task_id → Task
    pending_tasks: list[str]
    running_tasks: list[str]
    completed_tasks: list[str]
    failed_tasks: list[str]
    agent_outputs: dict[str, AgentOutput]  # task_id → AgentOutput
    rework_counts: dict[str, int]  # task_id → count
    quality_scores: dict[str, float]  # task_id → score
    current_task_id: str | None
    messages: list[dict[str, Any]]
    final_artifacts: list[Artifact]
    qa_execution_history: list[dict[str, Any]]
