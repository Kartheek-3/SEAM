import asyncio
import time
import json
from pydantic import ValidationError
from backend.llm.ollama_client import OllamaClient
from backend.schemas import ProjectPlan, RequirementSpec, RequirementItem

CURRENT_SYSTEM_PROMPT = """You are an expert Software Architect and Technical Project Manager.
Your task is to transform a structured RequirementSpec into an actionable ProjectPlan.
You must design the system components, select technology, and produce a fully decomposed list of tasks.

CRITICAL DIRECTIVES:
1. DO NOT invent unsupported features not found in the requirements.
2. Ensure task dependencies form a valid Directed Acyclic Graph (DAG) without circular dependencies.
3. Because the schemas are strict, embed Database requirements, API requirements, and Security considerations inside the component 'responsibilities' list or project 'architecture_summary'.
4. Because the Task schema is strict, embed testable acceptance criteria inside the task 'input_data' dictionary using the key "acceptance_criteria".
5. Use valid TaskType values: 'analysis', 'planning', 'coding', 'qa', 'delivery'. For general development tasks, use 'coding'.
6. Every task MUST have a unique string 'id' (e.g. 'T-1', 'T-2').
"""

OPTIMIZED_SYSTEM_PROMPT = """You are a Software Architect generating a minimal ProjectPlan JSON.

CRITICAL JSON OPTIMIZATION DIRECTIVES:
1. Output ONLY valid JSON. No markdown, no explanations, no text before or after.
2. OMIT ALL OPTIONAL/DEFAULT FIELDS in Task. Do NOT output: status, priority, dependencies, assigned_agent, input_data, output_data, rework_count, quality_score, completed_at.
3. Only output these Task fields: id, project_id, title, description, type, created_at.
4. Keep descriptions < 10 words.
5. Generate ONLY 1 minimal task per component.
6. Do NOT add ANY unnecessary fields, subtasks, or criteria.
7. OMIT empty arrays if possible (e.g., technology_recommendations).
"""

# Ecommerce Spec (Mocked realistically)
ecommerce_spec = RequirementSpec(
    project_id="ecommerce-catalog",
    functional_requirements=[
        RequirementItem(id="FR-1", description="User can view catalog", category="functional", priority="must"),
        RequirementItem(id="FR-2", description="User can add to cart", category="functional", priority="must")
    ],
    non_functional_requirements=[],
    ambiguities=[],
    assumptions=[],
    domain_entities=["Product", "Cart"]
)

ecommerce_spec_json = ecommerce_spec.model_dump_json(indent=2)

async def test_prompt(name: str, system_prompt: str, user_prompt: str):
    client = OllamaClient(model_name="llama3.1")
    print(f"\n--- RUNNING TEST: {name} ---")
    start_time = time.time()
    try:
        result = await client.generate_structured_output(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=ProjectPlan
        )
        duration = time.time() - start_time
        num_tasks = len(result.tasks)
        num_components = len(result.components)
        output_size = len(result.model_dump_json())
        print(f"[{name}] SUCCESS")
        print(f"[{name}] Duration: {duration:.2f}s")
        print(f"[{name}] Components: {num_components}")
        print(f"[{name}] Tasks: {num_tasks}")
        print(f"[{name}] Output Size: {output_size} bytes")
        print(f"[{name}] Valid: True")
        return {"duration": duration, "tasks": num_tasks, "components": num_components, "size": output_size, "valid": True, "result": result}
    except Exception as e:
        duration = time.time() - start_time
        print(f"[{name}] FAILED")
        print(f"[{name}] Duration: {duration:.2f}s")
        print(f"[{name}] Error: {e}")
        return {"duration": duration, "tasks": 0, "components": 0, "size": 0, "valid": False, "result": None}

async def main():
    # 1. Minimal Requirement Test
    minimal_req = "Goal: Hello World"
    res_a = await test_prompt("TEST A (Current Prompt / Minimal Req)", CURRENT_SYSTEM_PROMPT, minimal_req)
    res_b = await test_prompt("TEST B (Optimized Prompt / Minimal Req)", OPTIMIZED_SYSTEM_PROMPT, minimal_req)
    
    # 2. Realistic Test (Ecommerce)
    res_c = None
    if res_b["valid"]:
        res_c = await test_prompt("TEST C (Optimized Prompt / Ecommerce Req)", OPTIMIZED_SYSTEM_PROMPT, ecommerce_spec_json)

    print("\n\n--- FINAL COMPARISON ---")
    print("| Test | Prompt | Duration | Tasks | Components | Output Size | Valid |")
    print("|------|--------|----------|-------|------------|-------------|-------|")
    
    def format_row(name, prompt, res):
        if res is None: return ""
        return f"| {name} | {prompt} | {res['duration']:.2f}s | {res['tasks']} | {res['components']} | {res['size']} | {res['valid']} |"
        
    print(format_row("Minimal", "Current", res_a))
    print(format_row("Minimal", "Optimized", res_b))
    if res_c:
        print(format_row("Ecommerce", "Optimized", res_c))
        
    if res_a['valid'] and res_b['valid']:
        improvement = ((res_a['duration'] - res_b['duration']) / res_a['duration']) * 100
        print(f"\nApproximate minimal test improvement: {improvement:.2f}%")

if __name__ == "__main__":
    asyncio.run(main())
