"""
SEAM Backend Schemas — Project Plan

Structured output from the Planning & Design Agent. Contains the
architecture summary, component breakdown, decomposed task list,
and technology recommendations.

Source: docs/04_agent_specifications.md §3.2
"""

from pydantic import BaseModel

from backend.schemas.task import Task


class ComponentSpec(BaseModel):
    """A component identified during architectural design."""

    name: str
    description: str
    responsibilities: list[str] = []


class ProjectPlan(BaseModel):
    """
    Complete project plan produced by the Planning & Design Agent.

    This is the structured output placed in AgentOutput.result when
    the Planning & Design Agent completes its task. The Supervisor
    uses the task list to populate WorkflowState.tasks.
    """

    project_id: str
    architecture_summary: str
    components: list[ComponentSpec]
    tasks: list[Task]
    technology_recommendations: list[str] = []
