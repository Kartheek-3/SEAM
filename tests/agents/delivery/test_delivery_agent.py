"""
Tests for the Delivery Agent.
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
from agents.delivery.agent import DeliveryAgent, DeliveryGenerationResponse, GeneratedFile

now = datetime.now(timezone.utc)

class MockLLM:
    def __init__(self, responses: list[DeliveryGenerationResponse] = None, raise_error=False):
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
        
        # Default mock response
        return DeliveryGenerationResponse(
            files=[
                GeneratedFile(path="Dockerfile", content="FROM python:3.11", language="dockerfile"),
                GeneratedFile(path="docker-compose.yml", content="version: '3.8'", language="yaml"),
                GeneratedFile(path="README.md", content="# Project", language="markdown")
            ],
            metadata={"build": "success"}
        )

@pytest.fixture
def agent():
    agent = DeliveryAgent()
    agent.llm = MockLLM()
    return agent

def create_input(qa_verdict=QAVerdict.PASS, artifacts=None) -> AgentInput:
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
        
    qa_result = QAResult(
        task_id="qa-1",
        verdict=qa_verdict,
        score=1.0,
        evaluated_at=now
    )
        
    return AgentInput(
        task_id="del-1",
        task_type=TaskType.DELIVERY,
        context={"dependency_outputs": artifacts, "task_data": {}, "qa_result": qa_result.model_dump()},
        instructions="Package it"
    )

@pytest.mark.asyncio
async def test_qa_fail_gate_blocks(agent):
    # If QA result is FAIL, delivery must fail immediately.
    out = await agent.execute(create_input(qa_verdict=QAVerdict.FAIL))
    assert out.status == AgentStatus.FAILURE
    assert "qa verdict is" in out.feedback.lower()
    assert agent.llm.call_count == 0

@pytest.mark.asyncio
async def test_missing_qa_result(agent):
    # If QA result is missing entirely, delivery must fail immediately.
    inp = create_input()
    inp.context.pop("qa_result")
    out = await agent.execute(inp)
    assert out.status == AgentStatus.FAILURE
    assert "missing qa result" in out.feedback.lower()
    assert agent.llm.call_count == 0

@pytest.mark.asyncio
async def test_missing_artifacts(agent):
    out = await agent.execute(create_input(artifacts=[]))
    assert out.status == AgentStatus.FAILURE
    assert "no source code artifacts" in out.feedback.lower()
    assert agent.llm.call_count == 0

@pytest.mark.asyncio
async def test_successful_delivery(agent):
    out = await agent.execute(create_input())
    assert out.status == AgentStatus.SUCCESS
    assert out.agent_id == AgentRole.DELIVERY
    
    assert out.result["files_packaged"] == 4  # 1 source + 3 generated
    assert len(out.artifacts) == 4
    
    # Check that Dockerfile and compose were appended
    names = [a.name for a in out.artifacts]
    assert "src/main.py" in names
    assert "Dockerfile" in names
    assert "docker-compose.yml" in names

@pytest.mark.asyncio
async def test_duplicate_path_rejection(agent):
    bad_responses = [
        DeliveryGenerationResponse(
            files=[
                # Tries to overwrite the source file
                GeneratedFile(path="src/main.py", content="evil()", language="python")
            ]
        )
    ]
    agent.llm = MockLLM(responses=bad_responses)
    out = await agent.execute(create_input())
    
    # The first LLM call fails, the mock LLM's default response succeeds on retry 2.
    assert out.status == AgentStatus.SUCCESS
    assert agent.llm.call_count == 2
    assert "collides" in agent.llm.last_prompt.lower()
