
import asyncio
import time
import json
import os
from evaluation.runner import ExperimentRunner
from evaluation.schemas import ResultMode, SystemVariant
from agents.planning.agent import PlanningAgent

pass1_metrics = {}
pass2_metrics = []

original_run_pass1 = PlanningAgent._run_pass1
async def wrapped_run_pass1(self, *args, **kwargs):
    start = time.time()
    try:
        res = await original_run_pass1(self, *args, **kwargs)
        dur = time.time() - start
        pass1_metrics["duration"] = dur
        pass1_metrics["components"] = len(res.components)
        pass1_metrics["status"] = "SUCCESS"
        return res
    except Exception as e:
        pass1_metrics["duration"] = time.time() - start
        pass1_metrics["status"] = "FAILURE"
        raise e

original_run_pass2 = PlanningAgent._run_pass2_for_component
async def wrapped_run_pass2(self, req_spec_json, component, *args, **kwargs):
    start = time.time()
    try:
        res = await original_run_pass2(self, req_spec_json, component, *args, **kwargs)
        dur = time.time() - start
        pass2_metrics.append({
            "component": component.name,
            "duration": dur,
            "tasks": len(res.tasks),
            "status": "SUCCESS"
        })
        return res
    except Exception as e:
        pass2_metrics.append({
            "component": component.name,
            "duration": time.time() - start,
            "status": "FAILURE"
        })
        raise e

PlanningAgent._run_pass1 = wrapped_run_pass1
PlanningAgent._run_pass2_for_component = wrapped_run_pass2

async def main():
    runner = ExperimentRunner(results_dir="evaluation/results")
    print("Starting REAL Experiment #4...")
    result = await runner.run(
        scenario_id="ecommerce-catalog",
        variant=SystemVariant.FULL_SYSTEM,
        mode=ResultMode.REAL,
        model_identifier="llama3.1"
    )
    
    print("\n--- METRICS DUMP ---")
    print(json.dumps({
        "pass1": pass1_metrics,
        "pass2": pass2_metrics,
        "experiment": result.model_dump()
    }, indent=2))

if __name__ == "__main__":
    asyncio.run(main())

