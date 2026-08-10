import logging
import time
import json
import os
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from agents.base import BaseAgent, RAGService
from backend.schemas.agent_io import AgentInput, AgentOutput
from backend.schemas.enums import AgentStatus, AgentRole, ArtifactType
from backend.schemas.qa import QAVerdict
from backend.schemas.artifacts import Artifact
from agents.delivery.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from agents.delivery.exceptions import (
    DeliveryQAGateError,
    DeliveryMissingArtifactError,
    DeliveryValidationError
)

logger = logging.getLogger(__name__)

class GeneratedFile(BaseModel):
    path: str = Field(description="The relative path where the file should be saved")
    content: str = Field(description="The complete source code or file content")
    language: str = Field(description="The programming language or file type (e.g., dockerfile, yaml, markdown)")

class DeliveryGenerationResponse(BaseModel):
    files: list[GeneratedFile] = Field(default_factory=list, description="List of generated deployment and documentation files.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Packaging metadata.")

class DeliveryAgent(BaseAgent):
    """
    Delivery Agent responsible for final packaging, generating Docker configurations,
    and preparing release documentation.
    """
    def __init__(self, rag_service: RAGService | None = None):
        super().__init__(agent_id="delivery_agent", rag_service=rag_service)

    def _validate_qa_gate(self, input_data: AgentInput) -> None:
        """Deterministically enforces the QA gate."""
        qa_result = input_data.context.get("qa_result")
        if not qa_result:
            raise DeliveryQAGateError("Missing QA result. Delivery cannot proceed.")
        
        # Handle case where qa_result is a dict (serialized) or a QAResult object
        verdict = qa_result.get("verdict") if isinstance(qa_result, dict) else qa_result.verdict
        
        # Enum string comparison or enum value comparison
        if verdict != QAVerdict.PASS and verdict != "pass":
            raise DeliveryQAGateError(f"QA verdict is {verdict}. Delivery is blocked.")

    def _validate_path(self, path: str) -> str:
        """Deterministically ensure paths are safe."""
        if not path or not path.strip():
            raise DeliveryValidationError("Empty path provided.")
        norm_path = os.path.normpath(path)
        if os.path.isabs(norm_path) or norm_path.startswith(".."):
            raise DeliveryValidationError(f"Path traversal detected in path: {path}")
        return norm_path

    def _format_prompt(self, input_data: AgentInput) -> str:
        knowledge_text = ""
        if input_data.knowledge_context and input_data.knowledge_context.chunks:
            knowledge_text = "\n".join([chunk.content for chunk in input_data.knowledge_context.chunks])
        else:
            knowledge_text = "No additional domain knowledge provided."

        task_data = json.dumps(input_data.context.get("task_data", {}), indent=2)
        
        artifacts = input_data.context.get("dependency_outputs", [])
        artifacts_text = ""
        for art in artifacts:
            name = art.name if hasattr(art, "name") else art.get("name", "unknown")
            content = art.content if hasattr(art, "content") else art.get("content", "")
            artifacts_text += f"\n--- FILE: {name} ---\n{content}\n"

        return USER_PROMPT_TEMPLATE.format(
            task_data=task_data,
            artifacts_text=artifacts_text,
            knowledge=knowledge_text
        )

    async def execute(self, input_data: AgentInput) -> AgentOutput:
        start_time = time.time()
        logger.info(f"Task {input_data.task_id}: DeliveryAgent starting execution.")

        try:
            self._validate_qa_gate(input_data)
        except DeliveryQAGateError as e:
            logger.error(f"Task {input_data.task_id}: {e}")
            return AgentOutput(
                task_id=input_data.task_id,
                agent_id=AgentRole.DELIVERY,
                status=AgentStatus.FAILURE,
                result={},
                feedback=str(e),
                execution_time_ms=int((time.time() - start_time) * 1000)
            )

        source_artifacts = input_data.context.get("dependency_outputs", [])
        if not source_artifacts:
            logger.error(f"Task {input_data.task_id}: No source artifacts provided for delivery.")
            return AgentOutput(
                task_id=input_data.task_id,
                agent_id=AgentRole.DELIVERY,
                status=AgentStatus.FAILURE,
                result={},
                feedback="Delivery blocked: No source code artifacts were provided to package.",
                execution_time_ms=int((time.time() - start_time) * 1000)
            )

        # Track existing paths to prevent LLM from overwriting source files
        existing_paths = set()
        for art in source_artifacts:
            name = art.name if hasattr(art, "name") else art.get("name")
            if name:
                existing_paths.add(self._validate_path(name))

        user_prompt = self._format_prompt(input_data)
        
        max_retries = 3
        last_error = ""

        for attempt in range(max_retries):
            try:
                response = await self.llm.generate_structured_response(
                    system_prompt=SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                    response_model=DeliveryGenerationResponse
                )

                generated_artifacts = []
                for file in response.files:
                    safe_path = self._validate_path(file.path)
                    if safe_path in existing_paths:
                        raise DeliveryValidationError(f"Generated path '{safe_path}' collides with an existing source artifact.")
                    
                    if not file.content.strip():
                        raise DeliveryValidationError(f"Generated file '{safe_path}' is empty.")

                    # Assign artifact type based on extension
                    ext = os.path.splitext(safe_path)[1].lower()
                    art_type = ArtifactType.CONFIG
                    if ext == ".md":
                        art_type = ArtifactType.DOCUMENT
                    elif "dockerfile" in safe_path.lower():
                        art_type = ArtifactType.CONFIG

                    generated_artifacts.append(
                        Artifact(
                            id=f"art-{safe_path.replace('/', '-')}-{int(time.time())}",
                            project_id="default",
                            task_id=input_data.task_id,
                            type=art_type,
                            name=safe_path,
                            content=file.content,
                            language=file.language,
                            created_at=datetime.now(timezone.utc)
                        )
                    )

                execution_time = int((time.time() - start_time) * 1000)
                logger.info(f"Task {input_data.task_id}: DeliveryAgent completed packaging.")

                # Final combined artifacts (Source + Delivery)
                # If source artifacts are dicts, we leave them as dicts or we could cast them,
                # but AgentOutput allows a list of Artifact objects. We'll ensure all are objects.
                final_artifacts = []
                for art in source_artifacts:
                    if isinstance(art, dict):
                        final_artifacts.append(Artifact(**art))
                    else:
                        final_artifacts.append(art)
                
                final_artifacts.extend(generated_artifacts)

                return AgentOutput(
                    task_id=input_data.task_id,
                    agent_id=AgentRole.DELIVERY,
                    status=AgentStatus.SUCCESS,
                    result={"files_packaged": len(final_artifacts), "metadata": response.metadata},
                    artifacts=final_artifacts,
                    execution_time_ms=execution_time
                )

            except DeliveryValidationError as e:
                logger.warning(f"Validation error on attempt {attempt + 1}: {e}")
                last_error = str(e)
                user_prompt += f"\n\nValidation Error: {last_error}. Please fix this and generate again."
            except Exception as e:
                logger.warning(f"Unexpected error on attempt {attempt + 1}: {e}")
                last_error = str(e)
                user_prompt += f"\n\nError: {last_error}. Please fix this and generate again."

        logger.error(f"Task {input_data.task_id}: Delivery Agent failed to produce valid package after {max_retries} attempts.")
        return AgentOutput(
            task_id=input_data.task_id,
            agent_id=AgentRole.DELIVERY,
            status=AgentStatus.FAILURE,
            result={},
            feedback=f"Delivery failed due to malformed LLM responses or path collisions. Last error: {last_error}",
            execution_time_ms=int((time.time() - start_time) * 1000)
        )
