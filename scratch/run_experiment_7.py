"""
REAL Experiment #7 — Full Six-Agent Pipeline Validation
Runs via the production ExperimentRunner in REAL mode.
Captures additional stage-level telemetry via logging hooks.
"""
import asyncio
import json
import logging
import os
import sys
import time
import traceback
from datetime import datetime, timezone

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure detailed logging BEFORE any imports
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

from evaluation.runner import ExperimentRunner, TelemetryLLMClient, TelemetryRAGService
from evaluation.schemas import SystemVariant, ResultMode

logger = logging.getLogger("experiment7")

async def main():
    print("=" * 70)
    print("REAL EXPERIMENT #7 — FULL SIX-AGENT PIPELINE VALIDATION")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 70)
    
    runner = ExperimentRunner()
    
    overall_start = time.time()
    
    try:
        result = await runner.run(
            scenario_id="ecommerce-catalog",
            variant=SystemVariant.FULL_SYSTEM,
            mode=ResultMode.REAL,
            model_identifier="llama3.1",
        )
        overall_duration = time.time() - overall_start
        
        print("\n" + "=" * 70)
        print("EXPERIMENT #7 COMPLETED")
        print("=" * 70)
        
        print(f"\n--- RESULT SUMMARY ---")
        print(f"experiment_id:        {result.experiment_id}")
        print(f"scenario_id:          {result.scenario_id}")
        print(f"system_variant:       {result.system_variant.value}")
        print(f"result_mode:          {result.result_mode.value}")
        print(f"model:                {result.model}")
        print(f"domain:               {result.domain}")
        print(f"success:              {result.success}")
        print(f"delivery_status:      {result.delivery_status}")
        print(f"execution_time_sec:   {result.execution_time_sec}")
        print(f"overall_duration:     {round(overall_duration, 3)}")
        
        print(f"\n--- LLM TELEMETRY ---")
        print(f"llm_calls:            {result.llm_calls}")
        
        print(f"\n--- QA TELEMETRY ---")
        print(f"qa_score:             {result.qa_score}")
        if result.defect_counts:
            print(f"defects_critical:     {result.defect_counts.critical}")
            print(f"defects_major:        {result.defect_counts.major}")
            print(f"defects_minor:        {result.defect_counts.minor}")
        
        print(f"\n--- REWORK ---")
        print(f"rework_cycles:        {result.rework_cycles}")
        
        print(f"\n--- RAG TELEMETRY ---")
        print(f"rag_used:             {result.rag_used}")
        print(f"rag_retrievals:       {result.rag_retrievals}")
        print(f"rag_successes:        {result.rag_successes}")
        print(f"rag_failures:         {result.rag_failures}")
        print(f"chunks_retrieved:     {result.chunks_retrieved}")
        print(f"rag_latency_ms:       {result.rag_latency_ms}")
        print(f"knowledge_reused:     {result.knowledge_reused}")
        
        print(f"\n--- AGENT TELEMETRY ---")
        print(f"agent_failure_count:  {result.agent_failure_count}")
        print(f"task_completion_rate: {result.task_completion_rate}")
        
        print(f"\n--- REPRODUCIBILITY ---")
        print(f"commit_hash:          {result.reproducibility.commit_hash}")
        
        # Verify result was persisted
        results_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "evaluation", "results")
        result_files = sorted([f for f in os.listdir(results_dir) if f.endswith('.json')])
        print(f"\n--- PERSISTED RESULTS ---")
        print(f"total result files:   {len(result_files)}")
        for f in result_files:
            print(f"  {f}")
        
        # Dump the full result JSON
        print(f"\n--- FULL RESULT JSON ---")
        print(result.model_dump_json(indent=2))

    except Exception as e:
        overall_duration = time.time() - overall_start
        print(f"\n{'=' * 70}")
        print(f"EXPERIMENT #7 FAILED WITH EXCEPTION")
        print(f"{'=' * 70}")
        print(f"Exception type:  {type(e).__name__}")
        print(f"Exception msg:   {str(e)}")
        print(f"Duration:        {round(overall_duration, 3)}s")
        print(f"\n--- FULL TRACEBACK ---")
        traceback.print_exc()
        
        # Still check persisted results
        results_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "evaluation", "results")
        if os.path.isdir(results_dir):
            result_files = sorted([f for f in os.listdir(results_dir) if f.endswith('.json')])
            print(f"\n--- PERSISTED RESULTS ---")
            print(f"total result files:   {len(result_files)}")
            for f in result_files:
                print(f"  {f}")

if __name__ == "__main__":
    asyncio.run(main())
