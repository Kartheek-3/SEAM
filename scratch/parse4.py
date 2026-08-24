import re
import json

with open("scratch/exp15.log", "r", encoding="utf-16") as f:
    log = f.read()

# Unwrap lines that were wrapped by powershell (basically any newline not followed by 2026-)
log = re.sub(r'\n(?!2026-)', ' ', log)
lines = log.split('\n')

metrics = {}
metrics['analysis_success'] = sum(1 for l in lines if 'AnalysisAgent completed successfully' in l)
metrics['planning_success'] = sum(1 for l in lines if 'PlanningAgent completed successfully' in l)
metrics['supervisor_started'] = sum(1 for l in lines if 'SupervisorAgent starting execution' in l)
metrics['coding_dispatched'] = sum(1 for l in lines if 'CodingAgent starting execution' in l)
metrics['coding_completed'] = sum(1 for l in lines if 'CodingAgent completed successfully' in l)
metrics['coding_parser_errs'] = sum(1 for l in lines if 'CodingAgent - WARNING - LLM parsing/generation error' in l and 'OutputParserException' in l)
metrics['coding_value_errs'] = sum(1 for l in lines if 'CodingAgent - WARNING - LLM parsing/generation error' in l and 'ValueError' in l)

metrics['qa_dispatched'] = sum(1 for l in lines if 'QAAgent starting execution' in l)
metrics['qa_completed'] = sum(1 for l in lines if 'QAAgent completed evaluation' in l)
metrics['qa_pass'] = sum(1 for l in lines if 'Verdict: pass' in l)
metrics['qa_fail'] = sum(1 for l in lines if 'Verdict: fail' in l)
metrics['qa_parser_errs'] = sum(1 for l in lines if 'QAAgent - WARNING - Validation error on attempt' in l and 'OutputParserException' in l)
metrics['qa_value_errs'] = sum(1 for l in lines if 'QAAgent - WARNING - Validation error on attempt' in l and 'ValueError' in l)

metrics['reworks'] = sum(1 for l in lines if 'Initiating rework' in l)
metrics['deadlock'] = sum(1 for l in lines if 'Workflow Deadlock' in l)
metrics['delivery_started'] = sum(1 for l in lines if 'DeliveryAgent starting execution' in l)

print(json.dumps(metrics, indent=2))
