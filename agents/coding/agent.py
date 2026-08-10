import logging
import time
import json
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from agents.base import BaseAgent, RAGService
from backend.schemas.agent_io import AgentInput, AgentOutput
from backend.schemas.enums import AgentStatus, AgentRole, ArtifactType
from backend.schemas.artifacts import Artifact
from backend.schemas.qa import ReworkFeedback
from agents.coding.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE, REWORK_PROMPT_TEMPLATE
from agents.coding.exceptions import PathTraversalError, CodeGenerationError

logger = logging.getLogger(__name__)

class GeneratedFile(BaseModel):
    path: str = Field(..., description="Relative file path, e.g., 'src/main.py'")
    content: str = Field(..., description="The complete generated source code")
    language: str = Field(..., description="Programming language, e.g., 'python', 'json'")
    artifact_type: ArtifactType = Field(..., description="Type of artifact (usually 'code', 'test', or 'config')")

class CodeGenerationResponse(BaseModel):
    files: list[GeneratedFile] = Field(..., description="List of generated files")

from backend.llm.client import LLMClient

class CodingAgent(BaseAgent):
    """
    Coding Agent responsible for generating source code artifacts based on task specifications.
    """
    def __init__(self, llm_client: LLMClient, rag_service: RAGService | None = None):
        super().__init__(agent_id="coding_agent", rag_service=rag_service)
        self.llm = llm_client

    def _validate_path(self, path: str) -> None:
        """Ensure the path is strictly relative and contains no traversal operators."""
        if not path or not path.strip():
            raise PathTraversalError("File path cannot be empty.")
            
        normalized = path.replace("\\", "/")
        if normalized.startswith("/") or normalized.startswith("~"):
            raise PathTraversalError(f"Absolute paths are not allowed: {path}")
            
        parts = normalized.split("/")
        if ".." in parts:
            raise PathTraversalError(f"Path traversal is not allowed: {path}")

    def _format_prompt(self, input_data: AgentInput) -> str:
        knowledge_text = ""
        if input_data.knowledge_context and input_data.knowledge_context.chunks:
            knowledge_text = "\n".join([chunk.content for chunk in input_data.knowledge_context.chunks])
        else:
            knowledge_text = "No additional domain knowledge provided."

        task_data = json.dumps(input_data.context.get("task_data", {}), indent=2)
        dep_outputs = json.dumps(input_data.context.get("dependency_outputs", {}), indent=2)

        if input_data.rework_feedback:
            findings_text = "\n".join([f"- [{f.severity.value}] {f.description}" for f in input_data.rework_feedback.qa_result.findings])
            focus_areas = ", ".join(input_data.rework_feedback.focus_areas)
            
            return REWORK_PROMPT_TEMPLATE.format(
                instructions=input_data.instructions,
                task_data=task_data,
                dependency_outputs=dep_outputs,
                knowledge=knowledge_text,
                rework_instructions=input_data.rework_feedback.instructions,
                rework_findings=findings_text,
                rework_focus_areas=focus_areas
            )
        else:
            return USER_PROMPT_TEMPLATE.format(
                instructions=input_data.instructions,
                task_data=task_data,
                dependency_outputs=dep_outputs,
                knowledge=knowledge_text
            )

    async def execute(self, input_data: AgentInput) -> AgentOutput:
        start_time = time.time()
        logger.info(f"Task {input_data.task_id}: CodingAgent starting execution.")

        if not input_data.instructions.strip():
            return AgentOutput(
                task_id=input_data.task_id,
                agent_id=AgentRole.CODING,
                status=AgentStatus.FAILURE,
                result={},
                feedback="Instructions cannot be empty.",
                execution_time_ms=0
            )

        user_prompt = self._format_prompt(input_data)
        
        # Max retries for malformed JSON or empty code
        max_retries = 3
        last_error = ""

        for attempt in range(max_retries):
            try:
                response = await self.llm.generate_structured_response(
                    system_prompt=SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                    response_model=CodeGenerationResponse
                )

                if not response.files:
                    raise CodeGenerationError("LLM returned zero files.")

                artifacts = []
                for idx, gen_file in enumerate(response.files):
                    self._validate_path(gen_file.path)
                    
                    if not gen_file.content.strip():
                        raise CodeGenerationError(f"Generated file '{gen_file.path}' is empty.")
                        
                    artifacts.append(
                        Artifact(
                            id=f"art-{input_data.task_id}-{idx}",
                            project_id=input_data.context.get("project_id", "unknown"), # Can be injected via supervisor context if needed
                            task_id=input_data.task_id,
                            type=gen_file.artifact_type,
                            name=gen_file.path,
                            content=gen_file.content,
                            language=gen_file.language,
                            created_at=datetime.now(timezone.utc)
                        )
                    )

                execution_time = int((time.time() - start_time) * 1000)
                logger.info(f"Task {input_data.task_id}: CodingAgent completed successfully in {execution_time}ms.")

                return AgentOutput(
                    task_id=input_data.task_id,
                    agent_id=AgentRole.CODING,
                    status=AgentStatus.SUCCESS,
                    result={"files_generated": len(artifacts)},
                    artifacts=artifacts,
                    execution_time_ms=execution_time
                )

            except (PathTraversalError, CodeGenerationError) as e:
                logger.warning(f"Validation error on attempt {attempt + 1}: {e}")
                last_error = str(e)
                user_prompt += f"\n\nValidation Error: {last_error}. Please fix this and generate again."
            except Exception as e:
                logger.error(f"LLM execution failed: {e}")
                return AgentOutput(
                    task_id=input_data.task_id,
                    agent_id=AgentRole.CODING,
                    status=AgentStatus.FAILURE,
                    result={},
                    feedback=f"LLM failure: {str(e)}",
                    execution_time_ms=int((time.time() - start_time) * 1000)
                )

        return AgentOutput(
            task_id=input_data.task_id,
            agent_id=AgentRole.CODING,
            status=AgentStatus.FAILURE,
            result={},
            feedback=f"Code generation failed after {max_retries} attempts. Last error: {last_error}",
            execution_time_ms=int((time.time() - start_time) * 1000)
        )
