import json
import statistics
with open('scratch/diagnostic_9d12_results.json', 'r') as f:
    data = json.load(f)

successes = [d for d in data if d['final_success']]
first_attempt = [d for d in data if d['first_attempt_success']]
retries_recovered = [d for d in data if d['retry_recovery']]

all_calls = []
for d in data:
    all_calls.extend(d['calls'])
    
timeouts = [c for c in all_calls if c.get('timeout', False)]
parser_fails = [c for c in all_calls if not c.get('success', False) and not c.get('timeout', False)]
markdowns = [c for c in all_calls if c.get('markdown_detected', False)]
durations = [c['duration'] for c in all_calls]

if durations:
    mean_lat = statistics.mean(durations)
    median_lat = statistics.median(durations)
    p95_lat = statistics.quantiles(durations, n=20)[18] if len(durations) > 1 else max(durations)
else:
    mean_lat = median_lat = p95_lat = 0

print(f'Total tasks: {len(data)}')
print(f'First-attempt success rate: {len(first_attempt)}/{len(data)}')
print(f'Final success rate: {len(successes)}/{len(data)}')
print(f'Retry recovery rate: {len(retries_recovered)}/{len(data) - len(first_attempt) if len(data) > len(first_attempt) else 1}')
print(f'Total LLM calls: {len(all_calls)}')
print(f'Timeouts: {len(timeouts)}')
print(f'Parser failures: {len(parser_fails)}')
print(f'Markdown detected in calls: {len(markdowns)}/{len(all_calls)}')
print(f'Latency - Mean: {mean_lat:.2f}s, Median: {median_lat:.2f}s, P95: {p95_lat:.2f}s')

for c in all_calls:
    if not c.get('success', False):
        print(f"Failure: {c.get('exception_type')}, Result type: {c.get('parser_result_type')}")
