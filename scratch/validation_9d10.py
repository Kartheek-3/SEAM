import asyncio
import time
import json
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.schemas import AgentInput, TaskType
from backend.llm.ollama_client import OllamaClient
from agents.coding.agent import CodingAgent

logging.basicConfig(level=logging.INFO)

async def main():
    print("Starting Phase 9D.10 Validation...")
    
    # 1. Create bloated fake dependency output simulating earlier pipeline tasks
    bloated_code = "import os\n" + "def do_something_complex():\n    pass\n" * 200
    
    # Needs to match what Supervisor puts in context["dependency_outputs"]
    # which is a list of dictionary representations of Artifacts
    raw_deps = [
        {
            "id": "art-1",
            "project_id": "p-1",
            "task_id": "task-0",
            "type": "code",
            "name": "src/old_module.py",
            "content": bloated_code,
            "language": "python",
            "created_at": "2026-08-16T12:00:00Z"
        }
    ]
    
    instructions = "Create a Flask application for Products. It needs a main.py defining the API, a models.py defining the database model, and a requirements.txt file."
    task_data = {"auth": "jwt"}
    
    input_data = AgentInput(
        task_id="coding-test",
        task_type=TaskType.CODING,
        context={
            "task_data": task_data,
            "dependency_outputs": raw_deps
        },
        instructions=instructions,
        dependencies=["task-0"]
    )
    
    # Use real OllamaClient
    from evaluation.runner import TelemetryLLMClient
    
    base_llm = OllamaClient(model_name="llama3.1")
    llm_client = TelemetryLLMClient(base_llm)
    agent = CodingAgent(llm_client=llm_client)
    
    # Inspect prompt sizes
    prompt_text = agent._format_prompt(input_data)
    prompt_len = len(prompt_text)
    
    print(f"\nPrompt length BEFORE LLM execution: {prompt_len} chars")
    
    results = []
    for i in range(3):
        start = time.time()
        print(f"\nRunning Rep {i+1}...")
        
        try:
            out = await agent.execute(input_data)
            duration = time.time() - start
            success = (out.status == "success")
            files_gen = len(out.artifacts)
            feedback = out.feedback
            
            print(f"Rep {i+1} finished in {duration:.2f}s | Success={success} | Files={files_gen} | Feedback={feedback}")
            results.append({
                "rep": i+1,
                "duration": duration,
                "success": success,
                "files_gen": files_gen,
                "prompt_len": prompt_len
            })
        except Exception as e:
            duration = time.time() - start
            print(f"Rep {i+1} FAILED in {duration:.2f}s | Exception={e}")
            results.append({
                "rep": i+1,
                "duration": duration,
                "success": False,
                "error": str(e)
            })
            
    # Calculate stats
    successes = sum(1 for r in results if r["success"])
    print(f"\nFinal Result: {successes}/3 Success!")

if __name__ == "__main__":
    asyncio.run(main())
