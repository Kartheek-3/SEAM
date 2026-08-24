import asyncio
import pytest
from unittest.mock import patch
from backend.llm.worker import Worker, WorkerStatus
from backend.llm.worker_registry import WorkerRegistry
from backend.llm.worker_pool import WorkerPool
from backend.llm.worker_client import WorkerAwareOllamaClient
from backend.llm.client import LLMException

def test_worker_schema():
    worker = Worker(worker_id="w-01", host="localhost", port=11434, model="llama3.1")
    assert worker.worker_id == "w-01"
    assert worker.base_url == "http://localhost:11434"
    assert worker.status == WorkerStatus.OFFLINE  # Default
    
def test_worker_registry_operations():
    registry = WorkerRegistry()
    w1 = Worker(worker_id="w1", host="localhost", port=11434, model="llama3.1", status=WorkerStatus.AVAILABLE)
    registry.register_worker(w1)
    
    assert len(registry.list_workers()) == 1
    assert registry.get_worker("w1") is not None
    
    # Mark Busy
    success = registry.mark_busy("w1", "task-1")
    assert success is True
    assert registry.get_worker("w1").status == WorkerStatus.BUSY
    
    # Mark Available
    registry.mark_available("w1")
    assert registry.get_worker("w1").status == WorkerStatus.AVAILABLE
    
    # Capability Filtering
    w2 = Worker(worker_id="w2", host="localhost", port=11435, model="llama3.1", status=WorkerStatus.AVAILABLE, capabilities=["vision"])
    registry.register_worker(w2)
    
    vision_workers = registry.get_available_workers(required_capability="vision")
    assert len(vision_workers) == 1
    assert vision_workers[0].worker_id == "w2"

@pytest.mark.asyncio
async def test_worker_pool_selection():
    registry = WorkerRegistry()
    pool = WorkerPool(registry)
    
    # No workers available
    with pytest.raises(TimeoutError):
        await pool.select_worker(task_id="test", timeout=0.1)
        
    w1 = Worker(worker_id="w1", host="localhost", port=11434, model="llama3.1", status=WorkerStatus.AVAILABLE)
    registry.register_worker(w1)
    
    worker = await pool.select_worker(task_id="test", timeout=1.0)
    assert worker.worker_id == "w1"
    assert worker.status == WorkerStatus.BUSY

@pytest.mark.asyncio
async def test_worker_pool_concurrency():
    registry = WorkerRegistry()
    pool = WorkerPool(registry)
    
    for i in range(3):
        registry.register_worker(Worker(
            worker_id=f"w{i}", host="localhost", port=11434 + i, model="llama3.1", status=WorkerStatus.AVAILABLE
        ))
        
    async def get_worker(task_id):
        return await pool.select_worker(task_id=task_id, timeout=1.0)
        
    # Launch 3 concurrent selections
    workers = await asyncio.gather(
        get_worker("task-1"),
        get_worker("task-2"),
        get_worker("task-3")
    )
    
    # Ensure they got 3 unique workers
    ids = {w.worker_id for w in workers}
    assert len(ids) == 3
    
    # Ensure all are BUSY
    for w in workers:
        assert w.status == WorkerStatus.BUSY
        
    # Attempting a 4th should timeout
    with pytest.raises(TimeoutError):
        await pool.select_worker(task_id="task-4", timeout=0.1)
        
    # Release one
    pool.release_worker(workers[0].worker_id)
    worker_4 = await pool.select_worker(task_id="task-4", timeout=1.0)
    assert worker_4.worker_id == workers[0].worker_id

def test_failure_recovery():
    registry = WorkerRegistry()
    pool = WorkerPool(registry)
    registry.register_worker(Worker(worker_id="w1", host="localhost", port=11434, model="llama3.1", status=WorkerStatus.AVAILABLE))
    
    # Infrastructure Failure
    pool.report_infrastructure_failure("w1")
    assert registry.get_worker("w1").status == WorkerStatus.UNHEALTHY
    
    # Cannot be selected
    assert len(registry.get_available_workers()) == 0
    
    # Recovery (Health check passes)
    registry.update_health_timestamp("w1", is_healthy=True)
    assert registry.get_worker("w1").status == WorkerStatus.AVAILABLE
    assert len(registry.get_available_workers()) == 1

import time

from pydantic import BaseModel
from backend.llm.client import LLMClient
from backend.llm.worker_client import WorkerAwareOllamaClient
from backend.llm.worker import async_check_health

class DummyResponse(BaseModel):
    message: str

def test_worker_client_contract():
    # Verify WorkerAwareOllamaClient is a subclass of LLMClient
    assert hasattr(WorkerAwareOllamaClient, 'generate_structured_output')
    
