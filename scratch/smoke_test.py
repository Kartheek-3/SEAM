import asyncio
import json
import logging
from evaluation.runner import ExperimentRunner
from evaluation.schemas import SystemVariant, ResultMode

# Setup logging
logging.basicConfig(level=logging.INFO)

async def run_smoke_test():
    runner = ExperimentRunner()
    try:
        result = await runner.run(
            scenario_id="ecommerce-catalog",
            variant=SystemVariant.FULL_SYSTEM,
            mode=ResultMode.REAL,
            model_identifier="llama3.1"
        )
        print("--- SMOKE TEST RESULT ---")
        print(result.model_dump_json(indent=2))
        print("-------------------------")
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"FAILED TO EXECUTE: {e}")

if __name__ == "__main__":
    asyncio.run(run_smoke_test())
