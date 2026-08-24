import asyncio
import time
import socket
import aiohttp
import logging
import statistics
from typing import Optional

from backend.llm.ollama_client import OllamaClient
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("diagnostic_9d14")

class DummyResponse(BaseModel):
    summary: str

async def check_ollama_health(timeout=2.0) -> (bool, str, float):
    start = time.time()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:11434/", timeout=timeout) as response:
                if response.status == 200:
                    return True, "OK", time.time() - start
                return False, f"HTTP {response.status}", time.time() - start
    except aiohttp.ClientConnectorError as e:
        return False, f"Connection Refused/DNS: {e}", time.time() - start
    except asyncio.TimeoutError:
        return False, "Timeout", time.time() - start
    except Exception as e:
        return False, f"Other: {e}", time.time() - start

def check_tcp_localhost():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.0)
        result = sock.connect_ex(('127.0.0.1', 11434))
        sock.close()
        return result == 0
    except Exception:
        return False

async def run_diagnostic():
    results = {
        "baseline": {},
        "sequential": [],
        "sustained": [],
        "overall": {}
    }
    
    logger.info("=== Test A: Baseline Connectivity ===")
    health_ok, msg, lat = await check_ollama_health()
    tcp_ok = check_tcp_localhost()
    results["baseline"] = {
        "health_ok": health_ok,
        "msg": msg,
        "latency": lat,
        "tcp_ok": tcp_ok,
        "timestamp": time.time()
    }
    logger.info(f"Baseline Health: {health_ok} ({msg}) | Latency: {lat:.3f}s | TCP: {tcp_ok}")
    
    client = OllamaClient(model_name="llama3.1")
    
    logger.info("\n=== Test B & C: Sequential / Sustained REAL Load ===")
    prompts = [
        # Sustained load representative of Analysis/Planning
        "Analyze the following requirements: We need a product catalog API. Provide a brief summary.",
        "Pass 1: Generate architectural components for an ecommerce backend: catalog, auth, db, cache. Provide a brief summary.",
        "Pass 2: Elaborate on the Database component. Create tasks for schema and migrations. Provide a brief summary.",
        "Pass 2: Elaborate on the Cache component. Provide a brief summary.",
        "Pass 2: Elaborate on the Catalog API. Provide a brief summary.",
        "Generate python code for a simple API using FastAPI.",
        "Write a unit test for the fastAPI server.",
        "Explain the CAP theorem.",
        "Write a python script that performs matrix multiplication.",
        "Describe how an LRU cache works in detail."
    ]

    total_requests = len(prompts)
    successful = 0
    failed = 0
    timeouts = 0
    connection_failures = 0
    latencies = []
    
    for i, p in enumerate(prompts):
        logger.info(f"\n--- Request {i+1} ---")
        start = time.time()
        success = False
        exc_type = None
        exc_msg = None
        
        try:
            # We use structured generation to mirror the exact pipeline
            res = await client.generate_structured_output(
                system_prompt="You are a planning assistant.",
                user_prompt=p,
                response_model=DummyResponse
            )
            success = True
            successful += 1
            logger.info("Request Succeeded")
        except Exception as e:
            failed += 1
            exc_type = type(e).__name__
            exc_msg = str(e)
            logger.error(f"Request Failed: {exc_type} - {exc_msg}")
            if "time" in exc_msg.lower():
                timeouts += 1
            if "connect" in exc_msg.lower() or "dns" in exc_msg.lower():
                connection_failures += 1
                
        duration = time.time() - start
        if success:
            latencies.append(duration)
            
        logger.info(f"Duration: {duration:.2f}s")
        
        # Test D: Probe after request
        probe_start = time.time()
        health_ok, msg, lat = await check_ollama_health()
        tcp_ok = check_tcp_localhost()
        probe_duration = time.time() - probe_start
        logger.info(f"Post-request Probe: {health_ok} ({msg}) | Latency: {lat:.3f}s | TCP: {tcp_ok}")
        
        results["sequential"].append({
            "attempt": i + 1,
            "duration": duration,
            "success": success,
            "exc_type": exc_type,
            "exc_msg": exc_msg,
            "post_probe_ok": health_ok,
            "post_probe_msg": msg,
            "post_probe_tcp": tcp_ok,
            "post_probe_latency": lat
        })
        
        if not health_ok:
            logger.warning("Ollama unavailable after request! Starting recovery observation...")
            recovery_start = time.time()
            recovered = False
            for r_attempt in range(5):
                await asyncio.sleep(2)
                r_ok, r_msg, _ = await check_ollama_health()
                if r_ok:
                    recovered = True
                    rec_time = time.time() - recovery_start
                    logger.info(f"Ollama recovered after {rec_time:.2f}s")
                    results["sequential"][-1]["recovery_time"] = rec_time
                    break
            if not recovered:
                logger.error("Ollama did not recover within 10 seconds.")
                
        # Test E: Sleep detection (if duration of a simple sleep exceeds expected sleep by > 5s, host likely slept)
        sleep_start = time.time()
        await asyncio.sleep(1)
        sleep_duration = time.time() - sleep_start
        if sleep_duration > 5.0:
            logger.warning(f"Host sleep detected! Sleep took {sleep_duration:.2f}s instead of 1.0s")
            results["sequential"][-1]["host_sleep_detected"] = True

    results["overall"] = {
        "total_requests": total_requests,
        "successful": successful,
        "failed": failed,
        "timeouts": timeouts,
        "connection_failures": connection_failures,
        "mean_latency": statistics.mean(latencies) if latencies else 0,
        "median_latency": statistics.median(latencies) if latencies else 0,
        "p95_latency": statistics.quantiles(latencies, n=20)[18] if len(latencies) > 1 else (max(latencies) if latencies else 0),
        "max_latency": max(latencies) if latencies else 0
    }
    
    import json
    with open("scratch/diagnostic_9d14_results.json", "w") as f:
        json.dump(results, f, indent=2)
        
    logger.info("Diagnostic completed.")

if __name__ == "__main__":
    asyncio.run(run_diagnostic())
