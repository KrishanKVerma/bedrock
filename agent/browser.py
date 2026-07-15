"""Browser control layer.

Wraps Playwright. Everything that touches the actual browser lives here,
so the agent loop above it stays testable and the failure modes stay visible.
"""

from __future__ import annotations

from playwright.sync_api import Browser, Page, sync_playwright


class BrowserSession:
    """A live browser session the agent can drive."""

    def __init__(self, headless: bool = False) -> None:
        self._headless = headless
        self._pw = None
        self._browser: Browser | None = None
        self.page: Page | None = None

    def start(self) -> Page:
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=self._headless)
        self.page = self._browser.new_page()
        return self.page

    def goto(self, url: str) -> None:
        if self.page is None:
            raise RuntimeError("Session not started. Call start() first.")
        self.page.goto(url, wait_until="domcontentloaded")

    def title(self) -> str:
        if self.page is None:
            raise RuntimeError("Session not started.")
        return self.page.title()

    def html(self) -> str:
        if self.page is None:
            raise RuntimeError("Session not started.")
        return self.page.content()

    def stop(self) -> None:
        if self._browser:
            self._browser.close()
        if self._pw:
            self._pw.stop()

    def __enter__(self) -> "BrowserSession":
        self.start()
        return self

    def __exit__(self, *exc) -> None:
        self.stop()


if __name__ == "__main__":
    with BrowserSession(headless=False) as s:
        s.goto("https://example.com")
        print("TITLE:", s.title())
        print("HTML LENGTH:", len(s.html()))
