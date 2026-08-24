import logging
import uuid
from typing import Type, TypeVar

from pydantic import BaseModel, ValidationError
from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from backend.llm.client import LLMClient, LLMException
from backend.llm.worker_pool import WorkerPool
from backend.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

class WorkerAwareOllamaClient(LLMClient):
    """
    An adapter that implements the LLMClient protocol but routes requests
    through a WorkerPool to distribute load across multiple Ollama instances.
    """
    
    def __init__(self, worker_pool: WorkerPool, model_name: str = settings.ollama_model_general):
        self.worker_pool = worker_pool
        self.model_name = model_name

    async def generate_structured_output(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
    ) -> T:
        """
        Generate a structured response mapping to a Pydantic model by routing
        the request to an available worker from the pool.
        """
        task_id = f"llm-req-{uuid.uuid4().hex[:8]}"
        
        # 1. Select a worker (blocks until one is available)
        try:
            worker = await self.worker_pool.select_worker(task_id=task_id, timeout=settings.worker_lease_timeout)
        except TimeoutError as e:
            raise LLMException("Failed to acquire an available worker within timeout.") from e
            
        is_infrastructure_failure = False
        try:
            # 2. Configure the ephemeral LangChain Ollama instance for this worker
            llm = Ollama(
                base_url=worker.base_url,
                model=worker.model, # use worker's specific model if applicable
                temperature=0.1,
                timeout=settings.ollama_timeout
            )
            
            parser = JsonOutputParser(pydantic_object=response_model)
            format_instructions = parser.get_format_instructions()
            
            prompt = PromptTemplate(
                template="{system_prompt}\n\n{user_prompt}\n\n{format_instructions}",
                input_variables=["system_prompt", "user_prompt"],
                partial_variables={"format_instructions": format_instructions},
            )
            
            chain = prompt | llm | parser
            
            logger.debug(f"Calling model {worker.model} on worker {worker.worker_id} ({worker.base_url})")
            
            # 3. Execute request
            result_dict = await chain.ainvoke({
                "system_prompt": system_prompt,
                "user_prompt": user_prompt
            })
            
            if not isinstance(result_dict, dict):
                raise ValueError("LLM output did not parse into a JSON object mapping.")
                
            # Request succeeded
            return response_model(**result_dict)
            
        except ValidationError as e:
            # Model generation failure (schema issue) - worker is healthy
            logger.error(f"Failed to parse LLM output into {response_model.__name__} on worker {worker.worker_id}: {e}")
            raise e
            
        except TimeoutError as e:
            # Infrastructure failure - mark unhealthy
            logger.error(f"LLM generation timed out on worker {worker.worker_id}")
            is_infrastructure_failure = True
            raise LLMException("LLM generation timed out") from e
            
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            logger.error(f"LLM generation failed on worker {worker.worker_id}: {error_msg}")
            
            # Simple heuristic: if it's an OutputParserException or ValueError, it's a model generation error
            if "OutputParserException" not in error_msg and "ValueError" not in error_msg:
                # Assume infrastructure failure (ConnectionError, etc.)
                is_infrastructure_failure = True
                
            raise LLMException(f"LLM generation failed: {error_msg}")
            
        finally:
            # Ensure the worker is released or marked unhealthy, even if CancelledError occurs
            if is_infrastructure_failure:
                self.worker_pool.report_infrastructure_failure(worker.worker_id)
            else:
                self.worker_pool.release_worker(worker.worker_id)
