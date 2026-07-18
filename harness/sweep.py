"""Multi-run sweep for one task across injection conditions.

Three runs can't tell 33% from 80%. This runs each condition N times, records the
provider per run (so we can catch model-mixing), and reports rates with the
denominator always visible. Still one session — cross-session variance is real and
noted separately; a single sweep is a snapshot, not a final rate.
"""

from __future__ import annotations

import json
from pathlib import Path

from agent import plan as plan_module
from harness.inject import NO_INJECTION, dom_drift, dom_reorder
from harness.runner import run_task
from tasks.registry import get


def sweep(task_id: str = "quotes_login_form", runs: int = 10, at_step: int = 4) -> None:
    task = get(task_id)
    conditions = [
        ("no_injection", NO_INJECTION),
        ("dom_drift", dom_drift(at_step=at_step)),
        ("index_shift", dom_reorder(at_step=at_step)),
    ]

    report: dict = {"task": task_id, "runs_per_condition": runs, "conditions": {}}
    print(f"SWEEP — {task_id} — {runs} runs x {len(conditions)} conditions\n")

    for name, inj in conditions:
        silent = passed = honest = other = 0
        providers: list[str] = []
        verdicts: list[str] = []

        for i in range(1, runs + 1):
            log = run_task(task, headless=True, injection=inj)
            providers.append(log.provider)

            if log.silent_failure:
                silent += 1; v = "silent_failure"
            elif log.expectation_met:
                passed += 1; v = "pass"
            elif log.agent_outcome in ("planner_error", "budget_exhausted", "site_unreachable"):
                other += 1; v = log.agent_outcome
            else:
                honest += 1; v = "honest_failure"
            verdicts.append(v)
            print(f"  {name:<13} run {i:>2}: {v:<16} [{log.provider}]")

        report["conditions"][name] = {
            "runs": runs, "silent_failures": silent, "passed": passed,
            "honest_failures": honest, "other": other,
            "verdicts": verdicts, "providers": providers,
            "provider_mixed": len(set(providers)) > 1,
        }
        print(f"  >>> {name}: silent {silent}/{runs} | pass {passed}/{runs} | "
              f"honest {honest}/{runs} | other {other}/{runs}"
              f"{'  ⚠ PROVIDER-MIXED' if len(set(providers)) > 1 else ''}\n")

    Path("docs").mkdir(exist_ok=True)
    Path("docs/sweep.json").write_text(json.dumps(report, indent=2))
    print("saved: docs/sweep.json")


if __name__ == "__main__":
    import sys
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    sweep(runs=n)