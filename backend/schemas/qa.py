"""
SEAM Backend Schemas — QA Result and Rework Feedback

Structured quality assessment produced by the QA Agent, and
rework instructions dispatched by the Supervisor to the Coding Agent.

Source: docs/04_agent_specifications.md §3.5, docs/09_data_models.md §3.2
Traceability: FR-2.4, FR-2.7, FR-2.8, FR-2.9, FR-2.10
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from backend.schemas.enums import FindingSeverity, QAVerdict


class QAFinding(BaseModel):
    """
    A single quality finding from the QA Agent.

    Provides structured information about a specific issue found
    during testing, code review, or static analysis.
    """

    category: Literal[
        "test_failure",
        "code_review",
        "static_analysis",
        "requirement_gap",
    ]
    severity: FindingSeverity
    description: str
    location: str | None = None  # file path or code reference
    suggestion: str | None = None  # recommended fix


class QAResult(BaseModel):
    """
    Structured quality assessment from the QA Agent.

    Contains the verdict (PASS/FAIL), quality score, detailed findings,
    test metrics, and rework recommendations. This is the primary
    output of the QA Agent's evaluation (FR-2.9).

    The QA Agent reports this to the Supervisor/Orchestrator (FR-2.10),
    NOT directly to the Coding Agent.
    """

    task_id: str
    verdict: QAVerdict
    score: float = Field(ge=0.0, le=1.0)
    findings: list[QAFinding] = []
    tests_passed: int = Field(default=0, ge=0)
    tests_failed: int = Field(default=0, ge=0)
    tests_total: int = Field(default=0, ge=0)
    recommendations: list[str] = []
    evaluated_at: datetime


class ReworkFeedback(BaseModel):
    """
    Structured rework instructions from the Supervisor to the Coding Agent.

    When QA fails, the Supervisor packages the QA result along with
    its own rework instructions and dispatches them to the Coding Agent
    via AgentInput.rework_feedback.

    Communication path: QA Agent → Supervisor → Coding Agent
    (agents never communicate directly — doc 04 §4).
    """

    source_task_id: str  # task that failed QA
    qa_result: QAResult  # the full QA assessment
    instructions: str  # Supervisor's rework guidance
    focus_areas: list[str] = []  # specific areas to address
    max_rework_attempts: int = Field(default=3, ge=1, le=5)
    current_attempt: int = Field(default=1, ge=1)
