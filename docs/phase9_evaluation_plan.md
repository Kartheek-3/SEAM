# Phase 9: Evaluation and Research Validation Plan

## 1. Phase 9 Objective
The objective of Phase 9 is to experimentally evaluate whether the SEAM (Self-Evolving Autonomous Multi-Agent) framework provides measurable advantages over simpler software-development automation approaches. This phase will build the experimental harness to execute, measure, and analyze performance across multiple baselines without introducing new agents or breaking the core architecture.

## 2. Research Questions
- **RQ1**: Does dynamic multi-agent orchestration improve successful task completion compared with a simpler sequential baseline?
- **RQ2**: Does RAG-based domain knowledge improve generated software quality?
- **RQ3**: Does QA-driven adaptive rework improve final software quality and successful completion?
- **RQ4**: Does organizational knowledge reuse improve performance on subsequent projects?
- **RQ5**: What is the cost of SEAM in terms of execution time, LLM calls, and rework cycles?

## 3. Hypotheses
- **H1**: SEAM's dynamic orchestration significantly increases end-to-end task success rates versus static sequential baselines.
- **H2**: Enabling RAG significantly increases code quality scores and reduces initial defect counts.
- **H3**: Adaptive QA-driven rework resolves >80% of critical/major defects identified in the initial coding pass.
- **H4**: Access to a populated Organizational Knowledge Repository reduces rework cycles and execution time on similar future tasks.
- **H5**: SEAM incurs a measurable execution cost penalty (higher time, higher LLM invocations) but offsets it through lower defect rates and higher overall delivery success.

## 4. System Variants
1. **Full System**: SEAM + RAG + Supervisor + QA-driven rework + organizational knowledge reuse.
2. **Variant 1 (No RAG)**: SEAM without RAG injected at Analysis/Planning/Coding.
3. **Variant 2 (No Rework)**: SEAM without adaptive QA rework (fails immediately on QA rejection).
4. **Variant 3 (Cold Start)**: Full SEAM but starting with an empty knowledge repository.

## 5. Baselines
1. **Baseline A (Single LLM)**: Direct generation of software artifacts via a single large LLM prompt without agent specialization.
2. **Baseline B (Static Pipeline)**: A rigid pipeline (Analysis -> Planning -> Coding -> Delivery) lacking the dynamic Supervisor routing and QA verification loops.
3. **Baseline C (SEAM without RAG)**: The multi-agent system executing without domain knowledge retrieval.
4. **Baseline D (SEAM without adaptive QA rework)**: The multi-agent system where a QA failure terminates execution rather than triggering a rework cycle.

## 6. Experimental Scenarios
We will design a controlled set of software development scenarios spanning supported domains.
- **Scenario 1 (E-commerce)**: A product catalog REST API with CRUD operations and simulated inventory management constraints.
- **Scenario 2 (Healthcare)**: A secure patient intake form processing module demonstrating data anonymization rules.
- **Scenario 3 (Finance)**: A transaction ledger validation script requiring strict deterministic balance checks.
- **Scenario 4 (Education)**: A simple course enrollment service.
- **Scenario 5 (Travel)**: A flight availability fetching aggregator.

Each scenario will include:
- A deterministic requirement description
- Domain classification
- Explicit expected functionality and constraints
- An absolute set of acceptance criteria utilized by the QA Agent
- Expected complexity level

## 7. Metrics
1. **Task Completion Rate**: Percentage of individual tasks inside the Project Plan that transition to `SUCCESS`.
2. **End-to-End Success Rate**: Percentage of entirely completed projects successfully reaching `Delivery`.
3. **QA Quality Score**: The average numerical score returned by the `QAAgent`.
4. **Defect Count**: Tally of `CRITICAL`, `MAJOR`, and `MINOR` defects reported across all QA cycles.
5. **Number of Rework Cycles**: The count of `QA -> Supervisor -> Coding` cycles per task.
6. **LLM Invocation Count**: Total calls made to the `LLMClient` per end-to-end execution.
7. **Execution Time**: End-to-end wall-clock time from `RequirementSpec` to `Delivery`.
8. **Agent Failure Count**: Number of times an agent crashes or returns an explicit `FAILURE` status.
9. **Delivery Success Rate**: Projects successfully generating Dockerfiles and documentation.
10. **RAG Retrieval Success**: Number of times the `RAGService` retrieves context items successfully.
11. **Knowledge Reuse Rate**: Frequency at which previous project artifacts are retrieved and utilized.

## 8. Experimental Protocol
- **Control Variables**: Identical requirements, identical model configurations, static temperatures, fixed hardware specifications, and identical acceptance criteria across all executions.
- **Repetitions**: Each scenario will be run multiple times (e.g., N=5) per baseline/variant to account for LLM stochasticity.
- **Automation**: Executed purely through the upcoming automated Experiment Runner.

