"""Diagnostic: is the login silent failure real, or a perception-config artifact?"""

from harness.runner import run_task
from tasks.registry import get

task = get("quotes_login_form")
for i in range(1, 6):
    log = run_task(task, headless=True)
    print(f"run {i}: {log.summary()}")