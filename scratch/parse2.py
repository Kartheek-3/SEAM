import re
with open("scratch/exp15.log", "r", encoding="utf-16") as f:
    log = f.read()

log_lines = log.split('\n')
coding_completed = 0
for i, line in enumerate(log_lines):
    if "CodingAgent" in line and "completed successfully" in line:
        coding_completed += 1
    elif "CodingAgent" in line and "completed successfully" in log_lines[min(i+1, len(log_lines)-1)]:
        coding_completed += 1

print(f"Coding completed: {coding_completed}")
