import asyncio
import time
import json
from backend.llm.ollama_client import OllamaClient
from backend.schemas import ProjectPlan, RequirementSpec

async def main():
    client = OllamaClient(model_name="llama3.1")
    
    # 1. Test Unstructured Generation
    print("--- Test Unstructured Generation ---")
    prompt = "Hello, reply with exactly one word: 'World'"
    start_time = time.time()
    try:
        # We don't have unstructured in OllamaClient directly, but we can fake it or use llm directly
        result = await client.llm.ainvoke(prompt)
        dur = time.time() - start_time
        print(f"Success: True, Duration: {dur:.2f}s, Output size: {len(result)}")
    except Exception as e:
        print(f"Success: False, Error: {e}")

    # 2. Test Minimal ProjectPlan Generation
    print("\n--- Test Structured ProjectPlan Generation ---")
    system_prompt = "You are a software architect. Create a basic hello world plan."
    user_prompt = "Goal: Hello World\nComponents: 1\nTasks: 1"
    
    start_time = time.time()
    try:
        result = await client.generate_structured_output(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=ProjectPlan
        )
        dur = time.time() - start_time
        print(f"Success: True, Duration: {dur:.2f}s, Output fields: {len(result.model_dump().keys())}")
    except Exception as e:
        dur = time.time() - start_time
        print(f"Success: False, Duration: {dur:.2f}s, Error: {e}")
        
    # 3. Test Minimal RequirementSpec Generation (Analysis)
    print("\n--- Test Structured RequirementSpec Generation (Analysis) ---")
    system_prompt_a = "You are an analyst. Create a basic hello world requirement."
    user_prompt_a = "Goal: Hello World"
    
    start_time = time.time()
    try:
        result = await client.generate_structured_output(
            system_prompt=system_prompt_a,
            user_prompt=user_prompt_a,
            response_model=RequirementSpec
        )
        dur = time.time() - start_time
        print(f"Success: True, Duration: {dur:.2f}s, Output fields: {len(result.model_dump().keys())}")
    except Exception as e:
        dur = time.time() - start_time
        print(f"Success: False, Duration: {dur:.2f}s, Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
