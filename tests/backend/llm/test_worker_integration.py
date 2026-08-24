import json
import pytest
from backend.config import AppConfig
from backend.llm.worker_registry import WorkerRegistry
from backend.llm.worker_pool import WorkerPool
from backend.llm.worker import WorkerStatus
from pydantic import ValidationError

def test_ollama_workers_config_parsing():
    valid_json = json.dumps([
        {"worker_id": "w1", "host": "localhost", "port": 11434, "model": "llama"}
    ])
    config = AppConfig(ollama_workers=valid_json)
    assert config.ollama_workers == valid_json

def test_ollama_workers_config_validation():
    # Duplicate ID
    duplicate_id_json = json.dumps([
        {"worker_id": "w1", "host": "localhost", "port": 11434, "model": "llama"},
        {"worker_id": "w1", "host": "localhost", "port": 11435, "model": "llama"}
    ])
    with pytest.raises(ValidationError) as exc_info:
        AppConfig(ollama_workers=duplicate_id_json)
    assert "Duplicate worker_id" in str(exc_info.value)
    
    # Duplicate Endpoint
    duplicate_endpoint_json = json.dumps([
        {"worker_id": "w1", "host": "localhost", "port": 11434, "model": "llama"},
        {"worker_id": "w2", "host": "localhost", "port": 11434, "model": "llama"}
    ])
    with pytest.raises(ValidationError) as exc_info:
        AppConfig(ollama_workers=duplicate_endpoint_json)
    assert "Duplicate endpoint" in str(exc_info.value)
    
    # Missing Fields
    missing_fields_json = json.dumps([
        {"worker_id": "w1", "host": "localhost", "port": 11434}
    ])
    with pytest.raises(ValidationError) as exc_info:
        AppConfig(ollama_workers=missing_fields_json)
    assert "missing 'model'" in str(exc_info.value)
    
    # Not a list
    not_list_json = json.dumps({"worker_id": "w1"})
    with pytest.raises(ValidationError) as exc_info:
        AppConfig(ollama_workers=not_list_json)
    assert "JSON array" in str(exc_info.value)


import asyncio
from evaluation.runner import ExperimentRunner
from evaluation.schemas import SystemVariant, ResultMode
from unittest.mock import patch, AsyncMock

from backend.schemas import AgentStatus

@pytest.mark.asyncio
async def test_runner_construction_fallback():
    # If OLLAMA_WORKERS is empty, ExperimentRunner creates a single default-worker-1
    runner = ExperimentRunner(results_dir=".")
    
    with patch("backend.config.settings.ollama_workers", ""):
        with patch("backend.llm.worker_registry.global_registry.register_worker") as mock_register:
            with patch("agents.analysis.agent.AnalysisAgent.execute", new_callable=AsyncMock) as mock_agent:
                # We just want to see the initialization, so we mock analysis agent to fail gracefully or succeed
                mock_agent.return_value.status = AgentStatus.FAILURE
                try:
                    with patch("evaluation.runner.Retriever"):
                        with patch("evaluation.runner.OllamaEmbedder"):
                            await runner._run_real("exp-1", type("Scenario", (), {"scenario_id":"1", "domain":"dom", "requirement":"req"})(), SystemVariant.FULL_SYSTEM, type("Repro", (), {"model_identifier":"llama"})())
                except Exception:
                    pass
                
                assert mock_register.called
                args = mock_register.call_args[0][0]
                assert args.worker_id == "default-worker-1"

@pytest.mark.asyncio
async def test_runner_construction_multi():
    # If OLLAMA_WORKERS is set, ExperimentRunner registers them
    runner = ExperimentRunner(results_dir=".")
    valid_json = json.dumps([
        {"worker_id": "w1", "host": "localhost", "port": 11434, "model": "llama"}
    ])
    
    with patch("backend.config.settings.ollama_workers", valid_json):
        with patch("backend.llm.worker_registry.global_registry.register_worker") as mock_register:
            with patch("agents.analysis.agent.AnalysisAgent.execute", new_callable=AsyncMock) as mock_agent:
                mock_agent.return_value.status = AgentStatus.FAILURE
                try:
                    with patch("evaluation.runner.Retriever"):
                        with patch("evaluation.runner.OllamaEmbedder"):
                            await runner._run_real("exp-1", type("Scenario", (), {"scenario_id":"1", "domain":"dom", "requirement":"req"})(), SystemVariant.FULL_SYSTEM, type("Repro", (), {"model_identifier":"llama"})())
                except Exception:
                    pass
                
                assert mock_register.called
                args = mock_register.call_args[0][0]
                assert args.worker_id == "w1"
