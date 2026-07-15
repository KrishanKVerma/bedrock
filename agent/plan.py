"""Planning layer.

Given a task and what's currently on the page, decide the single next action.

The planner is deliberately constrained: it returns one structured decision, not
prose. Free-form output is how agents become unreliable — the parser breaks, or
worse, it half-works and the agent does something nobody intended. A fixed schema
means a bad plan fails loudly instead of quietly.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Literal

from dotenv import load_dotenv
from groq import Groq

from agent.perceive import PageState

load_dotenv()

_MODEL = "llama-3.3-70b-versatile"

ActionType = Literal["click", "type", "navigate", "done", "fail"]

_SYSTEM = """You are the planner for a browser agent. You are given a TASK, the \
current PAGE, and the ACTIONS ALREADY TAKEN. Decide the single next action.

Respond with ONLY a JSON object, no prose, no markdown fences:
{"action": "click"|"type"|"navigate"|"done"|"fail",
 "ref": <element number, or null>,
 "text": "<text to type, or URL to navigate to, or null>",
 "reason": "<one short sentence>"}

Rules:
- "click": press the element with that ref.
- "type": enter text into the element with that ref. Both ref and text required.
- "navigate": go to a URL. Put the URL in text.
- "done": the task is complete. Explain in reason what evidence shows this.
- "fail": the task cannot be completed from here. Explain why in reason.
- Only reference elements that appear in INTERACTIVE ELEMENTS.
- Do not repeat an action that already failed to change the page.
- Prefer the most direct route to the task. One step at a time."""


@dataclass(frozen=True, slots=True)
class Action:
    """One decision from the planner."""

    action: ActionType
    ref: int | None
    text: str | None
    reason: str

    def describe(self) -> str:
        if self.action == "click":
            return f"click [{self.ref}] — {self.reason}"
        if self.action == "type":
            return f"type {self.text!r} into [{self.ref}] — {self.reason}"
        if self.action == "navigate":
            return f"navigate to {self.text} — {self.reason}"
        return f"{self.action} — {self.reason}"


class PlannerError(RuntimeError):
    """The planner returned something we can't act on."""


def _client() -> Groq:
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY not set. Add it to .env (see .env.example).")
    return Groq(api_key=key)


def _parse(raw: str) -> Action:
    """Parse the model's JSON. Fail loudly — a malformed plan is a real signal."""
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        data: dict[str, Any] = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise PlannerError(f"Planner returned non-JSON: {raw[:200]!r}") from exc

    action = data.get("action")
    if action not in ("click", "type", "navigate", "done", "fail"):
        raise PlannerError(f"Unknown action: {action!r}")

    ref = data.get("ref")
    if ref is not None and not isinstance(ref, int):
        raise PlannerError(f"ref must be an int or null, got {ref!r}")

    if action in ("click", "type") and ref is None:
        raise PlannerError(f"Action {action!r} requires a ref")
    if action in ("type", "navigate") and not data.get("text"):
        raise PlannerError(f"Action {action!r} requires text")

    return Action(
        action=action,
        ref=ref,
        text=data.get("text"),
        reason=str(data.get("reason", "")).strip() or "(no reason given)",
    )


def plan(task: str, state: PageState, history: list[str] | None = None) -> Action:
    """Decide the next action for `task` given the current page.

    temperature=0 — a planner that gives different answers to the same page is
    a planner you cannot debug.
    """
    past = "\n".join(f"- {h}" for h in (history or [])) or "(nothing yet)"
    user = (
        f"TASK: {task}\n\n"
        f"ACTIONS ALREADY TAKEN:\n{past}\n\n"
        f"CURRENT PAGE:\n{state.to_prompt()}"
    )

    response = _client().chat.completions.create(
        model=_MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": user},
        ],
    )
    return _parse(response.choices[0].message.content or "")