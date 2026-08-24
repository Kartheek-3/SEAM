import enum
import logging
import asyncio
import socket
import urllib.request
import urllib.error
from typing import Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class WorkerStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    BUSY = "BUSY"
    UNHEALTHY = "UNHEALTHY"
    OFFLINE = "OFFLINE"
    DRAINING = "DRAINING"

class Worker(BaseModel):
    worker_id: str = Field(..., description="Unique identifier for the worker")
    host: str = Field(..., description="Worker host, e.g., 'localhost'")
    port: int = Field(..., description="Worker port, e.g., 11434")
    model: str = Field(..., description="Primary model loaded on this worker")
    capabilities: List[str] = Field(default_factory=list, description="List of capabilities (e.g., 'rag', 'coding')")
    status: WorkerStatus = Field(default=WorkerStatus.OFFLINE, description="Current status of the worker")
    current_task: Optional[str] = Field(default=None, description="Task ID currently being processed")
    last_health_check: Optional[datetime] = Field(default=None, description="Timestamp of last health check")
    metadata: dict = Field(default_factory=dict, description="Optional metadata")

    @property
    def base_url(self) -> str:
        """Returns the fully constructed base URL for this worker."""
        # Typically HTTP for Ollama unless configured otherwise
        return f"http://{self.host}:{self.port}"

def check_health(worker: Worker, timeout_sec: float = 1.0) -> bool:
    """
    Perform a synchronous health check on the specified worker.
    Returns True if healthy, False if unhealthy/unreachable.
    """
    try:
        # For Ollama, the /api/tags endpoint is a lightweight way to check readiness.
        url = f"{worker.base_url}/api/tags"
        request = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(request, timeout=timeout_sec) as response:
            return response.status == 200
    except (urllib.error.URLError, socket.timeout, ConnectionRefusedError, Exception) as e:
        logger.debug(f"Health check failed for {worker.worker_id} at {worker.base_url}: {e}")
        return False

async def async_check_health(worker: Worker, timeout_sec: float = 1.0) -> bool:
    """
    Perform an asynchronous, non-blocking health check on the specified worker.
    Uses asyncio.to_thread to prevent blocking the event loop.
    """
    return await asyncio.to_thread(check_health, worker, timeout_sec)

