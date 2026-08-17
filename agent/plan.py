"""Planning layer.

Given a task and what's currently on the page, decide the single next action.

The planner is deliberately constrained: it returns one structured decision, not
prose. Free-form output is how agents become unreliable — the parser breaks, or
worse, it half-works and the agent does something nobody intended. A fixed schema
means a bad plan fails loudly instead of quietly.

Provider policy: one model per measurement, never mixed. The provider AND the model
string that served each call are recorded on every run, so any result can be checked
after the fact. There is no automatic fallback: if the locked provider fails, the run
fails loudly rather than quietly continuing on a different brain.

The original instrument — Groq-served Llama-3.3-70B — was retired by the provider
mid-study. That arm is closed at 85 baseline runs and cannot be extended. Everything
measured on it stands; nothing can be added to it. This is the reason the model string
is recorded per run and not just the provider name.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Literal

from dotenv import load_dotenv
from groq import Groq
from openai import OpenAI

from agent.perceive import PageState

load_dotenv()

GROQ_MODEL = "openai/gpt-oss-120b"
OPENROUTER_MODEL = "meta-llama/llama-3.3-70b-instruct"
CEREBRAS_MODEL = "gpt-oss-120b"
GEMINI_MODEL = "gemini-3.5-flash"
MISTRAL_MODEL = "mistral-small-latest"

# Which provider AND model served the most recent call. Recorded into run logs.
last_provider: str = "none"

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


def _ask_groq(user: str) -> str:
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY not set.")
    r = Groq(api_key=key).chat.completions.create(
        model=GROQ_MODEL,
        temperature=0,
        messages=[{"role": "system", "content": _SYSTEM}, {"role": "user", "content": user}],
    )
    return r.choices[0].message.content or ""


def _ask_openrouter(user: str) -> str:
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY not set.")
    client = OpenAI(api_key=key, base_url="https://openrouter.ai/api/v1")
    r = client.chat.completions.create(
        model=OPENROUTER_MODEL,
        temperature=0,
        messages=[{"role": "system", "content": _SYSTEM}, {"role": "user", "content": user}],
    )
    return r.choices[0].message.content or ""


def _ask_cerebras(user: str) -> str:
    key = os.getenv("CEREBRAS_API_KEY")
    if not key:
        raise RuntimeError("CEREBRAS_API_KEY not set.")
    client = OpenAI(api_key=key, base_url="https://api.cerebras.ai/v1")
    r = client.chat.completions.create(
        model=CEREBRAS_MODEL,
        temperature=0,
        messages=[{"role": "system", "content": _SYSTEM}, {"role": "user", "content": user}],
    )
    return r.choices[0].message.content or ""


def _ask_gemini(user: str) -> str:
    import time

    from google import genai
    from google.genai import types

    # Free-tier rate limit is low; space the calls out rather than halting a sweep.
    time.sleep(6)

    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY not set.")
    client = genai.Client(api_key=key)
    r = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=user,
        config=types.GenerateContentConfig(
            system_instruction=_SYSTEM,
            temperature=0,
        ),
    )
    return r.text or ""


def _ask_mistral(user: str) -> str:
    key = os.getenv("MISTRAL_API_KEY")
    if not key:
        raise RuntimeError("MISTRAL_API_KEY not set.")
    client = OpenAI(api_key=key, base_url="https://api.mistral.ai/v1")
    r = client.chat.completions.create(
        model=MISTRAL_MODEL,
        temperature=0,
        messages=[{"role": "system", "content": _SYSTEM}, {"role": "user", "content": user}],
    )
    return r.choices[0].message.content or ""


_PROVIDERS = {
    "groq": (_ask_groq, lambda: GROQ_MODEL),
    "openrouter": (_ask_openrouter, lambda: OPENROUTER_MODEL),
    "cerebras": (_ask_cerebras, lambda: CEREBRAS_MODEL),
    "gemini": (_ask_gemini, lambda: GEMINI_MODEL),
    "mistral": (_ask_mistral, lambda: MISTRAL_MODEL),
}


def plan(task: str, state: PageState, history: list[str] | None = None) -> Action:
    """Decide the next action for `task` given the current page.

    temperature=0 - a planner that gives different answers to the same page is a
    planner you cannot debug. (Note: 0 reduces variance; it does not eliminate it.
    Non-determinism at temperature 0 is itself a finding this project records.)
    """
    global last_provider

    recent = (history or [])[-3:]
    past = "\n".join(f"- {h}" for h in recent) or "(nothing yet)"
    user = (
        f"TASK: {task}\n\n"
        f"ACTIONS ALREADY TAKEN:\n{past}\n\n"
        f"CURRENT PAGE:\n{state.to_prompt()}"
    )

    locked = os.getenv("BEDROCK_PROVIDER", "").lower()
    if locked not in _PROVIDERS:
        raise RuntimeError(
            f"BEDROCK_PROVIDER must be one of {sorted(_PROVIDERS)}; got {locked!r}. "
            "There is no default and no fallback: a measurement must name its model."
        )

    ask, model_of = _PROVIDERS[locked]
    raw = ask(user)
    last_provider = f"{locked}:{model_of()}"

    return _parse(raw)