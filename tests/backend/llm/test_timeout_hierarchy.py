import pytest
from pydantic import ValidationError
from backend.config import AppConfig

def test_timeout_hierarchy_valid():
    # Should not raise
    config = AppConfig(worker_health_timeout=2.0, ollama_timeout=300, worker_lease_timeout=360)
    assert config.worker_health_timeout == 2.0
    assert config.ollama_timeout == 300
    assert config.worker_lease_timeout == 360

def test_timeout_hierarchy_invalid_health():
    with pytest.raises(ValidationError, match="Invalid timeout hierarchy"):
        AppConfig(worker_health_timeout=400.0, ollama_timeout=300, worker_lease_timeout=360)

def test_timeout_hierarchy_invalid_lease():
    with pytest.raises(ValidationError, match="Invalid timeout hierarchy"):
        AppConfig(worker_health_timeout=2.0, ollama_timeout=300, worker_lease_timeout=150)
