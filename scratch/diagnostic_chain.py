import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath("."))

from backend.config import settings
from pydantic import BaseModel
from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from backend.schemas.planning import ProjectPlan

async def main():
    llm = Ollama(
        base_url=settings.ollama_base_url,
        model="llama3.1",
        temperature=0.1,
        timeout=settings.ollama_timeout
    )
    
    response_model = ProjectPlan
    parser = JsonOutputParser(pydantic_object=response_model)
    format_instructions = parser.get_format_instructions()
    
    prompt = PromptTemplate(
        template="{system_prompt}\n\n{user_prompt}\n\n{format_instructions}",
        input_variables=["system_prompt", "user_prompt"],
        partial_variables={"format_instructions": format_instructions},
    )

    chain = prompt | llm | parser

    system_prompt = "You are a software architect."
    user_prompt = "Design a very comprehensive ecommerce catalog system with 50 specific microtasks, detailing everything in extreme detail." * 10

    try:
        print("Invoking chain...")
        result = await chain.ainvoke({
            "system_prompt": system_prompt,
            "user_prompt": user_prompt
        })
        print("SUCCESS")
    except Exception as e:
        print("---REAL EXCEPTION CAUGHT---")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Exception Module: {getattr(type(e), '__module__', 'unknown')}")
        print(f"Exception repr: {repr(e)}")

if __name__ == "__main__":
    asyncio.run(main())
