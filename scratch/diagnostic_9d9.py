import asyncio
import time
import json
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pydantic import BaseModel, Field
from langchain_community.llms import Ollama
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from backend.schemas.enums import ArtifactType

from agents.coding.agent import CodeGenerationResponse
from agents.coding.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

logging.basicConfig(level=logging.INFO)

llm = Ollama(model="llama3.1", temperature=0.1, timeout=120.0)

async def measure_json(test_name, response_model, sys_prompt, user_prompt, reps=3):
    print(f"\n--- Running {test_name} ---")
    results = []
    
    parser = JsonOutputParser(pydantic_object=response_model)
    format_instructions = parser.get_format_instructions()
    prompt = PromptTemplate(
        template="{system_prompt}\n\n{user_prompt}\n\n{format_instructions}",
        input_variables=["system_prompt", "user_prompt"],
        partial_variables={"format_instructions": format_instructions},
    )
    
    # We capture raw output to check for markdown fences. We'll run the LLM separately from the parser
    raw_chain = prompt | llm

    prompt_val = prompt.format_prompt(system_prompt=sys_prompt, user_prompt=user_prompt).to_string()
    prompt_len = len(prompt_val)
    sys_len = len(sys_prompt)
    user_len = len(user_prompt)
    schema_len = len(format_instructions)

    for i in range(reps):
        start = time.time()
        success = False
        timeout = False
        val_error = None
        raw_output_len = 0
        md_fences = False
        files_gen = 0
        
        try:
            raw_res = await raw_chain.ainvoke({
                "system_prompt": sys_prompt,
                "user_prompt": user_prompt
            })
            raw_output_len = len(raw_res)
            if "```" in raw_res:
                md_fences = True
                
            parsed_res = parser.parse(raw_res)
            success = True
            if "files" in parsed_res:
                files_gen = len(parsed_res["files"])
        except Exception as e:
            if "timeout" in str(e).lower() or "read operation timed out" in str(e).lower():
                timeout = True
            else:
                val_error = str(e)
                
        duration = time.time() - start
        
        results.append({
            "test": test_name,
            "rep": i+1,
            "duration": duration,
            "success": success,
            "timeout": timeout,
            "val_error": bool(val_error),
            "output_len": raw_output_len,
            "prompt_len": prompt_len,
            "sys_len": sys_len,
            "user_len": user_len,
            "schema_len": schema_len,
            "md_fences": md_fences,
            "files_gen": files_gen,
            "error_msg": val_error
        })
        print(f"Rep {i+1}: {duration:.2f}s | Success={success} | MD Fences={md_fences} | Files={files_gen} | Err={bool(val_error)}")
    return results

async def measure_raw(test_name, sys_prompt, user_prompt, reps=3):
    print(f"\n--- Running {test_name} ---")
    results = []
    
    prompt = PromptTemplate(
        template="{system_prompt}\n\n{user_prompt}",
        input_variables=["system_prompt", "user_prompt"]
    )
    
    raw_chain = prompt | llm

    prompt_val = prompt.format_prompt(system_prompt=sys_prompt, user_prompt=user_prompt).to_string()
    prompt_len = len(prompt_val)
    sys_len = len(sys_prompt)
    user_len = len(user_prompt)

    for i in range(reps):
        start = time.time()
        success = False
        timeout = False
        val_error = None
        raw_output_len = 0
        md_fences = False
        
        try:
            raw_res = await raw_chain.ainvoke({
                "system_prompt": sys_prompt,
                "user_prompt": user_prompt
            })
            raw_output_len = len(raw_res)
            if "```" in raw_res:
                md_fences = True
            success = True
        except Exception as e:
            if "timeout" in str(e).lower() or "read operation timed out" in str(e).lower():
                timeout = True
            else:
                val_error = str(e)
                
        duration = time.time() - start
        
        results.append({
            "test": test_name,
            "rep": i+1,
            "duration": duration,
            "success": success,
            "timeout": timeout,
            "val_error": bool(val_error),
            "output_len": raw_output_len,
            "prompt_len": prompt_len,
            "sys_len": sys_len,
            "user_len": user_len,
            "schema_len": 0,
            "md_fences": md_fences,
            "files_gen": 0,
            "error_msg": val_error
        })
        print(f"Rep {i+1}: {duration:.2f}s | Success={success} | MD Fences={md_fences} | Err={bool(val_error)}")
    return results


