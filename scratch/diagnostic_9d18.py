import asyncio
import time
import json
import os
import sys
import logging
from io import StringIO

# Ensure import paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.llm.ollama_client import OllamaClient
from agents.qa.agent import QAAgent
from backend.schemas.agent_io import AgentInput
from backend.schemas import TaskType

async def run_qa_execution(rep_num, artifacts_text):
    print(f"\n--- Execution {rep_num} ---")
    
    # Capture logs to string buffer
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    qa_logger = logging.getLogger('agents.qa.agent')
    qa_logger.setLevel(logging.DEBUG)
    qa_logger.addHandler(handler)
    
    llm = OllamaClient()
    llm.generate_structured_response = llm.generate_structured_output
    qa_agent = QAAgent(llm_client=llm)
    
    task_data = {
        "requirements": "The system must store orders in MongoDB.",
        "acceptance_criteria": ["Database connection handles timeouts.", "Order schema includes order_id and customer_name."]
    }
    
    dep_outputs = [
        {"name": "src/main.py", "content": artifacts_text}
    ]
    
    input_data = AgentInput(
        task_id=f"qa-test-{rep_num}",
        task_type=TaskType.QA,
        instructions="Evaluate code artifacts against requirements for task 1234.",
        context={
            "task_data": task_data,
            "dependency_outputs": dep_outputs
        },
        dependencies=["1234"]
    )
    
    start_time = time.time()
    try:
        output = await qa_agent.execute(input_data)
        latency = time.time() - start_time
        
        qa_logger.removeHandler(handler)
        log_text = log_stream.getvalue()
        
        val_errors = log_text.count("ValueError")
        parse_errors = log_text.count("OutputParserException")
        timeouts = log_text.count("Timeout")
        attempts = 1 + log_text.count("Validation error on attempt")
        
        first_attempt_success = attempts == 1 and output.status == "SUCCESS"
        retry_required = attempts > 1
        
        return {
            "success": output.status == "SUCCESS",
            "verdict": output.result.get("verdict", "unknown") if output.result else "none",
            "latency": latency,
            "error": output.feedback if output.status == "FAILURE" else None,
            "val_errors": val_errors,
            "parse_errors": parse_errors,
            "timeouts": timeouts,
            "attempts": attempts,
            "first_attempt_success": first_attempt_success,
            "retry_required": retry_required
        }
    except Exception as e:
        qa_logger.removeHandler(handler)
        return {
            "success": False,
            "error": str(e),
            "latency": time.time() - start_time
        }

async def main():
    art_b = """import pymongo

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["orders"]
collection = db["order_data"]

schema = {
    "properties": {
        "order_id": {"type": "string"},
        "customer_name": {"type": "string"}
    },
    "required": ["order_id"]
}
collection.create_index([("order_id", 1)], unique=True)
"""
    
    num_reps = 5
    results = []
    
    print(f"{'='*60}\nRUNNING 9D.18 ISOLATED QA DIAGNOSTIC\n{'='*60}")
    for i in range(num_reps):
        res = await run_qa_execution(i+1, art_b)
        results.append(res)
        print(f"Success: {res.get('success')}, Verdict: {res.get('verdict')}, Latency: {res.get('latency'):.2f}s")
        print(f"  Attempts: {res.get('attempts')}, First Attempt Success: {res.get('first_attempt_success')}")
        print(f"  ValueErrors: {res.get('val_errors')}, ParseErrors: {res.get('parse_errors')}")
        if res.get('error'):
            print(f"  Error feedback: {res['error']}")
            
    successes = sum(1 for r in results if r.get('success'))
    first_successes = sum(1 for r in results if r.get('first_attempt_success'))
    val_errs = sum(r.get('val_errors', 0) for r in results)
    parse_errs = sum(r.get('parse_errors', 0) for r in results)
    
    print(f"\nRESULTS FOR 9D.18 DIAGNOSTIC:")
    print(f"Final Success Rate: {successes}/{num_reps}")
    print(f"First Attempt Success: {first_successes}/{num_reps}")
    print(f"Total ValueErrors: {val_errs}")
    print(f"Total OutputParserExceptions: {parse_errs}")

if __name__ == "__main__":
    asyncio.run(main())
