import asyncio
import logging
from pydantic import BaseModel

from backend.llm.worker_registry import WorkerRegistry
from backend.llm.worker_pool import WorkerPool
from backend.llm.worker import Worker, WorkerStatus
from backend.llm.worker_client import WorkerAwareOllamaClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class TestResponse(BaseModel):
    message: str

async def main():
    registry = WorkerRegistry()
    pool = WorkerPool(registry)
    
    # Register single worker
    w = Worker(worker_id="default-worker-1", host="localhost", port=11434, model="llama3.1", status=WorkerStatus.AVAILABLE)
    registry.register_worker(w)
    
    client = WorkerAwareOllamaClient(worker_pool=pool, model_name="llama3.1")
    
    logging.info("--- 1. Initial structured request ---")
    res1 = await client.generate_structured_output(
        system_prompt="You are a helpful assistant.",
        user_prompt="Reply with a simple greeting in the JSON schema requested.",
        response_model=TestResponse
    )
    logging.info(f"Response 1: {res1.message}")
    
    logging.info("--- 2. Induce infrastructure failure ---")
    pool.report_infrastructure_failure("default-worker-1")
    w = registry.get_worker("default-worker-1")
    logging.info(f"Worker status is now: {w.status}")
    
    logging.info("--- 3. Second structured request (triggers lazy recovery) ---")
    res2 = await client.generate_structured_output(
        system_prompt="You are a helpful assistant.",
        user_prompt="Reply with a farewell in the JSON schema requested.",
        response_model=TestResponse
    )
    logging.info(f"Response 2: {res2.message}")
    
    w = registry.get_worker("default-worker-1")
    logging.info(f"Final worker status: {w.status}")

if __name__ == "__main__":
    asyncio.run(main())
