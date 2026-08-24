import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath("."))

from pydantic import BaseModel
from backend.llm.ollama_client import OllamaClient

class DummyModel(BaseModel):
    name: str
    value: int

async def main():
    client = OllamaClient(model_name="llama3.1")
    try:
        print("Starting generate_structured_output...")
        result = await client.generate_structured_output(
            system_prompt="You are a helpful assistant.",
            user_prompt="Give me a dummy response with name 'test' and value 42.",
            response_model=DummyModel
        )
        print("SUCCESS:", result)
    except Exception as e:
        import traceback
        print("EXCEPTION TYPE:", type(e).__name__)
        print("EXCEPTION STR:", str(e))
        print("TRACEBACK:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
