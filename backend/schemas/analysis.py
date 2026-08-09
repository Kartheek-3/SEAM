"""
SEAM Backend Schemas — Requirement Specification

Structured output from the Analysis Agent. Captures functional
and non-functional requirements, ambiguities, assumptions, and
domain entities extracted from a project description.

Source: docs/04_agent_specifications.md §3.1
"""

from typing import Literal

from pydantic import BaseModel


class RequirementItem(BaseModel):
    """A single requirement extracted by the Analysis Agent."""

    id: str  # e.g., "FR-1", "NFR-2"
    description: str
    category: Literal["functional", "non_functional"]
    priority: Literal["must", "should", "could"] = "must"


class RequirementSpec(BaseModel):
    """
    Complete requirements specification produced by the Analysis Agent.

    This is the structured output placed in AgentOutput.result when
    the Analysis Agent completes its task. It feeds directly into
    the Planning & Design Agent as input.
    """

    project_id: str
    functional_requirements: list[RequirementItem]
    non_functional_requirements: list[RequirementItem]
    ambiguities: list[str] = []  # flagged unclear areas
    assumptions: list[str] = []  # stated assumptions
    domain_entities: list[str] = []  # identified domain concepts
