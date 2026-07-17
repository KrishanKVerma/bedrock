"""Run logging.

Every run writes a complete, replayable trace to disk: what the agent saw, what it
decided, what it did, and what happened as a result.

This exists because a claim without a trace is an anecdote. When this project says
"the agent reported success on a task it had undone," there is a file that shows
exactly that, step by step, and anyone can read it.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

RUNS_DIR = Path("runs")


@dataclass(slots=True)
class StepTrace:
    """One turn of the loop, fully recorded."""

    n: int
    url: str
    page_title: str
    elements_seen: int
    page_text_excerpt: str
    action: str
    action_ref: int | None
    action_text: str | None
    planner_reason: str
    result_ok: bool
    result_detail: str
    url_after: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class RunLog:
    """The complete record of one agent run."""

    run_id: str = field(default_factory=lambda: f"run_{uuid.uuid4().hex[:8]}")
    task_id: str = ""
    instruction: str = ""
    start_url: str = ""
    expectation: str = ""
    injected: str = "none"
    provider: str = ""
    started_at: float = field(default_factory=time.time)
    steps: list[StepTrace] = field(default_factory=list)

    # what the agent says
    agent_outcome: str = ""
    agent_claim: str = ""

    # what actually happened
    final_url: str = ""
    expectation_met: bool = False
    expectation_reason: str = ""

    # the verdict that matters
    silent_failure: bool = False
    elapsed: float = 0.0

    def add(self, step: StepTrace) -> None:
        self.steps.append(step)

    def finish(self) -> None:
        """Compute the verdict. Silent failure = claimed success, reality disagrees."""
        self.elapsed = round(time.time() - self.started_at, 2)
        self.silent_failure = self.agent_outcome == "done" and not self.expectation_met

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["steps"] = [s.to_dict() for s in self.steps]
        return d

    def save(self, directory: Path = RUNS_DIR) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{self.task_id}_{self.run_id}.json"
        path.write_text(json.dumps(self.to_dict(), indent=2))
        return path

    def summary(self) -> str:
        if self.silent_failure:
            verdict = "SILENT FAILURE"
        elif self.expectation_met:
            verdict = "pass"
        else:
            verdict = "fail (reported honestly)"
        return (
            f"{self.task_id} | {len(self.steps)} steps | "
            f"agent={self.agent_outcome} | reality={'met' if self.expectation_met else 'not met'} "
            f"| {verdict}"
        )


def load(path: str | Path) -> dict[str, Any]:
    """Read a saved run back. Replay starts here."""
    return json.loads(Path(path).read_text())