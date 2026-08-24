import json
import os
import re

log_file = 'scratch/exp14.log'
with open(log_file, 'r', encoding='utf-16') as f:
    text = f.read().replace('\n', ' ').replace('\r', ' ')
    text = re.sub(r'\s+', ' ', text)

results_dir = 'evaluation/results'
files = [os.path.join(results_dir, f) for f in os.listdir(results_dir) if f.startswith('exp-') and f.endswith('.json')]
latest_file = max(files, key=os.path.getmtime)
with open(latest_file, 'r') as f:
    data = json.load(f)

print("=== JSON DATA ===")
print(json.dumps(data, indent=2))
print("=================\n")

# Planning Pass 1
pass1_duration = re.search(r'Pass 1 completed in ([\d\.]+)s', text)
print(f"Pass 1: {pass1_duration.group(1) if pass1_duration else 'N/A'}")

# Pass 2
pass2_comps = re.findall(r'Pass 2 for component \'(.*?)\' completed in ([\d\.]+)s', text)
print(f"Pass 2 Components: {pass2_comps}")
print(f"Total Components generated: {len(pass2_comps)}")

# Tasks generated
tasks_generated = re.search(r'Generated (\d+) components and (\d+) tasks', text)
if tasks_generated:
    print(f"Generated {tasks_generated.group(1)} components and {tasks_generated.group(2)} tasks")

# Coding
coding_starts = len(re.findall(r': CodingAgent starting', text))
coding_completions = len(re.findall(r'CodingAgent completed successfully', text))
coding_llm_timeouts = len(re.findall(r'LLM generation timed out', text))
coding_llm_parsing = len(re.findall(r'LLM parsing/generation error', text))
coding_connection_errors = len(re.findall(r'ClientConnectorDNSError', text))

print(f"Coding Starts (Task Dispatch): {coding_starts}")
print(f"Coding Completions: {coding_completions}")
print(f"Coding Timeouts: {coding_llm_timeouts}")
print(f"Coding Parsing/Generation Errors (caught locally): {coding_llm_parsing}")
print(f"Coding Connection Errors: {coding_connection_errors}")

# QA
qa_starts = len(re.findall(r'QAAgent starting execution', text))
qa_completions = len(re.findall(r'QAAgent completed in', text))
qa_fails = len(re.findall(r'QA Agent failed to produce valid result', text))
qa_parsing_errors = len(re.findall(r'ValueError: LLM output did not parse into a JSON object mapping', text))

print(f"QA Starts: {qa_starts}")
print(f"QA Completions (success): {qa_completions}")
print(f"QA Task Fails (exhausted retries): {qa_fails}")
print(f"QA Local JSON Parsing Errors: {qa_parsing_errors}")

# Delivery
deliv_starts = len(re.findall(r'DeliveryAgent starting', text))
deliv_completions = len(re.findall(r'DeliveryAgent completed', text))
print(f"Delivery Starts: {deliv_starts}")
print(f"Delivery Completions: {deliv_completions}")

reworks = len(re.findall(r'Initiating rework', text))
print(f"Rework cycles triggered: {reworks}")

deadlock = re.search(r'Workflow Deadlock:', text)
print(f"Deadlock detected: {bool(deadlock)}")
if deadlock:
    deadlock_line = re.search(r'Workflow Deadlock:.*', text)
    if deadlock_line:
        print(f"Deadlock detail: {deadlock_line.group(0)}")
