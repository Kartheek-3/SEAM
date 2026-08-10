"""
Evaluation Runner — Experiment Execution Orchestrator

Loads scenarios, selects system variants, executes experiments,
collects metrics, and persists results.

Supports both REAL execution (with live LLM) and MOCK/SIMULATION
mode (with deterministic mock responses). Every result is explicitly
tagged with its ResultMode.

RESEARCH INTEGRITY: This runner never fabricates experimental results.
Mock mode produces clearly labelled simulation data only.
"""

import json
import logging
import os
import platform
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from evaluation.schemas import (
    ExperimentResult,
    ReproducibilityInfo,
    ResultMode,
    SystemVariant,
    DefectCounts,
)
from evaluation.scenarios import ScenarioDefinition, get_scenario, list_scenario_ids

logger = logging.getLogger(__name__)

# Default results directory (relative to project root)
DEFAULT_RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")


def generate_experiment_id() -> str:
    """Generate a unique experiment identifier."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    short_uuid = uuid.uuid4().hex[:8]
    return f"exp-{ts}-{short_uuid}"


def capture_reproducibility_info(
    model_identifier: str = "",
    config_snapshot: Optional[dict] = None,
    random_seed: Optional[int] = None,
) -> ReproducibilityInfo:
    """
    Capture the current environment state for reproducibility.
    """
    commit_hash = ""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            commit_hash = result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        commit_hash = "unavailable"

    env_info = {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor(),
    }

    return ReproducibilityInfo(
        commit_hash=commit_hash,
        model_identifier=model_identifier,
        configuration_snapshot=config_snapshot or {},
        environment_info=env_info,
        random_seed=random_seed,
    )


class ExperimentRunner:
    """
    Orchestrates experiment execution for a given scenario and system variant.

    Usage:
        runner = ExperimentRunner(results_dir="evaluation/results")
        result = await runner.run(
            scenario_id="ecommerce-catalog",
            variant=SystemVariant.FULL_SYSTEM,
            mode=ResultMode.MOCK,
        )
    """

    def __init__(self, results_dir: str = DEFAULT_RESULTS_DIR):
        self.results_dir = results_dir
        os.makedirs(self.results_dir, exist_ok=True)

    async def run(
        self,
        scenario_id: str,
        variant: SystemVariant,
        mode: ResultMode = ResultMode.MOCK,
        model_identifier: str = "",
        random_seed: Optional[int] = None,
        config_snapshot: Optional[dict] = None,
    ) -> ExperimentResult:
        """
        Execute a single experiment run.

        Args:
            scenario_id: ID of the scenario to execute.
            variant: Which system variant / baseline to use.
            mode: REAL or MOCK execution.
            model_identifier: LLM model name for reproducibility.
            random_seed: Optional seed for reproducibility.
            config_snapshot: Optional configuration for reproducibility.

        Returns:
            ExperimentResult with all metrics populated.
        """
        scenario = get_scenario(scenario_id)
        experiment_id = generate_experiment_id()

        logger.info(
            f"Starting experiment {experiment_id}: "
            f"scenario={scenario_id}, variant={variant.value}, mode={mode.value}"
        )

        repro = capture_reproducibility_info(
            model_identifier=model_identifier,
            config_snapshot=config_snapshot,
            random_seed=random_seed,
        )

        start_time = time.time()

        if mode == ResultMode.MOCK:
            result = await self._run_mock(experiment_id, scenario, variant, repro)
        else:
            result = await self._run_real(experiment_id, scenario, variant, repro)

        result.execution_time_sec = round(time.time() - start_time, 3)
        result.result_mode = mode

        self._persist_result(result)

        logger.info(
            f"Experiment {experiment_id} complete: "
            f"success={result.success}, qa_score={result.qa_score}"
        )

        return result

    async def _run_mock(
        self,
        experiment_id: str,
        scenario: ScenarioDefinition,
        variant: SystemVariant,
        repro: ReproducibilityInfo,
    ) -> ExperimentResult:
        """
        Execute a mock/simulation run.

        RESEARCH INTEGRITY NOTE:
        Mock results are SIMULATION data only. They are tagged with
        ResultMode.MOCK and must never be presented as real experimental
        results. Mock mode exists to validate the evaluation harness
        infrastructure and demonstrate data flow.
        """
        # Simulate variant-specific behavior patterns
        # These are NOT real performance measurements
        mock_profiles = {
            SystemVariant.FULL_SYSTEM: {
                "success": True,
                "llm_calls": 6,  # One per agent
                "rework_cycles": 1,
                "qa_score": 0.0,  # Not yet measured
                "defects": DefectCounts(critical=0, major=0, minor=0),
                "delivery_status": "SUCCESS",
                "rag_used": True,
                "knowledge_reused": True,
                "agent_failures": 0,
                "task_completion_rate": 0.0,  # Not yet measured
            },
            SystemVariant.BASELINE_A_SINGLE_LLM: {
                "success": True,
                "llm_calls": 1,
                "rework_cycles": 0,
                "qa_score": 0.0,
                "defects": DefectCounts(critical=0, major=0, minor=0),
                "delivery_status": "SUCCESS",
                "rag_used": False,
                "knowledge_reused": False,
                "agent_failures": 0,
                "task_completion_rate": 0.0,
            },
            SystemVariant.BASELINE_B_STATIC_PIPELINE: {
                "success": True,
                "llm_calls": 4,
                "rework_cycles": 0,
                "qa_score": 0.0,
                "defects": DefectCounts(critical=0, major=0, minor=0),
                "delivery_status": "SUCCESS",
                "rag_used": False,
                "knowledge_reused": False,
                "agent_failures": 0,
                "task_completion_rate": 0.0,
            },
            SystemVariant.BASELINE_C_NO_RAG: {
                "success": True,
                "llm_calls": 6,
                "rework_cycles": 1,
                "qa_score": 0.0,
                "defects": DefectCounts(critical=0, major=0, minor=0),
                "delivery_status": "SUCCESS",
                "rag_used": False,
                "knowledge_reused": False,
                "agent_failures": 0,
                "task_completion_rate": 0.0,
            },
            SystemVariant.BASELINE_D_NO_REWORK: {
                "success": True,
                "llm_calls": 5,
                "rework_cycles": 0,
                "qa_score": 0.0,
                "defects": DefectCounts(critical=0, major=0, minor=0),
                "delivery_status": "SUCCESS",
                "rag_used": True,
                "knowledge_reused": False,
                "agent_failures": 0,
                "task_completion_rate": 0.0,
            },
            SystemVariant.VARIANT_COLD_START: {
                "success": True,
                "llm_calls": 6,
                "rework_cycles": 1,
                "qa_score": 0.0,
                "defects": DefectCounts(critical=0, major=0, minor=0),
                "delivery_status": "SUCCESS",
                "rag_used": True,
                "knowledge_reused": False,
                "agent_failures": 0,
                "task_completion_rate": 0.0,
            },
        }

        profile = mock_profiles.get(variant, mock_profiles[SystemVariant.FULL_SYSTEM])

        return ExperimentResult(
            experiment_id=experiment_id,
            scenario_id=scenario.scenario_id,
            system_variant=variant,
            model=repro.model_identifier or "mock",
            domain=scenario.domain,
            success=profile["success"],
            llm_calls=profile["llm_calls"],
            rework_cycles=profile["rework_cycles"],
            qa_score=profile["qa_score"],
            defect_counts=profile["defects"],
            delivery_status=profile["delivery_status"],
            rag_used=profile["rag_used"],
            knowledge_reused=profile["knowledge_reused"],
            result_mode=ResultMode.MOCK,
            reproducibility=repro,
            agent_failure_count=profile["agent_failures"],
            task_completion_rate=profile["task_completion_rate"],
        )

    async def _run_real(
        self,
        experiment_id: str,
        scenario: ScenarioDefinition,
        variant: SystemVariant,
        repro: ReproducibilityInfo,
    ) -> ExperimentResult:
        """
        Execute a real experiment using the live SEAM system.

        This requires a running Ollama instance and the full agent pipeline.
        If the system is unavailable, the experiment fails gracefully.

        NOTE: Real execution is not yet fully wired. This placeholder
        returns a FAILURE result rather than fabricating data.
        """
        logger.warning(
            f"Real execution for variant {variant.value} is not yet implemented. "
            "Returning failure result. No data has been fabricated."
        )

        return ExperimentResult(
            experiment_id=experiment_id,
            scenario_id=scenario.scenario_id,
            system_variant=variant,
            model=repro.model_identifier,
            domain=scenario.domain,
            success=False,
            delivery_status="NOT_IMPLEMENTED",
            result_mode=ResultMode.REAL,
            reproducibility=repro,
        )

    def _persist_result(self, result: ExperimentResult) -> str:
        """
        Save an experiment result to disk as JSON.

        Returns the file path where the result was saved.
        """
        filename = f"{result.experiment_id}.json"
        filepath = os.path.join(self.results_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(result.model_dump_json(indent=2))

        logger.info(f"Result persisted: {filepath}")
        return filepath

    def load_results(self, scenario_id: str = "", variant: str = "") -> list[ExperimentResult]:
        """
        Load previously saved results, optionally filtered by scenario or variant.
        """
        results = []
        if not os.path.isdir(self.results_dir):
            return results

        for filename in os.listdir(self.results_dir):
            if not filename.endswith(".json"):
                continue
            filepath = os.path.join(self.results_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                result = ExperimentResult(**data)

                if scenario_id and result.scenario_id != scenario_id:
                    continue
                if variant and result.system_variant.value != variant:
                    continue

                results.append(result)
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Failed to load result {filepath}: {e}")

        return results
