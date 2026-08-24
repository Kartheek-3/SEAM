# Phase 9C: Two-Pass Planning Design

## 1. Problem
The `PlanningAgent` currently generates a complete `ProjectPlan`—including high-level components and deeply nested lists of `Task` objects—in a single LLM request. On local consumer hardware running `llama3.1` (16GB RAM), this massive structured generation consistently exceeds the hardcoded 120-second timeout, causing the official execution pipeline to fail.

## 2. Evidence
- Baseline ProjectPlan generation: ~120.77 seconds → timeout
- Optimized ProjectPlan generation (omitting defaults): ~121.00 seconds → timeout
- Analysis (simple generation): ~51-114 seconds (Success)
- Pydantic schema constraint checking during local generation scales poorly with deep nesting and wide arrays. Prompt optimization alone yielded 0% improvement.

## 3. Current Architecture
The current architecture uses a single prompt injected with the `RequirementSpec` and RAG context. The LangChain `OllamaClient.generate_structured_output()` method enforces the generation of the entire `ProjectPlan` in one inference pass.
`RequirementSpec → PlanningAgent.execute() → AgentOutput(ProjectPlan)`

## 4. Proposed Two-Pass Architecture
We propose decoupling architectural design from task decomposition.
- **Pass 1 (Architecture):** Identify high-level components and architecture.
- **Pass 2 (Decomposition):** Generate tasks for the identified components.
Both passes remain strictly internal to the `PlanningAgent`. The external `PlanningAgent.execute()` contract and `AgentOutput(ProjectPlan)` return type remain unchanged.

## 5. Pass 1 Design
Pass 1 transforms the `RequirementSpec` into an internal model representing the high-level architecture.
- **Goal:** Determine components, boundaries, and responsibilities.
- **Output:** `Pass1ArchitectureResult` (Internal Model).
- **Complexity:** Very low (comparable to Analysis phase, ~50s).

## 6. Pass 2 Design
Pass 2 receives the `RequirementSpec` and the `Pass1ArchitectureResult`.
- **Goal:** Generate a fully decomposed list of tasks.
- **Execution:** To definitively solve the latency constraint, Pass 2 will execute **Sequentially per Component** (Option B).
- **Output:** `Pass2TaskResult` (Internal Model) per component.
- **Complexity:** Low per request. Each request strictly generates a small array of `Task` schemas.

## 7. Internal Models
Two new internal models will be introduced within `agents.planning.internal_schemas` (or similar internal scope):
- `Pass1ArchitectureResult`: Contains `architecture_summary`, `technology_recommendations`, and a list of `ComponentSpec` objects.
- `Pass2TaskResult`: Contains a list of `Task` objects for a specific component.
**NO official domain schema (`ProjectPlan`, `Task`, `ComponentSpec`) will be modified.**

## 8. ProjectPlan Assembly
The Python execution layer inside `PlanningAgent.execute()` will instantiate the final official `ProjectPlan`:
```python
project_plan = ProjectPlan(
    project_id=req_spec.project_id,
    architecture_summary=pass1_result.architecture_summary,
    technology_recommendations=pass1_result.technology_recommendations,
    components=pass1_result.components,
    tasks=all_assembled_tasks
)
```

## 9. Dependency Handling
Generating tasks per component (Option B) risks breaking cross-component task dependencies.
**Strategy:** Sequentially pass the *accumulated list of generated tasks* as context into subsequent Pass 2 requests.
- Component 1 generates T1, T2.
- Component 2's prompt receives context: `Existing Tasks: [T1, T2]`. The LLM can now explicitly map T3 -> T2.
Final DFS validation will be performed on the fully assembled `ProjectPlan` to catch circular dependencies.

## 10. Retry Strategy
Retries are isolated:
- **Pass 1 Failure:** Retries only Pass 1 (max 2 retries).
- **Pass 2 Failure:** Retries only the specific component generation that failed (max 2 retries per component).
- **Final Assembly Failure (e.g., DFS Cycle):** Fails the agent run, falling back to adaptive rework triggered by the Supervisor.

