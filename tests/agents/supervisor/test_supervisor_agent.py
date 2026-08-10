"""
Tests for the Supervisor / Orchestrator Agent.
"""

import pytest
from datetime import datetime, timezone

from backend.schemas import (
    AgentInput, AgentOutput, AgentStatus, AgentRole, TaskType, Task, TaskStatus
)
from backend.schemas.planning import ProjectPlan
from backend.schemas.artifacts import Artifact, ArtifactType
from agents.supervisor.agent import SupervisorAgent
from agents.supervisor.exceptions import AgentNotFoundError, WorkflowDeadlockError
from agents.base import BaseAgent

now = datetime.now(timezone.utc)

class MockWorkerAgent(BaseAgent):
    def __init__(self, agent_id: str, status: AgentStatus = AgentStatus.SUCCESS, result: dict = None):
        super().__init__(agent_id=agent_id)
        self.default_status = status
        self.default_result = result or {}
        self.call_count = 0
        self.captured_inputs = []
        
    async def execute(self, input: AgentInput) -> AgentOutput:
        self.call_count += 1
        self.captured_inputs.append(input)
        return AgentOutput(
            task_id=input.task_id,
            agent_id=AgentRole.CODING, # Mocked
            status=self.default_status,
            result=self.default_result,
            artifacts=[Artifact(
                id=f"art-{input.task_id}",
                project_id="p-1",
                task_id=input.task_id,
                type=ArtifactType.CODE,
                name="code.py",
                content="print('hello')",
                created_at=now
            )] if self.default_status == AgentStatus.SUCCESS else [],
            execution_time_ms=10
        )

@pytest.fixture
def supervisor():
    registry = {
        TaskType.CODING: MockWorkerAgent("coding_agent"),
        TaskType.QA: MockWorkerAgent("qa_agent", result={"verdict": "pass"})
    }
    return SupervisorAgent(agent_registry=registry)

def create_input(tasks: list[Task]) -> AgentInput:
    plan = ProjectPlan(
        project_id="p-1",
        architecture_summary="Test",
        components=[],
        tasks=tasks
    )
    return AgentInput(
        task_id="sup-task",
        task_type=TaskType.PLANNING, # Doesn't matter for input
        context={"project_plan": plan.model_dump()},
        instructions="Execute"
    )

@pytest.mark.asyncio
async def test_normal_sequential_execution(supervisor):
    tasks = [
        Task(id="T-1", project_id="p-1", title="Code", description="", type=TaskType.CODING, created_at=now),
        Task(id="T-2", project_id="p-1", title="QA", description="", type=TaskType.QA, created_at=now, dependencies=["T-1"])
    ]
    
    out = await supervisor.execute(create_input(tasks))
    assert out.status == AgentStatus.SUCCESS
    
    # Both tasks should be completed
    assert "T-1" in out.result["completed_tasks"]
    assert "T-2" in out.result["completed_tasks"]
    assert len(out.result["final_artifacts"]) == 2
    
    coding_agent = supervisor.agent_registry[TaskType.CODING]
    assert coding_agent.call_count == 1

@pytest.mark.asyncio
async def test_rework_routing():
    # QA returns FAIL verdict -> T-1 should be reworked
    qa_mock = MockWorkerAgent("qa_agent", result={"verdict": "fail", "task_id": "T-1"})
    coding_mock = MockWorkerAgent("coding_agent")
    
    registry = {
        TaskType.CODING: coding_mock,
        TaskType.QA: qa_mock
    }
    supervisor = SupervisorAgent(agent_registry=registry)
    
    tasks = [
        Task(id="T-1", project_id="p-1", title="Code", description="", type=TaskType.CODING, created_at=now),
        Task(id="T-2", project_id="p-1", title="QA", description="", type=TaskType.QA, created_at=now, dependencies=["T-1"])
    ]
    
    # Since QA fails 3 times, T-1 will hit rework limit and fail
    out = await supervisor.execute(create_input(tasks))
    assert out.status == AgentStatus.FAILURE
    
    assert "T-1" in out.result["failed_tasks"]
    assert coding_mock.call_count == 4 # Initial + 3 retries
    assert qa_mock.call_count == 4 # QA runs after each code

@pytest.mark.asyncio
async def test_deadlock_detection(supervisor):
    tasks = [
        Task(id="T-1", project_id="p-1", title="Code", description="", type=TaskType.CODING, created_at=now, dependencies=["T-2"]),
        Task(id="T-2", project_id="p-1", title="QA", description="", type=TaskType.QA, created_at=now, dependencies=["T-1"])
    ]
    
    out = await supervisor.execute(create_input(tasks))
    assert out.status == AgentStatus.FAILURE
    assert "Deadlock detected" in out.feedback

@pytest.mark.asyncio
async def test_agent_not_found():
    registry = {}
    supervisor = SupervisorAgent(agent_registry=registry)
    tasks = [Task(id="T-1", project_id="p-1", title="Code", description="", type=TaskType.CODING, created_at=now)]
    
    out = await supervisor.execute(create_input(tasks))
    assert out.status == AgentStatus.FAILURE
    assert "No agent registered for TaskType: coding" in out.feedback
