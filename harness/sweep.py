"""Single-condition sweep.

A full 30-run sweep exhausts the daily token budget before the third condition
finishes, so conditions get truncated. This runs ONE condition per invocation —
~10 runs, safely under the cap — so every session produces one complete, clean
condition instead of two-and-a-half.

Usage:
    BEDROCK_PROVIDER=groq python -m harness.sweep no_injection 10
    BEDROCK_PROVIDER=groq python -m harness.sweep dom_drift 10
    BEDROCK_PROVIDER=groq python -m harness.sweep index_shift 10
    BEDROCK_PROVIDER=groq python -m harness.sweep modal 10
"""

from __future__ import annotations

import sys

from harness.inject import NO_INJECTION, dom_drift, dom_reorder, modal
from harness.runner import run_task
from tasks.registry import get

CONDITIONS = {
    "no_injection": NO_INJECTION,
    "dom_drift": dom_drift(at_step=4),
    "index_shift": dom_reorder(at_step=4),
    "modal": modal(at_step=4),
}


def sweep_condition(condition: str, runs: int, task_id: str = "quotes_login_form") -> None:
    if condition not in CONDITIONS:
        raise SystemExit(f"Unknown condition {condition!r}. Choose from {list(CONDITIONS)}")

    task = get(task_id)
    inj = CONDITIONS[condition]
    silent = passed = honest = other = 0
    providers: list[str] = []

    print(f"SWEEP — {task_id} — condition={condition} — {runs} runs\n")

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
        print(f"  run {i:>2}: {v:<16} [{log.provider}]")

    mixed = len(set(providers)) > 1
    print(f"\n>>> {condition}: silent {silent}/{runs} | pass {passed}/{runs} | "
          f"honest {honest}/{runs} | other {other}/{runs}"
          f"{'  ⚠ PROVIDER-MIXED — DISCARD' if mixed else ''}")
    tag_provider = providers[0] if providers else "groq"
    print(f"\nlog it: python -m tests.log_session <tag> {condition} {tag_provider} {runs} {silent} 60")


if __name__ == "__main__":
    cond = sys.argv[1] if len(sys.argv) > 1 else "no_injection"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    sweep_condition(cond, n)