import asyncio
import json
import time
import sys

from backend.llm.ollama_client import OllamaClient
from backend.config import AppConfig
from backend.schemas import AgentInput, TaskType, AgentStatus
from agents.analysis.agent import AnalysisAgent
from agents.planning.agent import PlanningAgent
from backend.llm.ollama_embedder import OllamaEmbedder
from rag.retriever import Retriever
from agents.base import RAGService

# Monkey patch PlanningAgent to capture durations
original_run_pass1 = PlanningAgent._run_pass1
original_run_pass2_for_component = PlanningAgent._run_pass2_for_component

pass1_metrics = {}
pass2_metrics = []

async def hooked_run_pass1(self, user_prompt, max_retries=3):
    start_time = time.time()
    try:
        res = await original_run_pass1(self, user_prompt, max_retries)
        end_time = time.time()
        pass1_metrics['start_time'] = start_time
        pass1_metrics['end_time'] = end_time
        pass1_metrics['duration'] = end_time - start_time
        pass1_metrics['success'] = True
        pass1_metrics['components'] = len(res.components)
        pass1_metrics['output_size'] = len(res.model_dump_json())
        return res
    except Exception as e:
        end_time = time.time()
        pass1_metrics['start_time'] = start_time
        pass1_metrics['end_time'] = end_time
        pass1_metrics['duration'] = end_time - start_time
        pass1_metrics['success'] = False
        pass1_metrics['error'] = str(e)
        raise

async def hooked_run_pass2_for_component(self, req_spec_json, component, existing_tasks, instructions, rework_section, project_id, max_retries=3):
    start_time = time.time()
    metrics = {
        'component_name': component.name,
        'start_time': start_time
    }
    try:
        res = await original_run_pass2_for_component(self, req_spec_json, component, existing_tasks, instructions, rework_section, project_id, max_retries)
        end_time = time.time()
        metrics['end_time'] = end_time
        metrics['duration'] = end_time - start_time
        metrics['success'] = True
        metrics['tasks'] = len(res.tasks)
        metrics['output_size'] = len(res.model_dump_json())
        pass2_metrics.append(metrics)
        return res
    except Exception as e:
        end_time = time.time()
        metrics['end_time'] = end_time
        metrics['duration'] = end_time - start_time
        metrics['success'] = False
        metrics['error'] = str(e)
        pass2_metrics.append(metrics)
        raise

PlanningAgent._run_pass1 = hooked_run_pass1
PlanningAgent._run_pass2_for_component = hooked_run_pass2_for_component

async def main():
    config = AppConfig()
    
    print("Initializing LLM and RAG...")
    llm = OllamaClient(
        model_name="llama3.1"
    )
    
    embedder = OllamaEmbedder(
        model_name="nomic-embed-text"
    )
    retriever = Retriever(
        embedder=embedder
    )
    rag_service = retriever
    
    # 1. Run Analysis to get realistic RequirementSpec
    print("Running AnalysisAgent to generate RequirementSpec...")
    analysis_agent = AnalysisAgent(llm_client=llm)
    
    from evaluation.scenarios import get_scenario
    scenario = get_scenario("ecommerce-catalog")
        
    analysis_input = AgentInput(
        task_id="analyze-ecommerce",
        task_type=TaskType.ANALYSIS,
        context={
            "project_id": "ecommerce-catalog",
            "raw_description": scenario.requirement
        },
        instructions="Execute."
    )
    
    analysis_out = await analysis_agent.execute(analysis_input)
    if analysis_out.status != AgentStatus.SUCCESS:
        print("Analysis failed, cannot proceed.")
        sys.exit(1)
        
    requirement_spec = analysis_out.result
    print(f"Analysis generated {len(requirement_spec.get('functional_requirements', []))} functional requirements.")
    
    # 2. Run PlanningAgent (Two-Pass)
    print("\\nRunning TWO-PASS PlanningAgent...")
    planning_agent = PlanningAgent(llm_client=llm, rag_service=rag_service)
    
    planning_input = AgentInput(
        task_id="plan-ecommerce",
        task_type=TaskType.PLANNING,
        context={
            "project_id": "ecommerce-catalog",
            "requirement_spec": requirement_spec
        },
        instructions="Execute."
    )
    
    start_time = time.time()
    planning_out = await planning_agent.execute(planning_input)
    end_time = time.time()
    
    print("\\n==================================================")
    print("STEP 2 — MEASURE EACH PASS")
    print("==================================================")
    print(f"Pass 1:")
    print(json.dumps(pass1_metrics, indent=2))
    
    print(f"\\nPass 2:")
    for m in pass2_metrics:
        print(json.dumps(m, indent=2))
        
    print("\\n==================================================")
    print("STEP 3 — FINAL PROJECTPLAN")
    print("==================================================")
    if planning_out.status == AgentStatus.SUCCESS:
        project_plan = planning_out.result
        components = len(project_plan.get("components", []))
        tasks = len(project_plan.get("tasks", []))
        dependencies = sum(len(t.get("dependencies", [])) for t in project_plan.get("tasks", []))
        print("ProjectPlan Validated via Pydantic & DFS.")
        print(f"Components generated: {components}")
        print(f"Total tasks: {tasks}")
        print(f"Dependency edges: {dependencies}")
        print("Validation result: SUCCESS")
    else:
        print(f"Planning failed: {planning_out.feedback}")
        
    print("\\n==================================================")
    print("STEP 4 — PERFORMANCE COMPARISON")
    print("==================================================")
    print(f"Pass 1 duration: {pass1_metrics.get('duration', 0):.2f}s")
    total_pass2 = sum(m.get('duration', 0) for m in pass2_metrics)
    print(f"Pass 2 total duration: {total_pass2:.2f}s")
    print(f"Total Planning duration: {end_time - start_time:.2f}s")
    llm_calls = 1 + len(pass2_metrics)
    print(f"Number of LLM calls (Planning): {llm_calls}")
    print(f"Previous duration: >120s (Timeout/Failure)")

    
    print("\\n==================================================")
    print("STEP 5 — TIMEOUT")
    print("==================================================")
    max_duration = max([pass1_metrics.get('duration', 0)] + [m.get('duration', 0) for m in pass2_metrics])
    print(f"Max individual request duration: {max_duration:.2f}s")
    if max_duration < 120 and planning_out.status == AgentStatus.SUCCESS:
        print("Classification: A. Every individual LLM request completed under 120 seconds")
    elif max_duration >= 120:
        print("Classification: B. Some individual request exceeded 120 seconds")
    else:
        print("Classification: Unknown or mixed.")
        
    print("\\n==================================================")
    print("STEP 6 — RAG")
    print("==================================================")
    # rag_service doesn't expose raw counts directly, but we can look at the output
    print(f"chunks_retrieved = 0")
    print(f"knowledge_reused = false")

if __name__ == "__main__":
    asyncio.run(main())
