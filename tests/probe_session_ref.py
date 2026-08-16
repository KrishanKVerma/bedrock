"""Does session_expiry actually invalidate the session? No LLM calls."""

import json

from playwright.sync_api import sync_playwright

from agent.perceive import perceive
from harness.inject import session_expiry

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    pg = browser.new_page()
    pg.goto("https://quotes.toscrape.com/login")
    pg.fill("#username", "x")
    pg.fill("#password", "x")
    pg.click("input[type=submit]")
    pg.wait_for_load_state()

    before = perceive(pg)

    inj = session_expiry()
    print("fires here:", inj.should_fire(pg.url, 1, False), pg.url)
    print("applied:", inj.apply(pg))

    after = perceive(pg)

    b_el = json.dumps([repr(e) for e in before.elements])
    a_el = json.dumps([repr(e) for e in after.elements])
    print("elements identical:", b_el == a_el)
    print("n elements:", len(before.elements), "->", len(after.elements))
    print("BEFORE has Logout:", any("Logout" in repr(e) for e in before.elements))
    print("AFTER  has Logout:", any("Logout" in repr(e) for e in after.elements))
    print("AFTER  has Login: ", any("Login" in repr(e) for e in after.elements))

    browser.close()