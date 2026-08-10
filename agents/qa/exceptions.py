"""
QA Agent Exceptions
"""

class QAMissingArtifactError(Exception):
    """Raised when the QA Agent is invoked without any source code artifacts to review."""
    pass

class QAValidationError(Exception):
    """Raised when the QA Agent encounters a malformed response from the LLM."""
    pass
