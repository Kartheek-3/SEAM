"""
Tests for the Analysis Agent covering 7 scenarios.
"""

import pytest
from datetime import datetime, timezone

from backend.schemas import (
    AgentInput, AgentStatus, AgentRole, RequirementSpec, RequirementItem, TaskType
)
from backend.llm.client import LLMClient, LLMException
from agents.analysis.agent import AnalysisAgent
from pydantic import BaseModel, ValidationError
from typing import Type

now = datetime.now(timezone.utc)

class MockLLMClient(LLMClient):
    """A mock LLM client for testing the Analysis Agent."""
    
    def __init__(self):
        self.responses = []
        self.exceptions = []
        self.call_count = 0

    async def generate_structured_output(self, system_prompt: str, user_prompt: str, response_model: Type[BaseModel]) -> BaseModel:
        self.call_count += 1
        
        if self.exceptions:
            raise self.exceptions.pop(0)
            
        if self.responses:
            return self.responses.pop(0)
            
        raise Exception("Mock exhausted")


@pytest.fixture
def agent():
    return AnalysisAgent(llm_client=MockLLMClient())

def create_input(raw_desc: str) -> AgentInput:
    return AgentInput(
        task_id="t-1",
        task_type=TaskType.ANALYSIS,
        context={"raw_description": raw_desc, "project_id": "p-1"},
        instructions="Analyze."
    )

@pytest.mark.asyncio
async def test_normal_requirement(agent):
    req_spec = RequirementSpec(
        project_id="p-1",
        functional_requirements=[RequirementItem(id="FR-1", description="Login", category="functional")],
        non_functional_requirements=[],
        ambiguities=[],
        assumptions=[],
        domain_entities=[]
    )
    agent.llm.responses = [req_spec]
    
    out = await agent.execute(create_input("Build a blog with user auth."))
    
    assert out.status == AgentStatus.SUCCESS
    assert agent.llm.call_count == 1
    assert out.result["functional_requirements"][0]["id"] == "FR-1"
    assert out.confidence >= 0.9

@pytest.mark.asyncio
async def test_ecommerce_requirement(agent):
    req_spec = RequirementSpec(
        project_id="p-1",
        functional_requirements=[],
        non_functional_requirements=[],
        ambiguities=[],
        assumptions=[],
        domain_entities=["Cart", "Product", "User", "Order"]
    )
    agent.llm.responses = [req_spec]
    
    out = await agent.execute(create_input("E-commerce store with cart."))
    
    assert out.status == AgentStatus.SUCCESS
    assert "Cart" in out.result["domain_entities"]

@pytest.mark.asyncio
async def test_healthcare_requirement(agent):
    req_spec = RequirementSpec(
        project_id="p-1",
        functional_requirements=[],
        non_functional_requirements=[RequirementItem(id="NFR-1", description="HIPAA", category="non_functional")],
        ambiguities=[],
        assumptions=[],
        domain_entities=["Patient"]
    )
    agent.llm.responses = [req_spec]
    
    out = await agent.execute(create_input("Healthcare app for patients."))
    
    assert out.status == AgentStatus.SUCCESS
    assert out.result["non_functional_requirements"][0]["description"] == "HIPAA"

@pytest.mark.asyncio
async def test_ambiguous_requirement(agent):
    req_spec = RequirementSpec(
        project_id="p-1",
        functional_requirements=[],
        non_functional_requirements=[],
        ambiguities=["What does it do?", "Who is the user?"],
        assumptions=[],
        domain_entities=[]
    )
    agent.llm.responses = [req_spec]
    
    out = await agent.execute(create_input("Build an app that does stuff."))
    
    assert out.status == AgentStatus.SUCCESS
    assert len(out.result["ambiguities"]) == 2
    assert out.confidence < 0.9  # Penalty applied

@pytest.mark.asyncio
async def test_empty_input(agent):
    out = await agent.execute(create_input(""))
    assert out.status == AgentStatus.FAILURE
    assert "empty" in out.feedback
    assert agent.llm.call_count == 0

@pytest.mark.asyncio
async def test_malformed_model_output_retry(agent):
    req_spec = RequirementSpec(
        project_id="p-1", functional_requirements=[], non_functional_requirements=[]
    )
    
    # First two calls raise validation error, third succeeds
    agent.llm.exceptions = [
        ValidationError.from_exception_data("error", line_errors=[]),
        ValidationError.from_exception_data("error", line_errors=[])
    ]
    agent.llm.responses = [req_spec]
    
    out = await agent.execute(create_input("Standard input."))
    
    assert out.status == AgentStatus.SUCCESS
    assert agent.llm.call_count == 3

@pytest.mark.asyncio
async def test_malformed_model_output_failure(agent):
    agent.llm.exceptions = [
        ValidationError.from_exception_data("error", line_errors=[]),
        ValidationError.from_exception_data("error", line_errors=[]),
        ValidationError.from_exception_data("error", line_errors=[])
    ]
    
    out = await agent.execute(create_input("Standard input."))
    
    assert out.status == AgentStatus.FAILURE
    assert agent.llm.call_count == 3
    assert "Failed to generate valid" in out.feedback

@pytest.mark.asyncio
async def test_llm_failure(agent):
    agent.llm.exceptions = [LLMException("API Timeout")]
    
    out = await agent.execute(create_input("Standard input."))
    
    assert out.status == AgentStatus.FAILURE
    assert agent.llm.call_count == 1
    assert "API Timeout" in out.feedback
