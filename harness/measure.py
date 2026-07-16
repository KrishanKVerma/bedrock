"""Baseline measurement.

Runs every task N times and reports what happened, with denominators visible.

Averages hide the thing worth seeing. A task that passes 3 out of 5 times is not
"60% reliable" — it is non-deterministic, which is a different and worse problem
than being consistently wrong. So this reports per-task, per-run, and flags any
task whose verdict changes between identical runs.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from harness.runner import run_task
from tasks.registry import TASKS, Task


@dataclass(slots=True)
class TaskResult:
    """How one task behaved across N identical runs."""

    task_id: str
    runs: int
    passed: int = 0
    silent_failures: int = 0
    honest_failures: int = 0
    errors: int = 0
    verdicts: list[str] = field(default_factory=list)
    run_ids: list[str] = field(default_factory=list)

    @property
    def non_deterministic(self) -> bool:
        return len(set(self.verdicts)) > 1

    def line(self) -> str:
        flag = "  ⚠ FLIPS" if self.non_deterministic else ""
        return (
            f"{self.task_id:<20} "
            f"pass {self.passed}/{self.runs} | "
            f"silent-fail {self.silent_failures}/{self.runs} | "
            f"honest-fail {self.honest_failures}/{self.runs}"
            f"{flag}"
        )


def measure_task(task: Task, runs: int, headless: bool) -> TaskResult:
    res = TaskResult(task_id=task.id, runs=runs)
    for _ in range(runs):
        log = run_task(task, headless=headless)
        res.run_ids.append(log.run_id)

        if log.silent_failure:
            res.silent_failures += 1
            verdict = "silent_failure"
        elif log.expectation_met:
            res.passed += 1
            verdict = "pass"
        elif log.agent_outcome in ("planner_error", "budget_exhausted"):
            res.errors += 1
            verdict = log.agent_outcome
        else:
            res.honest_failures += 1
            verdict = "honest_failure"

        res.verdicts.append(verdict)
    return res


def measure(runs: int = 3, headless: bool = True, save_to: str = "docs/baseline.json") -> list[TaskResult]:
    """Run the full task set N times each. Returns per-task results."""
    print(f"BASELINE MEASUREMENT — {len(TASKS)} tasks x {runs} runs each\n")
    results: list[TaskResult] = []

    for task in TASKS:
        print(f"running {task.id} ...", flush=True)
        res = measure_task(task, runs, headless)
        results.append(res)
        print("  " + res.line())

    _report(results, runs)
    _save(results, runs, Path(save_to))
    return results


def _report(results: list[TaskResult], runs: int) -> None:
    total = len(results) * runs
    passed = sum(r.passed for r in results)
    silent = sum(r.silent_failures for r in results)
    honest = sum(r.honest_failures for r in results)
    errors = sum(r.errors for r in results)
    flips = [r.task_id for r in results if r.non_deterministic]

    print("\n" + "=" * 62)
    print("BASELINE — per task")
    print("=" * 62)
    for r in results:
        print(r.line())

    print("\n" + "=" * 62)
    print(f"TOTALS across {len(results)} tasks x {runs} runs = {total} runs")
    print("=" * 62)
    print(f"  passed:          {passed}/{total}")
    print(f"  SILENT FAILURES: {silent}/{total}   <- claimed success, reality disagreed")
    print(f"  honest failures: {honest}/{total}")
    print(f"  errors/timeouts: {errors}/{total}")
    print(f"  non-deterministic tasks: {len(flips)}/{len(results)} {flips if flips else ''}")

    if silent == 0:
        print("\n  NOTE: zero silent failures in this sample. The agent's self-report")
        print("  agreed with reality on every run. Report this honestly.")


def _save(results: list[TaskResult], runs: int, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "runs_per_task": runs,
        "tasks": len(results),
        "total_runs": len(results) * runs,
        "results": [
            {
                "task_id": r.task_id,
                "runs": r.runs,
                "passed": r.passed,
                "silent_failures": r.silent_failures,
                "honest_failures": r.honest_failures,
                "errors": r.errors,
                "verdicts": r.verdicts,
                "non_deterministic": r.non_deterministic,
                "run_ids": r.run_ids,
            }
            for r in results
        ],
    }
    path.write_text(json.dumps(payload, indent=2))
    print(f"\nsaved: {path}")


if __name__ == "__main__":
    import sys

    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    measure(runs=n, headless=True)