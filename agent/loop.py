"""The agent loop.

perceive → plan → act → repeat, until the planner says done, the budget runs out,
or something breaks.

Note what this loop does NOT do: check whether the action achieved what the plan
intended. It acts and assumes, exactly like most browser agents. That is deliberate
— this is the baseline we are going to measure. VERIFY comes after we have numbers
proving why it's needed.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from agent.act import ActionResult, execute
from agent.browser import BrowserSession
from agent.perceive import perceive
from agent.plan import Action, PlannerError, plan


@dataclass(slots=True)
class Step:
    """One turn of the loop."""

    n: int
    action: Action
    result: ActionResult

    def describe(self) -> str:
        mark = "ok" if self.result.ok else "FAILED"
        return f"  {self.n}. {self.action.describe()}  →  {mark}: {self.result.detail}"


@dataclass(slots=True)
class RunReport:
    """Everything that happened in one run."""

    task: str
    start_url: str
    steps: list[Step] = field(default_factory=list)
    outcome: str = "incomplete"
    claim: str = ""
    final_url: str = ""

    def describe(self) -> str:
        lines = [
            f"TASK: {self.task}",
            f"START: {self.start_url}",
            "STEPS:",
            *(s.describe() for s in self.steps),
            f"OUTCOME: {self.outcome}",
            f"AGENT CLAIMS: {self.claim}",
            f"FINAL URL: {self.final_url}",
        ]
        return "\n".join(lines)


def run(task: str, start_url: str, max_steps: int = 8, headless: bool = False) -> RunReport:
    """Run `task` starting from `start_url`. Returns what happened."""
    report = RunReport(task=task, start_url=start_url)
    history: list[str] = []

    with BrowserSession(headless=headless) as session:
        session.goto(start_url)

        for n in range(1, max_steps + 1):
            state = perceive(session.page)

            try:
                action = plan(task, state, history)
            except PlannerError as exc:
                report.outcome = "planner_error"
                report.claim = str(exc)
                break

            if action.action in ("done", "fail"):
                report.outcome = action.action
                report.claim = action.reason
                break

            result = execute(session.page, action, state)
            report.steps.append(Step(n=n, action=action, result=result))
            history.append(f"{action.describe()} → {'ok' if result.ok else 'failed'}")

            if not result.ok:
                # A failed action is not fatal — the planner may route around it.
                continue
        else:
            report.outcome = "budget_exhausted"
            report.claim = f"stopped after {max_steps} steps"

        report.final_url = session.page.url

    return report