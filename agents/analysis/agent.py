"""
SEAM Analysis Agent Implementation
"""

import json
import logging
import time
from typing import Any

from pydantic import ValidationError

from agents.base import BaseAgent, RAGService
from agents.analysis.exceptions import EmptyInputError
from agents.analysis.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE, REWORK_SECTION_TEMPLATE, KNOWLEDGE_SECTION_TEMPLATE
from backend.llm.client import LLMClient, LLMException
from backend.schemas import (
    AgentInput,
    AgentOutput,
    AgentRole,
    AgentStatus,
    RequirementSpec,
)

logger = logging.getLogger(__name__)


class AnalysisAgent(BaseAgent):
    """
    Analysis Agent responsible for requirement understanding, domain identification,
    and constraint extraction.
    """

    def __init__(self, llm_client: LLMClient, rag_service: RAGService | None = None):
        """
        Initialize the Analysis Agent.

        Args:
            llm_client: The modular LLM client for structured generation.
            rag_service: Optional RAG service for retrieving past patterns (Phase 2+).
        """
        super().__init__(agent_id=AgentRole.ANALYSIS.value, rag_service=rag_service)
        self.llm = llm_client
        self.max_retries = 3

    async def execute(self, input: AgentInput) -> AgentOutput:
        """
        Execute the requirement analysis task.
        """
        task_id = input.task_id
        logger.info(f"Analysis Agent started for task: {task_id}")
        start_time = time.time()

        try:
            # 1. Input Validation
            raw_description = input.context.get("raw_description")
            if not raw_description or not str(raw_description).strip():
                logger.error(f"Task {task_id}: Empty input received.")
                raise EmptyInputError("The 'raw_description' context variable is missing or empty.")

            # Log length securely
            logger.info(f"Task {task_id}: Processing raw_description of length {len(raw_description)}")

            # 2. RAG Retrieval
            knowledge_section = ""
            if self.rag_service:
                logger.info(f"Task {task_id}: Attempting RAG retrieval for raw_description")
                try:
                    rag_context = await self.rag_service.retrieve(query=str(raw_description))
                    if rag_context and rag_context.chunks:
                        logger.info(f"Task {task_id}: Retrieved {len(rag_context.chunks)} chunks in {rag_context.retrieval_time_ms}ms")
                        chunks_text = "\n\n".join([f"Source: {c.source}\n{c.content}" for c in rag_context.chunks])
                        knowledge_section = KNOWLEDGE_SECTION_TEMPLATE.format(knowledge_text=chunks_text)
                    else:
                        logger.info(f"Task {task_id}: No relevant knowledge found.")
                except Exception as e:
                    logger.error(f"Task {task_id}: RAG retrieval failed: {e}")

            # 3. Build Prompts
            rework_section = ""
            if input.rework_feedback:
                findings_str = "\n".join(
                    f"- [{f.severity.value.upper()}] {f.description}" 
                    for f in input.rework_feedback.qa_result.findings
                )
                rework_section = REWORK_SECTION_TEMPLATE.format(
                    rework_instructions=input.rework_feedback.instructions,
                    focus_areas=", ".join(input.rework_feedback.focus_areas),
                    qa_findings=findings_str
                )

            user_prompt = USER_PROMPT_TEMPLATE.format(
                raw_description=raw_description,
                knowledge_section=knowledge_section,
                instructions=input.instructions,
                rework_section=rework_section
            )

            # 4. LLM Invocation & Retry Loop
            requirement_spec = await self._generate_with_retries(user_prompt, input.context.get("project_id", "unknown"))

            # Calculate confidence based on ambiguities
            ambiguity_penalty = min(len(requirement_spec.ambiguities) * 0.1, 0.4)
            confidence = max(0.0, 0.9 - ambiguity_penalty)

            execution_time_ms = int((time.time() - start_time) * 1000)
            logger.info(f"Task {task_id} completed successfully in {execution_time_ms}ms")

            return AgentOutput(
                task_id=task_id,
                agent_id=AgentRole.ANALYSIS,
                status=AgentStatus.SUCCESS,
                result=requirement_spec.model_dump(),
                artifacts=[],
                confidence=confidence,
                execution_time_ms=execution_time_ms,
            )

        except EmptyInputError as e:
            return self._build_failure_output(task_id, str(e), start_time)
        except LLMException as e:
            logger.error(f"Task {task_id}: LLM API failure: {e}")
            return self._build_failure_output(task_id, f"LLM API Error: {e}", start_time)
        except Exception as e:
            logger.error(f"Task {task_id}: Unexpected error: {e}", exc_info=True)
            return self._build_failure_output(task_id, f"Unexpected error: {e}", start_time)

    async def _generate_with_retries(self, user_prompt: str, project_id: str) -> RequirementSpec:
        """Helper to invoke LLM with self-correction retries."""
        current_user_prompt = user_prompt
        
        for attempt in range(1, self.max_retries + 1):
            try:
                # LLM call expecting RequirementSpec
                response_obj = await self.llm.generate_structured_output(
                    system_prompt=SYSTEM_PROMPT,
                    user_prompt=current_user_prompt,
                    response_model=RequirementSpec
                )
                
                # Enforce project_id matching
                if response_obj.project_id != project_id:
                    response_obj.project_id = project_id

                return response_obj

            except (ValidationError, json.JSONDecodeError) as e:
                logger.warning(f"Validation failure on attempt {attempt}: {e}")
                if attempt == self.max_retries:
                    raise Exception(f"Failed to generate valid RequirementSpec after {self.max_retries} attempts: {e}")
                
                # Append error to the prompt for self-correction
                current_user_prompt += f"\\n\\nYOUR PREVIOUS OUTPUT FAILED VALIDATION:\\n{str(e)}\\nPlease correct the JSON output."

    def _build_failure_output(self, task_id: str, feedback: str, start_time: float) -> AgentOutput:
        """Helper to construct a FAILURE AgentOutput."""
        return AgentOutput(
            task_id=task_id,
            agent_id=AgentRole.ANALYSIS,
            status=AgentStatus.FAILURE,
            result={},
            artifacts=[],
            confidence=0.0,
            feedback=feedback,
            execution_time_ms=int((time.time() - start_time) * 1000)
        )
