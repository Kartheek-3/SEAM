"""
Supervisor Agent Exceptions
"""

class SupervisorError(Exception):
    """Base exception for Supervisor Agent errors."""
    pass

class AgentNotFoundError(SupervisorError):
    """Raised when the Supervisor cannot find an agent for a specific TaskType."""
    pass

class WorkflowDeadlockError(SupervisorError):
    """Raised when there are pending tasks but none are ready to execute."""
    pass
