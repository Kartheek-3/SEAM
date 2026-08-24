import os

test_file = "tests/backend/llm/test_worker_pool.py"

with open(test_file, "r") as f:
    content = f.read()

# Fix the offline worker test
content = content.replace(
"""    registry.update_health_timestamp("w1", is_healthy=True)
    assert registry.get_worker("w1").status == WorkerStatus.AVAILABLE
    
    worker = await pool.select_worker(task_id="test", timeout=0.1)
    assert worker.worker_id == "w1"
""",
"""    registry.update_health_timestamp("w1", is_healthy=True)
    # MUST remain OFFLINE
    assert registry.get_worker("w1").status == WorkerStatus.OFFLINE
    
    with pytest.raises(TimeoutError):
        await pool.select_worker(task_id="test", timeout=0.1)
"""
)

# Add deterministic tests
new_tests = """
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
"""

with open(test_file, "w") as f:
    f.write(content + new_tests)

print("Tests updated.")
