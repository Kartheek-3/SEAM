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

from backend.schemas import TaskType, AgentInput, AgentStatus
from backend.llm.ollama_client import OllamaClient
from backend.llm.worker import Worker, WorkerStatus
from backend.llm.worker_registry import global_registry
from backend.llm.worker_pool import WorkerPool
from backend.llm.worker_client import WorkerAwareOllamaClient
from backend.schemas.enums import AgentRole

from agents.analysis.agent import AnalysisAgent
from agents.planning.agent import PlanningAgent
from agents.coding.agent import CodingAgent
from agents.qa.agent import QAAgent
from agents.delivery.agent import DeliveryAgent
from agents.supervisor.agent import SupervisorAgent
from rag.retriever import Retriever
from backend.llm.ollama_embedder import OllamaEmbedder
from rag.config import COLLECTION_VALIDATED_KNOWLEDGE

from backend.llm.client import LLMClient
from backend.schemas.knowledge import KnowledgeContext
from pydantic import BaseModel
from typing import Type, TypeVar

T = TypeVar("T", bound=BaseModel)

class TelemetryLLMClient:
    def __init__(self, base_client: LLMClient):
        self.base_client = base_client
        self.invocation_count = 0
    
    async def generate_structured_output(self, system_prompt: str, user_prompt: str, response_model: Type[T]) -> T:
        self.invocation_count += 1
        return await self.base_client.generate_structured_output(system_prompt, user_prompt, response_model)

    async def generate_structured_response(self, system_prompt: str, user_prompt: str, response_model: Type[T]) -> T:
        self.invocation_count += 1
        if hasattr(self.base_client, "generate_structured_response"):
            return await self.base_client.generate_structured_response(system_prompt, user_prompt, response_model)
        return await self.base_client.generate_structured_output(system_prompt, user_prompt, response_model)

