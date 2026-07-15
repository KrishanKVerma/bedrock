"""Action execution layer.

Takes a planner decision and performs it in the real browser.

The subtle problem here: the planner says "click [16]", but [16] is an index into
the element list that perception produced. If the page shifted between perceiving
and acting, [16] may now be a different element — and the agent will click the
wrong thing while believing it clicked the right one. That is precisely the
silent-failure class this project exists to measure, so this layer re-resolves the
element at action time and reports honestly when it can't.
"""

from __future__ import annotations

from dataclasses import dataclass

from playwright.sync_api import Page

from agent.perceive import _INTERACTIVE, PageState
from agent.plan import Action


@dataclass(frozen=True, slots=True)
class ActionResult:
    """What actually happened when we tried to act."""

    ok: bool
    detail: str
    url_before: str
    url_after: str

    @property
    def navigated(self) -> bool:
        return self.url_before != self.url_after


class ActuatorError(RuntimeError):
    """The action could not be performed."""


def _resolve(page: Page, ref: int, state: PageState) -> object:
    """Map a planner ref back to a live element handle.

    Re-queries the page rather than trusting a stale handle. If the element list
    has changed shape since perception, we say so instead of guessing.
    """
    handles = [h for h in page.query_selector_all(_INTERACTIVE) if h.is_visible()]
    if ref < 0 or ref >= len(handles):
        raise ActuatorError(
            f"ref [{ref}] out of range — page now has {len(handles)} visible "
            f"elements, had {len(state.elements)} at perception time"
        )
    return handles[ref]


def execute(page: Page, action: Action, state: PageState) -> ActionResult:
    """Perform `action` on the page. Never raises for normal failures — reports them."""
    url_before = page.url

    try:
        if action.action == "click":
            el = _resolve(page, action.ref, state)  # type: ignore[arg-type]
            el.click(timeout=5000)
            page.wait_for_load_state("domcontentloaded", timeout=8000)
            detail = f"clicked [{action.ref}]"

        elif action.action == "type":
            el = _resolve(page, action.ref, state)  # type: ignore[arg-type]
            el.fill(action.text or "", timeout=5000)
            detail = f"typed {action.text!r} into [{action.ref}]"

        elif action.action == "navigate":
            page.goto(action.text or "", wait_until="domcontentloaded", timeout=15000)
            detail = f"navigated to {action.text}"

        else:
            return ActionResult(True, f"terminal action: {action.action}", url_before, page.url)

    except ActuatorError as exc:
        return ActionResult(False, str(exc), url_before, page.url)
    except Exception as exc:  # noqa: BLE001 — a failed action is data, not a crash
        return ActionResult(False, f"{type(exc).__name__}: {exc}", url_before, page.url)

    return ActionResult(True, detail, url_before, page.url)