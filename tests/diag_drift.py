"""Diagnostic: does the agent survive the page changing under it?

Injects at step 4 - the post-login page, where the agent sees 60 elements and
picks a ref. Injecting earlier hits the 7-element login page, which is discarded
on navigation and proves nothing.
"""

from harness.inject import NO_INJECTION, dom_drift, dom_reorder
from harness.runner import run_task
from tasks.registry import get

task = get("quotes_login_form")

for label, inj in [
    ("no injection ", NO_INJECTION),
    ("class/id drift", dom_drift(at_step=4)),
    ("index shift   ", dom_reorder(at_step=4)),
]:
    print(f"\n--- {label} ---")
    for i in range(1, 4):
        log = run_task(task, headless=True, injection=inj)
        print(f"  run {i}: {log.summary()}")