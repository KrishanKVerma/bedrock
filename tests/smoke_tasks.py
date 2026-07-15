"""Manual check: run one task and see whether the agent's claim matches reality."""

import sys

from agent.loop import run
from tasks.registry import get

task_id = sys.argv[1] if len(sys.argv) > 1 else "wiki_search"
task = get(task_id)

print(f"RUNNING: {task.describe()}")
print(f"EXPECT:  {task.expect.describe()}\n")

report = run(task.instruction, task.start_url, max_steps=task.max_steps)
print(report.describe())

passed, reason = task.expect.check(report.final_url, report.final_text)
print(f"\nAGENT SAID:  {report.outcome} — {report.claim}")
print(f"REALITY:     {'PASS' if passed else 'FAIL'} — {reason}")
if report.outcome == "done" and not passed:
    print("\n>>> SILENT FAILURE: agent claimed success, expectation not met.")