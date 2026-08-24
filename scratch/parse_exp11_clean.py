with open('scratch/exp11.log', 'r', encoding='utf-16') as f:
    text = f.read().replace('\n', '')

import re

coding_started = len(re.findall(r'CodingAgent starting', text))
coding_completed = len(re.findall(r'CodingAgent completed successfully', text))
qa_started = len(re.findall(r'QAAgent starting', text))
qa_completed = len(re.findall(r'QAAgent completed', text))

timeouts = len(re.findall(r'LLM execution failed: LLM generation timed out', text))
parsing = len(re.findall(r'OutputParserException', text))
value_errors = len(re.findall(r'ValueError', text))
type_errors = len(re.findall(r'TypeError', text))

print(f"Coding Started: {coding_started}")
print(f"Coding Completed: {coding_completed}")
print(f"QA Started: {qa_started}")
print(f"QA Completed: {qa_completed}")
print(f"Timeouts: {timeouts}")
print(f"Parsing Exceptions: {parsing}")
print(f"Value Errors: {value_errors}")
print(f"Type Errors: {type_errors}")

reworks = len(re.findall(r'Initiating rework', text))
print(f"Reworks: {reworks}")
