import json
import os
import re

log_file = 'scratch/exp13.log'
with open(log_file, 'r', encoding='utf-16') as f:
    text = f.read().replace('\n', ' ')

# Basic log text for easier searching line by line for some things
with open(log_file, 'r', encoding='utf-16') as f:
    lines = f.readlines()

results_dir = 'evaluation/results'
files = [os.path.join(results_dir, f) for f in os.listdir(results_dir) if f.startswith('exp-') and f.endswith('.json')]
latest_file = max(files, key=os.path.getmtime)
with open(latest_file, 'r') as f:
    data = json.load(f)

print(json.dumps(data, indent=2))

# Planning Pass 1
pass1_duration = re.search(r'Pass 1 completed in ([\d\.]+)s', text)
print(f"Pass 1: {pass1_duration.group(1) if pass1_duration else 'N/A'}")

# Pass 2
pass2_comps = re.findall(r'Pass 2 for component \'(.*?)\' completed in ([\d\.]+)s', text)
print(f"Pass 2 Components: {pass2_comps}")

# Coding
coding_starts = len(re.findall(r': CodingAgent starting', text))
coding_completions = len(re.findall(r'CodingAgent completed successfully', text))
coding_llm_timeouts = len(re.findall(r'timed out', text))
coding_llm_parsing = len(re.findall(r'LLM parsing/generation error', text))

print(f"Coding Starts (Task Dispatch): {coding_starts}")
print(f"Coding Completions: {coding_completions}")
print(f"Timeouts: {coding_llm_timeouts}")
print(f"Parsing Errors (caught locally): {coding_llm_parsing}")

# QA
qa_starts = len(re.findall(r'QAAgent starting execution', text))
qa_completions = len(re.findall(r'QAAgent completed in', text))
print(f"QA Starts: {qa_starts}")
print(f"QA Completions: {qa_completions}")

# Delivery
deliv_starts = len(re.findall(r'DeliveryAgent starting', text))
deliv_completions = len(re.findall(r'DeliveryAgent completed', text))
print(f"Delivery Starts: {deliv_starts}")
print(f"Delivery Completions: {deliv_completions}")

reworks = len(re.findall(r'Initiating rework', text))
print(f"Rework cycles: {reworks}")

deadlock = re.search(r'Workflow Deadlock detected', text)
print(f"Deadlock: {bool(deadlock)}")
