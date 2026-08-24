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

# Setup exactly like production CodingAgent
from agents.coding.agent import CodeGenerationResponse
from agents.coding.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

logging.basicConfig(level=logging.INFO)

llm = Ollama(model="llama3.1", temperature=0.1, timeout=120.0)

class TinyJSON(BaseModel):
    summary: str
    files: list[str]

async def measure_raw(prompt_text, reps=3):
    print(f"\n--- Running TEST A: Plain Coding Response ---")
    results = []
    for i in range(reps):
        start = time.time()
        success = False
        timeout = False
        output_len = 0
        try:
            res = await llm.ainvoke(prompt_text)
            success = True
            output_len = len(res)
        except Exception as e:
            if "timeout" in str(e).lower():
                timeout = True
        duration = time.time() - start
        results.append({
            "test": "A",
            "rep": i+1,
            "duration": duration,
            "success": success,
            "timeout": timeout,
            "output_len": output_len
        })
        print(f"Rep {i+1}: {duration:.2f}s | Success={success} | Timeout={timeout} | Len={output_len}")
    return results

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
    chain = prompt | llm | parser

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
        
        # We need to capture raw output to check for markdown fences. We'll run the LLM separately from the parser
        raw_chain = prompt | llm
        
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


async def main():
    print("Starting Phase 9D.8 Diagnostic...")
    
    # TEST A: Plain text
    res_a = await measure_raw("Write a 5-line python script that prints hello world.", reps=3)
    
    # TEST B: Tiny JSON
    res_b = await measure_json(
        "TEST B: Tiny JSON",
        TinyJSON,
        "You are an assistant.",
        "Return a JSON object with a summary and a list of 2 file names.",
        reps=3
    )
    
    # TEST C: Current Schema + Tiny Task
    user_prompt_c = USER_PROMPT_TEMPLATE.format(
        instructions="Print hello world",
        task_data="{}",
        dependency_outputs="{}",
        knowledge="None"
    )
    res_c = await measure_json(
        "TEST C: Current Schema + Tiny Task",
        CodeGenerationResponse,
        SYSTEM_PROMPT,
        user_prompt_c,
        reps=3
    )
    
    # TEST D: Current Schema + Small Realistic Task
    user_prompt_d = USER_PROMPT_TEMPLATE.format(
        instructions="Create a simple Product model with fields id, name and price in python.",
        task_data="{\"lang\":\"python\"}",
        dependency_outputs="{}",
        knowledge="None"
    )
    res_d = await measure_json(
        "TEST D: Current Schema + Small Realistic",
        CodeGenerationResponse,
        SYSTEM_PROMPT,
        user_prompt_d,
        reps=3
    )
    
    # TEST E: Current Schema + Multi-file Task
    user_prompt_e = USER_PROMPT_TEMPLATE.format(
        instructions="Create a Flask application for Products. It needs a main.py defining the API, a models.py defining the database model, and a requirements.txt file.",
        task_data="{\"auth\": \"jwt\"}",
        dependency_outputs="{\"db_uri\": \"sqlite:///app.db\"}",
        knowledge="Use SQLAlchemy"
    )
    res_e = await measure_json(
        "TEST E: Current Schema + Multi-file Task",
        CodeGenerationResponse,
        SYSTEM_PROMPT,
        user_prompt_e,
        reps=3
    )
    
    all_results = {
        "A": res_a,
        "B": res_b,
        "C": res_c,
        "D": res_d,
        "E": res_e
    }
    
    with open("scratch/diagnostic_9d8_results.json", "w") as f:
        json.dump(all_results, f, indent=2)

if __name__ == "__main__":
    asyncio.run(main())
