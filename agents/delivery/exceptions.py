"""
Delivery Agent Exceptions
"""

class DeliveryQAGateError(Exception):
    """Raised when the Delivery Agent is invoked without a passing QA verdict."""
    pass

class DeliveryMissingArtifactError(Exception):
    """Raised when the Delivery Agent is invoked without any source code artifacts to package."""
    pass

class DeliveryValidationError(Exception):
    """Raised when the Delivery Agent encounters a malformed response from the LLM or path collision."""
    pass
