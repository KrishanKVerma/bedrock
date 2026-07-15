"""Perception layer.

Turns a live page into a compact, structured description an LLM can reason about.

Raw HTML is useless to a planner — it's mostly noise, and it blows the context
window. What the planner actually needs is: what can I interact with, what does
it say, and how do I refer to it later. That's what this produces.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

from playwright.sync_api import Page

# Elements an agent can actually act on.
_INTERACTIVE = (
    "a, button, input, textarea, select, "
    "[role=button], [role=link], [role=textbox], [onclick]"
)


@dataclass(frozen=True, slots=True)
class Element:
    """One interactive thing on the page."""

    ref: int          # stable handle the planner uses to refer to this element
    tag: str
    text: str         # visible label
    role: str | None
    name: str | None  # accessible name / aria-label / placeholder
    value: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def describe(self) -> str:
        label = self.text or self.name or self.value or ""
        label = label.strip()[:80]
        role = self.role or self.tag
        return f"[{self.ref}] {role}: {label!r}" if label else f"[{self.ref}] {role}"


@dataclass(frozen=True, slots=True)
class PageState:
    """Everything the planner knows about the page right now."""

    url: str
    title: str
    text: str               # visible page text, trimmed
    elements: list[Element]

    def to_prompt(self, max_text: int = 1500) -> str:
        """Render the page for an LLM. Compact by design."""
        body = self.text[:max_text]
        listing = "\n".join(e.describe() for e in self.elements)
        return (
            f"URL: {self.url}\n"
            f"TITLE: {self.title}\n\n"
            f"VISIBLE TEXT:\n{body}\n\n"
            f"INTERACTIVE ELEMENTS:\n{listing}"
        )


def perceive(page: Page, max_elements: int = 60) -> PageState:
    """Read the current page into a PageState.

    Only visible elements are included — an agent can't click what a user can't see,
    and hidden elements are a common source of confident wrong plans.
    """
    handles = page.query_selector_all(_INTERACTIVE)

    elements: list[Element] = []
    for h in handles:
        if len(elements) >= max_elements:
            break
        try:
            if not h.is_visible():
                continue
            text = (h.inner_text() or "").strip()
            name = (
                h.get_attribute("aria-label")
                or h.get_attribute("placeholder")
                or h.get_attribute("name")
            )
            elements.append(
                Element(
                    ref=len(elements),
                    tag=(h.evaluate("e => e.tagName") or "").lower(),
                    text=text,
                    role=h.get_attribute("role"),
                    name=name,
                    value=h.get_attribute("value"),
                )
            )
        except Exception:  # noqa: BLE001 — a stale/detached node must not kill perception
            continue

    try:
        body_text = page.inner_text("body")
    except Exception:  # noqa: BLE001
        body_text = ""

    return PageState(
        url=page.url,
        title=page.title(),
        text=" ".join(body_text.split()),
        elements=elements,
    )


if __name__ == "__main__":
    from agent.browser import BrowserSession

    with BrowserSession(headless=False) as s:
        s.goto("https://example.com")
        state = perceive(s.page)
        print(state.to_prompt())
