import json
import logging
import time
from typing import Any

from pydantic import ValidationError

from agents.base import BaseAgent, RAGService
from agents.planning.exceptions import EmptyRequirementSpecError, CircularDependencyError
from agents.planning.prompts import (
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
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
from backend.schemas.planning import ProjectPlan

logger = logging.getLogger(__name__)

class PlanningAgent(BaseAgent):
    """
    Planning & Design Agent.
    Transforms a RequirementSpec into a ProjectPlan containing actionable tasks.
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
            
            req_spec_json = json.dumps(requirement_spec_dict, indent=2)

            # 2. RAG Retrieval
            knowledge_section = ""
            if self.rag_service:
                logger.info(f"Task {task_id}: Attempting RAG retrieval for architecture context")
                try:
                    # Querying RAG based on the raw project_id and key requirements
                    query_str = f"Architecture patterns for project {input.context.get('project_id', '')}"
                    rag_context = await self.rag_service.retrieve(query=query_str)
                    if rag_context and rag_context.chunks:
                        logger.info(f"Task {task_id}: Retrieved {len(rag_context.chunks)} chunks in {rag_context.retrieval_time_ms}ms")
                        chunks_text = "\\n\\n".join([f"Source: {c.source}\\n{c.content}" for c in rag_context.chunks])
                        knowledge_section = KNOWLEDGE_SECTION_TEMPLATE.format(knowledge_text=chunks_text)
                    else:
                        logger.info(f"Task {task_id}: No relevant architecture knowledge found.")
                except Exception as e:
                    logger.error(f"Task {task_id}: RAG retrieval failed: {e}")

            # 3. Build Prompts
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

            user_prompt = USER_PROMPT_TEMPLATE.format(
                requirement_spec=req_spec_json,
                knowledge_section=knowledge_section,
                instructions=input.instructions,
                rework_section=rework_section
            )

            # 4. LLM Invocation & Graph Validation Loop
            project_plan = await self._generate_with_retries(user_prompt, input.context.get("project_id", "unknown"))

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

    async def _generate_with_retries(self, user_prompt: str, project_id: str, max_retries: int = 3) -> ProjectPlan:
        """Invokes the LLM and handles schema/graph validation retries."""
        current_prompt = user_prompt

        for attempt in range(max_retries):
            try:
                plan = await self.llm.generate_structured_output(
                    system_prompt=SYSTEM_PROMPT,
                    user_prompt=current_prompt,
                    response_model=ProjectPlan
                )
                
                # Fix up project IDs in generated tasks
                for task in plan.tasks:
                    if not task.project_id:
                        task.project_id = project_id
                
                # Graph Validation (Cycle Detection)
                self._validate_task_dependencies(plan.tasks)

                return plan

            except ValidationError as e:
                logger.warning(f"Schema validation failed on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    raise Exception(f"Failed to generate valid ProjectPlan after {max_retries} attempts. Last error: {e}")
                
                # Append error to prompt for next attempt
                current_prompt += f"\\n\\n[SYSTEM: Your previous output failed schema validation. Error:\\n{e}\\nPlease correct the JSON format.]"
            except CircularDependencyError as e:
                logger.warning(f"Circular dependency detected on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    raise Exception(f"Failed to generate acyclic task graph after {max_retries} attempts. Last error: {e}")
                
                current_prompt += f"\\n\\n[SYSTEM: Your previous output contained a circular task dependency or invalid reference. Error:\\n{e}\\nPlease correct the 'dependencies' fields.]"
            except LLMException as e:
                logger.error(f"LLM API failed on attempt {attempt + 1}: {e}")
                raise

        raise Exception("Unexpected exit from retry loop.")

    def _validate_task_dependencies(self, tasks: list[Task]) -> None:
        """Validates that all dependencies exist and form a DAG without cycles."""
        task_ids = {t.id for t in tasks}
        
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
