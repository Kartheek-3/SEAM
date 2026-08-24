import re

with open('scratch/exp11.log', 'r', encoding='utf-16') as f:
    log_data = f.read()

analysis_pattern = re.search(r'Task .*?-analysis completed successfully in (\d+)ms', log_data)
analysis_duration = analysis_pattern.group(1) if analysis_pattern else 'Unknown'
print(f'Analysis Duration: {analysis_duration}ms')

pass1_pattern = re.search(r'Pass 1 completed in ([\d\.]+)s after (\d+) attempts', log_data)
print(f'Pass 1: {pass1_pattern.groups() if pass1_pattern else ""}')

pass2_pattern = re.findall(r'Pass 2 for component \'(.*?)\' completed in ([\d\.]+)s after (\d+) attempts', log_data)
print('Pass 2 Components:')
for p in pass2_pattern:
    print(f'  Component: {p[0]}, duration: {p[1]}s, attempts: {p[2]}')
    
planning_generated = re.search(r'Generated (\d+) components and (\d+) tasks\.', log_data)
print(f'Planning Generated: {planning_generated.groups() if planning_generated else ""}')

coding_tasks = re.findall(r'Task (.*?): CodingAgent completed successfully in (\d+)ms\.', log_data)
print('Coding Tasks Completed:')
for t in coding_tasks:
    print(f'  Task {t[0]}: {t[1]}ms')

coding_timeouts = len(re.findall(r'LLM execution failed: LLM generation timed out', log_data))
print(f'Coding timeouts: {coding_timeouts}')

coding_parsing = len(re.findall(r'OutputParserException', log_data))
print(f'Coding parsing errors: {coding_parsing}')

type_errors = len(re.findall(r'ValueError: LLM output did not parse into a JSON object mapping', log_data))
print(f'Coding ValueErrors (was TypeError): {type_errors}')

qa_tasks = re.findall(r'Task (.*?): QAAgent starting execution', log_data)
qa_completed = re.findall(r'Task (.*?): QAAgent completed in (\d+)ms\.', log_data)
print(f'QA reached: {len(qa_tasks) > 0}')
print(f'QA completed tasks: {len(qa_completed)}')

qa_rework = len(re.findall(r'Initiating rework', log_data))
print(f'QA reworks requested: {qa_rework}')

deadlock = re.search(r'Workflow Deadlock detected.*?Pending tasks: (\[.*?\])', log_data)
print(f'Deadlock: {deadlock.group(1) if deadlock else ""}')
