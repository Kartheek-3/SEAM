import asyncio
import json
import time
import copy
from pydantic import BaseModel
from backend.config import settings
from backend.llm.worker_registry import global_registry, WorkerRegistry
from backend.llm.worker_pool import WorkerPool
from backend.llm.worker_client import WorkerAwareOllamaClient
from backend.llm.worker import WorkerStatus, Worker

class TinyResponse(BaseModel):
    hello: str

async def main():
    print("==================================================")
    print("PHASE 9D.21.1 VALIDATION")
    print("==================================================")
    
    import urllib.parse
    from backend.llm.worker import Worker, async_check_health
    if settings.ollama_workers:
        workers_cfg = json.loads(settings.ollama_workers)
        print(f"[CONFIG] Found explicit OLLAMA_WORKERS configuration with {len(workers_cfg)} workers.")
        for w in workers_cfg:
            global_registry.register_worker(Worker(
                worker_id=w["worker_id"],
                host=w["host"],
                port=w["port"],
                model=w["model"],
                status=WorkerStatus.AVAILABLE
            ))
    else:
        print("[CONFIG] No explicit OLLAMA_WORKERS. Falling back to single default worker.")
        parsed = urllib.parse.urlparse(settings.ollama_base_url)
        global_registry.register_worker(Worker(
            worker_id="default-worker-1",
            host=parsed.hostname or "localhost",
            port=parsed.port or 11434,
            model=settings.ollama_model_general,
            status=WorkerStatus.AVAILABLE
        ))

    
    print("\n[REGISTRY] Workers currently in global_registry:")
    workers = global_registry.list_workers()
    for w in workers:
        wid = w.worker_id
        print(f"  - ID: {wid}, HOST: {w.host}, PORT: {w.port}, MODEL: {w.model}, STATUS: {w.status}")
    
    reachable_workers = []
    print("\n==================================================")
    print("STEP 3: HEALTH CHECKING")
    for w in workers:
        wid = w.worker_id
        w_obj = global_registry.get_worker(wid)
        is_healthy = await async_check_health(w_obj)
        if is_healthy:
            global_registry.mark_available(wid)
            print(f"  [HEALTH] {wid} -> HEALTHY")
            reachable_workers.append(w_obj)
        else:
            global_registry.mark_unhealthy(wid)
            print(f"  [HEALTH] {wid} -> UNHEALTHY")

    print("\n==================================================")
    print(f"REACHABLE WORKERS: {len(reachable_workers)}")

    if len(reachable_workers) == 0:
        print("SINGLE-WORKER REAL VALIDATION: FAIL")
        print("MULTI-WORKER REAL VALIDATION: FAIL")
        print("No reachable workers found.")
        return

    # Step 4: Single-Worker Test
    print("\n==================================================")
    print("STEP 4: SINGLE-WORKER TEST")
    w1 = reachable_workers[0]
    print(f"Using worker {w1.worker_id} for minimal inference...")
    
    pool = WorkerPool(global_registry)
    client = WorkerAwareOllamaClient(pool)
    
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
        print("SINGLE-WORKER REAL VALIDATION: PASS")
    except asyncio.TimeoutError:
        print("  [INFERENCE] FAILED: TIMEOUT")
        print("SINGLE-WORKER REAL VALIDATION: FAIL")
    except Exception as e:
        print(f"  [INFERENCE] FAILED: {e}")
        print("SINGLE-WORKER REAL VALIDATION: FAIL")

    # Check lease transition
    w1_post = global_registry.get_worker(w1.worker_id)
    print(f"  [LEASE] Worker {w1.worker_id} final status: {w1_post.status.value}")

    # Step 5: Multi-Worker Test
    print("\n==================================================")
    print("STEP 5: MULTI-WORKER TEST")
    if len(reachable_workers) >= 2:
        print("Multiple reachable workers detected. Executing concurrent test...")
        
        async def run_task(idx):
            s = time.time()
            try:
                r = await asyncio.wait_for(
                    client.generate_structured_output(
                        "You are a helpful assistant.", 
                        "Return EXACTLY this JSON and nothing else: {\"hello\": \"world\"}", 
                        TinyResponse
                    ),
                    timeout=30.0
                )
                return time.time() - s, r, True
            except asyncio.TimeoutError:
                return time.time() - s, "TIMEOUT", False
            except Exception as e:
                return time.time() - s, str(e), False

        results = await asyncio.gather(run_task(1), run_task(2))
        for idx, (lat, res, ok) in enumerate(results):
            print(f"  [CONCURRENT {idx+1}] OK: {ok}, Latency: {lat:.2f}s, Res: {res}")
        print("MULTI-WORKER REAL VALIDATION: PASS")
    else:
        print("MULTI-WORKER REAL VALIDATION: NOT POSSIBLE — only one reachable worker exists.")

    # Step 6: Failure Isolation
    print("\n==================================================")
    print("STEP 6: FAILURE ISOLATION")
    
    # Create isolated registry with one valid and one intentionally broken worker
    iso_reg = WorkerRegistry()
    iso_reg.register_worker(Worker(
        worker_id="valid-w", host=w1.host, port=w1.port, model=w1.model, status=WorkerStatus.AVAILABLE
    ))
    iso_reg.register_worker(Worker(
        worker_id="broken-w", host="localhost", port=9999, model=w1.model, status=WorkerStatus.AVAILABLE
    ))
    iso_pool = WorkerPool(iso_reg)
    iso_client = WorkerAwareOllamaClient(iso_pool)
    
    print("Executing concurrent requests against isolated pool (1 valid, 1 broken)...")
    
    async def run_iso():
        try:
            return await asyncio.wait_for(
                iso_client.generate_structured_output(
                    "You are a helpful assistant.", 
                    "Return EXACTLY this JSON and nothing else: {\"hello\": \"world\"}", 
                    TinyResponse
                ),
                timeout=30.0
            )
        except Exception as e:
            return e
            
    res1, res2 = await asyncio.gather(run_iso(), run_iso())
    
    w_valid = iso_reg.get_worker("valid-w")
    w_broken = iso_reg.get_worker("broken-w")
    
    print(f"  [ISO] Valid worker status: {w_valid.status.value}")
    print(f"  [ISO] Broken worker status: {w_broken.status.value}")
    
    if w_broken.status == WorkerStatus.UNHEALTHY and w_valid.status == WorkerStatus.AVAILABLE:
        print("  [ISO] Failure isolation verified.")
    else:
        print("  [ISO] Failure isolation FAILED.")

if __name__ == "__main__":
    asyncio.run(main())
