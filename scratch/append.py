import os

content = '''
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
'''

with open('tests/agents/supervisor/test_supervisor_agent.py', 'a') as f:
    f.write(content)
