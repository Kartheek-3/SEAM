import sys
import os
import asyncio

# Ensure PYTHONPATH is correct
sys.path.insert(0, os.path.abspath("."))

from evaluation.runner import ExperimentRunner
from evaluation.schemas import ResultMode, SystemVariant

async def main():
    runner = ExperimentRunner(results_dir="evaluation/results")
    
    result = await runner.run(
        scenario_id="ecommerce-catalog",
        variant=SystemVariant.FULL_SYSTEM,
        mode=ResultMode.REAL,
        model_identifier="llama3.1"
    )
    
    print("---EXPERIMENT_RESULT_JSON---")
    print(result.model_dump_json(indent=2))
    print("---EXPERIMENT_RESULT_JSON_END---")

if __name__ == "__main__":
    asyncio.run(main())
