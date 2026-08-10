"""
Tests for the Coding Agent.
"""

import pytest
from datetime import datetime, timezone
from typing import Any

from backend.schemas import (
    AgentInput, AgentOutput, AgentStatus, AgentRole, TaskType, ArtifactType,
    KnowledgeContext, KnowledgeChunk
)
from backend.schemas.qa import ReworkFeedback, QAResult, QAVerdict, FindingSeverity, QAFinding
from agents.coding.agent import CodingAgent, CodeGenerationResponse, GeneratedFile
from agents.coding.exceptions import PathTraversalError, CodeGenerationError

now = datetime.now(timezone.utc)

class MockLLM:
    def __init__(self, responses: list[CodeGenerationResponse] = None, raise_error=False):
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
        return CodeGenerationResponse(files=[
            GeneratedFile(path="src/main.py", content="print('hello')", language="python", artifact_type=ArtifactType.CODE)
        ])

@pytest.fixture
def agent():
    return CodingAgent(llm_client=MockLLM())

def create_input(instructions: str = "Write a python script", context=None, rework=None) -> AgentInput:
    return AgentInput(
        task_id="coding-1",
        task_type=TaskType.CODING,
        context=context or {"project_id": "p-1"},
        instructions=instructions,
        rework_feedback=rework
    )

@pytest.mark.asyncio
async def test_basic_generation(agent):
    out = await agent.execute(create_input())
    assert out.status == AgentStatus.SUCCESS
    assert out.agent_id == AgentRole.CODING
    assert len(out.artifacts) == 1
    assert out.artifacts[0].name == "src/main.py"
    assert out.artifacts[0].content == "print('hello')"
    assert out.artifacts[0].type == ArtifactType.CODE

@pytest.mark.asyncio
async def test_empty_instructions(agent):
    out = await agent.execute(create_input("   "))
    assert out.status == AgentStatus.FAILURE
    assert "Instructions cannot be empty" in out.feedback

@pytest.mark.asyncio
async def test_llm_failure(agent):
    agent.llm = MockLLM(raise_error=True)
    out = await agent.execute(create_input())
    assert out.status == AgentStatus.FAILURE
    assert "LLM failure" in out.feedback

@pytest.mark.asyncio
async def test_path_traversal_protection(agent):
    bad_responses = [
        CodeGenerationResponse(files=[
            GeneratedFile(path="../../etc/passwd", content="hacked", language="python", artifact_type=ArtifactType.CODE)
        ]),
        CodeGenerationResponse(files=[
            GeneratedFile(path="/root/secret", content="hacked", language="python", artifact_type=ArtifactType.CODE)
        ]),
        CodeGenerationResponse(files=[
            GeneratedFile(path="", content="hacked", language="python", artifact_type=ArtifactType.CODE)
        ])
    ]
    agent.llm = MockLLM(responses=bad_responses)
    out = await agent.execute(create_input())
    
    # It should retry 3 times and then fail
    assert out.status == AgentStatus.FAILURE
    assert agent.llm.call_count == 3
    assert "Path traversal is not allowed" in out.feedback or "Absolute paths are not allowed" in out.feedback or "File path cannot be empty" in out.feedback

@pytest.mark.asyncio
async def test_empty_code_protection(agent):
    bad_responses = [
        CodeGenerationResponse(files=[
            GeneratedFile(path="src/main.py", content="   ", language="python", artifact_type=ArtifactType.CODE)
        ])
    ] * 3
    agent.llm = MockLLM(responses=bad_responses)
    out = await agent.execute(create_input())
    assert out.status == AgentStatus.FAILURE
    assert "Generated file 'src/main.py' is empty" in out.feedback

@pytest.mark.asyncio
async def test_rework_integration(agent):
    rework = ReworkFeedback(
        source_task_id="coding-1",
        qa_result=QAResult(
            task_id="qa-1",
            verdict=QAVerdict.FAIL,
            score=0.4,
            findings=[QAFinding(category="code_review", description="Missing tests", severity=FindingSeverity.MAJOR)],
            evaluated_at=now
        ),
        instructions="Add tests",
        focus_areas=["tests"]
    )
    
    out = await agent.execute(create_input(rework=rework))
    assert out.status == AgentStatus.SUCCESS
    
    # Check that rework instructions were injected into the prompt
    assert "QA REWORK FEEDBACK" in agent.llm.last_prompt
    assert "Missing tests" in agent.llm.last_prompt
    assert "Add tests" in agent.llm.last_prompt
