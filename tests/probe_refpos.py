"""Isolation probe: does the Logout link's ref position drive the silent failure?

For every silent-failure run, record the ref of the final click (the self-undo)
and how many elements were visible when it happened. If the undo consistently lands
on a low ref, ref-position is directly implicated.
"""

from harness.runner import run_task
from tasks.registry import get

task = get("quotes_login_form")
sf_refs = []

for i in range(1, 11):
    log = run_task(task, headless=True)
    last_click_ref = None
    last_elems = None
    for s in log.steps:
        if s.action == "click":
            last_click_ref = s.action_ref
            last_elems = s.elements_seen
    tag = "SILENT" if log.silent_failure else "ok"
    print(f"run {i:>2}: {tag:<7} last_click_ref={last_click_ref} elems_at_click={last_elems} steps={len(log.steps)}")
    if log.silent_failure:
        sf_refs.append(last_click_ref)

print(f"\nsilent failures: {len(sf_refs)}/10")
print(f"refs the agent clicked to undo itself: {sf_refs}")
print("→ consistently low (0-2) = ref-position directly implicated")