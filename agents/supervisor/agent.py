import logging
import time
from typing import Literal, Dict

from langgraph.graph import StateGraph, END

from agents.base import BaseAgent, RAGService
from backend.schemas.workflow import WorkflowState
from backend.schemas import TaskType, AgentInput, AgentOutput, AgentStatus, AgentRole, Task
from backend.schemas.planning import ProjectPlan
from agents.supervisor.exceptions import AgentNotFoundError, WorkflowDeadlockError

logger = logging.getLogger(__name__)

class SupervisorAgent(BaseAgent):
    """
    Supervisor / Orchestrator Agent.
    Executes the ProjectPlan using a LangGraph state machine.
    """

    def __init__(self, agent_registry: Dict[TaskType, BaseAgent], rag_service: RAGService | None = None):
        super().__init__(agent_id="supervisor_agent", rag_service=rag_service)
        self.agent_registry = agent_registry
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(WorkflowState)
        
        workflow.add_node("task_dispatch", self._node_task_dispatch)
        workflow.add_node("agent_execution", self._node_agent_execution)
        workflow.add_node("eval_output", self._node_eval_output)
        
        workflow.set_entry_point("task_dispatch")
        
        workflow.add_conditional_edges(
            "task_dispatch",
            self._route_from_dispatch,
            {
                "agent_execution": "agent_execution",
                "end": END
            }
        )
        
        workflow.add_edge("agent_execution", "eval_output")
        workflow.add_edge("eval_output", "task_dispatch")
        
        return workflow.compile()

    def _initialize_state(self, plan: ProjectPlan) -> WorkflowState:
        tasks_dict = {t.id: t for t in plan.tasks}
        
        # Phase 9D.15: Synthesize workflow-level QA and Delivery tasks —
        # but ONLY for CODING tasks that don't already have an explicit QA task
        # pointing to them, and only if no explicit DELIVERY task already exists.
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        
        coding_task_ids = [t.id for t in plan.tasks if t.type == TaskType.CODING]
        
        # Build set of CODING task IDs that already have an explicit QA dependent
        already_covered_by_qa = set()
        for t in plan.tasks:
            if t.type == TaskType.QA:
                for dep in t.dependencies:
                    if dep in tasks_dict and tasks_dict[dep].type == TaskType.CODING:
                        already_covered_by_qa.add(dep)
        
        # Check whether the plan already has an explicit DELIVERY task
        has_explicit_delivery = any(t.type == TaskType.DELIVERY for t in plan.tasks)
        
        qa_task_ids = []
        for c_id in coding_task_ids:
            if c_id in already_covered_by_qa:
                # An explicit QA task already covers this coding task — don't double-synthesize
                continue
            c_task = tasks_dict[c_id]
            qa_id = f"qa-{c_id}"
            qa_task = Task(
                id=qa_id,
                project_id=plan.project_id,
                title=f"QA for {c_task.title}",
                description=f"Evaluate code artifacts against requirements for task {c_id}.",
                type=TaskType.QA,
                dependencies=[c_id],
                priority=1,
                created_at=now
            )
            tasks_dict[qa_id] = qa_task
            qa_task_ids.append(qa_id)
            
        # Only synthesize delivery-global when:
        # - There are newly synthesized QA tasks (meaning there are uncovered coding tasks), AND
        # - The plan doesn't already have an explicit DELIVERY task
        if qa_task_ids and not has_explicit_delivery:
            delivery_task = Task(
                id="delivery-global",
                project_id=plan.project_id,
                title="Final Delivery",
                description="Generate deployment documentation and Dockerfile.",
                type=TaskType.DELIVERY,
                dependencies=qa_task_ids,
                priority=0,
                created_at=now
            )
            tasks_dict[delivery_task.id] = delivery_task

        return {
            "project_id": plan.project_id,
            "current_phase": "TASK_DISPATCH",
            "tasks": tasks_dict,
            "pending_tasks": list(tasks_dict.keys()),
            "running_tasks": [],
            "completed_tasks": [],
            "failed_tasks": [],
            "agent_outputs": {},
            "rework_counts": {},
            "quality_scores": {},
            "current_task_id": None,
            "messages": [],
            "final_artifacts": [],
            "qa_execution_history": []
        }

    async def execute(self, input: AgentInput) -> AgentOutput:
        start_time = time.time()
        logger.info(f"Task {input.task_id}: SupervisorAgent starting execution.")

        plan_dict = input.context.get("project_plan")
        if not plan_dict:
            return AgentOutput(
                task_id=input.task_id,
                agent_id=AgentRole.SUPERVISOR,
                status=AgentStatus.FAILURE,
                result={},
                feedback="Missing project_plan in context",
                execution_time_ms=0
            )

        try:
            plan = ProjectPlan(**plan_dict)
            initial_state = self._initialize_state(plan)
            
            final_state = await self.graph.ainvoke(initial_state)
            
            status = AgentStatus.FAILURE if final_state["failed_tasks"] else AgentStatus.SUCCESS
            
            # Serialize WorkflowState for output (removing Pydantic objects if necessary)
            # In our case, the Pydantic Task objects can be serialized automatically by AgentOutput
            
            execution_time = int((time.time() - start_time) * 1000)
            logger.info(f"Task {input.task_id}: SupervisorAgent completed in {execution_time}ms.")

            return AgentOutput(
                task_id=input.task_id,
                agent_id=AgentRole.SUPERVISOR,
                status=status,
                result=final_state, # Note: Pydantic will serialize this TypedDict
                artifacts=final_state["final_artifacts"],
                execution_time_ms=execution_time
            )

        except WorkflowDeadlockError as e:
            logger.error(f"Workflow Deadlock: {e}")
            return AgentOutput(
                task_id=input.task_id,
                agent_id=AgentRole.SUPERVISOR,
                status=AgentStatus.FAILURE,
                result={},
                feedback=str(e),
                execution_time_ms=int((time.time() - start_time) * 1000)
            )
        except Exception as e:
            logger.error(f"Supervisor execution failed: {e}")
            return AgentOutput(
                task_id=input.task_id,
                agent_id=AgentRole.SUPERVISOR,
                status=AgentStatus.FAILURE,
                result={},
                feedback=f"Execution failed: {str(e)}",
                execution_time_ms=int((time.time() - start_time) * 1000)
            )

    async def _node_task_dispatch(self, state: WorkflowState) -> WorkflowState:
        ready_tasks = []
        for t_id in state["pending_tasks"]:
            task = state["tasks"][t_id]
            
            deps_met = True
            for dep in task.dependencies:
                if dep not in state["completed_tasks"]:
                    deps_met = False
                    break
            
            if any(dep in state["failed_tasks"] for dep in task.dependencies):
                continue
                
            if state["rework_counts"].get(t_id, 0) > 3:
                # Max retries exceeded
                continue
                
            if deps_met:
                ready_tasks.append(t_id)

        if not ready_tasks:
            # Filter out tasks that legitimately exceeded retries or are permanently blocked
            runnable_pending = []
            for t in state["pending_tasks"]:
                task = state["tasks"][t]
                if state["rework_counts"].get(t, 0) <= 3 and not any(dep in state["failed_tasks"] for dep in task.dependencies):
                    runnable_pending.append(t)
            
            if runnable_pending and not state["running_tasks"]:
                raise WorkflowDeadlockError(f"Deadlock detected. Pending tasks: {runnable_pending}")
            
            # Workflow complete (or waiting on running tasks, though basic LangGraph runs sequentially here)
            state["current_task_id"] = None
            return state

        # Priority selection
        rework_tasks = [t for t in ready_tasks if state["rework_counts"].get(t, 0) > 0]
        if rework_tasks:
            selected_id = sorted(rework_tasks)[0]
        else:
            ready_objects = [state["tasks"][t] for t in ready_tasks]
            ready_objects.sort(key=lambda x: (-x.priority, x.id))
            selected_id = ready_objects[0].id

        state["current_task_id"] = selected_id
        state["pending_tasks"].remove(selected_id)
        state["running_tasks"].append(selected_id)
        
        return state

    def _route_from_dispatch(self, state: WorkflowState) -> Literal["agent_execution", "end"]:
        if state["current_task_id"] is None:
            return "end"
        return "agent_execution"

    async def _node_agent_execution(self, state: WorkflowState) -> WorkflowState:
        task_id = state["current_task_id"]
        task = state["tasks"][task_id]
        
        agent = self.agent_registry.get(task.type)
        if not agent:
            raise AgentNotFoundError(f"No agent registered for TaskType: {task.type.value}")
            
        dep_outputs = []
        qa_result = None
        qa_results = []
        
        for dep in task.dependencies:
            if dep in state["agent_outputs"]:
                out = state["agent_outputs"][dep]
                dep_outputs.extend([a.model_dump(mode='json') for a in out.artifacts])
                
                if state["tasks"][dep].type == TaskType.QA:
                    qa_result = out.result
                    # Ensure we pass the task ID with the result so Delivery can map it
                    if isinstance(out.result, dict):
                        out.result["task_id"] = dep
                    else:
                        out.result.task_id = dep
                    qa_results.append(out.result)
                    
                    # Phase 9D.16: Traverse backwards to grab the corresponding Coding artifacts for Delivery
                    for qa_dep in state["tasks"][dep].dependencies:
                        if qa_dep in state["agent_outputs"] and state["tasks"][qa_dep].type == TaskType.CODING:
                            coding_out = state["agent_outputs"][qa_dep]
                            dep_outputs.extend([a.model_dump(mode='json') for a in coding_out.artifacts])
                            
                elif state["tasks"][dep].type == TaskType.ANALYSIS:
                    qa_result = out.result # Just in case it's requirement spec, wait no, requirement spec is passed differently.
                
        context = {
            "task_data": task.input_data,
            "dependency_outputs": dep_outputs
        }
        if qa_result:
            context["qa_result"] = qa_result
        if qa_results:
            context["qa_results"] = qa_results
        
        agent_input = AgentInput(
            task_id=task_id,
            task_type=task.type,
            context=context,
            instructions=task.description or "Execute task",
            dependencies=task.dependencies
        )
        
        output = await agent.execute(agent_input)
        
        state["agent_outputs"][task_id] = output
        return state

    async def _node_eval_output(self, state: WorkflowState) -> WorkflowState:
        task_id = state["current_task_id"]
        output = state["agent_outputs"][task_id]
        task = state["tasks"][task_id]
        
        state["running_tasks"].remove(task_id)
        
        # Append QA executions to history for telemetry and audit
        if task.type == TaskType.QA:
            history_record = {
                "task_id": task_id,
                "attempt": state["rework_counts"].get(task_id, 0) + 1,
                "rework_cycle": state["rework_counts"].get(task_id, 0),
                "verdict": output.result.get("verdict", "fail") if isinstance(output.result, dict) else getattr(output.result, "verdict", "fail"),
                "timestamp": int(time.time()),
                "execution_time_ms": output.execution_time_ms,
                "failure_state": output.feedback if output.status != AgentStatus.SUCCESS else None
            }
            state["qa_execution_history"].append(history_record)
        
        if output.status == AgentStatus.SUCCESS:
            state["completed_tasks"].append(task_id)
            state["final_artifacts"].extend(output.artifacts)
            
            # QA-Driven Rework Logic
            if task.type == TaskType.QA:
                qa_result = output.result
                if qa_result.get("verdict") == "fail":
                    source_ids = [dep for dep in task.dependencies if state["tasks"][dep].type == TaskType.CODING]
                    source_id = source_ids[0] if source_ids else (task.dependencies[0] if task.dependencies else None)
                    
                    if source_id and source_id in state["completed_tasks"]:
                        rework_count = state["rework_counts"].get(source_id, 0)
                        if rework_count < 3:
                            logger.info(f"QA failed for {source_id}. Initiating rework (attempt {rework_count + 1}).")
                            state["completed_tasks"].remove(source_id)
                            state["pending_tasks"].append(source_id)
                            state["rework_counts"][source_id] = rework_count + 1
                            
                            # Re-queue dependent tasks
                            for t in state["tasks"].values():
                                if source_id in t.dependencies:
                                    if t.id in state["completed_tasks"]:
                                        state["completed_tasks"].remove(t.id)
                                    if t.id in state["failed_tasks"]:
                                        state["failed_tasks"].remove(t.id)
                                    if t.id not in state["pending_tasks"]:
                                        state["pending_tasks"].append(t.id)
                        else:
                            logger.warning(f"QA failed for {source_id}. Max rework attempts exceeded.")
                            if source_id in state["completed_tasks"]:
                                state["completed_tasks"].remove(source_id)
                            if source_id not in state["failed_tasks"]:
                                state["failed_tasks"].append(source_id)
                            
                            # Phase 9D.16: Ensure QA task is also marked as failed to block dependents (like Delivery)
                            if task_id in state["completed_tasks"]:
                                state["completed_tasks"].remove(task_id)
                            if task_id not in state["failed_tasks"]:
                                state["failed_tasks"].append(task_id)
        else:
            # Agent explicitly failed (e.g. timeout)
            current_rework = state["rework_counts"].get(task_id, 0)
            if current_rework < 3:
                state["pending_tasks"].append(task_id)
                state["rework_counts"][task_id] = current_rework + 1
            else:
                state["failed_tasks"].append(task_id)
                
        state["current_task_id"] = None
        return state
