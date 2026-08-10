"""
Ollama Client Implementation

Implements the LLMClient protocol using LangChain's Ollama bindings
and structured output parsing to return strongly-typed Pydantic models.
"""

import logging
from typing import Type, TypeVar

from pydantic import BaseModel, ValidationError
from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from backend.llm.client import LLMClient, LLMException
from backend.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class OllamaClient(LLMClient):
    """
    Ollama-backed implementation of the LLMClient Protocol.
    Uses LangChain to query the local Ollama instance and parse the JSON output.
    """

    def __init__(self, model_name: str = settings.ollama_model_general):
        self.model_name = model_name
        try:
            self.llm = Ollama(
                base_url=settings.ollama_base_url,
                model=self.model_name,
                temperature=0.1,
                timeout=settings.ollama_timeout
            )
        except Exception as e:
            logger.error(f"Failed to initialize Ollama LLM: {e}")
            raise LLMException(f"Ollama initialization failed: {e}")

    async def generate_structured_output(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
    ) -> T:
        """
        Generate a structured response mapping to a Pydantic model.
        """
        parser = JsonOutputParser(pydantic_object=response_model)
        
        # We append format instructions to strictly enforce JSON schema.
        format_instructions = parser.get_format_instructions()
        
        prompt = PromptTemplate(
            template="{system_prompt}\n\n{user_prompt}\n\n{format_instructions}",
            input_variables=["system_prompt", "user_prompt"],
            partial_variables={"format_instructions": format_instructions},
        )

        chain = prompt | self.llm | parser
        
        try:
            logger.debug(f"Calling Ollama model {self.model_name}")
            result_dict = await chain.ainvoke({
                "system_prompt": system_prompt,
                "user_prompt": user_prompt
            })
            
            # The JsonOutputParser parses it to a dict. We convert it to the Pydantic model.
            return response_model(**result_dict)
            
        except ValidationError as e:
            logger.error(f"Failed to parse LLM output into {response_model.__name__}: {e}")
            raise e
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise LLMException(f"LLM generation failed: {str(e)}")
