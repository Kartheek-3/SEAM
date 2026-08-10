"""
Planning & Design Agent Exceptions
"""

class PlanningAgentError(Exception):
    """Base exception for Planning Agent errors."""
    pass

class EmptyRequirementSpecError(PlanningAgentError):
    """Raised when the RequirementSpec provided in the context is empty or missing."""
    pass

class CircularDependencyError(PlanningAgentError):
    """Raised when the generated task dependency graph contains a cycle."""
    pass
