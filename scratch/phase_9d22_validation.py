import asyncio
import json
import time
from pydantic import BaseModel
from backend.config import settings
from backend.llm.worker_registry import global_registry, WorkerRegistry
from backend.llm.worker_pool import WorkerPool
from backend.llm.worker_client import WorkerAwareOllamaClient
from backend.llm.worker import WorkerStatus, Worker, async_check_health
import urllib.parse
from backend.llm.client import LLMException

class TinyResponse(BaseModel):
    hello: str

async def main():
    print("==================================================")
    print("PHASE 9D.22 VALIDATION")
    print("==================================================")
    
    # Configuration
    print("[CONFIG] Falling back to single default worker.")
    parsed = urllib.parse.urlparse(settings.ollama_base_url)
    global_registry.register_worker(Worker(
        worker_id="default-worker-1",
        host=parsed.hostname or "localhost",
        port=parsed.port or 11434,
        model=settings.ollama_model_general,
        status=WorkerStatus.AVAILABLE
    ))

    print("\n==================================================")
    print("STEP 2: HEALTH CHECKING")
    w_obj = global_registry.get_worker("default-worker-1")
    is_healthy = await async_check_health(w_obj)
    if is_healthy:
        global_registry.mark_available("default-worker-1")
        print(f"  [HEALTH] default-worker-1 -> HEALTHY")
    else:
        global_registry.mark_unhealthy("default-worker-1")
        print(f"  [HEALTH] default-worker-1 -> UNHEALTHY")
        return

    pool = WorkerPool(global_registry)
    client = WorkerAwareOllamaClient(pool)

    print("\n==================================================")
    print("STEP 3: SINGLE REAL INFERENCE")
    start = time.time()
    try:
        res = await asyncio.wait_for(
            client.generate_structured_output(
                "You are a helpful assistant.", 
                "Return EXACTLY this JSON and nothing else: {\"hello\": \"world\"}", 
                TinyResponse
            ),
            timeout=30.0
        )
        latency = time.time() - start
        print(f"  [INFERENCE] SUCCESS. Latency: {latency:.2f}s. Result: {res}")
    except Exception as e:
        print(f"  [INFERENCE] FAILED: {e}")
        
    print(f"  [LEASE] Final status: {global_registry.get_worker('default-worker-1').status.value}")

    print("\n==================================================")
    print("STEP 4: SEQUENTIAL REAL REQUESTS")
    for i in range(1, 4):
        s = time.time()
        try:
            r = await asyncio.wait_for(
                client.generate_structured_output(
                    "You are a helpful assistant.", 
                    f"Return EXACTLY this JSON and nothing else: {{\"hello\": \"req{i}\"}}", 
                    TinyResponse
                ),
                timeout=30.0
            )
            lat = time.time() - s
            w_stat = global_registry.get_worker('default-worker-1').status.value
            print(f"  [SEQ {i}] Latency: {lat:.2f}s, Res: {r}, Worker: {w_stat}")
        except Exception as e:
            print(f"  [SEQ {i}] FAILED: {e}")
            
    print("\n==================================================")
    print("STEP 5: FAILURE CLASSIFICATION")
    
    print("  [TEST 5A] Model-generation failure")
    try:
        # Invalid schema demand
        await asyncio.wait_for(
            client.generate_structured_output(
                "You are a helpful assistant.", 
                "Return an invalid json format.", 
                TinyResponse
            ),
            timeout=30.0
        )
        print("  [TEST 5A] FAILED to raise exception.")
    except Exception as e:
        print(f"  [TEST 5A] Exception raised: {type(e).__name__}: {e}")
    print(f"  [TEST 5A] Worker status: {global_registry.get_worker('default-worker-1').status.value}")
    
    print("\n  [TEST 5B] Infrastructure failure")
    iso_reg = WorkerRegistry()
    iso_reg.register_worker(Worker(
        worker_id="broken-w", host="localhost", port=9999, model="llama3.1", status=WorkerStatus.AVAILABLE
    ))
    iso_pool = WorkerPool(iso_reg)
    iso_client = WorkerAwareOllamaClient(iso_pool)
    try:
        await asyncio.wait_for(
            iso_client.generate_structured_output("sys", "user", TinyResponse),
            timeout=10.0
        )
    except Exception as e:
        print(f"  [TEST 5B] Exception raised: {type(e).__name__}")
    print(f"  [TEST 5B] Broken worker status: {iso_reg.get_worker('broken-w').status.value}")

    print("\n==================================================")
    print("STEP 6: CANCELLATION TEST")
    
    async def cancel_test():
        task = asyncio.create_task(
            client.generate_structured_output("You are slow.", "Write a 500 word essay.", TinyResponse)
        )
        await asyncio.sleep(0.5)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            print("  [CANCELLATION] Task cancelled successfully.")
        except Exception as e:
            print(f"  [CANCELLATION] Exception: {e}")
            
    await cancel_test()
    print(f"  [CANCELLATION] Worker status post-cancel: {global_registry.get_worker('default-worker-1').status.value}")


if __name__ == "__main__":
    asyncio.run(main())
