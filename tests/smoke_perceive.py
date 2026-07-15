"""Quick manual check: does perception hold up on a busy real page?"""

from agent.browser import BrowserSession
from agent.perceive import perceive

with BrowserSession(headless=False) as s:
    s.goto("https://news.ycombinator.com")
    print(perceive(s.page).to_prompt()[:2000])