## 9. RAG Evaluation
Compare `Full System` vs `Baseline C (SEAM without RAG)` over identical scenarios.
Evaluate the difference in QA Quality Score, initial defect counts, and RAG retrieval relevance against the baseline to prove domain context impact.

## 10. Adaptive Rework Evaluation
Compare `Full System` vs `Baseline D (No Rework)`.
Track the defect reduction delta between the first QA pass and the final Delivery pass in the Full System, comparing the successful completion percentage against Baseline D's immediate termination upon a failed QA gate.

## 11. Knowledge Reuse Evaluation
Compare `Variant 3 (Cold Start)` vs `Full System (Pre-populated)`.
Pre-populate the knowledge base with validated artifacts from a related sub-domain, then measure execution time and defect count reduction on a subsequent overlapping scenario.

## 12. Experiment Runner Design
We will introduce an `evaluation/` directory housing the experimental harness:
- `evaluation/scenarios/`: JSON files defining deterministic requirements.
- `evaluation/baselines/`: Wrapper scripts implementing Baseline A and B.
- `evaluation/runners/`: The orchestrator for executing repetitions of a scenario.
- `evaluation/metrics/`: Calculation utilities for tokens, time, and success.
- `evaluation/reports/`: Markdown generators.
- `evaluation/results/`: JSON/CSV storage of raw execution data.
- `evaluation/analysis/`: Statistical comparison scripts.

## 13. Result Schema
```json
{
  "experiment_id": "exp-001",
  "scenario_id": "ecommerce-catalog",
  "system_variant": "baseline_c_no_rag",
  "timestamp": "2026-08-10T12:00:00Z",
  "model": "llama3.1",
  "domain": "ecommerce",
  "success": true,
  "execution_time_sec": 45.2,
  "llm_calls": 12,
  "rework_cycles": 2,
  "qa_score": 0.85,
  "defect_counts": {"critical": 0, "major": 1, "minor": 3},
  "delivery_status": "SUCCESS",
  "rag_used": false,
  "knowledge_reused": false
}
```

## 14. Statistical Analysis
- Generate mean, median, and standard deviation for Execution Time, LLM Calls, and QA Score.
- Compute success percentage (End-to-End Success Rate).
- Rely on straightforward percentage improvements and variance analysis; deeper statistical significance testing (e.g., paired t-tests) will be applied if sample sizes allow.

## 15. Reproducibility
- All scenarios are strictly predefined in JSON.
- The `evaluation/runners` will output a metadata snapshot logging the exact Git commit hash, model identifiers, environment configuration, and random seeds used by the runtime to ensure full reproducibility.

## 16. Threats to Validity
- **LLM Stochasticity**: Results may fluctuate per run even at low temperatures.
- **Sample Size**: Small iteration counts may distort averages and reduce statistical significance.
- **Model Dependence**: Performance is inherently coupled to the specific local Ollama models used.
- **Static QA Limitations**: The `QAAgent` evaluates statically; it does not compile or run test suites dynamically, limiting true functional validation.
- **Hardware Dependence**: Execution time metrics will vary significantly across host machines.

## 17. Expected Outputs
1. A raw Experiment Dataset (JSON).
2. Baseline Comparison Tables.
3. Metric visual plots.
4. RAG and Adaptive Rework analytical summaries.
5. Statistical summaries and a finalized Research Conclusions document discussing SEAM's viability.

## 18. Acceptance Criteria
- All 5 Research Questions have corresponding data.
- The Evaluation Runner executes without manual intervention.
- The resulting datasets conform exactly to the Result Schema.
- Zero modifications to production Agents or Supervisor logic.

## 19. Implementation Phases
- **Phase 9A**: Construct `evaluation/scenarios` and `evaluation/metrics`.
- **Phase 9B**: Implement the `evaluation/runners` and Baseline wrappers.
- **Phase 9C**: Execute experiments and generate `evaluation/results/`.
- **Phase 9D**: Synthesize the final Research Conclusion report.

## 20. Files Expected to Change
- **New Files**: `docs/phase9_evaluation_plan.md`, `evaluation/*` directory components.
- **Documentation Updates**: `docs/17_results.md` (to be populated with real experimental data), `docs/14_evaluation.md` (syncing traceability of metrics to the new runner).

## 21. Files That Must Not Change
- `agents/**` (Agent behaviors and architectures must remain completely untouched)
- `backend/schemas/**` (Core data contracts)
- `tests/**` (Existing tests must not be weakened or modified)
- Core architectural documentation like `docs/03_architecture.md`
