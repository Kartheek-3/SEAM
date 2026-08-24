import asyncio
import time
import json
from pydantic import BaseModel, Field
from backend.llm.ollama_client import OllamaClient
from evaluation.scenarios import get_scenario
from backend.config import AppConfig

# Model for Tiny JSON
class TinyPass1(BaseModel):
    components: list[str] = Field(description="List of component names")

async def test_a_plain_text(llm, req_text):
    print("Running Test A: Plain Text...")
    prompt = f"System: Extract a list of components from these requirements.\nUser:\n{req_text}"
    start = time.time()
    try:
        # We invoke the raw langchain model directly for plain text
        res = await llm.llm.ainvoke(prompt)
        dur = time.time() - start
        print(f"Test A completed in {dur:.2f}s")
        return {"duration": dur, "status": "SUCCESS"}
    except Exception as e:
        dur = time.time() - start
        print(f"Test A failed in {dur:.2f}s: {e}")
        return {"duration": dur, "status": "FAILURE"}

async def test_b_tiny_json(llm, req_text):
    print("Running Test B: Tiny JSON...")
    system_prompt = "Extract a list of components from the requirements."
    start = time.time()
    try:
        res = await llm.generate_structured_output(system_prompt, req_text, TinyPass1)
        dur = time.time() - start
        print(f"Test B completed in {dur:.2f}s")
        return {"duration": dur, "status": "SUCCESS", "components": len(res.components)}
    except Exception as e:
        dur = time.time() - start
        print(f"Test B failed in {dur:.2f}s: {e}")
        return {"duration": dur, "status": "FAILURE"}

async def test_c_current_pass1(llm, req_text):
    print("Running Test C: Current Pass 1...")
    from agents.planning.internal_schemas import Pass1ArchitectureResult
    from agents.planning.prompts import PASS_1_SYSTEM_PROMPT, PASS_1_USER_PROMPT_TEMPLATE
    user_prompt = PASS_1_USER_PROMPT_TEMPLATE.format(
        requirement_spec=req_text,
        knowledge_section="",
        instructions="",
        rework_section=""
    )
    start = time.time()
    try:
        res = await llm.generate_structured_output(PASS_1_SYSTEM_PROMPT, user_prompt, Pass1ArchitectureResult)
        dur = time.time() - start
        print(f"Test C completed in {dur:.2f}s")
        return {"duration": dur, "status": "SUCCESS", "components": len(res.components)}
    except Exception as e:
        dur = time.time() - start
        print(f"Test C failed in {dur:.2f}s: {e}")
        return {"duration": dur, "status": "FAILURE"}

async def main():
    print("Initializing OllamaClient...")
    llm = OllamaClient(model_name="llama3.1")
    scenario = get_scenario("ecommerce-catalog")
    req_text = scenario.requirement
    
    res_a = await test_a_plain_text(llm, req_text)
    res_b = await test_b_tiny_json(llm, req_text)
    res_c = await test_c_current_pass1(llm, req_text)
    
    print("\n--- RESULTS ---")
    print(json.dumps({"Test A": res_a, "Test B": res_b, "Test C": res_c}, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
