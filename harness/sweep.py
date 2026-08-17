"""Single-condition sweep.

Runs ONE injection condition per invocation, so every session produces one
complete, clean condition rather than several truncated ones. Per-run evidence is
written to docs/evidence/sweep_<condition>.json, and a sweep halted by a provider
rate limit still saves what it completed - denominators below are the runs that
actually finished, never the runs that were requested.

Usage:
    BEDROCK_PROVIDER=groq python -m harness.sweep no_injection 50
    BEDROCK_PROVIDER=groq python -m harness.sweep dom_drift 50
    BEDROCK_PROVIDER=groq python -m harness.sweep index_shift 50
    BEDROCK_PROVIDER=groq python -m harness.sweep modal 50
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from harness.inject import NO_INJECTION, dom_drift, dom_reorder, modal, session_expiry
from harness.runner import run_task
from tasks.registry import get


CONDITIONS = {
    "no_injection": NO_INJECTION,
    "dom_drift": dom_drift(),
    "index_shift": dom_reorder(),
    "modal": modal(),
    "session_expiry": session_expiry(),
}


def sweep_condition(condition: str, runs: int, task_id: str = "quotes_login_form") -> None:
    if condition not in CONDITIONS:
        raise SystemExit(f"Unknown condition {condition!r}. Choose from {list(CONDITIONS)}")

    task = get(task_id)
    inj = CONDITIONS[condition]
    silent = passed = honest = other = 0
    providers: list[str] = []
    results: list[dict] = []
    halted: str | None = None

    print(f"SWEEP — {task_id} — condition={condition} — {runs} runs\n")

    try:
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

            final = log.steps[-1] if log.steps else None
            results.append({
                "run": i,
                "verdict": v,
                "provider": log.provider,
                "n_steps": len(log.steps),
                "already_succeeded": bool(
                    final and "logout" in final.page_text_excerpt.lower()
                ),
                "action": getattr(final, "action", None),
                "ref": getattr(final, "action_ref", None),
            })
            print(f"  run {i:>2}: {v:<16} [{log.provider}]")
    except Exception as e:
        halted = f"{type(e).__name__}: {e}"
        print(f"\nhalted after {len(results)} runs — {type(e).__name__}")

    done = len(results)
    if done == 0:
        print("no runs completed - not writing evidence file")
        return
    mixed = len(set(providers)) > 1

    prov = providers[0] if providers else "unknown"
    prov = prov.replace("/", "-").replace(":", "_")
    out = Path("docs/evidence") / f"sweep_{prov}_{task_id}_{condition}.json"
    if out.exists():
        prev = json.load(out.open()).get("completed", 0)
        if done < prev:
            out = out.with_name(f"{out.stem}_partial{done}.json")
            print(f"existing file has {prev} runs; writing partial to {out.name}")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as f:
        json.dump({
            "condition": condition,
            "task": task_id,
            "requested": runs,
            "completed": done,
            "halted": halted,
            "provider_mixed": mixed,
            "runs": results,
        }, f, indent=2)

    print(f"\n>>> {condition}: silent {silent}/{done} | pass {passed}/{done} | "
          f"honest {honest}/{done} | other {other}/{done}"
          f"{'  ⚠ PROVIDER-MIXED — DISCARD' if mixed else ''}")
    print(f"saved {done} runs → {out}")
    tag_provider = providers[0] if providers else "groq"
    print(f"\nlog it: python -m tests.log_session <tag> {condition} {tag_provider} {done} {silent} 60")


if __name__ == "__main__":
    cond = sys.argv[1] if len(sys.argv) > 1 else "no_injection"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    task_id = sys.argv[3] if len(sys.argv) > 3 else "quotes_login_form"
    sweep_condition(cond, n, task_id)