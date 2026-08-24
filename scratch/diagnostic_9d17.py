import asyncio
import time
import json
import os
import sys

# Ensure import paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from langchain_community.llms import Ollama
from langchain_core.output_parsers import JsonOutputParser
from agents.qa.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from agents.qa.agent import QAEvaluationResponse

async def run_test_repetition(llm, parser, format_instructions, instructions, task_data_text, artifacts_text, knowledge_text, rep_num, is_retry=False, prev_error=None):
    user_prompt = USER_PROMPT_TEMPLATE.format(
        instructions=instructions,
        task_data=task_data_text,
        artifacts_text=artifacts_text,
        knowledge=knowledge_text
    )
    
    if is_retry and prev_error:
        user_prompt += f"\n\nValidation Error: {prev_error}. You MUST return a single JSON object (mapping) matching the schema, not a raw JSON array."
        
    final_prompt = f"{SYSTEM_PROMPT}\n\n{user_prompt}\n\n{format_instructions}"
    
    start = time.time()
    try:
        raw_output = await llm.ainvoke(final_prompt)
        latency = time.time() - start
    except Exception as e:
        return {"error": str(e), "latency": time.time() - start}
        
    has_markdown = "```" in raw_output
    has_json_obj = "{" in raw_output and "}" in raw_output
    has_json_array = "[" in raw_output and "]" in raw_output
    
    parser_error = None
    value_error = None
    parsed = None
    try:
        parsed_dict = parser.parse(raw_output)
        if not isinstance(parsed_dict, dict):
            value_error = "LLM output did not parse into a JSON object mapping."
        else:
            parsed = True
    except Exception as e:
        if "OutputParserException" in type(e).__name__:
            parser_error = str(e)
        else:
            value_error = str(e)
            
    return {
        "latency": latency,
        "raw_len": len(raw_output),
        "raw_first_500": raw_output[:500],
        "has_markdown": has_markdown,
        "has_json_obj": has_json_obj,
        "has_json_array": has_json_array,
        "parser_error": parser_error is not None,
        "value_error": value_error is not None,
        "success": parsed is not None,
        "error_msg": parser_error or value_error,
        "prompt_len": len(final_prompt)
    }

async def run_test_condition(name, artifacts_text, task_data="{}", num_reps=5, is_retry=False):
    print(f"\n{'='*60}\nRUNNING {name}\n{'='*60}")
    
    instructions = "Evaluate code artifacts against requirements for task 1234."
    knowledge_text = "No additional domain knowledge provided."
    
    parser = JsonOutputParser(pydantic_object=QAEvaluationResponse)
    format_instructions = parser.get_format_instructions()
    
    llm = Ollama(
        base_url="http://localhost:11434",
        model="llama3.1",
        temperature=0.1,
        timeout=120.0
    )
    
    results = []
    prev_error = "OutputParserException: Invalid json output: \n```\ndef main(): pass\n```"
    
    for i in range(num_reps):
        print(f"Repetition {i+1}/{num_reps}...")
        res = await run_test_repetition(
            llm, parser, format_instructions, instructions, task_data, artifacts_text, knowledge_text, i+1, is_retry, prev_error
        )
        results.append(res)
        if "error" in res:
            print(f"  -> ERROR: {res['error']}")
        else:
            print(f"  -> Success: {res['success']} (Md={res['has_markdown']}, JSON={res['has_json_obj']}, ParserErr={res['parser_error']}, ValErr={res['value_error']})")
            if not res['success']:
                print(f"     Msg: {res['error_msg'][:100]}...")
            if i == 0:
                print(f"  -> Prompt size: {res['prompt_len']} chars")
                print(f"  -> Raw output (first 200 chars):\n{res['raw_first_500'][:200]}\n")
                
    successes = sum(1 for r in results if r.get('success'))
    md_rate = sum(1 for r in results if r.get('has_markdown'))
    parse_err = sum(1 for r in results if r.get('parser_error'))
    val_err = sum(1 for r in results if r.get('value_error'))
    
    print(f"\nRESULTS FOR {name}:")
    print(f"Success Rate: {successes}/{num_reps}")
    print(f"Markdown Rate: {md_rate}/{num_reps}")
    print(f"Parser Err Rate: {parse_err}/{num_reps}")
    print(f"Value Err Rate: {val_err}/{num_reps}")

async def main():
    # TEST A - Minimal artifact
    art_a = "\n--- FILE: test.py ---\ndef hello():\n    return 'world'\n"
    await run_test_condition("TEST A - Minimal artifact", art_a)
    
    # TEST B - Realistic single-file artifact
    art_b = """
--- FILE: src/main.py ---
import pymongo

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
    await run_test_condition("TEST B - Realistic single-file artifact", art_b)
    
    # TEST C - Multi-file dependency context
    art_c = art_b + "\n--- FILE: requirements.txt ---\npymongo==4.6.0\n\n--- FILE: Dockerfile ---\nFROM python:3.12\nCOPY . .\n"
    await run_test_condition("TEST C - Multi-file dependency context", art_c)
    
    # TEST E - Exact retry formatting (using realistic artifact)
    await run_test_condition("TEST E - Exact retry formatting", art_b, is_retry=True)

if __name__ == "__main__":
    asyncio.run(main())