## 11. RAG Strategy
**Option A: RAG in Pass 1 only.**
- Pass 1 is responsible for architectural decisions, tech stack, and component boundaries. This is where domain knowledge (e.g., previous architectures, DB standards) is most relevant.
- Pass 2 is pure mechanical decomposition of requirements into tasks. Injecting RAG into Pass 2 per component would unnecessarily bloat the prompt and increase latency without yielding better task mechanics.

## 12. Failure Handling
- **Pass 1 Timeout / Malformed:** Agent fails, returning `AgentOutput` with `status="failed"`.
- **Pass 2 Timeout / Malformed:** Retries the component. If max retries exhaust, Agent fails.
- **Invalid Final ProjectPlan / Circular Dependency:** Agent fails with detailed exception string in `AgentOutput.error`.
The external Supervisor contract natively handles `AgentOutput(status="failed")`.

## 13. Performance Model
**Current:** One massive 120s+ timeout block. Single point of failure.
**Proposed:**
- Pass 1: ~40-50 seconds.
- Pass 2 (3 Components): ~30 seconds per component (Sequential).
Total execution time may be longer than 120s (e.g., ~140s), but individual LLM requests will comfortably sit well below the 120s timeout constraint, preventing socket closure and native generation failure. 

## 14. Option Comparison (Pass 2)
**Option A: One Request for All Tasks.**
- *Pros:* Easiest dependency mapping.
- *Cons:* Very high risk of hitting the 120s timeout again due to generating a massive array of 15-field Pydantic tasks.
**Option B: Independent Requests per Component.** *(Recommended)*
- *Pros:* Safest defense against timeouts. Granular retry limits blast radius.
- *Cons:* Slower overall clock time. Requires careful passing of accumulated task IDs for dependency mapping.

## 15. Supervisor Compatibility
The Supervisor merely calls `await planning_agent.execute(state)`. Since `PlanningAgent` orchestrates Pass 1 and Pass 2 internally and ultimately instantiates and returns a compliant `AgentOutput[ProjectPlan]`, the Supervisor requires **zero modifications**.

## 16. Test Strategy
New unit tests within `test_planning_agent.py`:
1. `test_pass1_success`: Mocks Pass 1 LLM response.
2. `test_pass2_success`: Mocks Pass 2 per-component responses.
3. `test_pass1_timeout`: Asserts agent fails gracefully.
4. `test_cross_component_dependencies`: Verifies accumulated task context allows valid dependencies.
5. `test_circular_dependency`: Ensures `ProjectPlan` assembly DFS fails correctly.
6. Existing tests ensuring `PlanningAgent` returns valid `ProjectPlan` remain untouched.

## 17. Rollback Strategy
Preserve the existing `CURRENT_SYSTEM_PROMPT` and single-pass execution block within `agent.py`. A feature flag `USE_TWO_PASS_PLANNING = True` can be introduced to toggle the behavior. If two-pass introduces unexpected logical regressions, setting it to `False` immediately restores Phase 9B behavior without duplicate LLM calls.

## 18. Risks
- **Overall Latency:** Total agent execution time will increase. While it bypasses the *individual* 120s socket timeout, overall run duration per experiment will climb.
- **Orphaned Dependencies:** Component sequential generation might result in slightly less cohesive cross-component relationships compared to a monolithic LLM pass.

## 19. Recommendation
Proceed with Two-Pass Planning utilizing **Option B** (Sequential per component) for Pass 2, and RAG limited to Pass 1. Introduce internal models `Pass1ArchitectureResult` and `Pass2TaskResult` without modifying domain schemas.

## 20. Implementation Phases
1. Create internal schemas in `agents/planning/schemas.py`.
2. Split prompts in `agents/planning/prompts.py`.
3. Refactor `PlanningAgent.execute()` to orchestrate the sequential passes and assemble the final `ProjectPlan`.
4. Update/add tests in `tests/agents/planning/test_planning_agent.py`.