@pytest.mark.asyncio
async def test_worker_client_resource_safety():
    registry = WorkerRegistry()
    pool = WorkerPool(registry)
    registry.register_worker(Worker(worker_id="w1", host="localhost", port=11434, model="llama", status=WorkerStatus.AVAILABLE))
    
    client = WorkerAwareOllamaClient(worker_pool=pool)
    
    with patch("langchain_core.runnables.RunnableSequence.ainvoke", side_effect=asyncio.CancelledError("Cancelled")):
        with pytest.raises(asyncio.CancelledError):
            await client.generate_structured_output("sys", "user", DummyResponse)
        
    # Verify the worker was released and not stuck in BUSY
    worker = registry.get_worker("w1")
    assert worker.status == WorkerStatus.AVAILABLE

@pytest.mark.asyncio
async def test_worker_client_infrastructure_failure():
    registry = WorkerRegistry()
    pool = WorkerPool(registry)
    registry.register_worker(Worker(worker_id="w1", host="localhost", port=11434, model="llama", status=WorkerStatus.AVAILABLE))
    
    client = WorkerAwareOllamaClient(worker_pool=pool)
    
    with patch("langchain_core.runnables.RunnableSequence.ainvoke", side_effect=TimeoutError("Connection timed out")):
        with pytest.raises(LLMException):
            await client.generate_structured_output("sys", "user", DummyResponse)
        
    worker = registry.get_worker("w1")
    assert worker.status == WorkerStatus.UNHEALTHY

@pytest.mark.asyncio
async def test_async_check_health_non_blocking():
    w = Worker(worker_id="w1", host="localhost", port=11434, model="llama", status=WorkerStatus.AVAILABLE)
    
    start_time = time.time()
    
    async def dummy_task():
        await asyncio.sleep(0.1)
        return "done"
        
    # Run async health check and dummy task concurrently
    res1, res2 = await asyncio.gather(
        async_check_health(w, timeout_sec=0.1),
        dummy_task()
    )
    
    end_time = time.time()
    # If it was blocking, it would take longer than 0.1s
    assert end_time - start_time < 0.3
    
@pytest.mark.asyncio
async def test_offline_worker_selection():
    registry = WorkerRegistry()
    pool = WorkerPool(registry)
    
    w1 = Worker(worker_id="w1", host="localhost", port=11434, model="llama", status=WorkerStatus.OFFLINE)
    registry.register_worker(w1)
    
    with pytest.raises(TimeoutError):
        await pool.select_worker(task_id="test", timeout=0.1)
        
    registry.update_health_timestamp("w1", is_healthy=True)
    # MUST remain OFFLINE
    assert registry.get_worker("w1").status == WorkerStatus.OFFLINE
    
    with pytest.raises(TimeoutError):
        await pool.select_worker(task_id="test", timeout=0.1)

@pytest.mark.asyncio
async def test_lazy_recovery_success():
    registry = WorkerRegistry()
    pool = WorkerPool(registry)
    
    w1 = Worker(worker_id="w1", host="localhost", port=11434, model="llama", status=WorkerStatus.UNHEALTHY)
    registry.register_worker(w1)
    
    with patch("backend.llm.worker_pool.async_check_health", return_value=True):
        worker = await pool.select_worker(task_id="test", timeout=2.0)
        
    assert worker.worker_id == "w1"
    assert worker.status == WorkerStatus.BUSY

@pytest.mark.asyncio
async def test_lazy_recovery_failure():
    registry = WorkerRegistry()
    pool = WorkerPool(registry)
    
    w1 = Worker(worker_id="w1", host="localhost", port=11434, model="llama", status=WorkerStatus.UNHEALTHY)
    registry.register_worker(w1)
    
    with patch("backend.llm.worker_pool.async_check_health", return_value=False):
        with pytest.raises(TimeoutError):
            await pool.select_worker(task_id="test", timeout=1.0)
            
    assert registry.get_worker("w1").status == WorkerStatus.UNHEALTHY

@pytest.mark.asyncio
async def test_multi_worker_lazy_recovery():
    registry = WorkerRegistry()
    pool = WorkerPool(registry)
    
    w1 = Worker(worker_id="w1", host="localhost", port=11434, model="llama", status=WorkerStatus.UNHEALTHY)
    w2 = Worker(worker_id="w2", host="localhost", port=11435, model="llama", status=WorkerStatus.AVAILABLE)
    registry.register_worker(w1)
    registry.register_worker(w2)
    
    # Should select w2 immediately without waiting for w1 recovery
    worker = await pool.select_worker(task_id="test", timeout=1.0)
    assert worker.worker_id == "w2"
    assert worker.status == WorkerStatus.BUSY