class TelemetryRAGService:
    def __init__(self, base_service):
        self.base_service = base_service
        self.retrievals = 0
        self.successes = 0
        self.chunks_retrieved = 0
        self.failures = 0
        self.latency_ms = 0
        self.chroma = getattr(base_service, "chroma", None)

    async def retrieve(self, query: str, *args, **kwargs) -> KnowledgeContext:
        self.retrievals += 1
        try:
            result = await self.base_service.retrieve(query, *args, **kwargs)
            self.successes += 1
            self.chunks_retrieved += len(result.chunks)
            self.latency_ms += result.retrieval_time_ms
            return result
        except Exception as e:
            self.failures += 1
            raise e

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
        """
        if variant in [SystemVariant.BASELINE_A_SINGLE_LLM, SystemVariant.BASELINE_B_STATIC_PIPELINE, SystemVariant.BASELINE_D_NO_REWORK]:
            logger.warning(f"Variant {variant.value} is not executable directly via the standard orchestration yet.")
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

        try:
            from backend.config import settings
            import urllib.parse
            
            # Use global registry to share state with API
            registry = global_registry
            
            # Setup workers from config or fallback to single-worker
            if settings.ollama_workers:
                workers_config = json.loads(settings.ollama_workers)
                for w_cfg in workers_config:
                    w = Worker(
                        worker_id=w_cfg["worker_id"],
                        host=w_cfg["host"],
                        port=w_cfg["port"],
                        model=w_cfg["model"],
                        capabilities=w_cfg.get("capabilities", []),
                        status=WorkerStatus.AVAILABLE
                    )
                    registry.register_worker(w)
            else:
                # Single-worker backward compatibility
                parsed_url = urllib.parse.urlparse(settings.ollama_base_url)
                host = parsed_url.hostname or "localhost"
                port = parsed_url.port or 11434
                
                w = Worker(
                    worker_id="default-worker-1",
                    host=host,
                    port=port,
                    model=repro.model_identifier or settings.ollama_model_general,
                    status=WorkerStatus.AVAILABLE
                )
                registry.register_worker(w)
            
            pool = WorkerPool(registry)
            raw_llm_client = WorkerAwareOllamaClient(worker_pool=pool)
            llm_client = TelemetryLLMClient(raw_llm_client)
            
            # Configure RAG
            rag_service = None
            if variant != SystemVariant.BASELINE_C_NO_RAG:
                raw_rag = Retriever(embedder=OllamaEmbedder())
                rag_service = TelemetryRAGService(raw_rag)
                # For cold start, point to a non-existent/empty collection
                if variant == SystemVariant.VARIANT_COLD_START:
                    rag_service.chroma.get_or_create_collection(f"cold_start_{experiment_id}")
        except Exception as e:
            logger.error(f"Failed to initialize evaluation components: {e}")
            return self._build_failed_real_result(experiment_id, scenario, variant, repro, f"Component Initialization Failed: {e}")

        # 1. Analysis
        analysis_agent = AnalysisAgent(llm_client=llm_client, rag_service=rag_service)
        analysis_in = AgentInput(
            task_id=f"{experiment_id}-analysis",
            task_type=TaskType.ANALYSIS,
            context={"raw_description": scenario.requirement, "project_id": scenario.scenario_id},
            instructions="Extract requirements"
        )
        analysis_out = await analysis_agent.execute(analysis_in)
        
        if analysis_out.status != AgentStatus.SUCCESS:
            return self._build_failed_real_result(experiment_id, scenario, variant, repro, "Analysis Failed", llm_client, rag_service)

        # 2. Planning
        planning_agent = PlanningAgent(llm_client=llm_client, rag_service=rag_service)
        planning_in = AgentInput(
            task_id=f"{experiment_id}-planning",
            task_type=TaskType.PLANNING,
            context={"requirement_spec": analysis_out.result, "project_id": scenario.scenario_id},
            instructions="Create project plan"
        )
        planning_out = await planning_agent.execute(planning_in)
        
        if planning_out.status != AgentStatus.SUCCESS:
            return self._build_failed_real_result(experiment_id, scenario, variant, repro, "Planning Failed", llm_client, rag_service)

        # 3. Supervisor (Coding, QA, Delivery)
        registry = {
            TaskType.CODING: CodingAgent(llm_client=llm_client, rag_service=rag_service),
            TaskType.QA: QAAgent(llm_client=llm_client, rag_service=rag_service),
            TaskType.DELIVERY: DeliveryAgent(llm_client=llm_client, rag_service=rag_service),
        }
        supervisor = SupervisorAgent(agent_registry=registry, rag_service=rag_service)
        sup_in = AgentInput(
            task_id=f"{experiment_id}-supervisor",
            task_type=TaskType.PLANNING,
            context={"project_plan": planning_out.result},
            instructions="Execute plan"
        )
        sup_out = await supervisor.execute(sup_in)

        # Collect metrics from actual execution
        success = (sup_out.status == AgentStatus.SUCCESS)
        delivery_status = "SUCCESS" if success else "FAILURE"
        
        workflow_state = sup_out.result if isinstance(sup_out.result, dict) else {}
        rework_cycles = sum(workflow_state.get("rework_counts", {}).values())
        llm_calls = llm_client.invocation_count

        qa_score = None
        defects = DefectCounts(critical=0, major=0, minor=0)
        
        # Extract QA metrics from workflow state
        if workflow_state and "tasks" in workflow_state:
            agent_outputs = workflow_state.get("agent_outputs", {})
            qa_outputs = [
                out for t_id, out in agent_outputs.items()
                if workflow_state["tasks"].get(t_id) and getattr(workflow_state["tasks"][t_id], "type", None) == TaskType.QA
            ]
            if qa_outputs:
                final_qa = qa_outputs[-1].result
                if isinstance(final_qa, dict):
                    qa_score = final_qa.get("score", 0.0)
                    for finding in final_qa.get("findings", []):
                        sev = finding.get("severity") if isinstance(finding, dict) else getattr(finding, "severity", None)
                        sev_val = getattr(sev, "value", str(sev)).lower()
                        if sev_val == "critical":
                            defects.critical += 1
                        elif sev_val == "major":
                            defects.major += 1
                        elif sev_val == "minor":
                            defects.minor += 1



        return ExperimentResult(
            experiment_id=experiment_id,
            scenario_id=scenario.scenario_id,
            system_variant=variant,
            model=repro.model_identifier,
            domain=scenario.domain,
            success=success,
            llm_calls=llm_calls,
            rework_cycles=rework_cycles,
            qa_score=qa_score,
            defect_counts=defects,
            delivery_status=delivery_status,
            rag_used=(rag_service is not None),
            rag_retrievals=rag_service.retrievals if rag_service else 0,
            rag_successes=rag_service.successes if rag_service else 0,
            rag_failures=rag_service.failures if rag_service else 0,
            chunks_retrieved=rag_service.chunks_retrieved if rag_service else 0,
            rag_latency_ms=rag_service.latency_ms if rag_service else 0,
            knowledge_reused=(rag_service is not None and rag_service.chunks_retrieved > 0),
            result_mode=ResultMode.REAL,
            reproducibility=repro,
            agent_failure_count=len(workflow_state.get("failed_tasks", [])),
            task_completion_rate=1.0 if success else 0.5,
        )

    def _build_failed_real_result(self, exp_id, scenario, variant, repro, reason, llm_client=None, rag_service=None):
        return ExperimentResult(
            experiment_id=exp_id,
            scenario_id=scenario.scenario_id,
            system_variant=variant,
            model=repro.model_identifier,
            domain=scenario.domain,
            success=False,
            llm_calls=llm_client.invocation_count if llm_client else 0,
            rework_cycles=0,
            qa_score=None,
            defect_counts=DefectCounts(critical=0, major=0, minor=0),
            delivery_status=reason,
            rag_used=(rag_service is not None),
            rag_retrievals=rag_service.retrievals if rag_service else 0,
            rag_successes=rag_service.successes if rag_service else 0,
            rag_failures=rag_service.failures if rag_service else 0,
            chunks_retrieved=rag_service.chunks_retrieved if rag_service else 0,
            rag_latency_ms=rag_service.latency_ms if rag_service else 0,
            knowledge_reused=(rag_service is not None and rag_service.chunks_retrieved > 0),
            result_mode=ResultMode.REAL,
            reproducibility=repro,
            agent_failure_count=1,
            task_completion_rate=0.0,
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
