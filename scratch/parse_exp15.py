import json
import re
import sys

def parse_log(logfile, jsonfile):
    with open(logfile, 'r', encoding='utf-16') as f:
        log = f.read()
    # Remove powershell line wrapping
    log = re.sub(r'\n(?!2026)', ' ', log)

    with open(jsonfile, 'r', encoding='utf-8') as f:
        res = json.load(f)

    metrics = {
        "analysis_success": "AnalysisAgent completed successfully" in log,
        "planning_survived": "PlanningAgent completed successfully" in log,
        "projectplan_valid": "ProjectPlan validation successful" in log or "ProjectPlan assembled" in log,
        "supervisor_executed": "SupervisorAgent starting execution" in log,
        "tasks_dispatched": len(re.findall(r"Task [a-zA-Z0-9\-]+: (CodingAgent|QAAgent|DeliveryAgent) starting", log)),
        "coding_dispatched": len(re.findall(r"Task [a-zA-Z0-9\-]+: CodingAgent starting", log)),
        "coding_completed": len(re.findall(r"Task [a-zA-Z0-9\-]+: CodingAgent completed successfully", log)),
        "coding_failures": len(re.findall(r"Task [a-zA-Z0-9\-]+: CodingAgent failed", log)),
        "coding_parser_exceptions": len(re.findall(r"CodingAgent - WARNING - LLM parsing/generation error on attempt.*OutputParserException", log)),
        "coding_value_errors": len(re.findall(r"CodingAgent - WARNING - LLM parsing/generation error on attempt.*ValueError", log)),
        "qa_dispatched": len(re.findall(r"Task qa-[a-zA-Z0-9\-]+: QAAgent starting", log)),
        "qa_completed": len(re.findall(r"Task qa-[a-zA-Z0-9\-]+: QAAgent completed", log)),
        "qa_pass": len(re.findall(r"Verdict: pass", log)),
        "qa_fail": len(re.findall(r"Verdict: fail", log)),
        "qa_parser_exceptions": len(re.findall(r"QAAgent - WARNING - Validation error on attempt.*OutputParserException", log)),
        "qa_value_errors": len(re.findall(r"QAAgent - WARNING - Validation error on attempt.*ValueError", log)),
        "qa_timeouts": len(re.findall(r"QAAgent - WARNING - Validation error on attempt.*Timeout", log)),
        "reworks": len(re.findall(r"Initiating rework", log)),
        "delivery_dispatched": "DeliveryAgent starting" in log,
        "deadlock": "Workflow Deadlock:" in log,
        "json_success": res.get("success", False)
    }
    
    print(json.dumps(metrics, indent=2))

if __name__ == "__main__":
    parse_log("scratch/exp15.log", "evaluation/results/exp-20260821085833-ae43f8d7.json")
