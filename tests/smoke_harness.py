"""Manual check: run a task under the harness and save the trace."""

import sys

from harness.runner import run_task
from tasks.registry import get

task = get(sys.argv[1] if len(sys.argv) > 1 else "quotes_login_form")
log = run_task(task)

print("\n" + log.summary())
print(f"AGENT CLAIM: {log.agent_claim}")
print(f"REALITY:     {log.expectation_reason}")
print(f"TRACE SAVED: runs/{log.task_id}_{log.run_id}.json")