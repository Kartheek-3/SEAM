import logging
from typing import Dict, List, Optional
from threading import Lock
from datetime import datetime, timezone
from backend.llm.worker import Worker, WorkerStatus

logger = logging.getLogger(__name__)

class WorkerRegistry:
    """
    A thread-safe registry for managing a pool of LLM workers.
    This maintains the logical state of all known workers.
    """
    def __init__(self):
        self._workers: Dict[str, Worker] = {}
        self._lock = Lock()

    def register_worker(self, worker: Worker) -> None:
        """Register a new worker or update an existing one by ID."""
        with self._lock:
            self._workers[worker.worker_id] = worker
            logger.debug(f"Registered worker: {worker.worker_id}")

    def unregister_worker(self, worker_id: str) -> None:
        """Remove a worker from the registry."""
        with self._lock:
            if worker_id in self._workers:
                del self._workers[worker_id]
                logger.debug(f"Unregistered worker: {worker_id}")

    def get_worker(self, worker_id: str) -> Optional[Worker]:
        """Retrieve a specific worker by ID."""
        with self._lock:
            return self._workers.get(worker_id)

    def list_workers(self) -> List[Worker]:
        """Return a snapshot list of all registered workers."""
        with self._lock:
            return list(self._workers.values())

    def get_available_workers(self, required_capability: Optional[str] = None) -> List[Worker]:
        """
        Return a list of workers that are currently AVAILABLE.
        Optionally filter by a required capability.
        """
        with self._lock:
            available = [w for w in self._workers.values() if w.status == WorkerStatus.AVAILABLE]
            
            if required_capability:
                available = [w for w in available if required_capability in w.capabilities]
                
            # Deterministic sorting (e.g. by worker_id) ensures predictability
            available.sort(key=lambda w: w.worker_id)
            return available

    def mark_busy(self, worker_id: str, task_id: str) -> bool:
        """
        Mark a worker as BUSY and assign it a task.
        Returns True if successful, False if the worker was not AVAILABLE.
        """
        with self._lock:
            worker = self._workers.get(worker_id)
            if worker and worker.status == WorkerStatus.AVAILABLE:
                worker.status = WorkerStatus.BUSY
                worker.current_task = task_id
                return True
            return False

    def mark_available(self, worker_id: str) -> None:
        """Mark a worker as AVAILABLE and clear its current task."""
        with self._lock:
            worker = self._workers.get(worker_id)
            if worker and worker.status in (WorkerStatus.BUSY, WorkerStatus.UNHEALTHY):
                worker.status = WorkerStatus.AVAILABLE
                worker.current_task = None

    def mark_unhealthy(self, worker_id: str) -> None:
        """Mark a worker as UNHEALTHY (e.g., due to connection timeout)."""
        with self._lock:
            worker = self._workers.get(worker_id)
            if worker:
                worker.status = WorkerStatus.UNHEALTHY
                worker.current_task = None

    def mark_offline(self, worker_id: str) -> None:
        """Mark a worker as entirely OFFLINE."""
        with self._lock:
            worker = self._workers.get(worker_id)
            if worker:
                worker.status = WorkerStatus.OFFLINE
                worker.current_task = None

    def update_health_timestamp(self, worker_id: str, is_healthy: bool) -> None:
        """Update the health check timestamp and conditionally transition status."""
        with self._lock:
            worker = self._workers.get(worker_id)
            if not worker:
                return
                
            worker.last_health_check = datetime.now(timezone.utc)
            
            # If the health check failed, mark UNHEALTHY unless it's already OFFLINE
            if not is_healthy and worker.status != WorkerStatus.OFFLINE:
                worker.status = WorkerStatus.UNHEALTHY
                worker.current_task = None
            
            # If it was UNHEALTHY and now passes, restore to AVAILABLE
            # OFFLINE workers must NOT be automatically recovered by a health check
            elif is_healthy and worker.status == WorkerStatus.UNHEALTHY:
                worker.status = WorkerStatus.AVAILABLE
                worker.current_task = None

# Global registry for the API/prototype
global_registry = WorkerRegistry()
