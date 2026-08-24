from backend.llm.worker_registry import global_registry

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from evaluation.runner import ExperimentRunner

api_router = APIRouter()
runner = ExperimentRunner()

@api_router.get("/experiments", response_model=List[Dict[str, Any]])
def get_experiments():
    """
    Returns a list of all historical experiments.
    """
    results = runner.load_results()
    
    # Transform raw backend schemas to frontend-friendly formats
    # to avoid deep coupling or leaking domain models directly to the view
    experiments = []
    for r in results:
        # Reconstruct high-level stages based on the summary metrics
        # (Since detailed tasks are not persisted)
        stages = []
        if r.success:
            stages = [
                {"name": "Analysis", "status": "SUCCESS", "duration": "-"},
                {"name": "Planning", "status": "SUCCESS", "duration": "-"},
                {"name": "ProjectPlan", "status": "SUCCESS", "duration": "-"},
                {"name": "Supervisor", "status": "SUCCESS", "duration": f"{r.execution_time_sec}s"},
                {"name": "Coding", "status": "SUCCESS", "duration": "-"},
                {"name": "QA", "status": "SUCCESS", "duration": "-"},
                {"name": "Delivery", "status": "SUCCESS", "duration": "-"}
            ]
        else:
            stages = [
                {"name": "Analysis", "status": "SUCCESS", "duration": "-"},
                {"name": "Planning", "status": "SUCCESS", "duration": "-"},
                {"name": "ProjectPlan", "status": "SUCCESS", "duration": "-"},
                {"name": "Supervisor", "status": "FAILED", "duration": f"{r.execution_time_sec}s"}
            ]

        experiments.append({
            "id": r.experiment_id,
            "scenario": r.scenario_id,
            "model": r.model,
            "mode": r.result_mode.value.upper() if hasattr(r.result_mode, "value") else str(r.result_mode).upper(),
            "duration": f"{r.execution_time_sec}s",
            "llmCalls": r.llm_calls,
            "tasks": f"{int(r.task_completion_rate * 100)}%",
            "status": "SUCCESS" if r.success else "FAILED",
            "stages": stages
        })
    
    # Sort descending by id/timestamp
    experiments.sort(key=lambda x: x["id"], reverse=True)
    return experiments


@api_router.get("/experiments/{experiment_id}", response_model=Dict[str, Any])
def get_experiment(experiment_id: str):
    """
    Returns detailed metrics for a specific experiment.
    """
    results = runner.load_results()
    for r in results:
        if r.experiment_id == experiment_id or r.experiment_id == f"exp-{experiment_id}":
            stages = []
            if r.success:
                stages = [
                    {"name": "Analysis", "status": "SUCCESS", "duration": "-"},
                    {"name": "Planning", "status": "SUCCESS", "duration": "-"},
                    {"name": "ProjectPlan", "status": "SUCCESS", "duration": "-"},
                    {"name": "Supervisor", "status": "SUCCESS", "duration": f"{r.execution_time_sec}s"},
                    {"name": "Coding", "status": "SUCCESS", "duration": "-"},
                    {"name": "QA", "status": "SUCCESS", "duration": "-"},
                    {"name": "Delivery", "status": "SUCCESS", "duration": "-"}
                ]
            else:
                stages = [
                    {"name": "Analysis", "status": "SUCCESS", "duration": "-"},
                    {"name": "Planning", "status": "SUCCESS", "duration": "-"},
                    {"name": "ProjectPlan", "status": "SUCCESS", "duration": "-"},
                    {"name": "Supervisor", "status": "FAILED", "duration": f"{r.execution_time_sec}s"}
                ]

            return {
                "id": r.experiment_id,
                "scenario": r.scenario_id,
                "model": r.model,
                "mode": r.result_mode.value.upper() if hasattr(r.result_mode, "value") else str(r.result_mode).upper(),
                "duration": f"{r.execution_time_sec}s",
                "llmCalls": r.llm_calls,
                "tasks": f"{int(r.task_completion_rate * 100)}%",
                "status": "SUCCESS" if r.success else "FAILED",
                "stages": stages
            }
    
    raise HTTPException(status_code=404, detail="Experiment not found")


@api_router.get("/experiments/{experiment_id}/live", response_model=Dict[str, Any])
def get_experiment_live(experiment_id: str):
    """
    Returns live monitoring state.
    Since current architecture stores execution state solely in the CLI process memory
    without IPC or file persistence, live state is explicitly 'unknown'.
    """
    return {
        "experiment_id": experiment_id,
        "status": "unknown",
        "current_stage": "unknown",
        "started_at": None,
        "elapsed_seconds": None,
        "stages": {
            "analysis": None,
            "planning": None,
            "supervisor": None,
            "coding": None,
            "qa": None,
            "rework": None,
            "delivery": None
        }
    }


@api_router.get("/experiments/{experiment_id}/tasks/live", response_model=List[Dict[str, Any]])
def get_experiment_tasks_live(experiment_id: str):
    """
    Returns live tasks state.
    Since execution state is purely in-memory in the CLI process,
    this returns an empty list.
    """
    return []


@api_router.get("/experiments/{experiment_id}/events", response_model=List[Dict[str, Any]])
def get_experiment_events(experiment_id: str):
    """
    Returns live SSE or polling events.
    Currently no event stream is generated by the CLI process.
    """
    return []


@api_router.get("/projects", response_model=List[Dict[str, Any]])
def get_projects():
    """
    Returns active projects. Since SEAM evaluates ephemerally,
    this currently returns an empty list for historical runs.
    """
    return []

@api_router.get("/projects/{project_id}", response_model=Dict[str, Any])
def get_project(project_id: str):
    raise HTTPException(status_code=404, detail="Project not found")


@api_router.get("/tasks", response_model=List[Dict[str, Any]])
def get_tasks():
    """
    Returns active tasks. Empty for historical runs as they are not persisted.
    """
    return []

@api_router.get("/tasks/{task_id}", response_model=Dict[str, Any])
def get_task(task_id: str):
    raise HTTPException(status_code=404, detail="Task not found")


@api_router.get("/artifacts", response_model=List[Dict[str, Any]])
def get_artifacts():
    return []


@api_router.get("/artifacts/{artifact_id}", response_model=Dict[str, Any])
def get_artifact(artifact_id: str):
    raise HTTPException(status_code=404, detail="Artifact not found")


@api_router.get("/qa/{task_id}", response_model=Dict[str, Any])
def get_qa(task_id: str):
    raise HTTPException(status_code=404, detail="QA result not found")


@api_router.get("/delivery/{project_id}", response_model=Dict[str, Any])
def get_delivery(project_id: str):
    raise HTTPException(status_code=404, detail="Delivery status not found")


@api_router.get("/agents/status", response_model=Dict[str, Any])
def get_agent_status():
    return {"status": "idle"}

@api_router.get("/api/v1/workers", response_model=Dict[str, Any])
def get_workers():
    """
    Returns the current state of the distributed worker pool registry.
    This reflects the active execution state of workers initialized by the system.
    """
    workers = global_registry.list_workers()
    return {
        "workers": [
            {
                "worker_id": w.worker_id,
                "host": w.host,
                "port": w.port,
                "model": w.model,
                "status": w.status.value if hasattr(w.status, 'value') else w.status
            } for w in workers
        ]
    }
