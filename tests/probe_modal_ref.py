"""Does modal change anything the planner can see? No LLM calls."""

import json

from playwright.sync_api import sync_playwright

from agent.perceive import perceive
from harness.inject import modal

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    pg = browser.new_page()
    pg.goto("https://quotes.toscrape.com/login")
    pg.fill("#username", "x")
    pg.fill("#password", "x")
    pg.click("input[type=submit]")
    pg.wait_for_load_state()

    before = perceive(pg)

    inj = modal()
    print("fires here:", inj.should_fire(pg.url, 1, False), pg.url)
    print("applied:", inj.apply(pg))

    after = perceive(pg)

    b_el = json.dumps([repr(e) for e in before.elements])
    a_el = json.dumps([repr(e) for e in after.elements])
    print("elements identical:", b_el == a_el)
    print("n elements:", len(before.elements), "->", len(after.elements))
    print("text identical:", getattr(before, "page_text", None) == getattr(after, "page_text", None))

    for i, e in enumerate(after.elements[:6]):
        print(i, repr(e)[:90])

    browser.close()
    