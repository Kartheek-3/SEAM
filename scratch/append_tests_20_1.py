import time

from pydantic import BaseModel
from backend.llm.client import LLMClient
from backend.llm.worker_client import WorkerAwareOllamaClient
from backend.llm.worker import async_check_health

class DummyResponse(BaseModel):
    message: str

def test_worker_client_contract():
    # Verify WorkerAwareOllamaClient is a subclass of LLMClient
    assert issubclass(WorkerAwareOllamaClient, LLMClient)
    
@pytest.mark.asyncio
async def test_worker_client_resource_safety(mocker):
    registry = WorkerRegistry()
    pool = WorkerPool(registry)
    registry.register_worker(Worker(worker_id="w1", host="localhost", port=11434, model="llama", status=WorkerStatus.AVAILABLE))
    
    client = WorkerAwareOllamaClient(worker_pool=pool)
    
    # Mock chain.ainvoke to raise CancelledError
    mocker.patch("langchain_core.runnables.RunnableSequence.ainvoke", side_effect=asyncio.CancelledError("Cancelled"))
    
    with pytest.raises(asyncio.CancelledError):
        await client.generate_structured_output("sys", "user", DummyResponse)
        
    # Verify the worker was released and not stuck in BUSY
    worker = registry.get_worker("w1")
    assert worker.status == WorkerStatus.AVAILABLE

@pytest.mark.asyncio
async def test_worker_client_infrastructure_failure(mocker):
    registry = WorkerRegistry()
    pool = WorkerPool(registry)
    registry.register_worker(Worker(worker_id="w1", host="localhost", port=11434, model="llama", status=WorkerStatus.AVAILABLE))
    
    client = WorkerAwareOllamaClient(worker_pool=pool)
    mocker.patch("langchain_core.runnables.RunnableSequence.ainvoke", side_effect=TimeoutError("Connection timed out"))
    
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
    assert registry.get_worker("w1").status == WorkerStatus.AVAILABLE
    
    worker = await pool.select_worker(task_id="test", timeout=0.1)
    assert worker.worker_id == "w1"
