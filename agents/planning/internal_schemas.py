from typing import List
from pydantic import BaseModel, Field
from backend.schemas.planning import ComponentSpec, Task

class Pass1ArchitectureResult(BaseModel):
    """
    Internal model representing the output of Planning Pass 1.
    Contains high-level architectural design and components, but no decomposed tasks.
    """
    architecture_summary: str = Field(
        ...,
        description="High-level description of the system architecture, patterns, data flow, and key tech decisions."
    )
    technology_recommendations: List[str] = Field(
        default_factory=list,
        description="List of recommended technologies, frameworks, and tools."
    )
    components: List[ComponentSpec] = Field(
        ...,
        description="List of architectural components."
    )

class MinimalTask(BaseModel):
    """
    Internal minimal task schema for LLM generation.
    Decoupled from the domain Task schema to avoid LLM validation bottlenecks.
    """
    local_id: str = Field(
        ...,
        description="A unique local identifier for this task (e.g. 'T-1', 'api-1')"
    )
    title: str = Field(..., description="Short task title")
    description: str = Field(..., description="Detailed task description and acceptance criteria")
    depends_on: List[str] = Field(
        default_factory=list,
        description="List of local_ids of other tasks this task depends on"
    )

class Pass2TaskResult(BaseModel):
    """
    Internal model representing the output of Planning Pass 2 for a single component.
    Contains only the decomposed tasks for that component.
    """
    tasks: List[MinimalTask] = Field(
        ...,
        description="List of fully decomposed actionable tasks for the current component."
    )
