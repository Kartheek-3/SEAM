"""
Coding Agent Exceptions
"""

class CodingError(Exception):
    """Base exception for Coding Agent errors."""
    pass

class PathTraversalError(CodingError):
    """Raised when the LLM attempts to generate code outside the allowed project paths."""
    pass

class CodeGenerationError(CodingError):
    """Raised when the agent fails to generate valid code artifacts."""
    pass
