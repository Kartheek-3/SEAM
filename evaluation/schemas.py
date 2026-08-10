"""
Evaluation Schemas — Data Models for Experiment Results

Evaluation-specific Pydantic models that capture experiment metadata,
scenario definitions, metric results, and reproducibility information.

These models are entirely separate from the production schemas in
backend/schemas/. They observe the production system without modifying it.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class SystemVariant(str, Enum):
    """Identifies the system configuration under evaluation."""
    FULL_SYSTEM = "full_system"
    BASELINE_A_SINGLE_LLM = "baseline_a_single_llm"
    BASELINE_B_STATIC_PIPELINE = "baseline_b_static_pipeline"
    BASELINE_C_NO_RAG = "baseline_c_no_rag"
    BASELINE_D_NO_REWORK = "baseline_d_no_rework"
    VARIANT_COLD_START = "variant_cold_start"


class ResultMode(str, Enum):
    """Indicates whether experiment data came from a real or mock execution."""
    REAL = "real"
    MOCK = "mock"


class ScenarioComplexity(str, Enum):
    """Complexity classification for evaluation scenarios."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DefectCounts(BaseModel):
    """Structured defect tally from QA evaluation."""
    critical: int = Field(default=0, ge=0)
    major: int = Field(default=0, ge=0)
    minor: int = Field(default=0, ge=0)


class ScenarioDefinition(BaseModel):
    """
    A deterministic software-development scenario used as experiment input.
    """
    scenario_id: str
    domain: str
    complexity: ScenarioComplexity
    requirement: str = Field(..., min_length=1)
    acceptance_criteria: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    expected_functionality: list[str] = Field(default_factory=list)
    evaluation_criteria: list[str] = Field(default_factory=list)


class ReproducibilityInfo(BaseModel):
    """
    Metadata required to reproduce an experiment exactly.
    """
    commit_hash: str = ""
    model_identifier: str = ""
    configuration_snapshot: dict[str, Any] = Field(default_factory=dict)
    environment_info: dict[str, Any] = Field(default_factory=dict)
    random_seed: Optional[int] = None


class ExperimentResult(BaseModel):
    """
    Machine-readable result of a single experiment execution.

    Schema matches the approved Phase 9 evaluation plan (Section 13).
    """
    experiment_id: str
    scenario_id: str
    system_variant: SystemVariant
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    model: str = ""
    domain: str = ""
    success: bool = False
    execution_time_sec: float = Field(default=0.0, ge=0.0)
    llm_calls: int = Field(default=0, ge=0)
    rework_cycles: int = Field(default=0, ge=0)
    qa_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    defect_counts: DefectCounts = Field(default_factory=DefectCounts)
    delivery_status: str = ""
    rag_used: bool = False
    rag_retrievals: int = Field(default=0, ge=0)
    rag_successes: int = Field(default=0, ge=0)
    rag_failures: int = Field(default=0, ge=0)
    chunks_retrieved: int = Field(default=0, ge=0)
    rag_latency_ms: int = Field(default=0, ge=0)
    knowledge_reused: bool = False
    result_mode: ResultMode = ResultMode.MOCK
    reproducibility: ReproducibilityInfo = Field(default_factory=ReproducibilityInfo)
    agent_failure_count: int = Field(default=0, ge=0)
    task_completion_rate: float = Field(default=0.0, ge=0.0, le=1.0)
