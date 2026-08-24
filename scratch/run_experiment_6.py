import asyncio
import sys
import logging
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from evaluation.runner import ExperimentRunner
from evaluation.schemas import ResultMode, SystemVariant

# Setup logging to ensure we capture the logger.info from agents
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

async def main():
    runner = ExperimentRunner(results_dir="evaluation/results")
    print("Starting REAL Experiment #6...")
    result = await runner.run(
        scenario_id="ecommerce-catalog",
        variant=SystemVariant.FULL_SYSTEM,
        mode=ResultMode.REAL,
        model_identifier="llama3.1"
    )
    print("Experiment finished.")

if __name__ == "__main__":
    asyncio.run(main())
