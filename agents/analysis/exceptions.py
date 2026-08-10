"""
Exceptions specific to the Analysis Agent.
"""

class AnalysisError(Exception):
    """Base exception for the Analysis Agent."""
    pass

class EmptyInputError(AnalysisError):
    """Raised when the provided raw description is empty or missing."""
    pass
