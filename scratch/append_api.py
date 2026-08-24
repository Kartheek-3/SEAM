with open('backend/api.py', 'r') as f:
    c = f.read()

import_str = 'from backend.llm.worker_registry import global_registry\n\n'
new_endpoint = '''
@api_router.get("/api/v1/workers", response_model=Dict[str, Any])
def get_workers():
    """Returns the current state of the distributed worker pool registry."""
    workers = global_registry.list_workers()
    return {
        "workers": [
            {
                "worker_id": w.worker_id,
                "host": w.host,
                "port": w.port,
                "model": w.model,
                "status": w.status.value if hasattr(w.status, 'value') else w.status
            } for w in workers
        ]
    }
'''

if 'get_workers' not in c:
    c = import_str + c + new_endpoint
    with open('backend/api.py', 'w') as f:
        f.write(c)
