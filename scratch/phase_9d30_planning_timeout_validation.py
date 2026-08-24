import asyncio
import logging
import os
import sys

# Configure path so we can import from SEAM
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.config import settings
from backend.llm.worker_pool import WorkerPool
from backend.llm.worker_registry import WorkerRegistry
from backend.llm.worker import Worker, WorkerStatus
from backend.llm.worker_client import WorkerAwareOllamaClient
from evaluation.runner import TelemetryLLMClient
from agents.planning.agent import PlanningAgent
from backend.schemas import AgentInput, TaskType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_planning_validation():
    logger.info(f"Using ollama_timeout={settings.ollama_timeout}s, worker_lease_timeout={settings.worker_lease_timeout}s")
    
    # 1. Setup minimal worker pool
    registry = WorkerRegistry()
    w = Worker(
        worker_id="default-worker-1",
        host="localhost",
        port=11434,
        model=settings.ollama_model_general,
        status=WorkerStatus.AVAILABLE
    )
    registry.register_worker(w)
    pool = WorkerPool(registry)
    
    # 2. Setup LLM client
    raw_llm_client = WorkerAwareOllamaClient(worker_pool=pool)
    llm_client = TelemetryLLMClient(raw_llm_client)
    
    # 3. Setup dummy analysis output (requirement spec)
    dummy_requirement_spec = {
        "summary": "A complex e-commerce catalog API.",
        "requirements": [
            "Users can view products.",
            "Users can add products to cart.",
            "Users can checkout."
        ],
        "constraints": ["Must use Python", "Must use FastAPI"]
    }
    
    # 4. Run Planning Agent
    planning_agent = PlanningAgent(llm_client=llm_client)
    planning_in = AgentInput(
        task_id="planning-validation-1",
        task_type=TaskType.PLANNING,
        context={"requirement_spec": dummy_requirement_spec, "project_id": "test-project"},
        instructions="Create project plan"
    )
    
    logger.info("Executing PlanningAgent...")
    result = await planning_agent.execute(planning_in)
    
    logger.info(f"Planning Agent Status: {result.status}")
    if result.status == "success":
        logger.info("Validation PASSED: PlanningAgent completed successfully without timeout.")
    else:
        logger.error(f"Validation FAILED: PlanningAgent failed with feedback: {result.feedback}")

if __name__ == "__main__":
    asyncio.run(run_planning_validation())
