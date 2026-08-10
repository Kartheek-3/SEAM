"""
Evaluation Baselines — System Variant Wrappers

Defines the baseline configurations approved in the Phase 9 evaluation plan.

Each baseline is a description and configuration record, not a separate
agent or modified pipeline. The actual execution is handled by the
ExperimentRunner which configures the existing SEAM system accordingly.

IMPORTANT:
- Baseline A (Single LLM) and Baseline B (Static Pipeline) cannot be
  fairly implemented by simply reconfiguring the existing six-agent system.
  They require dedicated wrapper logic that is documented here but flagged
  as NOT YET EXECUTABLE for real experiments.
- Baseline C (No RAG) and Baseline D (No Rework) can be achieved by
  configuring the existing system (disabling RAG or rework respectively).
"""

from dataclasses import dataclass
from evaluation.schemas import SystemVariant


@dataclass(frozen=True)
class BaselineConfig:
    """Describes a baseline / system variant configuration."""
    variant: SystemVariant
    name: str
    description: str
    rag_enabled: bool
    rework_enabled: bool
    multi_agent: bool
    knowledge_preloaded: bool
    executable: bool  # Whether this can currently be executed against the real system


BASELINES: dict[SystemVariant, BaselineConfig] = {
    SystemVariant.FULL_SYSTEM: BaselineConfig(
        variant=SystemVariant.FULL_SYSTEM,
        name="Full SEAM",
        description=(
            "Complete SEAM system: Analysis → Planning → Supervisor → "
            "Coding → QA (with adaptive rework) → Delivery, with RAG "
            "and organizational knowledge reuse enabled."
        ),
        rag_enabled=True,
        rework_enabled=True,
        multi_agent=True,
        knowledge_preloaded=True,
        executable=True,
    ),
    SystemVariant.BASELINE_A_SINGLE_LLM: BaselineConfig(
        variant=SystemVariant.BASELINE_A_SINGLE_LLM,
        name="Baseline A: Single LLM",
        description=(
            "Direct generation of software artifacts via a single large "
            "LLM prompt without agent specialization. The entire requirement "
            "is passed as one prompt and the LLM generates all code directly."
        ),
        rag_enabled=False,
        rework_enabled=False,
        multi_agent=False,
        knowledge_preloaded=False,
        executable=False,  # Requires a dedicated single-prompt wrapper
    ),
    SystemVariant.BASELINE_B_STATIC_PIPELINE: BaselineConfig(
        variant=SystemVariant.BASELINE_B_STATIC_PIPELINE,
        name="Baseline B: Static Sequential Pipeline",
        description=(
            "A rigid pipeline (Analysis → Planning → Coding → Delivery) "
            "lacking the dynamic Supervisor routing and QA verification loops. "
            "No rework cycles. No QA agent involvement."
        ),
        rag_enabled=False,
        rework_enabled=False,
        multi_agent=True,
        knowledge_preloaded=False,
        executable=False,  # Requires bypassing Supervisor + QA
    ),
    SystemVariant.BASELINE_C_NO_RAG: BaselineConfig(
        variant=SystemVariant.BASELINE_C_NO_RAG,
        name="Baseline C: SEAM without RAG",
        description=(
            "The full multi-agent system executing without domain knowledge "
            "retrieval. Agents receive no RAG context in their prompts."
        ),
        rag_enabled=False,
        rework_enabled=True,
        multi_agent=True,
        knowledge_preloaded=False,
        executable=True,  # Can disable RAG by passing rag_service=None
    ),
    SystemVariant.BASELINE_D_NO_REWORK: BaselineConfig(
        variant=SystemVariant.BASELINE_D_NO_REWORK,
        name="Baseline D: SEAM without Adaptive QA Rework",
        description=(
            "The full multi-agent system where a QA failure terminates "
            "execution rather than triggering a rework cycle through "
            "the Supervisor."
        ),
        rag_enabled=True,
        rework_enabled=False,
        multi_agent=True,
        knowledge_preloaded=False,
        executable=False,  # Requires configurable rework toggle in Supervisor
    ),
    SystemVariant.VARIANT_COLD_START: BaselineConfig(
        variant=SystemVariant.VARIANT_COLD_START,
        name="Variant: Cold Start",
        description=(
            "Full SEAM system but starting with an empty knowledge "
            "repository. No previous organizational knowledge available."
        ),
        rag_enabled=True,
        rework_enabled=True,
        multi_agent=True,
        knowledge_preloaded=False,
        executable=True,  # Run with empty knowledge store
    ),
}


def get_baseline(variant: SystemVariant) -> BaselineConfig:
    """Retrieve baseline configuration by variant."""
    if variant not in BASELINES:
        raise KeyError(f"Unknown variant: {variant}. Available: {list(BASELINES.keys())}")
    return BASELINES[variant]


def list_executable_baselines() -> list[BaselineConfig]:
    """Return only baselines that can currently be executed against the real system."""
    return [b for b in BASELINES.values() if b.executable]


def list_all_baselines() -> list[BaselineConfig]:
    """Return all baseline configurations."""
    return list(BASELINES.values())
