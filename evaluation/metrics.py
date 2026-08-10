"""
Evaluation Metrics — Deterministic Metric Calculations

Pure calculation functions for all 11 metrics defined in the approved
Phase 9 evaluation plan. Each function operates on ExperimentResult
objects or lists thereof.

No values are fabricated. Functions return 0.0 or empty results when
insufficient data is provided.
"""

from evaluation.schemas import ExperimentResult, DefectCounts


# ─── Metric 1: Task Completion Rate ────────────────────────────────────────────

def task_completion_rate(completed_tasks: int, total_tasks: int) -> float:
    """
    Percentage of individual tasks that transitioned to SUCCESS.

    Formula: completed_tasks / total_tasks
    Returns 0.0 if total_tasks is 0.
    """
    if total_tasks <= 0:
        return 0.0
    return completed_tasks / total_tasks


# ─── Metric 2: End-to-End Success Rate ─────────────────────────────────────────

def end_to_end_success_rate(results: list[ExperimentResult]) -> float:
    """
    Percentage of experiment runs that completed successfully
    (result.success == True).

    Formula: count(success==True) / count(total)
    Returns 0.0 if no results provided.
    """
    if not results:
        return 0.0
    successes = sum(1 for r in results if r.success)
    return successes / len(results)


# ─── Metric 3: QA Quality Score ────────────────────────────────────────────────

def mean_qa_score(results: list[ExperimentResult]) -> float:
    """
    Average numerical QA score across all experiment results.

    Formula: sum(qa_score) / count(results)
    Returns 0.0 if no results provided.
    """
    if not results:
        return 0.0
    return sum(r.qa_score for r in results) / len(results)


# ─── Metric 4: Defect Counts ──────────────────────────────────────────────────

def total_defect_counts(results: list[ExperimentResult]) -> DefectCounts:
    """
    Aggregate defect counts (critical, major, minor) across all results.
    """
    critical = sum(r.defect_counts.critical for r in results)
    major = sum(r.defect_counts.major for r in results)
    minor = sum(r.defect_counts.minor for r in results)
    return DefectCounts(critical=critical, major=major, minor=minor)


# ─── Metric 5: Rework Cycles ──────────────────────────────────────────────────

def mean_rework_cycles(results: list[ExperimentResult]) -> float:
    """
    Average number of QA -> Supervisor -> Coding rework cycles per execution.

    Formula: sum(rework_cycles) / count(results)
    Returns 0.0 if no results provided.
    """
    if not results:
        return 0.0
    return sum(r.rework_cycles for r in results) / len(results)


# ─── Metric 6: LLM Invocation Count ───────────────────────────────────────────

def total_llm_calls(results: list[ExperimentResult]) -> int:
    """Total LLM invocations across all experiment results."""
    return sum(r.llm_calls for r in results)


def mean_llm_calls(results: list[ExperimentResult]) -> float:
    """Average LLM invocations per experiment run."""
    if not results:
        return 0.0
    return sum(r.llm_calls for r in results) / len(results)


# ─── Metric 7: Execution Time ─────────────────────────────────────────────────

def mean_execution_time(results: list[ExperimentResult]) -> float:
    """Average execution time in seconds across all results."""
    if not results:
        return 0.0
    return sum(r.execution_time_sec for r in results) / len(results)


# ─── Metric 8: Agent Failure Count ────────────────────────────────────────────

def total_agent_failures(results: list[ExperimentResult]) -> int:
    """Total agent failures across all experiment results."""
    return sum(r.agent_failure_count for r in results)


# ─── Metric 9: Delivery Success Rate ──────────────────────────────────────────

def delivery_success_rate(results: list[ExperimentResult]) -> float:
    """
    Percentage of experiments where delivery_status == 'SUCCESS'.

    Formula: count(delivery_status=='SUCCESS') / count(total)
    Returns 0.0 if no results provided.
    """
    if not results:
        return 0.0
    delivered = sum(1 for r in results if r.delivery_status == "SUCCESS")
    return delivered / len(results)


# ─── Metric 10: RAG Retrieval Success ─────────────────────────────────────────

def rag_retrieval_success_rate(results: list[ExperimentResult]) -> float:
    """
    Percentage of experiments where RAG was used (rag_used == True).

    This measures how often the RAG pipeline successfully contributed context.
    Formula: count(rag_used==True) / count(total)
    Returns 0.0 if no results provided.
    """
    if not results:
        return 0.0
    used = sum(1 for r in results if r.rag_used)
    return used / len(results)


# ─── Metric 11: Knowledge Reuse Rate ──────────────────────────────────────────

def knowledge_reuse_rate(results: list[ExperimentResult]) -> float:
    """
    Percentage of experiments where knowledge from previous projects
    was retrieved and utilized (knowledge_reused == True).

    Formula: count(knowledge_reused==True) / count(total)
    Returns 0.0 if no results provided.
    """
    if not results:
        return 0.0
    reused = sum(1 for r in results if r.knowledge_reused)
    return reused / len(results)


# ─── Statistical Helpers ───────────────────────────────────────────────────────

def std_dev(values: list[float]) -> float:
    """Population standard deviation."""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return variance ** 0.5


def median(values: list[float]) -> float:
    """Median of a list of floats."""
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    mid = n // 2
    if n % 2 == 0:
        return (sorted_vals[mid - 1] + sorted_vals[mid]) / 2
    return sorted_vals[mid]


def percentage_improvement(baseline: float, treatment: float) -> float:
    """
    Percentage improvement of treatment over baseline.

    Formula: ((treatment - baseline) / baseline) * 100
    Returns 0.0 if baseline is 0.
    """
    if baseline == 0.0:
        return 0.0
    return ((treatment - baseline) / baseline) * 100.0
