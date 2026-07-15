"""Manual check: can the agent complete a real multi-step task on its own?"""

from agent.loop import run

report = run(
    task="Find the top story on Hacker News and open its comments page.",
    start_url="https://news.ycombinator.com",
    max_steps=5,
)
print(report.describe())