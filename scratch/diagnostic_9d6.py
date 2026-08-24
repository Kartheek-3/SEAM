import asyncio
import time
import json
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.llm.ollama_client import OllamaClient
from agents.planning.internal_schemas import Pass2TaskResult
from backend.schemas.planning import ComponentSpec
from agents.planning.prompts import PASS_2_SYSTEM_PROMPT, PASS_2_USER_PROMPT_TEMPLATE
from pydantic import ValidationError

logging.basicConfig(level=logging.INFO)

async def measure_pass2(client, name, component_spec, req_text, arch_summary, existing_tasks, reps=3):
    print(f"\n--- Running Diagnostic for {name} ---")
    results = []
    
    component_json = component_spec.model_dump_json(indent=2)
    user_prompt = PASS_2_USER_PROMPT_TEMPLATE.format(
        compact_requirements=req_text,
        architecture_summary=arch_summary,
        existing_tasks_context=existing_tasks,
        component_json=component_json,
        instructions="Execute task",
        rework_section=""
    )
    
    for i in range(reps):
        start = time.time()
        success = False
        timeout = False
        validation_error = None
        tasks_count = 0
        
        try:
            res = await client.generate_structured_output(
                system_prompt=PASS_2_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                response_model=Pass2TaskResult
            )
            success = True
            tasks_count = len(res.tasks)
        except ValidationError as e:
            validation_error = str(e)
        except Exception as e:
            if "timeout" in str(e).lower() or "read operation timed out" in str(e).lower():
                timeout = True
            else:
                validation_error = str(e)
                
        duration = time.time() - start
        
        rep_result = {
            "rep": i + 1,
            "duration": duration,
            "success": success,
            "timeout": timeout,
            "validation_error": bool(validation_error),
            "tasks_count": tasks_count,
            "prompt_chars": len(user_prompt) + len(PASS_2_SYSTEM_PROMPT),
            "req_chars": len(req_text),
            "arch_chars": len(arch_summary),
            "existing_chars": len(existing_tasks),
        }
        print(f"Rep {i+1}: {duration:.2f}s | Success={success} | Timeout={timeout} | Tasks={tasks_count}")
        results.append(rep_result)
        
    return results

async def main():
    client = OllamaClient(model_name="llama3.1")
    
    # 1. Product Service Production Fake Data
    req_text = "- REQ-1: Product catalog retrieval (must)\n- REQ-2: Product search (must)\n- REQ-3: Fast response times (must)"
    arch_summary = "A scalable microservice architecture using REST APIs for Product and Cart. Postgres for relational storage."
    existing_tasks = "Task ID: 123 - Setup DB\nTask ID: 124 - Setup auth"
    
    prod_comp = ComponentSpec(
        name="Product Service",
        description="Handles product catalog retrieval, filtering, and search functionality. Connects to Postgres.",
        responsibilities=["Product retrieval", "Product search", "Caching", "Rate limiting"],
        dependencies=["Database", "Auth Service"]
    )
    
    # 2. Minimal Controlled Component
    minimal_comp = ComponentSpec(
        name="Ping API",
        description="Returns 200 OK",
        responsibilities=["Healthcheck"],
        dependencies=[]
    )
    minimal_req_text = "- REQ-1: Healthcheck (must)"
    
    print("\nStarting Jitter Diagnostic...")
    
    prod_res = await measure_pass2(
        client, "Production Product Service", prod_comp, req_text, arch_summary, existing_tasks, reps=3
    )
    
    min_res = await measure_pass2(
        client, "Minimal Ping API", minimal_comp, minimal_req_text, "A simple server", "No previous tasks exist yet.", reps=3
    )
    
    with open("scratch/diagnostic_results.json", "w") as f:
        json.dump({"prod": prod_res, "min": min_res}, f, indent=2)
        
if __name__ == "__main__":
    asyncio.run(main())
