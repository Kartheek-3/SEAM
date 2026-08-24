import asyncio
import time
import json
import uuid

from backend.llm.worker_registry import global_registry
from backend.llm.worker_pool import WorkerPool
from backend.llm.worker import Worker, WorkerStatus
from backend.llm.worker_client import WorkerAwareOllamaClient
from backend.schemas.task import Task
from backend.schemas.enums import TaskType, TaskStatus
from backend.schemas.agent_io import AgentInput
from agents.coding.agent import CodingAgent
from agents.qa.agent import QAAgent
from datetime import datetime, timezone

async def main():
    # Setup Worker Pool
    global_registry._workers.clear()
    w = Worker(worker_id="default-worker-1", host="localhost", port=11434, model="llama3.1", status=WorkerStatus.AVAILABLE)
    global_registry.register_worker(w)
    pool = WorkerPool(global_registry)
    client = WorkerAwareOllamaClient(worker_pool=pool, model_name="llama3.1")
    
    # Initialize Agents
    coding_agent = CodingAgent(llm_client=client)
    qa_agent = QAAgent(llm_client=client)
    
    # Define Controlled Task
    task_id = str(uuid.uuid4())
    task = Task(
        id=task_id,
        project_id="test",
        title="Product Catalog API",
        description="Create a FastAPI router with GET /products (list products) and POST /products (create product) endpoints.",
        type=TaskType.CODING,
        created_at=datetime.now(timezone.utc),
        input_data={
            "acceptance_criteria": [
                "Must use FastAPI APIRouter.",
                "Must define GET /products endpoint returning a list of dicts.",
                "Must define POST /products endpoint returning the created product dict.",
                "Must include Pydantic models for request and response."
            ]
        }
    )
    
    agent_input = AgentInput(
        task_id=task.id,
        task_type=task.type,
        instructions=task.description,
        context={
            "task_data": task.model_dump(mode="json"),
            "dependency_outputs": [],
            "project_id": task.project_id
        }
    )
    
    print("========================================")
    print("STEP 2 - CODING GENERATION")
    print("========================================")
    
    artifact = None
    try:
        coding_output = await coding_agent.execute(agent_input)
        print(f"Coding output status: {coding_output.status}")
        if coding_output.artifacts:
            artifact = coding_output.artifacts[0]
            print(f"Generated {len(coding_output.artifacts)} artifacts. Showing first:")
            print(artifact.content)
    except Exception as e:
        print(f"Coding failed: {e}")
        return

    if not artifact:
        print("No artifact generated")
        return

    print("\n========================================")
    print("STEP 3 - QA EVALUATION")
    print("========================================")
    qa_input = AgentInput(
        task_id=task.id,
        task_type=TaskType.QA,
        instructions=f"Evaluate artifact for task {task.title}",
        context={
            "task_data": task.model_dump(mode="json"),
            "artifact_data": artifact.model_dump(mode="json"),
            "project_id": task.project_id
        }
    )
    
    qa_result = None
    try:
        qa_output = await qa_agent.execute(qa_input)
        qa_result = qa_output.result
        print(f"QA Result dict: {json.dumps(qa_result, indent=2)}")
    except Exception as e:
        print(f"QA failed: {e}")
        return

    print("\n========================================")
    print("STEP 5 - REWORK ANALYSIS")
    print("========================================")
    if qa_result and qa_result.get("status") == "fail":
        from backend.schemas.qa import ReworkFeedback
        
        # We must construct a proper QA Evaluation Response and ReworkFeedback
        # For simplicity, we just use the raw qa_result dictionary if possible
        print("Rework needed!")
        # Rework simulation would happen here if we map the QA output to ReworkFeedback correctly
        
if __name__ == "__main__":
    asyncio.run(main())
