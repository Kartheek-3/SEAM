import asyncio
import time
import json
import os
import sys
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.llm.ollama_client import OllamaClient
from agents.coding.agent import CodingAgent
from agents.qa.agent import QAAgent
from backend.schemas.agent_io import AgentInput, AgentOutput
from backend.schemas.enums import TaskType, AgentStatus
from backend.schemas.qa import ReworkFeedback, QAResult, QAFinding

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

async def run_rework_loop():
    print("="*60)
    print("PHASE 9D.19: QA SEMANTICS & REWORK EFFECTIVENESS DIAGNOSTIC")
    print("="*60)
    
    llm = OllamaClient()
    coding_agent = CodingAgent(llm_client=llm)
    llm.generate_structured_response = llm.generate_structured_output
    qa_agent = QAAgent(llm_client=llm)
    
    task_data = {
        "requirements": "Create a FastAPI endpoint /orders that accepts a POST request to store an order in MongoDB.",
        "acceptance_criteria": [
            "Must use FastAPI.",
            "Must connect to MongoDB.",
            "Order payload must require order_id and customer_name.",
            "Must handle database connection timeouts gracefully."
        ]
    }
    
    task_id = "test-ecommerce-orders"
    instructions = "Implement the /orders endpoint exactly as required."
    
    rework_feedback = None
    artifacts = []
    
    for attempt in range(1, 4):
        print(f"\n--- LOOP {attempt} : CODING ---")
        
        coding_input = AgentInput(
            task_id=task_id,
            task_type=TaskType.CODING,
            instructions=instructions,
            context={"task_data": task_data},
            dependencies=[],
            rework_feedback=rework_feedback
        )
        
        coding_output = await coding_agent.execute(coding_input)
        if coding_output.status != AgentStatus.SUCCESS:
            print(f"Coding failed: {coding_output.feedback}")
            return
            
        artifacts = coding_output.artifacts
        print(f"Generated {len(artifacts)} artifacts.")
        for a in artifacts:
            print(f"\n[Artifact: {a.name}]\n{a.content[:300]}...\n")
            
        print(f"\n--- LOOP {attempt} : QA ---")
        
        qa_input = AgentInput(
            task_id=task_id,
            task_type=TaskType.QA,
            instructions=instructions,
            context={
                "task_data": task_data,
                "dependency_outputs": artifacts
            },
            dependencies=[]
        )
        
        qa_output = await qa_agent.execute(qa_input)
        if qa_output.status != AgentStatus.SUCCESS:
            print(f"QA execution failed: {qa_output.feedback}")
            return
            
        qa_result_dict = qa_output.result
        verdict = qa_result_dict.get("verdict")
        findings = qa_result_dict.get("findings", [])
        
        print(f"QA Verdict: {verdict}")
        print(f"Tests Passed: {qa_result_dict.get('tests_passed')} / {qa_result_dict.get('tests_total')}")
        
        print("Findings:")
        for f in findings:
            print(f"  - [{f.get('severity')}] {f.get('description')}")
            
        if verdict == "pass":
            print("\nSUCCESS! QA Passed.")
            break
            
        print("\nQA Failed. Constructing ReworkFeedback...")
        
        # Convert raw dicts back to QAFinding models to satisfy the AgentInput signature
        pydantic_findings = [QAFinding(**f) for f in findings]
        
        rework_feedback = ReworkFeedback(
            qa_result=QAResult(**qa_result_dict),
            instructions="Fix the defects identified by QA.",
            focus_areas=["MongoDB connection", "Timeout handling", "Schema validation"]
        )

if __name__ == "__main__":
    asyncio.run(run_rework_loop())
