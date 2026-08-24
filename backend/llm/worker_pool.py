import asyncio
import logging
from typing import Optional
from datetime import datetime, timezone

from backend.llm.worker import Worker, check_health, async_check_health, WorkerStatus
from backend.llm.worker_registry import WorkerRegistry

logger = logging.getLogger(__name__)

class WorkerPool:
    """
    Manages the selection and assignment of workers from the registry.
    Ensures safe concurrency and deterministic assignment.
    """
    def __init__(self, registry: WorkerRegistry):
        self.registry = registry
        self._recovering_workers = set()

    async def _recover_worker(self, worker_id: str) -> None:
        """Asynchronously probe an UNHEALTHY worker to see if it has recovered."""
        self._recovering_workers.add(worker_id)
        try:
            worker = self.registry.get_worker(worker_id)
            if not worker or worker.status != WorkerStatus.UNHEALTHY:
                return
                
            is_healthy = await async_check_health(worker, timeout_sec=2.0)
            self.registry.update_health_timestamp(worker_id, is_healthy)
            if is_healthy:
                logger.info(f"Worker {worker_id} recovered and is now AVAILABLE.")
        finally:
            self._recovering_workers.discard(worker_id)

    async def select_worker(self, task_id: str, required_capability: Optional[str] = None, timeout: float = 60.0) -> Worker:
        """
        Block until an AVAILABLE worker is found, then mark it BUSY and return it.
        If timeout is reached, raises TimeoutError.
        """
        start_time = asyncio.get_event_loop().time()
        
        while True:
            # Get list of currently available workers
            available_workers = self.registry.get_available_workers(required_capability)
            
            for worker in available_workers:
                # Attempt atomic assignment
                if self.registry.mark_busy(worker.worker_id, task_id):
                    # We successfully locked this worker for our task
                    logger.debug(f"Assigned task {task_id} to worker {worker.worker_id}")
                    return worker
                    
            # Lazy recovery of UNHEALTHY workers
            now = datetime.now(timezone.utc)
            for w in self.registry.list_workers():
                if w.status == WorkerStatus.UNHEALTHY and w.worker_id not in self._recovering_workers:
                    # 5 second cooldown backoff
                    if w.last_health_check is None or (now - w.last_health_check).total_seconds() > 5.0:
                        asyncio.create_task(self._recover_worker(w.worker_id))

            # Check timeout
            if asyncio.get_event_loop().time() - start_time > timeout:
                logger.error(f"Timeout waiting for an available worker for task {task_id}")
                raise TimeoutError("No available worker found within timeout.")
                
            # Wait before polling again
            await asyncio.sleep(0.5)

    def release_worker(self, worker_id: str) -> None:
        """Release a busy worker back to the AVAILABLE pool."""
        self.registry.mark_available(worker_id)
        logger.debug(f"Released worker {worker_id} to AVAILABLE pool.")

    def report_infrastructure_failure(self, worker_id: str) -> None:
        """
        Mark a worker UNHEALTHY due to a confirmed infrastructure failure
        (e.g., Connection Refused, Timeout). It will not be selected again
        until its health is restored.
        """
        self.registry.mark_unhealthy(worker_id)
        logger.warning(f"Worker {worker_id} marked UNHEALTHY due to infrastructure failure.")
