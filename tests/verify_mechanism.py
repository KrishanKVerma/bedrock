"""Mechanism verification.

Claim: silent failure = the agent had ALREADY satisfied the task, then took one
extra step that undid it. Prediction: on every silent-failure run, the page state
at the start of the final (undo) step already shows success ("Logout" present),
and the final action clicks it away.

Passing runs are labeled too, as a contrast class. Note: passes terminate ON the
success-producing action (click[4]=Login), so already_succeeded=False for them is
partly definitional — the real content of the contrast is that silent runs take
one step BEYOND the terminal action.
"""

import json
import sys

from harness.runner import run_task
from tasks.registry import get

SESSIONS = int(sys.argv[1]) if len(sys.argv) > 1 else 1

task = get("quotes_login_form")
results = []
silent_total = confirmed = 0
pass_total = pass_already = 0
halted = None

try:
    for s in range(1, SESSIONS + 1):
        for i in range(1, 11):
            log = run_task(task, headless=True)
            final = log.steps[-1]
            # labeled for EVERY run, independent of outcome
            already_succeeded = "logout" in final.page_text_excerpt.lower()
            clicked = final.action == "click"

            if log.silent_failure:
                silent_total += 1
                verdict = already_succeeded and clicked
                confirmed += int(verdict)
                tag = f"SILENT | mechanism_holds={verdict}"
            else:
                pass_total += 1
                pass_already += int(already_succeeded)
                tag = "ok"

            results.append({
                "session": s,
                "run": i,
                "silent": log.silent_failure,
                "already_succeeded": already_succeeded,
                "action": final.action,
                "ref": final.action_ref,
            })
            print(f"s{s} run {i:>2}: {tag} | already_succeeded={already_succeeded} "
                  f"| final={final.action}[{final.action_ref}]")
except Exception as e:
    halted = f"{type(e).__name__}: {e}"
    print(f"\nhalted after {len(results)} runs — {type(e).__name__}")

with open("docs/evidence/mechanism_runs.json", "w") as f:
    json.dump({"halted": halted, "runs": results}, f, indent=2)

print(f"\nsilent: {confirmed}/{silent_total} mechanism holds")
print(f"passes: {pass_already}/{pass_total} also reached success state before final step")
print(f"saved {len(results)} runs → docs/evidence/mechanism_runs.json")