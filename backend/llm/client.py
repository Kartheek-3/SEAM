"""
Abstract LLM Client Interface

Provides a modular protocol for LLM providers (e.g., Llama 3.1, OpenAI, mock providers)
to generate structured output matching a Pydantic schema.
"""

from typing import Protocol, Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMException(Exception):
    """Base exception for LLM provider errors (network, timeout, auth)."""
    pass


class LLMClient(Protocol):
    """
    Protocol defining the required interface for LLM providers in SEAM.
    """

    async def generate_structured_output(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
    ) -> T:
        """
        Generate a structured response from the LLM matching the provided Pydantic model.

        Args:
            system_prompt: The system persona and general instructions.
            user_prompt: The specific request and context.
            response_model: The Pydantic model class to validate the output against.

        Returns:
            An instance of the response_model containing the LLM's output.

        Raises:
            LLMException: If the underlying API call fails.
            pydantic.ValidationError: If the LLM output cannot be parsed into the schema.
        """
        ...
