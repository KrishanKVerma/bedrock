"""The harness.

Wraps the agent loop, records everything, and judges the outcome independently of
what the agent says about itself.

The key design point: the harness never asks the agent whether it succeeded. It
asks the page. The agent's claim is recorded as data to be checked, not as a
result to be trusted.
"""

from __future__ import annotations

from agent.act import execute
from agent.browser import BrowserSession
from agent.perceive import perceive
from agent.plan import PlannerError, plan
from harness.runlog import RunLog, StepTrace
from tasks.registry import Task


def run_task(task: Task, headless: bool = False, save: bool = True) -> RunLog:
    """Run one task under observation. Returns the full log."""
    log = RunLog(
        task_id=task.id,
        instruction=task.instruction,
        start_url=task.start_url,
        expectation=task.expect.describe(),
    )
    history: list[str] = []

    with BrowserSession(headless=headless) as session:
        session.goto(task.start_url)

        for n in range(1, task.max_steps + 1):
            state = perceive(session.page)

            try:
                action = plan(task.instruction, state, history)
            except PlannerError as exc:
                log.agent_outcome = "planner_error"
                log.agent_claim = str(exc)
                break

            if action.action in ("done", "fail"):
                log.agent_outcome = action.action
                log.agent_claim = action.reason
                break

            result = execute(session.page, action, state)

            log.add(
                StepTrace(
                    n=n,
                    url=state.url,
                    page_title=state.title,
                    elements_seen=len(state.elements),
                    page_text_excerpt=state.text[:300],
                    action=action.action,
                    action_ref=action.ref,
                    action_text=action.text,
                    planner_reason=action.reason,
                    result_ok=result.ok,
                    result_detail=result.detail,
                    url_after=result.url_after,
                )
            )
            history.append(f"{action.describe()} → {'ok' if result.ok else 'failed'}")
        else:
            log.agent_outcome = "budget_exhausted"
            log.agent_claim = f"stopped after {task.max_steps} steps"

        # Judge against the page, not against the agent's opinion of itself.
        log.final_url = session.page.url
        try:
            page_text = " ".join(session.page.inner_text("body").split())
        except Exception:  # noqa: BLE001
            page_text = ""

        met, reason = task.expect.check(log.final_url, page_text)
        log.expectation_met = met
        log.expectation_reason = reason

    log.finish()
    if save:
        log.save()
    return log