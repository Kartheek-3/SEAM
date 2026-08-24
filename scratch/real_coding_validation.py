import asyncio
import json
import logging
import py_compile
import os
import sys

from backend.llm.worker_registry import global_registry
from backend.llm.worker_pool import WorkerPool
from backend.llm.worker import Worker, WorkerStatus
from backend.llm.worker_client import WorkerAwareOllamaClient
from backend.schemas.task import Task
from backend.schemas.enums import TaskType
from backend.schemas.agent_io import AgentInput, AgentStatus
from backend.schemas.qa import ReworkFeedback, QAResult, QAVerdict, FindingSeverity, QAFinding
from agents.coding.agent import CodingAgent

logging.basicConfig(level=logging.INFO)

async def run_real_validation():
    print("====================================")
    print("REAL ISOLATED CODING VALIDATION")
    print("====================================")
    
    global_registry._workers.clear()
    w = Worker(worker_id="default-worker-1", host="localhost", port=11434, model="llama3.1", status=WorkerStatus.AVAILABLE)
    global_registry.register_worker(w)
    pool = WorkerPool(global_registry)
    client = WorkerAwareOllamaClient(worker_pool=pool, model_name="llama3.1")
    agent = CodingAgent(llm_client=client)
    
    tasks = [] # Skipped since they already passed
    
    results = []
    
    for i, t in enumerate(tasks):
        print(f"\\n--- Task {i+1}: {t['desc']} ---")
        inp = AgentInput(
            task_id=f"real-task-{i}",
            task_type=TaskType.CODING,
            instructions=t['desc'],
            context={"project_id": "test"}
        )
        
        out = await agent.execute(inp)
        
        print(f"Status: {out.status}")
        if out.status == AgentStatus.SUCCESS:
            print(f"Artifacts: {len(out.artifacts)}")
            print(f"Time: {out.execution_time_ms} ms")
            # Syntax validation
            for art in out.artifacts:
                temp_file = f"scratch/temp_{i}_{art.name.replace('/', '_')}"
                with open(temp_file, "w") as f:
                    f.write(art.content)
                try:
                    py_compile.compile(temp_file, doraise=True)
                    print(f"[{art.name}] SYNTAX_VALID")
                    results.append("SYNTAX_VALID")
                except py_compile.PyCompileError as e:
                    print(f"[{art.name}] SYNTAX_INVALID: {e}")
                    results.append("SYNTAX_INVALID")
        else:
            print(f"Feedback: {out.feedback}")
            results.append("FAIL")
            
    print("\\n\\n====================================")
    print("REAL ISOLATED REWORK VALIDATION")
    print("====================================")
    
    rework_tasks = [
        {"desc": "Fix the division function to handle ZeroDivisionError.", "orig": "def div(a,b): return a/b", "fb": "Missing error handling for division by zero."},
        {"desc": "Add an email regex validator to the User model.", "orig": "class User: email: str", "fb": "Missing email validation."},
        {"desc": "Add a timeout to the requests.get call.", "orig": "import requests\\nrequests.get('http://api')", "fb": "Missing timeout handling on external request."}
    ]
    
    from datetime import datetime, timezone
    
    for i, t in enumerate(rework_tasks):
        print(f"\\n--- Rework Task {i+1}: {t['desc']} ---")
        
        rework = ReworkFeedback(
            source_task_id=f"rw-{i}",
            qa_result=QAResult(
                task_id=f"qa-rw-{i}",
                verdict=QAVerdict.FAIL,
                score=0.0,
                findings=[QAFinding(category="code_review", description=t["fb"], severity=FindingSeverity.MAJOR)],
                evaluated_at=datetime.now(timezone.utc)
            ),
            instructions=t["desc"],
            focus_areas=["error_handling"]
        )
        
        inp = AgentInput(
            task_id=f"real-rw-{i}",
            task_type=TaskType.CODING,
            instructions=t['desc'],
            context={"project_id": "test"},
            rework_feedback=rework
        )
        
        out = await agent.execute(inp)
        print(f"Status: {out.status}")
        if out.status == AgentStatus.SUCCESS:
            print(f"Artifacts: {len(out.artifacts)}")
            print(f"Time: {out.execution_time_ms} ms")
        else:
            print(f"Feedback: {out.feedback}")
            
    print("\\n\\n====================================")
    print("CONTEXT SIZE VALIDATION")
    print("====================================")
    
    contexts = [
        {"label": "Minimal context", "deps": []},
        {"label": "Realistic single-file context", "deps": [{"id": "a", "name": "foo.py", "type": "code", "content": "x = 1"}]},
        {"label": "Realistic multi-file context", "deps": [
            {"id": "a", "name": "foo.py", "type": "code", "content": "x = 1"},
            {"id": "b", "name": "bar.py", "type": "code", "content": "y = 2"},
            {"id": "c", "name": "baz.py", "type": "code", "content": "z = 3"}
        ]}
    ]
    
    for ctx in contexts:
        print(f"\\n--- Context: {ctx['label']} ---")
        inp = AgentInput(
            task_id=f"ctx-test",
            task_type=TaskType.CODING,
            instructions="Write a python function that returns True.",
            context={"project_id": "test", "dependency_outputs": ctx["deps"]}
        )
        out = await agent.execute(inp)
        print(f"Status: {out.status}")
        if out.status == AgentStatus.SUCCESS:
            print(f"Artifacts: {len(out.artifacts)}")
            print(f"Time: {out.execution_time_ms} ms")
        else:
            print(f"Feedback: {out.feedback}")

if __name__ == "__main__":
    asyncio.run(run_real_validation())
