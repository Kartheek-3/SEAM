import logging
import time
import json
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

from agents.base import BaseAgent, RAGService
from backend.schemas.agent_io import AgentInput, AgentOutput
from backend.schemas.enums import AgentStatus, AgentRole, FindingSeverity, QAVerdict
from backend.schemas.qa import QAResult, QAFinding
from agents.qa.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from agents.qa.exceptions import QAValidationError, QAMissingArtifactError

logger = logging.getLogger(__name__)

class QAEvaluationResponse(BaseModel):
    findings: list[QAFinding] = Field(default_factory=list, description="List of identified issues in the code.")
    tests_passed: int = Field(default=0, description="Estimated number of acceptance criteria fully satisfied.")
    tests_failed: int = Field(default=0, description="Estimated number of acceptance criteria not satisfied.")
    tests_total: int = Field(default=0, description="Total number of acceptance criteria evaluated.")
    recommendations: list[str] = Field(default_factory=list, description="General architectural or structural recommendations.")

from backend.llm.client import LLMClient

class QAAgent(BaseAgent):
    """
    QA Agent responsible for static code analysis, semantic review against requirements,
    and structured QA result generation.
    """
    def __init__(self, llm_client: LLMClient, rag_service: RAGService | None = None):
        super().__init__(agent_id="qa_agent", rag_service=rag_service)
        self.llm = llm_client

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
            # handle cases where artifact is a dict or an Artifact model
            name = art.name if hasattr(art, "name") else art.get("name", "unknown")
            content = art.content if hasattr(art, "content") else art.get("content", "")
            artifacts_text += f"\n--- FILE: {name} ---\n{content}\n"

        return USER_PROMPT_TEMPLATE.format(
            instructions=input_data.instructions,
            task_data=task_data,
            artifacts_text=artifacts_text,
            knowledge=knowledge_text
        )

    def _calculate_qa_score(self, findings: list[QAFinding]) -> float:
        """Calculate a QA score based on findings. 1.0 is perfect."""
        score = 1.0
        for finding in findings:
            if finding.severity == FindingSeverity.CRITICAL:
                score -= 0.4
            elif finding.severity == FindingSeverity.MAJOR:
                score -= 0.2
            elif finding.severity == FindingSeverity.MINOR:
                score -= 0.05
        return max(0.0, min(1.0, score))

    def _determine_verdict(self, findings: list[QAFinding], tests_failed: int) -> QAVerdict:
        """Determine PASS/FAIL verdict deterministically based on findings."""
        if tests_failed > 0:
            return QAVerdict.FAIL
            
        for finding in findings:
            if finding.severity in [FindingSeverity.CRITICAL, FindingSeverity.MAJOR]:
                return QAVerdict.FAIL
        return QAVerdict.PASS

    async def execute(self, input_data: AgentInput) -> AgentOutput:
        start_time = time.time()
        logger.info(f"Task {input_data.task_id}: QAAgent starting execution.")

        artifacts = input_data.context.get("dependency_outputs", [])
        if not artifacts:
            # Deterministic failure when no code is provided
            logger.warning(f"Task {input_data.task_id}: QA invoked with no source artifacts.")
            missing_result = QAResult(
                task_id=input_data.task_id,
                verdict=QAVerdict.FAIL,
                score=0.0,
                findings=[
                    QAFinding(
                        category="static_analysis",
                        severity=FindingSeverity.CRITICAL,
                        description="No source code artifacts were provided for QA review.",
                        suggestion="Ensure Coding Agent generated files successfully."
                    )
                ],
                evaluated_at=datetime.now(timezone.utc)
            )
            return AgentOutput(
                task_id=input_data.task_id,
                agent_id=AgentRole.QA,
                status=AgentStatus.SUCCESS, # QA successfully performed its job of failing the code
                result=missing_result.model_dump(),
                execution_time_ms=int((time.time() - start_time) * 1000)
            )

        user_prompt = self._format_prompt(input_data)
        
        max_retries = 3
        last_error = ""

        for attempt in range(max_retries):
            try:
                response = await self.llm.generate_structured_response(
                    system_prompt=SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                    response_model=QAEvaluationResponse
                )

                score = self._calculate_qa_score(response.findings)
                verdict = self._determine_verdict(response.findings, response.tests_failed)
                
                qa_result = QAResult(
                    task_id=input_data.task_id,
                    verdict=verdict,
                    score=score,
                    findings=response.findings,
                    tests_passed=response.tests_passed,
                    tests_failed=response.tests_failed,
                    tests_total=response.tests_total,
                    recommendations=response.recommendations,
                    evaluated_at=datetime.now(timezone.utc)
                )

                execution_time = int((time.time() - start_time) * 1000)
                logger.info(f"Task {input_data.task_id}: QAAgent completed evaluation. Verdict: {verdict.value}")

                return AgentOutput(
                    task_id=input_data.task_id,
                    agent_id=AgentRole.QA,
                    status=AgentStatus.SUCCESS,
                    result=qa_result.model_dump(),
                    artifacts=[], # In Phase 5, QA does not generate code or persist tests natively
                    execution_time_ms=execution_time
                )

            except Exception as e:
                logger.warning(f"Validation error on attempt {attempt + 1}: {e}")
                last_error = str(e)
                user_prompt += f"\n\nValidation Error: {last_error}. Please ensure output matches the schema."

        logger.error(f"Task {input_data.task_id}: QA Agent failed to produce valid result after {max_retries} attempts.")
        return AgentOutput(
            task_id=input_data.task_id,
            agent_id=AgentRole.QA,
            status=AgentStatus.FAILURE,
            result={},
            feedback=f"QA evaluation failed due to malformed LLM responses. Last error: {last_error}",
            execution_time_ms=int((time.time() - start_time) * 1000)
        )
