"""Voice entry point. Speech -> registered task -> the existing agent loop.

Accessibility layer, not a research component. The reliability work upstream is
unchanged; this only changes how the instruction arrives.

Deliberate constraint: speech selects from a fixed set of registered tasks. It never
becomes a free-form instruction. Turning arbitrary speech into arbitrary browser
actions is a real safety problem and is out of scope here - the point of this project
is that you cannot trust an agent's account of what it did, which argues for narrowing
what it can be asked to do, not widening it.
"""

import speech_recognition as sr

from harness.runner import run_task
from tasks.registry import get

# Spoken phrase -> registered task id. Longest-match-first is not needed while the
# keys are this distinct, but keep them unambiguous if you add more.
TASKS = {
    "log in": "quotes_login_form",
    "login": "quotes_login_form",
    "count": "element_count_tracking",
    "elements": "element_count_tracking",
    "controls": "herokuapp_dynamic_controls",
    "dynamic": "herokuapp_dynamic_controls",
}


def listen() -> str:
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=0.5)
        print("listening...")
        audio = r.listen(source, timeout=10, phrase_time_limit=15)
    return r.recognize_google(audio)


def match_task(said: str) -> str | None:
    said = said.lower()
    return next((task_id for phrase, task_id in TASKS.items() if phrase in said), None)


if __name__ == "__main__":
    said = listen()
    print("heard:", said)

    task_id = match_task(said)
    if task_id is None:
        known = sorted(set(TASKS.values()))
        raise SystemExit(f"No registered task matches {said!r}.\nKnown tasks: {known}")

    print("running:", task_id)
    log = run_task(get(task_id), headless=True)

    # The same two lines the whole project is about: what the agent says, and what
    # an independent check against the real end state found.
    print("agent claim:      ", log.agent_claim)
    print("independent check:", log.expectation_met, "-", log.expectation_reason)
    if log.silent_failure:
        print("\nSILENT FAILURE - the agent reported success and the check disagreed.")