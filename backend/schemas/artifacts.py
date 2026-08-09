"""
SEAM Backend Schemas — Artifact

A generated project artifact (code file, document, test, config, diagram)
produced by any agent during task execution.

Source: docs/09_data_models.md §2.4
Traceability: FR-5.3
"""

from datetime import datetime

from pydantic import BaseModel

from backend.schemas.enums import ArtifactType


class Artifact(BaseModel):
    """A discrete artifact produced by an agent."""

    id: str
    project_id: str
    task_id: str
    type: ArtifactType
    name: str
    content: str
    language: str | None = None  # e.g., "python", "javascript" — for code artifacts
    created_at: datetime
