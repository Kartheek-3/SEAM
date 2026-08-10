"""
Tests for the QA Agent.
"""

import pytest
from datetime import datetime, timezone
from typing import Any

from backend.schemas import (
    AgentInput, AgentOutput, AgentStatus, AgentRole, TaskType, ArtifactType,
    KnowledgeContext, KnowledgeChunk
)
from backend.schemas.artifacts import Artifact
from backend.schemas.qa import QAResult, QAVerdict, FindingSeverity, QAFinding
from agents.qa.agent import QAAgent, QAEvaluationResponse

now = datetime.now(timezone.utc)

class MockLLM:
    def __init__(self, responses: list[QAEvaluationResponse] = None, raise_error=False):
        self.responses = responses or []
        self.raise_error = raise_error
        self.call_count = 0
        self.last_prompt = ""

    async def generate_structured_response(self, system_prompt: str, user_prompt: str, response_model: type) -> Any:
        self.call_count += 1
        self.last_prompt = user_prompt
        if self.raise_error:
            raise ValueError("LLM API Failed")
        
        if self.call_count <= len(self.responses):
            return self.responses[self.call_count - 1]
        
        # Default mock response - PASS
        return QAEvaluationResponse(
            findings=[],
            tests_passed=1,
            tests_failed=0,
            tests_total=1,
            recommendations=["Looks good"]
        )

@pytest.fixture
def agent():
    return QAAgent(llm_client=MockLLM())

def create_input(artifacts=None) -> AgentInput:
    if artifacts is None:
        artifacts = [
            Artifact(
                id="art-1",
                project_id="p-1",
                task_id="t-1",
                type=ArtifactType.CODE,
                name="src/main.py",
                content="print('hello')",
                language="python",
                created_at=now
            )
        ]
        
    return AgentInput(
        task_id="qa-1",
        task_type=TaskType.QA,
        context={"dependency_outputs": artifacts, "task_data": {"acceptance_criteria": "Must print hello"}},
        instructions="Review code"
    )

@pytest.mark.asyncio
async def test_missing_artifacts(agent):
    out = await agent.execute(create_input(artifacts=[]))
    assert out.status == AgentStatus.SUCCESS
    
    assert out.result["verdict"] == "fail"
    assert len(out.result["findings"]) == 1
    assert out.result["findings"][0]["severity"] == FindingSeverity.CRITICAL

@pytest.mark.asyncio
async def test_basic_qa_pass(agent):
    out = await agent.execute(create_input())
    assert out.status == AgentStatus.SUCCESS
    assert out.agent_id == AgentRole.QA
    
    assert out.result["verdict"] == "pass"
    assert out.result["score"] == 1.0

@pytest.mark.asyncio
async def test_basic_qa_fail(agent):
    bad_responses = [
        QAEvaluationResponse(
            findings=[
                QAFinding(
                    category="code_review",
                    severity=FindingSeverity.MAJOR,
                    description="Missing error handling",
                    location="src/main.py"
                )
            ],
            tests_passed=0,
            tests_failed=1,
            tests_total=1,
            recommendations=["Add try-except"]
        )
    ]
    agent.llm = MockLLM(responses=bad_responses)
    out = await agent.execute(create_input())
    assert out.status == AgentStatus.SUCCESS
    
    assert out.result["verdict"] == "fail"
    assert out.result["score"] == 0.8  # 1.0 - 0.2 (MAJOR)
    assert len(out.result["findings"]) == 1

@pytest.mark.asyncio
async def test_malformed_json_retry_and_failure(agent):
    agent.llm = MockLLM(raise_error=True)
    out = await agent.execute(create_input())
    
    # QA agent returns FAILURE if it entirely fails to produce a report
    assert out.status == AgentStatus.FAILURE
    assert agent.llm.call_count == 3
    assert "QA evaluation failed due to malformed LLM responses" in out.feedback
