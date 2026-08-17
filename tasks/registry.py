"""Task definitions.

A task is not just an instruction — it's an instruction plus a machine-checkable
definition of what success actually looks like.

That second part is the whole point. The agent will tell us it succeeded; the
expectation tells us whether it did. Without an independent success criterion,
"the agent said done" is the only signal available, and that signal is exactly
the one this project distrusts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal

TaskKind = Literal["search_extract", "form_fill"]


@dataclass(frozen=True, slots=True)
class Expectation:
    """A checkable definition of success, evaluated against the final page.

    Deliberately dumb: URL substrings and page text. Anything smarter would be
    another model making another judgement, and then the checker needs a checker.
    """

    url_contains: str | None = None
    text_contains: str | None = None
    text_absent: str | None = None
    custom: Callable[[str, str], bool] | None = None  # (url, page_text) -> bool

    def check(self, url: str, page_text: str) -> tuple[bool, str]:
        """Return (passed, reason)."""
        if self.url_contains and self.url_contains not in url:
            return False, f"URL missing {self.url_contains!r} (got {url})"
        if self.text_contains and self.text_contains.lower() not in page_text.lower():
            return False, f"page text missing {self.text_contains!r}"
        if self.text_absent and self.text_absent.lower() in page_text.lower():
            return False, f"page text unexpectedly contains {self.text_absent!r}"
        if self.custom and not self.custom(url, page_text):
            return False, "custom check failed"
        return True, "expectation met"

    def describe(self) -> str:
        parts = []
        if self.url_contains:
            parts.append(f"url contains {self.url_contains!r}")
        if self.text_contains:
            parts.append(f"text contains {self.text_contains!r}")
        if self.text_absent:
            parts.append(f"text absent {self.text_absent!r}")
        if self.custom:
            parts.append("custom check")
        return " AND ".join(parts) or "(no expectation)"


@dataclass(frozen=True, slots=True)
class Task:
    """One thing we ask the agent to do, and how we'll know if it really did it."""

    id: str
    kind: TaskKind
    instruction: str
    start_url: str
    expect: Expectation
    max_steps: int = 8

    def describe(self) -> str:
        return f"{self.id} [{self.kind}]: {self.instruction}"


# ---------- The task set ----------
# Public, stable, robots-friendly sites. Real pages, no auth, no scraping at volume.

TASKS: list[Task] = [
    Task(
        id="hn_top_comments",
        kind="search_extract",
        instruction="Open the comments page of the top story on Hacker News.",
        start_url="https://news.ycombinator.com",
        expect=Expectation(url_contains="item?id="),
    ),
    Task(
        id="hn_newest",
        kind="search_extract",
        instruction="Navigate to the 'new' section showing the newest submissions.",
        start_url="https://news.ycombinator.com",
        expect=Expectation(url_contains="newest"),
    ),
    Task(
        id="wiki_search",
        kind="search_extract",
        instruction="Search Wikipedia for 'Alan Turing' and open his article.",
        start_url="https://en.wikipedia.org",
        expect=Expectation(url_contains="Alan_Turing", text_contains="computer scientist"),
    ),
    Task(
        id="quotes_search_form",
        kind="form_fill",
        instruction=(
            "Search the site for quotes tagged 'humor' by using the tag link, "
            "then confirm humor quotes are shown."
        ),
        start_url="https://quotes.toscrape.com",
        expect=Expectation(url_contains="tag/humor"),
        max_steps=8,
    ),
    
    Task(
        id="quotes_login_form",
        kind="form_fill",
        instruction="Log in with username 'admin' and password 'admin'.",
        start_url="https://quotes.toscrape.com/login",
        expect=Expectation(text_contains="Logout"),
        max_steps=8,
    ),
    Task(
        id="add_element_analog",
        kind="form_fill",
        instruction="Click the 'Add Element' button to add one element to the page.",
        start_url="https://the-internet.herokuapp.com/add_remove_elements/",
        expect=Expectation(text_contains="Delete"),
        max_steps=8,
    ),
    Task(
        id="herokuapp_login_analog",
        kind="form_fill",
        instruction="Log in with username 'tomsmith' and password 'SuperSecretPassword!'.",
        start_url="https://the-internet.herokuapp.com/login",
        # True structural analog of quotes_login_form: multi-step, success triggers
        # a page transition to a secure area, and a Logout control sits on the new
        # page at a reachable ref. This tests the REFINED mechanism (multi-step +
        # transition), unlike add_element_analog which was single-click.
        expect=Expectation(text_contains="Logout", url_contains="secure"),
        max_steps=8,
    ),
        Task(
        id="element_count_tracking",
        kind="form_fill",
        instruction="Make sure there are exactly two elements on the page.",
        start_url="https://the-internet.herokuapp.com/add_remove_elements/",
        # State-tracking test. The page starts empty; each 'Add Element' click adds
        # one Delete button. The agent must count its own actions and stop at two.
        # Nothing is hidden and nothing is perturbed - the only difficulty is
        # tracking a count across steps and checking it against the page.
        expect=Expectation(custom=lambda url, text: text.count("Delete") == 2),
        max_steps=10,
    ),
]

BY_ID = {t.id: t for t in TASKS}


def get(task_id: str) -> Task:
    if task_id not in BY_ID:
        raise KeyError(f"Unknown task: {task_id}. Have: {sorted(BY_ID)}")
    return BY_ID[task_id]