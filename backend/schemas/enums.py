"""
SEAM Backend Schemas — Enumerations

Shared enumerations used across all data contracts.
These enforce the six-agent architecture constraint (C3)
and provide type-safe status tracking.
"""

from enum import Enum


class TaskType(str, Enum):
    """Types of tasks corresponding to agent specialisations."""

    ANALYSIS = "analysis"
    PLANNING = "planning"
    CODING = "coding"
    QA = "qa"
    DELIVERY = "delivery"


class TaskStatus(str, Enum):
    """Lifecycle status of a task within the workflow."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REWORK = "rework"


class AgentRole(str, Enum):
    """
    The six executable agents in SEAM.

    This enum restricts valid role values and enforces constraint C3
    (exactly six agents, no additional agents) at the type level.
    Note that this enum alone does not enforce the entire architecture;
    the actual agent implementations are defined by the architecture
    and agent registry.
    """

    ANALYSIS = "analysis"
    PLANNING = "planning"
    SUPERVISOR = "supervisor"
    CODING = "coding"
    QA = "qa"
    DELIVERY = "delivery"


class ArtifactType(str, Enum):
    """Classification of generated project artifacts."""

    CODE = "code"
    DOCUMENT = "document"
    TEST = "test"
    CONFIG = "config"
    DIAGRAM = "diagram"


class AgentStatus(str, Enum):
    """Outcome status of an agent execution."""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILURE = "failure"


class QAVerdict(str, Enum):
    """Binary quality verdict from the QA Agent."""

    PASS = "pass"
    FAIL = "fail"


class FindingSeverity(str, Enum):
    """Severity classification for QA findings."""

    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    INFO = "info"
