import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath("."))

from backend.llm.ollama_client import OllamaClient
from backend.schemas.planning import ProjectPlan

async def main():
    client = OllamaClient(model_name="llama3.1")
    
    # Large user prompt that takes time to process
    system_prompt = "You are a software architect."
    user_prompt = "Design a very comprehensive ecommerce catalog system with 50 specific microtasks, detailing everything in extreme detail." * 10
    
    try:
        print("Starting generate_structured_output for ProjectPlan...")
        result = await client.generate_structured_output(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_model=ProjectPlan
        )
        print("SUCCESS:", len(result.tasks))
    except Exception as e:
        print("---EXCEPTION CAUGHT---")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception repr: {repr(e)}")
        print(f"Exception module: {getattr(type(e), '__module__', 'unknown')}")

if __name__ == "__main__":
    asyncio.run(main())
