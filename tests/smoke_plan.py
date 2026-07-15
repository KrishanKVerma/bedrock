"""Manual check: can the planner pick a sensible first action?"""

from agent.browser import BrowserSession
from agent.perceive import perceive
from agent.plan import plan

TASK = "Find the top story on Hacker News and open its comments."

with BrowserSession(headless=False) as s:
    s.goto("https://news.ycombinator.com")
    state = perceive(s.page)
    action = plan(TASK, state)
    print("TASK:", TASK)
    print("PLAN:", action.describe())
    print("RAW:", action)