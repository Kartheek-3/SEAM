import re
import json

with open("scratch/exp15.log", "r", encoding="utf-16") as f:
    raw_log = f.read()

# Filter out lines that start with PowerShell NativeCommandError garbage
clean_lines = []
for line in raw_log.split('\n'):
    if line.startswith('    + ') or line.startswith('+ ') or 'RemoteException' in line or 'NativeCommandError' in line:
        continue
    # Some lines start with 'python : ' or just ' '
    line = re.sub(r'^python : ', '', line)
    clean_lines.append(line.strip())

clean_log = " ".join(clean_lines)

# Now we can just use regex on clean_log
metrics = {}
metrics['analysis_success'] = 'AnalysisAgent completed successfully' in clean_log
metrics['planning_success'] = 'PlanningAgent completed successfully' in clean_log
metrics['supervisor_started'] = 'SupervisorAgent starting execution' in clean_log
metrics['coding_dispatched'] = len(re.findall(r'CodingAgent starting execution', clean_log))
metrics['coding_completed'] = len(re.findall(r'CodingAgent completed successfully', clean_log))
metrics['coding_parser_errs'] = len(re.findall(r'OutputParserException', clean_log))
metrics['coding_value_errs'] = len(re.findall(r'ValueError', clean_log))

metrics['qa_dispatched'] = len(re.findall(r'QAAgent starting execution', clean_log))
metrics['qa_completed'] = len(re.findall(r'QAAgent completed evaluation', clean_log))
metrics['qa_pass'] = len(re.findall(r'Verdict: pass', clean_log))
metrics['qa_fail'] = len(re.findall(r'Verdict: fail', clean_log))
metrics['qa_parser_errs'] = len(re.findall(r'OutputParserException', clean_log))

metrics['reworks'] = len(re.findall(r'Initiating rework', clean_log))
metrics['deadlock'] = len(re.findall(r'Workflow Deadlock', clean_log))
metrics['delivery_started'] = len(re.findall(r'DeliveryAgent starting execution', clean_log))

print(json.dumps(metrics, indent=2))
