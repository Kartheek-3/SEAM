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
    def __init__(self, agent_id: str, status: AgentStatus = AgentStatus.SUCCESS, result: dict = None, project_id: str = "p-1"):
        super().__init__(agent_id=agent_id)
        self.default_status = status
        self.default_result = result or {}
        self.project_id = project_id
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
                project_id=self.project_id,
                task_id=input.task_id,
                type=ArtifactType.CODE,
                name="code.py",
                content="print('hello')",
                created_at=now
            )] if (self.default_status == AgentStatus.SUCCESS and self.agent_id in ["coding_agent", "delivery_agent"]) else [],
            execution_time_ms=10
        )

@pytest.fixture
def supervisor():
    registry = {
        TaskType.CODING: MockWorkerAgent("coding_agent"),
        TaskType.QA: MockWorkerAgent("qa_agent", result={"verdict": "pass"}),
        TaskType.DELIVERY: MockWorkerAgent("delivery_agent")
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
    # Only T-1 (coding) produces artifacts; QA and Delivery mocks return no artifacts
    assert len(out.result["final_artifacts"]) == 1
    
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

class AdaptiveMockQA(BaseAgent):
    def __init__(self, agent_id: str, fails_before_pass: int = 1):
        super().__init__(agent_id=agent_id)
        self.fails_before_pass = fails_before_pass
        self.call_count = 0
        
    async def execute(self, input: AgentInput) -> AgentOutput:
        self.call_count += 1
        verdict = "fail" if self.call_count <= self.fails_before_pass else "pass"
        return AgentOutput(
            task_id=input.task_id,
            agent_id=AgentRole.QA,
            status=AgentStatus.SUCCESS,
            result={"verdict": verdict},
            artifacts=[],
            execution_time_ms=10
        )

@pytest.mark.asyncio
async def test_qa_pass_after_rework_routes_to_delivery():
    coding_mock = MockWorkerAgent("coding_agent")
    qa_mock = AdaptiveMockQA("qa_agent", fails_before_pass=2)
    delivery_mock = MockWorkerAgent("delivery_agent")
    
    registry = {
        TaskType.CODING: coding_mock,
        TaskType.QA: qa_mock,
        TaskType.DELIVERY: delivery_mock
    }
    supervisor = SupervisorAgent(agent_registry=registry)
    
    # One coding task
    tasks = [
        Task(id="T-1", project_id="p-1", title="Code", description="", type=TaskType.CODING, created_at=now)
    ]
    
    out = await supervisor.execute(create_input(tasks))
    assert out.status == AgentStatus.SUCCESS
    
    # Coding called 3 times (initial + 2 reworks)
    assert coding_mock.call_count == 3
    # QA called 3 times (fails 2 times, passes 3rd time)
    assert qa_mock.call_count == 3
    # Delivery called 1 time
    assert delivery_mock.call_count == 1
    
    # Delivery only runs after QA passes, so it runs exactly once
    assert "delivery-global" in out.result["completed_tasks"]

@pytest.mark.asyncio
async def test_multiple_coding_tasks_isolated_qa():
    coding_mock = MockWorkerAgent("coding_agent")
    qa_mock = MockWorkerAgent("qa_agent", result={"verdict": "pass"})
    delivery_mock = MockWorkerAgent("delivery_agent")
    
    registry = {
        TaskType.CODING: coding_mock,
        TaskType.QA: qa_mock,
        TaskType.DELIVERY: delivery_mock
    }
    supervisor = SupervisorAgent(agent_registry=registry)
    
    tasks = [
        Task(id="T-1", project_id="p-1", title="Code 1", description="", type=TaskType.CODING, created_at=now),
        Task(id="T-2", project_id="p-1", title="Code 2", description="", type=TaskType.CODING, created_at=now)
    ]
    
    out = await supervisor.execute(create_input(tasks))
    assert out.status == AgentStatus.SUCCESS
    
    assert coding_mock.call_count == 2
    assert qa_mock.call_count == 2
    assert delivery_mock.call_count == 1
    
    assert "qa-T-1" in out.result["completed_tasks"]
    assert "qa-T-2" in out.result["completed_tasks"]
    assert "delivery-global" in out.result["completed_tasks"]

class AdaptiveMockQA(BaseAgent):
    def __init__(self, agent_id: str, fails_before_pass: int = 1):
        super().__init__(agent_id=agent_id)
        self.fails_before_pass = fails_before_pass
        self.call_count = 0
        
    async def execute(self, input: AgentInput) -> AgentOutput:
        self.call_count += 1
        verdict = "fail" if self.call_count <= self.fails_before_pass else "pass"
        return AgentOutput(
            task_id=input.task_id,
            agent_id=AgentRole.QA,
            status=AgentStatus.SUCCESS,
            result={"verdict": verdict},
            artifacts=[],
            execution_time_ms=10
        )

@pytest.mark.asyncio
async def test_qa_pass_after_rework_routes_to_delivery():
    coding_mock = MockWorkerAgent("coding_agent")
    qa_mock = AdaptiveMockQA("qa_agent", fails_before_pass=2)
    delivery_mock = MockWorkerAgent("delivery_agent")
    
    registry = {
        TaskType.CODING: coding_mock,
        TaskType.QA: qa_mock,
        TaskType.DELIVERY: delivery_mock
    }
    supervisor = SupervisorAgent(agent_registry=registry)
    
    tasks = [Task(id="T-1", project_id="p-1", title="Code", description="", type=TaskType.CODING, created_at=now)]
    
    out = await supervisor.execute(create_input(tasks))
    assert out.status == AgentStatus.SUCCESS
    assert coding_mock.call_count == 3
    assert qa_mock.call_count == 3
    assert delivery_mock.call_count == 1
    assert "delivery-global" in out.result["completed_tasks"]

@pytest.mark.asyncio
async def test_multiple_coding_tasks_isolated_qa():
    coding_mock = MockWorkerAgent("coding_agent")
    qa_mock = MockWorkerAgent("qa_agent", result={"verdict": "pass"})
    delivery_mock = MockWorkerAgent("delivery_agent")
    registry = {TaskType.CODING: coding_mock, TaskType.QA: qa_mock, TaskType.DELIVERY: delivery_mock}
    supervisor = SupervisorAgent(agent_registry=registry)
    
    tasks = [
        Task(id="T-1", project_id="p-1", title="Code 1", description="", type=TaskType.CODING, created_at=now),
        Task(id="T-2", project_id="p-1", title="Code 2", description="", type=TaskType.CODING, created_at=now)
    ]
    out = await supervisor.execute(create_input(tasks))
    assert out.status == AgentStatus.SUCCESS
    assert coding_mock.call_count == 2
    assert qa_mock.call_count == 2
    assert delivery_mock.call_count == 1
    assert "qa-T-1" in out.result["completed_tasks"]
    assert "qa-T-2" in out.result["completed_tasks"]
    assert "delivery-global" in out.result["completed_tasks"]

@pytest.mark.asyncio
async def test_delivery_receives_source_artifacts():
    coding_mock = MockWorkerAgent("coding_agent")
    qa_mock = MockWorkerAgent("qa_agent", result={"verdict": "pass"})
    
    class InspectingDeliveryMock(MockWorkerAgent):
        async def execute(self, input: AgentInput) -> AgentOutput:
            self.captured_inputs.append(input)
            dep_outputs = input.context.get("dependency_outputs", [])
            assert len(dep_outputs) > 0, "Delivery did not receive source artifacts"
            assert dep_outputs[0]["name"] == "code.py"
            return await super().execute(input)
            
    delivery_mock = InspectingDeliveryMock("delivery_agent")
    registry = {TaskType.CODING: coding_mock, TaskType.QA: qa_mock, TaskType.DELIVERY: delivery_mock}
    supervisor = SupervisorAgent(agent_registry=registry)
    tasks = [Task(id="T-1", project_id="p-1", title="Code", description="", type=TaskType.CODING, created_at=now)]
    
    out = await supervisor.execute(create_input(tasks))
    assert out.status == AgentStatus.SUCCESS
    assert delivery_mock.call_count == 1

@pytest.mark.asyncio
async def test_delivery_receives_qa_results():
    coding_mock = MockWorkerAgent("coding_agent")
    qa_mock = MockWorkerAgent("qa_agent", result={"verdict": "pass", "details": "all good"})
    
    class InspectingDeliveryMock(MockWorkerAgent):
        async def execute(self, input: AgentInput) -> AgentOutput:
            self.captured_inputs.append(input)
            qa_res = input.context.get("qa_result")
            assert qa_res is not None, "Delivery did not receive QA results"
            assert qa_res["verdict"] == "pass"
            assert qa_res["details"] == "all good"
            return await super().execute(input)
            
    delivery_mock = InspectingDeliveryMock("delivery_agent")
    registry = {TaskType.CODING: coding_mock, TaskType.QA: qa_mock, TaskType.DELIVERY: delivery_mock}
    supervisor = SupervisorAgent(agent_registry=registry)
    tasks = [Task(id="T-1", project_id="p-1", title="Code", description="", type=TaskType.CODING, created_at=now)]
    
    out = await supervisor.execute(create_input(tasks))
    assert out.status == AgentStatus.SUCCESS
    assert delivery_mock.call_count == 1

@pytest.mark.asyncio
async def test_delivery_receives_reworked_artifacts():
    class MutableCodingMock(MockWorkerAgent):
        async def execute(self, input: AgentInput) -> AgentOutput:
            self.call_count += 1
            content = f"content_v{self.call_count}"
            return AgentOutput(
                task_id=input.task_id,
                agent_id=AgentRole.CODING,
                status=AgentStatus.SUCCESS,
                result={},
                artifacts=[Artifact(
                    id=f"art-{input.task_id}",
                    project_id="p-1",
                    task_id=input.task_id,
                    type=ArtifactType.CODE,
                    name="code.py",
                    content=content,
                    created_at=now
                )],
                execution_time_ms=10
            )
            
    coding_mock = MutableCodingMock("coding_agent")
    qa_mock = AdaptiveMockQA("qa_agent", fails_before_pass=1)
    
    class InspectingDeliveryMock(MockWorkerAgent):
        async def execute(self, input: AgentInput) -> AgentOutput:
            dep_outputs = input.context.get("dependency_outputs", [])
            assert len(dep_outputs) == 1
            assert dep_outputs[0]["content"] == "content_v2"
            return await super().execute(input)
            
    delivery_mock = InspectingDeliveryMock("delivery_agent")
    registry = {TaskType.CODING: coding_mock, TaskType.QA: qa_mock, TaskType.DELIVERY: delivery_mock}
    supervisor = SupervisorAgent(agent_registry=registry)
    tasks = [Task(id="T-1", project_id="p-1", title="Code", description="", type=TaskType.CODING, created_at=now)]
    
    out = await supervisor.execute(create_input(tasks))
    assert out.status == AgentStatus.SUCCESS
    assert coding_mock.call_count == 2
    assert qa_mock.call_count == 2
    assert delivery_mock.call_count == 1

@pytest.mark.asyncio
async def test_delivery_waits_for_all_qa_tasks():
    coding_mock = MockWorkerAgent("coding_agent")
    qa_mock = MockWorkerAgent("qa_agent", result={"verdict": "pass"})
    delivery_mock = MockWorkerAgent("delivery_agent")
    registry = {TaskType.CODING: coding_mock, TaskType.QA: qa_mock, TaskType.DELIVERY: delivery_mock}
    supervisor = SupervisorAgent(agent_registry=registry)
    
    tasks = [
        Task(id="T-1", project_id="p-1", title="Code 1", description="", type=TaskType.CODING, created_at=now),
        Task(id="T-2", project_id="p-1", title="Code 2", description="", type=TaskType.CODING, created_at=now)
    ]
    out = await supervisor.execute(create_input(tasks))
    assert out.status == AgentStatus.SUCCESS
    assert delivery_mock.call_count == 1

@pytest.mark.asyncio
async def test_delivery_not_called_when_any_qa_fails():
    coding_mock = MockWorkerAgent("coding_agent")
    class FailingQA(MockWorkerAgent):
        async def execute(self, input: AgentInput) -> AgentOutput:
            self.call_count += 1
            verdict = "fail" if input.task_id == "qa-T-2" else "pass"
            return AgentOutput(
                task_id=input.task_id,
                agent_id=AgentRole.QA,
                status=AgentStatus.SUCCESS,
                result={"verdict": verdict},
                artifacts=[],
                execution_time_ms=10
            )
            
    qa_mock = FailingQA("qa_agent")
    delivery_mock = MockWorkerAgent("delivery_agent")
    registry = {TaskType.CODING: coding_mock, TaskType.QA: qa_mock, TaskType.DELIVERY: delivery_mock}
    supervisor = SupervisorAgent(agent_registry=registry)
    
    tasks = [
        Task(id="T-1", project_id="p-1", title="Code 1", description="", type=TaskType.CODING, created_at=now),
        Task(id="T-2", project_id="p-1", title="Code 2", description="", type=TaskType.CODING, created_at=now)
    ]
    out = await supervisor.execute(create_input(tasks))
    assert out.status == AgentStatus.FAILURE
    assert delivery_mock.call_count == 0

@pytest.mark.asyncio
async def test_delivery_executes_exactly_once():
    coding_mock = MockWorkerAgent("coding_agent")
    qa_mock = AdaptiveMockQA("qa_agent", fails_before_pass=2)
    delivery_mock = MockWorkerAgent("delivery_agent")
    registry = {TaskType.CODING: coding_mock, TaskType.QA: qa_mock, TaskType.DELIVERY: delivery_mock}
    supervisor = SupervisorAgent(agent_registry=registry)
    tasks = [Task(id="T-1", project_id="p-1", title="Code", description="", type=TaskType.CODING, created_at=now)]
    
    out = await supervisor.execute(create_input(tasks))
    assert out.status == AgentStatus.SUCCESS
    assert delivery_mock.call_count == 1

@pytest.mark.asyncio
async def test_delivery_context_preserves_project_id():
    coding_mock = MockWorkerAgent("coding_agent", project_id="p-999")
    qa_mock = MockWorkerAgent("qa_agent", result={"verdict": "pass"})
    
    class InspectingDeliveryMock(MockWorkerAgent):
        async def execute(self, input: AgentInput) -> AgentOutput:
            dep_outputs = input.context.get("dependency_outputs", [])
            assert dep_outputs[0]["project_id"] == "p-999"
            return await super().execute(input)
            
    delivery_mock = InspectingDeliveryMock("delivery_agent")
    registry = {TaskType.CODING: coding_mock, TaskType.QA: qa_mock, TaskType.DELIVERY: delivery_mock}
    supervisor = SupervisorAgent(agent_registry=registry)
    tasks = [Task(id="T-1", project_id="p-999", title="Code", description="", type=TaskType.CODING, created_at=now)]
    
    out = await supervisor.execute(create_input(tasks))
    assert out.status == AgentStatus.SUCCESS

@pytest.mark.asyncio
async def test_delivery_context_datetime_serialization():
    coding_mock = MockWorkerAgent("coding_agent")
    qa_mock = MockWorkerAgent("qa_agent", result={"verdict": "pass"})
    class InspectingDeliveryMock(MockWorkerAgent):
        async def execute(self, input: AgentInput) -> AgentOutput:
            dep_outputs = input.context.get("dependency_outputs", [])
            assert isinstance(dep_outputs[0]["created_at"], str)
            return await super().execute(input)
            
    delivery_mock = InspectingDeliveryMock("delivery_agent")
    registry = {TaskType.CODING: coding_mock, TaskType.QA: qa_mock, TaskType.DELIVERY: delivery_mock}
    supervisor = SupervisorAgent(agent_registry=registry)
    tasks = [Task(id="T-1", project_id="p-1", title="Code", description="", type=TaskType.CODING, created_at=now)]
    out = await supervisor.execute(create_input(tasks))
    assert out.status == AgentStatus.SUCCESS

@pytest.mark.asyncio
async def test_delivery_multiple_coding_artifacts_are_isolated():
    coding_mock = MockWorkerAgent("coding_agent")
    qa_mock = MockWorkerAgent("qa_agent", result={"verdict": "pass"})
    class InspectingDeliveryMock(MockWorkerAgent):
        async def execute(self, input: AgentInput) -> AgentOutput:
            dep_outputs = input.context.get("dependency_outputs", [])
            assert len(dep_outputs) == 2
            task_ids = set(a["task_id"] for a in dep_outputs)
            assert "T-1" in task_ids
            assert "T-2" in task_ids
            return await super().execute(input)
            
    delivery_mock = InspectingDeliveryMock("delivery_agent")
    registry = {TaskType.CODING: coding_mock, TaskType.QA: qa_mock, TaskType.DELIVERY: delivery_mock}
    supervisor = SupervisorAgent(agent_registry=registry)
    tasks = [
        Task(id="T-1", project_id="p-1", title="Code 1", description="", type=TaskType.CODING, created_at=now),
        Task(id="T-2", project_id="p-1", title="Code 2", description="", type=TaskType.CODING, created_at=now)
    ]
    out = await supervisor.execute(create_input(tasks))
    assert out.status == AgentStatus.SUCCESS