async def main():
    print("Starting Phase 9D.9 Diagnostic...")
    
    # 1. Create bloated fake dependency output simulating earlier pipeline tasks
    bloated_code = "import os\n" + "def do_something_complex():\n    pass\n" * 200
    bloated_dep = json.dumps([
        {
            "id": "art-1",
            "name": "src/old_module.py",
            "type": "code",
            "content": bloated_code,
            "language": "python"
        }
    ], indent=2)
    
    summarized_dep = json.dumps([
        {
            "id": "art-1",
            "name": "src/old_module.py",
            "type": "code",
            "description": "Legacy module handling complex things",
            "symbols": ["do_something_complex"]
        }
    ], indent=2)
    
    truncated_code = bloated_code[:1000] + "... (truncated)"
    truncated_dep = json.dumps([
        {
            "id": "art-1",
            "name": "src/old_module.py",
            "type": "code",
            "content": truncated_code,
            "language": "python"
        }
    ], indent=2)
    
    # Task to perform
    instructions = "Create a Flask application for Products. It needs a main.py defining the API, a models.py defining the database model, and a requirements.txt file."
    task_data = "{\"auth\": \"jwt\"}"
    knowledge = "Use SQLAlchemy"
    
    # TEST A: Current Real Context (Bloated)
    user_prompt_a = USER_PROMPT_TEMPLATE.format(
        instructions=instructions,
        task_data=task_data,
        dependency_outputs=bloated_dep,
        knowledge=knowledge
    )
    res_a = await measure_json("TEST A: Current Real Context", CodeGenerationResponse, SYSTEM_PROMPT, user_prompt_a, reps=3)
    
    # TEST B: No dependency outputs
    user_prompt_b = USER_PROMPT_TEMPLATE.format(
        instructions=instructions,
        task_data=task_data,
        dependency_outputs="[]",
        knowledge=knowledge
    )
    res_b = await measure_json("TEST B: No dependency_outputs", CodeGenerationResponse, SYSTEM_PROMPT, user_prompt_b, reps=3)
    
    # TEST C: Summarized
    user_prompt_c = USER_PROMPT_TEMPLATE.format(
        instructions=instructions,
        task_data=task_data,
        dependency_outputs=summarized_dep,
        knowledge=knowledge
    )
    res_c = await measure_json("TEST C: Summarized dependency_outputs", CodeGenerationResponse, SYSTEM_PROMPT, user_prompt_c, reps=3)
    
    # TEST D: Truncated
    user_prompt_d = USER_PROMPT_TEMPLATE.format(
        instructions=instructions,
        task_data=task_data,
        dependency_outputs=truncated_dep,
        knowledge=knowledge
    )
    res_d = await measure_json("TEST D: Truncated dependency_outputs", CodeGenerationResponse, SYSTEM_PROMPT, user_prompt_d, reps=3)
    
    # TEST E: Plain-text coding generation
    plain_text_system = SYSTEM_PROMPT + "\n\nFormat your output exactly like this for each file:\nFILE: path/to/file.py\n```python\nprint('hello')\n```"
    user_prompt_e = USER_PROMPT_TEMPLATE.format(
        instructions=instructions,
        task_data=task_data,
        dependency_outputs=bloated_dep,
        knowledge=knowledge
    )
    res_e = await measure_raw("TEST E: Plain-text coding generation", plain_text_system, user_prompt_e, reps=3)
    
    all_results = {
        "A": res_a,
        "B": res_b,
        "C": res_c,
        "D": res_d,
        "E": res_e
    }
    
    with open("scratch/diagnostic_9d9_results.json", "w") as f:
        json.dump(all_results, f, indent=2)

if __name__ == "__main__":
    asyncio.run(main())
