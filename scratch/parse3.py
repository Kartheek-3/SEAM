import json

with open("scratch/exp15.log", "r", encoding="utf-16") as f:
    lines = f.readlines()

def count_in_lines(target):
    return sum(1 for line in lines if target in line)

def count_regex_in_lines(target):
    import re
    return sum(1 for line in lines if re.search(target, line))

print(f"Analysis successful: {count_in_lines('AnalysisAgent completed successfully') > 0}")
print(f"Planning pass 1 successful: {count_in_lines('PlanningAgent completed successfully') > 0}")
print(f"ProjectPlan valid: {count_in_lines('ProjectPlan validation successful') > 0 or count_in_lines('ProjectPlan assembled') > 0}")
print(f"Supervisor executed: {count_in_lines('SupervisorAgent starting execution') > 0}")
print(f"Coding tasks dispatched: {count_in_lines('CodingAgent starting execution')}")

coding_completed = 0
for i, line in enumerate(lines):
    if "CodingAgent" in line and "completed successfully" in line:
        coding_completed += 1
    elif "CodingAgent" in line and i < len(lines)-1 and "completed successfully" in lines[i+1]:
        coding_completed += 1
print(f"Coding tasks completed: {coding_completed}")

print(f"Coding parsing failures: {count_in_lines('CodingAgent - WARNING - LLM parsing/generation error on attempt')}")
print(f"QA tasks dispatched: {count_in_lines('QAAgent starting execution')}")

qa_completed = 0
for i, line in enumerate(lines):
    if "QAAgent completed evaluation" in line:
        qa_completed += 1
    elif "QAAgent" in line and i < len(lines)-1 and "completed evaluation" in lines[i+1]:
        qa_completed += 1
print(f"QA tasks completed: {qa_completed}")

print(f"QA PASS: {count_in_lines('Verdict: pass')}")
print(f"QA FAIL: {count_in_lines('Verdict: fail')}")
print(f"QA parsing failures: {count_in_lines('QAAgent - WARNING - Validation error on attempt')}")
print(f"Reworks: {count_in_lines('Initiating rework')}")
print(f"Delivery dispatched: {count_in_lines('DeliveryAgent starting execution') > 0}")
print(f"Deadlock: {count_in_lines('Workflow Deadlock') > 0}")

with open("evaluation/results/exp-20260821085833-ae43f8d7.json", "r") as f:
    res = json.load(f)
print(f"LLM Calls: {res['llm_calls']}")
print(f"Execution time: {res['execution_time_sec']}")
print(f"Rework cycles: {res['rework_cycles']}")
print(f"Delivery status: {res['delivery_status']}")
