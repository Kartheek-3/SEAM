import json
import re
from datetime import datetime

log_file = "scratch/exp18.log"

metrics = {
    "total_leases": 0,
    "infrastructure_failures": 0,
    "recovery_attempts": 0,
    "successful_recoveries": 0,
    "failed_recoveries": 0,
    "recovery_events": []
}

with open(log_file, "r", encoding="utf-16") as f:
    lines = f.readlines()

current_failure = None
for line in lines:
    if "Assigned task" in line:
        metrics["total_leases"] += 1
    elif "marked UNHEALTHY" in line:
        metrics["infrastructure_failures"] += 1
        current_failure = {"timestamp": line.split(" - ")[0], "worker_id": "default-worker-1", "exception": "TimeoutError/ConnectionError"}
    elif "recovered and is now AVAILABLE" in line:
        metrics["successful_recoveries"] += 1
        metrics["recovery_attempts"] += 1
        if current_failure:
            current_failure["recovery_time"] = line.split(" - ")[0]
            metrics["recovery_events"].append(current_failure)
            current_failure = None

print(json.dumps(metrics, indent=2))
