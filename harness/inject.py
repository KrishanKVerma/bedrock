"""Failure-mode injection.

Production doesn't wait politely for an agent to finish. Buttons move, classes get
renamed, elements appear and disappear between the moment the agent looks and the
moment it acts. Benchmarks never do this, which is why benchmark scores don't
survive contact with real sites.

So the harness manufactures the chaos rather than hoping for it.

Injectors are deliberately crude — real JS mutations on the live page, not mocks.
An agent that only survives simulated drift hasn't proven anything.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal

from playwright.sync_api import Page

InjectionKind = Literal["none", "dom_drift", "modal"]


@dataclass(frozen=True, slots=True)
class Injection:
    """One way to break the page mid-run."""

    kind: InjectionKind
    at_step: int  # inject before this step number (1-indexed)
    apply: Callable[[Page], str]  # returns a description of what it did

    def describe(self) -> str:
        return f"{self.kind} at step {self.at_step}"


NO_INJECTION = Injection(kind="none", at_step=0, apply=lambda p: "none")


# ---------- DOM selector drift ----------


def _drift(page: Page) -> str:
    """Rename classes and ids on interactive elements.

    This is what a site redeploy looks like to an agent: the page is visually
    identical, the labels are identical, but every hook the agent might have
    latched onto is now different. A human notices nothing. An agent that keyed
    on structure breaks.
    """
    changed = page.evaluate(
        """() => {
            const els = document.querySelectorAll(
                'a, button, input, textarea, select, [role=button], [role=link]'
            );
            let n = 0;
            els.forEach((el, i) => {
                if (el.className && typeof el.className === 'string') {
                    el.className = 'drifted-' + i + '-' + Math.random().toString(36).slice(2, 7);
                    n++;
                }
                if (el.id) {
                    el.id = 'drift_' + i;
                    n++;
                }
                if (el.hasAttribute('data-test')) {
                    el.setAttribute('data-test', 'drift-' + i);
                    n++;
                }
            });
            return n;
        }"""
    )
    return f"renamed class/id/data-test on {changed} attributes"


def dom_drift(at_step: int = 2) -> Injection:
    return Injection(kind="dom_drift", at_step=at_step, apply=_drift)


# ---------- Reorder: the harder version of drift ----------


def _reorder(page: Page) -> str:
    """Insert hidden-then-shown decoy links at the top of the DOM.

    Shifts every element index after them. The page looks nearly the same to a
    human; every ref the agent holds is now off by N. This is the failure our own
    diagnostic implicated: an agent that says "click [1]" is trusting an index it
    has no reason to trust.
    """
    n = page.evaluate(
        """() => {
            const body = document.body;
            let added = 0;
            for (let i = 0; i < 3; i++) {
                const a = document.createElement('a');
                a.href = '#';
                a.textContent = 'Sponsored';
                a.style.cssText = 'display:inline-block;padding:2px;font-size:11px;opacity:0.6';
                body.insertBefore(a, body.firstChild);
                added++;
            }
            return added;
        }"""
    )
    return f"inserted {n} decoy links at top of DOM (all refs shift by {n})"


def dom_reorder(at_step: int = 2) -> Injection:
    return Injection(kind="dom_drift", at_step=at_step, apply=_reorder)