"""Does dom_drift change anything the planner can see? No LLM calls."""

import json

from playwright.sync_api import sync_playwright

from agent.perceive import perceive
from harness.inject import dom_drift

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    pg = browser.new_page()
    pg.goto("https://quotes.toscrape.com/login")
    pg.fill("#username", "x")
    pg.fill("#password", "x")
    pg.click("input[type=submit]")
    pg.wait_for_load_state()

    before = perceive(pg)

    inj = dom_drift()
    print("fires here:", inj.should_fire(pg.url, 1, False), pg.url)
    print("applied:", inj.apply(pg))

    after = perceive(pg)

    b_el = json.dumps([repr(e) for e in before.elements])
    a_el = json.dumps([repr(e) for e in after.elements])
    print("elements identical:", b_el == a_el)
    print("n elements:", len(before.elements), "->", len(after.elements))

    b_txt = getattr(before, "page_text", None)
    a_txt = getattr(after, "page_text", None)
    print("text identical:", b_txt == a_txt)

    if b_el != a_el:
        for i, (x, y) in enumerate(zip(before.elements, after.elements)):
            if repr(x) != repr(y):
                print("first diff at", i, "\n  before:", repr(x)[:100], "\n  after: ", repr(y)[:100])
                break

    browser.close()