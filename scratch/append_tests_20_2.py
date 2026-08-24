
import asyncio
from evaluation.runner import ExperimentRunner
from evaluation.schemas import SystemVariant, ResultMode
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_runner_construction_fallback(mocker):
    # If OLLAMA_WORKERS is empty, ExperimentRunner creates a single default-worker-1
    runner = ExperimentRunner(results_dir=".")
    
    with patch("backend.config.settings.ollama_workers", ""):
        with patch("backend.llm.worker_registry.global_registry.register_worker") as mock_register:
            with patch("agents.analysis.agent.AnalysisAgent.execute", new_callable=AsyncMock) as mock_agent:
                # We just want to see the initialization, so we mock analysis agent to fail gracefully or succeed
                mock_agent.return_value.status = 1
                try:
                    await runner._run_real("exp-1", type("Scenario", (), {"scenario_id":"1", "domain":"dom", "requirement":"req"})(), SystemVariant.FULL_SYSTEM, type("Repro", (), {"model_identifier":"llama"})())
                except Exception:
                    pass
                
                assert mock_register.called
                args = mock_register.call_args[0][0]
                assert args.worker_id == "default-worker-1"

@pytest.mark.asyncio
async def test_runner_construction_multi(mocker):
    # If OLLAMA_WORKERS is set, ExperimentRunner registers them
    runner = ExperimentRunner(results_dir=".")
    valid_json = json.dumps([
        {"worker_id": "w1", "host": "localhost", "port": 11434, "model": "llama"}
    ])
    
    with patch("backend.config.settings.ollama_workers", valid_json):
        with patch("backend.llm.worker_registry.global_registry.register_worker") as mock_register:
            with patch("agents.analysis.agent.AnalysisAgent.execute", new_callable=AsyncMock) as mock_agent:
                mock_agent.return_value.status = 1
                try:
                    await runner._run_real("exp-1", type("Scenario", (), {"scenario_id":"1", "domain":"dom", "requirement":"req"})(), SystemVariant.FULL_SYSTEM, type("Repro", (), {"model_identifier":"llama"})())
                except Exception:
                    pass
                
                assert mock_register.called
                args = mock_register.call_args[0][0]
                assert args.worker_id == "w1"
