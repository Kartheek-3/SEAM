import asyncio
import json
import logging
from datetime import datetime, timezone

from backend.llm.ollama_client import OllamaClient
from agents.qa.agent import QAAgent
from backend.schemas.agent_io import AgentInput, Artifact
from backend.schemas.enums import AgentRole
from langchain_community.llms import Ollama
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate

logging.basicConfig(level=logging.INFO)

async def run_diagnostic():
    print("=== QA Agent Real Isolated Validation ===")
    llm = OllamaClient(model_name="llama3.1")
    if not hasattr(llm, 'generate_structured_response'):
        llm.generate_structured_response = llm.generate_structured_output
    qa_agent = QAAgent(llm_client=llm)
    
    source_code = """
def calculate_total(price, tax_rate):
    # This might have a bug if price is negative
    return price + (price * tax_rate)
"""
    artifact = Artifact(
        id="a-1",
        project_id="p-1",
        task_id="t-1",
        type="code",
        name="calculator.py",
        content=source_code,
        version=1,
        agent_id=AgentRole.CODING,
        created_at=datetime.now(timezone.utc)
    )
    
    input_data = AgentInput(
        task_id="t-1",
        task_type="qa",
        instructions="Review this python code for logical bugs and edge cases.",
        context={
            "dependency_outputs": [artifact]
        }
    )
    
    for i in range(3):
        print(f"\\n--- Iteration {i+1} ---")
        try:
            output = await qa_agent.execute(input_data)
            print("Final Status:", output.status)
            if 'score' in output.result:
                print(f"Score: {output.result['score']} | Verdict: {output.result.get('verdict')}")
            else:
                print("Result payload:", output.result)
        except Exception as e:
            print("Exception:", e)

if __name__ == "__main__":
    asyncio.run(run_diagnostic())
