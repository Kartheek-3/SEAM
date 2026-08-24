import asyncio
import time
import uuid

from evaluation.runner import ExperimentRunner
from evaluation.schemas import ResultMode, SystemVariant

def run_experiment_19():
    print("====================================")
    print("LAUNCHING REAL EXPERIMENT #19")
    print("====================================")
    
    runner = ExperimentRunner()
    start_time = time.time()
    
    try:
        result = asyncio.run(runner.run(
            scenario_id="ecommerce-catalog",
            variant=SystemVariant.FULL_SYSTEM,
            mode=ResultMode.REAL,
            model_identifier="llama3.1"
        ))
        
        print("\\n\\n====================================")
        print("EXPERIMENT 19 COMPLETED")
        print("====================================")
        print(f"Duration: {time.time() - start_time:.2f} seconds")
        print(f"Final Success: {result.success}")
    except Exception as e:
        print(f"EXPERIMENT FAILED WITH EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_experiment_19()
