import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, List

from pydantic import ValidationError

from agents.base import BaseAgent, RAGService
from agents.planning.exceptions import EmptyRequirementSpecError, CircularDependencyError
from agents.planning.internal_schemas import Pass1ArchitectureResult, Pass2TaskResult
from agents.planning.prompts import (
    PASS_1_SYSTEM_PROMPT,
    PASS_2_SYSTEM_PROMPT,
    PASS_1_USER_PROMPT_TEMPLATE,
    PASS_2_USER_PROMPT_TEMPLATE,
    REWORK_SECTION_TEMPLATE,
    KNOWLEDGE_SECTION_TEMPLATE
)
from backend.llm.client import LLMClient, LLMException
from backend.schemas import (
    AgentInput,
    AgentOutput,
    AgentStatus,
    AgentRole,
    Task
)
from backend.schemas.enums import TaskType, TaskStatus
from backend.schemas.planning import ProjectPlan, ComponentSpec

logger = logging.getLogger(__name__)

class PlanningAgent(BaseAgent):
    """
    Planning & Design Agent.
    Transforms a RequirementSpec into a ProjectPlan containing actionable tasks.
    Utilizes a Two-Pass Architecture to avoid timeout constraints.
    """

    def __init__(self, llm_client: LLMClient, rag_service: RAGService | None = None):
        super().__init__(agent_id="planning_agent", rag_service=rag_service)
        self.llm = llm_client

    async def execute(self, input: AgentInput) -> AgentOutput:
        start_time = time.time()
        task_id = input.task_id
        logger.info(f"Task {task_id}: PlanningAgent starting execution.")

        try:
            # 1. Input Validation
            requirement_spec_dict = input.context.get("requirement_spec")
            if not requirement_spec_dict:
                raise EmptyRequirementSpecError("RequirementSpec is missing from context.")
            
            # Construct a COMPACT planning input to avoid token bloat
            functional_reqs = requirement_spec_dict.get("functional_requirements", [])
            non_functional_reqs = requirement_spec_dict.get("non_functional_requirements", [])
            
            compact_reqs = []
            for fr in functional_reqs:
                compact_reqs.append(f"- {fr.get('id', '')}: {fr.get('description', '')} ({fr.get('priority', 'must')})")
            for nfr in non_functional_reqs:
                compact_reqs.append(f"- {nfr.get('id', '')}: {nfr.get('description', '')} ({nfr.get('priority', 'must')})")
                
            compact_req_text = "\n".join(compact_reqs)
            
            project_id = input.context.get("project_id", "unknown")

            # 2. RAG Retrieval (Pass 1 Only)
            knowledge_section = ""
            if self.rag_service:
                logger.info(f"Task {task_id}: Attempting RAG retrieval for architecture context")
                try:
                    # Querying RAG based on the raw project_id and key requirements
                    query_str = f"Architecture patterns for project {project_id}"
                    rag_context = await self.rag_service.retrieve(query=query_str)
                    if rag_context and rag_context.chunks:
                        logger.info(f"Task {task_id}: Retrieved {len(rag_context.chunks)} chunks in {rag_context.retrieval_time_ms}ms")
                        chunks_text = "\\n\\n".join([f"Source: {c.source}\\n{c.content}" for c in rag_context.chunks])
                        knowledge_section = KNOWLEDGE_SECTION_TEMPLATE.format(knowledge_text=chunks_text)
                    else:
                        logger.info(f"Task {task_id}: No relevant architecture knowledge found.")
                except Exception as e:
                    logger.error(f"Task {task_id}: RAG retrieval failed: {e}")

            # 3. Build Rework Section
            rework_section = ""
            if input.rework_feedback:
                findings_str = "\\n".join(
                    f"- [{f.severity.value.upper()}] {f.description}" 
                    for f in input.rework_feedback.qa_result.findings
                )
                rework_section = REWORK_SECTION_TEMPLATE.format(
                    rework_instructions=input.rework_feedback.instructions,
                    focus_areas=", ".join(input.rework_feedback.focus_areas) + f"\\n\\nQA Findings:\\n{findings_str}"
                )

            # 4. Pass 1: Architecture
            pass1_user_prompt = PASS_1_USER_PROMPT_TEMPLATE.format(
                compact_requirements=compact_req_text,
                knowledge_section=knowledge_section,
                instructions=input.instructions,
                rework_section=rework_section
            )
            
            pass1_result = await self._run_pass1(pass1_user_prompt)
            
            # 5. Pass 2: Task Decomposition per Component
            all_assembled_tasks: List[Task] = []
            
            for component in pass1_result.components:
                pass2_result = await self._run_pass2_for_component(
                    compact_req_text=compact_req_text,
                    architecture_summary=pass1_result.architecture_summary,
                    component=component,
                    existing_tasks=all_assembled_tasks,
                    instructions=input.instructions,
                    rework_section=rework_section,
                    project_id=project_id
                )
                
                # Map MinimalTask to official Task
                local_id_to_uuid = {
                    mt.local_id: str(uuid.uuid4()) for mt in pass2_result.tasks
                }
                
                for mt in pass2_result.tasks:
                    mapped_deps = []
                    for dep in mt.depends_on:
                        if dep in local_id_to_uuid:
                            mapped_deps.append(local_id_to_uuid[dep])
                        else:
                            # Assume it's a UUID from existing_tasks_context
                            mapped_deps.append(dep)
                            
                    new_task = Task(
                        id=local_id_to_uuid[mt.local_id],
                        project_id=project_id,
                        title=mt.title,
                        description=mt.description,
                        type=TaskType.CODING, # Default safe deterministic value
                        status=TaskStatus.PENDING,
                        dependencies=mapped_deps,
                        created_at=datetime.now(timezone.utc)
                    )
                    all_assembled_tasks.append(new_task)
                
            # 6. Final Assembly
            project_plan = ProjectPlan(
                project_id=project_id,
                architecture_summary=pass1_result.architecture_summary,
                technology_recommendations=pass1_result.technology_recommendations,
                components=pass1_result.components,
                tasks=all_assembled_tasks
            )
            logger.info(f"Task {task_id}: Generated {len(project_plan.components)} components and {len(project_plan.tasks)} tasks.")
            
            # 7. Final DFS Dependency Validation
            self._validate_task_dependencies(project_plan.tasks)

            # Calculate confidence heuristically based on the richness of tasks
            confidence = min(0.95, 0.5 + (len(project_plan.tasks) * 0.05))

            execution_time = int((time.time() - start_time) * 1000)
            logger.info(f"Task {task_id}: PlanningAgent completed in {execution_time}ms.")

            return AgentOutput(
                task_id=task_id,
                agent_id=AgentRole.PLANNING,
                status=AgentStatus.SUCCESS,
                result=project_plan.model_dump(),
                confidence=confidence,
                execution_time_ms=execution_time
            )

        except EmptyRequirementSpecError as e:
            logger.warning(f"Task {task_id}: {e}")
            return AgentOutput(
                task_id=task_id,
                agent_id=AgentRole.PLANNING,
                status=AgentStatus.FAILURE,
                result={},
                feedback=str(e),
                execution_time_ms=int((time.time() - start_time) * 1000)
            )
        except Exception as e:
            logger.error(f"Task {task_id}: PlanningAgent execution failed: {e}")
            return AgentOutput(
                task_id=task_id,
                agent_id=AgentRole.PLANNING,
                status=AgentStatus.FAILURE,
                result={},
                feedback=f"Execution failed: {str(e)}",
                execution_time_ms=int((time.time() - start_time) * 1000)
            )

    async def _run_pass1(self, user_prompt: str, max_retries: int = 3) -> Pass1ArchitectureResult:
        start_time = time.time()
        current_prompt = user_prompt
        for attempt in range(max_retries):
            try:
                result = await self.llm.generate_structured_output(
                    system_prompt=PASS_1_SYSTEM_PROMPT,
                    user_prompt=current_prompt,
                    response_model=Pass1ArchitectureResult
                )
                duration = time.time() - start_time
                logger.info(f"Pass 1 completed in {duration:.2f}s after {attempt + 1} attempts.")
                return result
            except ValidationError as e:
                logger.warning(f"Pass 1 Schema validation failed on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    raise Exception(f"Failed to generate Pass1ArchitectureResult after {max_retries} attempts. Last error: {e}")
                current_prompt += f"\\n\\n[SYSTEM: Your previous Pass 1 output failed schema validation. Error:\\n{e}\\nPlease correct the JSON format.]"
            except LLMException as e:
                logger.error(f"Pass 1 LLM failure on attempt {attempt + 1}/{max_retries}:\n{e}. Retrying.")
                if attempt == max_retries - 1:
                    raise
        raise Exception("Unexpected exit from Pass 1 retry loop.")

    async def _run_pass2_for_component(
        self,
        compact_req_text: str,
        architecture_summary: str,
        component: ComponentSpec,
        existing_tasks: List[Task],
        instructions: str,
        rework_section: str,
        project_id: str,
        max_retries: int = 3
    ) -> Pass2TaskResult:
        
        # Build compact context of existing tasks to allow valid cross-component dependencies
        existing_tasks_context = "\\n".join([f"Task ID: {t.id} - {t.title}" for t in existing_tasks])
        if not existing_tasks_context:
            existing_tasks_context = "No previous tasks exist yet."
            
        component_json = component.model_dump_json(indent=2)
        
        user_prompt = PASS_2_USER_PROMPT_TEMPLATE.format(
            compact_requirements=compact_req_text,
            architecture_summary=architecture_summary,
            existing_tasks_context=existing_tasks_context,
            component_json=component_json,
            instructions=instructions,
            rework_section=rework_section
        )
        
        start_time = time.time()
        current_prompt = user_prompt
        for attempt in range(max_retries):
            try:
                result = await self.llm.generate_structured_output(
                    system_prompt=PASS_2_SYSTEM_PROMPT,
                    user_prompt=current_prompt,
                    response_model=Pass2TaskResult
                )
                
                # project_id normalization is now handled in the mapper in execute()
                        
                duration = time.time() - start_time
                logger.info(f"Pass 2 for component '{component.name}' completed in {duration:.2f}s after {attempt + 1} attempts.")
                return result
            except ValidationError as e:
                logger.warning(f"Pass 2 Schema validation failed on attempt {attempt + 1} for component '{component.name}': {e}")
                if attempt == max_retries - 1:
                    raise Exception(f"Failed to generate Pass2TaskResult for component '{component.name}' after {max_retries} attempts. Last error: {e}")
                current_prompt += f"\\n\\n[SYSTEM: Your previous Pass 2 output failed schema validation. Error:\\n{e}\\nPlease correct the JSON format.]"
            except LLMException as e:
                logger.error(f"Pass 2 component '{component.name}' LLM failure on attempt {attempt + 1}/{max_retries}:\n{e}. Retrying.")
                if attempt == max_retries - 1:
                    raise
        raise Exception("Unexpected exit from Pass 2 retry loop.")

    def _validate_task_dependencies(self, tasks: list[Task]) -> None:
        """Validates that all dependencies exist and form a DAG without cycles."""
        task_ids = set()
        for t in tasks:
            if t.id in task_ids:
                raise CircularDependencyError(f"Duplicate task ID detected: '{t.id}'")
            task_ids.add(t.id)
        
        # Build adjacency list: dep -> task
        graph = {t_id: [] for t_id in task_ids}
        
        for t in tasks:
            for dep in t.dependencies:
                if dep not in task_ids:
                    raise CircularDependencyError(f"Task '{t.id}' references unknown dependency '{dep}'")
                graph[dep].append(t.id)

        # DFS Cycle Detection
        visited = {}
        def dfs(node: str) -> bool:
            if visited.get(node) == "visiting":
                return True # cycle
            if visited.get(node) == "visited":
                return False
                
            visited[node] = "visiting"
            for neighbor in graph.get(node, []):
                if dfs(neighbor):
                    return True
            visited[node] = "visited"
            return False

        for node in graph:
            if dfs(node):
                raise CircularDependencyError(f"Cycle detected involving task '{node}'")
