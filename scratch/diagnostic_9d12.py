import asyncio
import time
import json
import logging
import re
from typing import Type, TypeVar
from pydantic import BaseModel
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from backend.llm.ollama_client import OllamaClient
from agents.coding.agent import CodingAgent
from backend.schemas.agent_io import AgentInput
from backend.schemas.enums import TaskType
from backend.llm.client import LLMException

T = TypeVar("T", bound=BaseModel)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("diagnostic_9d12")

class DiagnosticOllamaClient(OllamaClient):
    def __init__(self, metrics_list):
        super().__init__(model_name="llama3.1")
        self.metrics_list = metrics_list
        self.current_attempt = 1

    async def generate_structured_output(self, system_prompt: str, user_prompt: str, response_model: Type[T]) -> T:
        parser = JsonOutputParser(pydantic_object=response_model)
        format_instructions = parser.get_format_instructions()
        prompt = PromptTemplate(
            template="{system_prompt}\n\n{user_prompt}\n\n{format_instructions}",
            input_variables=["system_prompt", "user_prompt"],
            partial_variables={"format_instructions": format_instructions},
        )
        
        full_prompt = prompt.format(system_prompt=system_prompt, user_prompt=user_prompt)
        prompt_size = len(full_prompt)
        
        start_time = time.time()
        
        metric = {
            "attempt": self.current_attempt,
            "prompt_size": prompt_size,
            "duration": 0,
            "timeout": False,
            "exception_type": None,
            "parser_result_type": None,
            "markdown_detected": False,
            "success": False
        }
        self.current_attempt += 1

        try:
            # Get raw string first to inspect it
            raw_response = await self.llm.ainvoke(full_prompt)
            duration = time.time() - start_time
            metric["duration"] = duration
            metric["response_size"] = len(raw_response)
            
            if "```" in raw_response:
                metric["markdown_detected"] = True
                
            # Now parse it manually exactly as Langchain does
            result_dict = parser.parse(raw_response)
            
            metric["parser_result_type"] = type(result_dict).__name__
            
            if not isinstance(result_dict, dict):
                raise ValueError("LLM output did not parse into a JSON object mapping.")
                
            model_instance = response_model(**result_dict)
            metric["success"] = True
            self.metrics_list.append(metric)
            return model_instance
            
        except TimeoutError as e:
            metric["timeout"] = True
            metric["exception_type"] = "TimeoutError"
            metric["duration"] = time.time() - start_time
            self.metrics_list.append(metric)
            raise LLMException("LLM generation timed out") from e
        except Exception as e:
            metric["exception_type"] = type(e).__name__
            metric["duration"] = time.time() - start_time
            self.metrics_list.append(metric)
            raise LLMException(f"LLM generation failed: {e}")

async def run_diagnostic():
    configs = [
        # Config 1: Very simple task
        {
            "id": "simple-1",
            "instructions": "Write a python script that prints hello world in src/hello.py",
            "complexity": "simple"
        },
        # Config 2: Medium task
        {
            "id": "medium-1",
            "instructions": "Write a python module src/math_utils.py containing functions for add, subtract, multiply, divide. Include type hints and docstrings.",
            "complexity": "medium"
        },
        # Config 3: Complex multi-file task
        {
            "id": "complex-1",
            "instructions": "Write a FastApi server in src/main.py with two endpoints: GET /health and POST /data. Also create src/models.py with a pydantic model DataPayload containing id (int) and name (str).",
            "complexity": "complex"
        },
        # We will repeat these to get 10 iterations.
        {"id": "simple-2", "instructions": "Write a config file in config/settings.json containing { 'theme': 'dark' }", "complexity": "simple"},
        {"id": "medium-2", "instructions": "Write a python script src/parser.py that reads a CSV file and prints the rows. Handle FileNotFoundError.", "complexity": "medium"},
        {"id": "complex-2", "instructions": "Write a python script src/scraper.py that fetches a URL using requests, parses HTML using BeautifulSoup, and saves titles to data/titles.txt.", "complexity": "complex"},
        {"id": "simple-3", "instructions": "Write a markdown file docs/README.md saying welcome.", "complexity": "simple"},
        {"id": "medium-3", "instructions": "Write a python script src/db.py that connects to sqlite memory db and creates a users table.", "complexity": "medium"},
        {"id": "complex-3", "instructions": "Write a user authentication module src/auth.py with JWT generation and validation using PyJWT. Use a secret key from env.", "complexity": "complex"},
        {"id": "complex-4", "instructions": "Write a complete CRUD application for Products with FastAPI in src/app.py and Pydantic schemas in src/schemas.py.", "complexity": "complex"}
    ]
    
    all_metrics = []
    
    for i, config in enumerate(configs):
        print(f"\n=== Running Iteration {i+1}/10: {config['id']} ({config['complexity']}) ===")
        metrics_list = []
        client = DiagnosticOllamaClient(metrics_list)
        agent = CodingAgent(llm_client=client)
        
        input_data = AgentInput(
            task_id=config["id"],
            task_type=TaskType.CODING,
            context={"dependency_outputs": []},
            instructions=config["instructions"],
            dependencies=[]
        )
        
        output = await agent.execute(input_data)
        
        # Analyze recovery
        final_success = (output.status.value == "success")
        first_attempt_success = (len(metrics_list) > 0 and metrics_list[0]["success"])
        retry_recovery = (not first_attempt_success and final_success)
        
        summary = {
            "iteration": i + 1,
            "task_id": config["id"],
            "complexity": config["complexity"],
            "attempts": len(metrics_list),
            "final_success": final_success,
            "first_attempt_success": first_attempt_success,
            "retry_recovery": retry_recovery,
            "calls": metrics_list
        }
        all_metrics.append(summary)
        print(f"Result: {output.status.value}, Attempts: {len(metrics_list)}")
        
    with open("scratch/diagnostic_9d12_results.json", "w") as f:
        json.dump(all_metrics, f, indent=2)

if __name__ == "__main__":
    asyncio.run(run_diagnostic())
