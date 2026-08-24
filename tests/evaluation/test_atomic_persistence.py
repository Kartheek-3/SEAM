import os
import pytest
from evaluation.runner import ExperimentRunner
from evaluation.schemas import ExperimentResult, SystemVariant, ReproducibilityInfo, ResultMode, DefectCounts

def test_atomic_persistence(tmp_path):
    runner = ExperimentRunner(results_dir=str(tmp_path))
    result = ExperimentResult(
        experiment_id="test-exp-123",
        scenario_id="test",
        system_variant=SystemVariant.BASELINE_C_NO_RAG,
        model="test",
        domain="test",
        success=True,
        llm_calls=1,
        rework_cycles=0,
        qa_score=1.0,
        defect_counts=DefectCounts(critical=0, major=0, minor=0),
        delivery_status="SUCCESS",
        rag_used=False,
        rag_retrievals=0,
        rag_successes=0,
        rag_failures=0,
        chunks_retrieved=0,
        rag_latency_ms=0,
        knowledge_reused=False,
        result_mode=ResultMode.MOCK,
        reproducibility=ReproducibilityInfo(commit_hash="abc", model_identifier="test", configuration_snapshot={}),
        agent_failure_count=0,
        task_completion_rate=1.0
    )
    
    filepath = runner._persist_result(result)
    assert os.path.exists(filepath)
    assert not os.path.exists(filepath + ".tmp")
