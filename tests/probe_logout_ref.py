"""Where does Logout sit after index_shift fires? No planner, no LLM calls."""

from playwright.sync_api import sync_playwright

from agent.perceive import perceive
from harness.inject import dom_reorder

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page()
    pg.goto("https://quotes.toscrape.com/login")
    pg.fill("#username", "x")
    pg.fill("#password", "x")
    pg.click("input[type=submit]")
    pg.wait_for_load_state()

    inj = dom_reorder()
    print("fires here:", inj.should_fire(pg.url, 1, False), pg.url)
    inj.apply(pg)

    state = perceive(pg)
    for i, e in enumerate(state.elements):
        print(i, repr(e)[:90])
    b.close()