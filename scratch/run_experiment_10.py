import asyncio
import sys
import logging
import json
from evaluation.runner import ExperimentRunner
from evaluation.schemas import ResultMode, SystemVariant

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

async def main():
    runner = ExperimentRunner(results_dir="evaluation/results")
    print("Starting REAL Experiment #10...")
    result = await runner.run(
        scenario_id="ecommerce-catalog",
        variant=SystemVariant.FULL_SYSTEM,
        mode=ResultMode.REAL,
        model_identifier="llama3.1"
    )
    print("Experiment finished.")
    print(f"Result ID: {result.experiment_id}")

if __name__ == "__main__":
    asyncio.run(main())
