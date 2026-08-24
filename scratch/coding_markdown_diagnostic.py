import asyncio
import time
import json
import uuid
import re
from typing import List, Dict

from backend.llm.worker_registry import global_registry
from backend.llm.worker_pool import WorkerPool
from backend.llm.worker import Worker, WorkerStatus
from backend.llm.worker_client import WorkerAwareOllamaClient
from backend.schemas.task import Task
from backend.schemas.enums import TaskType
from backend.schemas.agent_io import AgentInput
from agents.coding.agent import CodingAgent
from agents.coding.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from datetime import datetime, timezone

from pydantic import BaseModel, Field

# Mock models for structured output
class GeneratedFile(BaseModel):
    path: str
    content: str
    language: str
    artifact_type: str

class CodeGenerationResponse(BaseModel):
    files: List[GeneratedFile]

# Markdown prompt
MARKDOWN_SYSTEM_PROMPT = """You are a senior software engineer responsible for generating production-ready code.
Your task is to write code that strictly fulfills the provided specifications.

Rules:
1. Generate complete, working code.
2. Avoid unsupported features, placeholders, or unfinished blocks.
3. Adhere strictly to the requested programming languages and frameworks.
4. Output your source code using Markdown fenced code blocks. 
5. Provide the exact file path as an HTML comment IMMEDIATELY BEFORE the fenced code block, like this:
   <!-- path: src/main.py -->
   ```python
   print("hello world")
   ```
"""

def extract_markdown_files(text: str) -> List[Dict]:
    files = []
    # Regex to find: <!-- path: something --> followed by ```lang ... ```
    # Make sure to handle optional spaces and newlines
    pattern = r"<!--\s*path:\s*(.+?)\s*-->\s*```([a-zA-Z0-9]*)\n(.*?)```"
    matches = re.finditer(pattern, text, re.DOTALL)
    for match in matches:
        path = match.group(1).strip()
        lang = match.group(2).strip()
        content = match.group(3)
        files.append({
            "path": path,
            "content": content,
            "language": lang,
            "artifact_type": "code"
        })
    return files

async def main():
    # Setup Worker Pool
    global_registry._workers.clear()
    w = Worker(worker_id="default-worker-1", host="localhost", port=11434, model="llama3.1", status=WorkerStatus.AVAILABLE)
    global_registry.register_worker(w)
    pool = WorkerPool(global_registry)
    client = WorkerAwareOllamaClient(worker_pool=pool, model_name="llama3.1")
    
    # Define Controlled Task (Product Catalog API)
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
    
    # 1. We need the formatted user prompt
    coding_agent = CodingAgent(llm_client=client)
    user_prompt = coding_agent._format_prompt(agent_input)
    
    print("========================================")
    print("A/B DIAGNOSTIC: llama3.1 Code Generation")
    print("========================================")
    
    # Method A: JSON Envelope
    print("\n--- METHOD A: JSON Envelope ---")
    start_a = time.time()
    #try:
    #    # We can bypass agent logic slightly just to test the raw generation
    #    res_a = await client.generate_structured_output(
    #        system_prompt=SYSTEM_PROMPT,
    #        user_prompt=user_prompt,
    #        response_model=CodeGenerationResponse
    #    )
    #    dur_a = time.time() - start_a
    #    print(f"[SUCCESS] JSON generation took {dur_a:.2f}s")
    #    print(f"Files extracted: {len(res_a.files)}")
    #except Exception as e:
    #    dur_a = time.time() - start_a
    #    print(f"[FAILED] JSON generation failed after {dur_a:.2f}s")
    #    print(f"Error: {str(e)}")
        
    # Method B: Markdown
    print("\n--- METHOD B: Markdown + Regex Extraction ---")
    start_b = time.time()
    try:
        import urllib.request
        import urllib.parse
        import json
        worker = await pool.select_worker("diagnostic")
        try:
            url = f"{worker.base_url}/api/generate"
            full_prompt = f"{MARKDOWN_SYSTEM_PROMPT}\n\n{user_prompt}"
            
            data = {
                "model": worker.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {"temperature": 0.1}
            }
            
            req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
            
            response = await asyncio.to_thread(urllib.request.urlopen, req, timeout=300)
            res_data = json.loads(response.read().decode('utf-8'))
            raw_content = res_data.get('response', '')
            
            dur_b = time.time() - start_b
            print(f"[SUCCESS] Markdown generation took {dur_b:.2f}s")
            print("RAW CONTENT:")
            print(raw_content)
            
            files = extract_markdown_files(raw_content)
            print(f"Files extracted via regex: {len(files)}")
            for f in files:
                print(f" - Path: {f['path']}")
                print(f" - Content length: {len(f['content'])} bytes")
                
        finally:
            pool.release_worker(worker.worker_id)
            
    except Exception as e:
        dur_b = time.time() - start_b
        print(f"[FAILED] Markdown generation failed after {dur_b:.2f}s")
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
