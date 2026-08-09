# 16 — Experiments

> **Document Status:** Initial Draft
> **Last Updated:** Phase 0

---

## 1. Overview

This document describes the experiment design for evaluating SEAM. Experiments
are structured to test specific hypotheses about the multi-agent framework's
effectiveness.

## 2. Research Questions

| RQ | Question |
|----|---------|
| RQ1 | Does a multi-agent architecture produce higher-quality code than a single-agent approach? |
| RQ2 | Does RAG-augmented generation improve agent output quality compared to unaugmented generation? |
| RQ3 | Does the organizational knowledge repository improve performance on repeated similar tasks? |
| RQ4 | Does dynamic orchestration (with rework cycles) produce better outcomes than static sequential execution? |
| RQ5 | What is the impact of each individual agent on overall system quality? |

## 3. Experiment Design

### Experiment 1: Multi-Agent vs. Single-Agent

**Hypothesis:** SEAM's six-agent architecture produces higher quality outputs
than a single LLM agent handling all tasks.

| Variable | Control | Treatment |
|----------|---------|-----------|
| Architecture | Single LLM agent | Six-agent SEAM |
| Input | Same benchmark projects | Same benchmark projects |
| Metric | Code quality, task completion, quality score | Same |

### Experiment 2: RAG vs. No-RAG

**Hypothesis:** RAG-augmented agents produce more relevant and accurate
outputs than agents without RAG context.

| Variable | Control | Treatment |
|----------|---------|-----------|
| RAG | Disabled | Enabled |
| Input | Same benchmark projects | Same benchmark projects |
| Metric | Retrieval precision, code quality, completeness | Same |

### Experiment 3: Knowledge Reuse

**Hypothesis:** Agents with access to the knowledge repository perform better
on tasks similar to previously completed ones.

| Variable | Control | Treatment |
|----------|---------|-----------|
| Knowledge | Empty repository | Pre-populated repository |
| Input | Similar project descriptions | Same |
| Metric | Quality score, rework count, latency | Same |

### Experiment 4: Dynamic vs. Static Orchestration

**Hypothesis:** Dynamic orchestration with QA-driven rework produces higher
quality outcomes than a static sequential pipeline.

| Variable | Control | Treatment |
|----------|---------|-----------|
| Orchestration | Static pipeline (no rework) | Dynamic with rework cycles |
| Input | Same benchmark projects | Same benchmark projects |
| Metric | Final quality score, defect rate | Same |

## 4. Benchmark Projects

| ID | Project Description | Complexity |
|----|-------------------|-----------|
| BP-01 | Simple REST API (CRUD operations) | Low |
| BP-02 | Authentication system with JWT | Medium |
| BP-03 | E-commerce backend with multiple modules | High |
| BP-04 | Chat application with WebSocket | Medium |
| BP-05 | Data pipeline with validation | Medium |

*Benchmark projects will be refined during Phase 4.*

## 5. Experiment Execution Protocol

1. **Setup**: Configure SEAM for the experiment variant
2. **Execute**: Run each benchmark project through the system
3. **Collect**: Gather all metrics automatically
4. **Repeat**: Run each experiment 3 times for consistency
5. **Analyse**: Compare metrics across variants
6. **Report**: Document findings in [17_results.md](17_results.md)

## 6. Statistical Analysis

- Mean and standard deviation across runs
- Paired t-tests or Wilcoxon signed-rank tests for significance
- Effect size calculations (Cohen's d)
- Significance threshold: p < 0.05

## 7. Experiment Directory Structure

```
evaluation/
├── benchmarks/
│   ├── bp01_crud_api.json
│   ├── bp02_auth_jwt.json
│   ├── bp03_ecommerce.json
│   ├── bp04_chat_websocket.json
│   └── bp05_data_pipeline.json
├── metrics/
│   ├── collector.py
│   └── reporter.py
├── baselines/
│   ├── single_agent.py
│   └── static_pipeline.py
└── analysis/
    └── compare.py
```
