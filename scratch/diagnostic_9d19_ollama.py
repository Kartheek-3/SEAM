from pydantic import BaseModel
class TestModel(BaseModel):
    status: str
import asyncio
import time
import psutil
import socket
import urllib.request
import urllib.error

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.llm.ollama_client import OllamaClient

async def check_tcp():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect(('localhost', 11434))
        s.close()
        return True
    except Exception as e:
        print(f"TCP Check failed: {e}")
        return False

async def check_http():
    try:
        r = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=1)
        return r.status == 200
    except Exception as e:
        print(f"HTTP Check failed: {e}")
        return False

async def make_request(llm, idx, concurrent=False):
    start = time.time()
    try:
        print(f"[{'CONCURRENT' if concurrent else 'SEQUENTIAL'}] Request {idx} starting...")
        # A simple generation task
        res = await llm.generate_structured_output(
            system_prompt="You are a helpful assistant.",
            user_prompt="Give me a small JSON with {'status': 'ok'}",
            response_model=TestModel
        )
        latency = time.time() - start
        print(f"[{'CONCURRENT' if concurrent else 'SEQUENTIAL'}] Request {idx} SUCCESS in {latency:.2f}s")
        return {"status": "success", "latency": latency}
    except Exception as e:
        latency = time.time() - start
        err_type = type(e).__name__
        err_str = str(e)
        print(f"[{'CONCURRENT' if concurrent else 'SEQUENTIAL'}] Request {idx} FAILED in {latency:.2f}s: {err_type} - {err_str[:100]}")
        return {"status": "error", "error_type": err_type, "error": err_str}

async def run_diagnostics():
    print("="*60)
    print("PHASE 9D.19: OLLAMA INFRASTRUCTURE STABILITY DIAGNOSTIC")
    print("="*60)
    
    tcp_ok = await check_tcp()
    http_ok = await check_http()
    print(f"Base Availability -> TCP: {tcp_ok}, HTTP: {http_ok}")
    
    ram = psutil.virtual_memory()
    print(f"System RAM: {ram.percent}% used of {ram.total / 1024**3:.1f} GB")
    
    cpu = psutil.cpu_percent(interval=1)
    print(f"CPU Utilization: {cpu}%")
    print("-" * 60)
    
    llm = OllamaClient()
    
    # 1. Sequential Test
    print("\n--- SEQUENTIAL TEST (3 requests) ---")
    seq_results = []
    for i in range(3):
        res = await make_request(llm, i)
        seq_results.append(res)
        
    # 2. Concurrent Test
    print("\n--- CONCURRENT TEST (3 requests) ---")
    tasks = [make_request(llm, i, concurrent=True) for i in range(3)]
    conc_results = await asyncio.gather(*tasks)
    
    # Summary
    print("\n" + "="*60)
    print("RESULTS SUMMARY")
    
    def summarize(name, results):
        successes = sum(1 for r in results if r['status'] == 'success')
        errors = [r['error_type'] for r in results if r['status'] == 'error']
        latencies = [r['latency'] for r in results if r['status'] == 'success']
        avg_lat = sum(latencies)/len(latencies) if latencies else 0
        print(f"{name}: {successes}/{len(results)} successes, Avg Latency: {avg_lat:.2f}s")
        if errors:
            print(f"  Errors: {errors}")
            
    summarize("Sequential", seq_results)
    summarize("Concurrent", conc_results)
    
if __name__ == "__main__":
    asyncio.run(run_diagnostics())
