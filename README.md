# bedrock

**A browser agent, and a harness that checks whether it actually did the task.**

The agent loop is commoditized. Knowing whether the loop worked is not. Bedrock builds
both, then measures the gap between what an agent reports and what actually happened.

---

## The claim

**An agent's account of its own work is not evidence of what it did.** Across 160 runs on
four tasks and two models, there was not one instance of an agent reporting that it could
not do the job. Every failure was reported as a success.

The clearest case: a login task where the agent enters credentials, submits, succeeds —
then observes the "Logout" link, correctly identifies it as evidence of success, and
clicks it, logging itself out. It reports success. Nothing errors. The only thing that
catches it is an independent check against real end state, defined before the run and
never shown to the agent.

The reasoning on that final step is *correct*:

```
1 type  2  | need to enter username
2 type  3  | need to enter password
3 click 4  | Login button is now ready to be clicked
4 click 1  | Logout link is present, indicating a successful login
```

The agent identifies the right evidence and draws the right conclusion. Then it clicks
the evidence away. Not a perception failure and not a capability failure — a correct
inference that terminates in an action instead of a stop.

---

## Results

**The mechanism is deterministic where the rate is not.** On the login task, 33/85 (39%)
silent failures across 8 sessions, with the rate swinging 10%–67% between sessions at
temperature 0. But across 112 instrumented runs there is **not one exception** to the
signature: a pass takes exactly 3 steps and ends on ref[4]; a silent failure takes exactly
4 and ends on ref[1]. A benchmark reporting only the rate would read a deterministic
failure as noise.

**Verified by prediction, not inspection (N=17).** Every silent failure had already
reached the success state at the start of its final step, then clicked it away. 17/17.
Step budget ruled out: raising `max_steps` 8→12 changed nothing — the agent never used
more than 4 of 12.

**One intervention removes it, and not by fixing anything.** Inserting three decoy links
moves Logout from ref[1] to ref[4] and changes nothing else — same element, still visible,
still labelled, still clickable. Rate goes to **0/26**. Verified by a probe with no model
calls. Note what that means: the failure didn't go away, the target did. An agent that
still doesn't know it's finished, but whose destructive control has moved, looks reliable
until the page layout changes.

**Reliability is a property of the task/model pair, not the model.** Same harness, same
config:

| Task | Mistral Small | gpt-oss-120b |
|---|---|---|
| login | 0/20 | 0/20 |
| element count | 18/20 | 20/20 |
| dynamic controls | 20/20 | 19/20 |
| delete to one | 12/20 | 2/20 |

77/80 silent on the two tasks where both models fail. **Neither model dominates** —
gpt-oss is worse on element count and dramatically better on delete-to-one. There is no
ordering, only pairs. Which also means the login task, where this project's headline
mechanism lives, is the *outlier*: it's the one task these models reliably pass.

**Two more failure classes, found by widening the task set.**

*Weak-evidence verification* — the agent checks its work against a signal that doesn't
discriminate. Under session expiry it concludes success because "the page shows quotes,"
which is true logged-in or logged-out. On an async task it reports an input enabled while
the page still reads "Enabling…" — asserting a transition it never waited to observe.

*State-tracking failure* — asked to leave exactly two elements on a page, the agent clicks
Add seven times, each step reasoning "add another to verify there are exactly two," then
claims exactly two are visible.

**Modal is a barrier, not a fix.** With a blocking overlay, 0/20 silent — but 3 of those
runs still *chose* the self-undo and the overlay intercepted the click. On one of them the
agent then reported *failure* on a run that had succeeded. The self-report is decoupled
from reality in both directions.

---

## Walk-backs

Four claims retracted publicly, with the data kept in the repo.

**1. A variance figure that belonged to the instrument.** Early sessions read 80%, 33%,
30%, 50% and looked like dramatic non-determinism. The perception config had been tuned
between runs, re-indexing the element list and moving the destructive element out of
reach. The instability was mine.

**2. A generalisation claim that failed its own test.** Two purpose-built analogs — one
single-click, one multi-step with a page transition — both returned 0/10. The mechanism
reproduced on one task only. That non-reproducibility is itself the argument for post-hoc
checks: you cannot write the check before you've seen the failure.

**3. Injection results measured against the wrong page.** The trigger matched
`quotes.toscrape.com/`, which also matches `/login`. Every injection fired on the login
page and was spent before the agent reached the page the failure lives on. Two full
conditions measured a perturbation that never arrived.

**4. The harness told the agent it had been tampered with.** After fixing (3), the runner
still appended the injection's own description to the planner's prompt. Under every
injection the agent was warned, in plain English, on exactly the step where the failure
would otherwise occur. Three conditions returned zero silent failures because of it.

**The harness has caught five of its own measurement errors before any reached a claim.**
The fifth: the original mechanism-verification script evaluated the success signature only
inside the silent-failure branch, so it could only ever print 100%. *A verification that
cannot return a negative is not a verification.*

Every one of those errors made the numbers *more* interesting, not less.

---

## Built vs not built

**Built.** An independent postcondition checker — a criterion defined in advance,
evaluated against real end state, never shown to the agent, never trusting its report.
Replayable per-run traces recording the element clicked, step count, planner reasoning,
and the provider *and model string* that served each call.

**Not built.** Decision-time action scoring. Nothing enumerates the available actions and
scores them for reversibility *before* the agent acts. Every failure here was diagnosed
post hoc from traces. Knowing that silent failures take one step past success and click
the same element does not mean anything in the loop notices at the time.

That gap is the obvious next thing to build, and the measured mechanism gives it a narrow
first target: flag actions that revert the postcondition the agent is working toward.

---

## The instrument was retired mid-study

Groq removed `llama-3.3-70b-versatile` from its API while this project was running. Every
number in the mechanism section was measured on it. **That arm is closed at 85 runs and
cannot be extended**, and the planned hardening phase — add a fix, measure before and
after — is no longer possible, because no available model exhibits the failure to fix.

Stated rather than hidden, because it is the sharpest available illustration of what this
repo argues: a reliability number measured on a provider-hosted model is contingent on
something the provider can delete without notice, and a benchmark published one month may
be unreproducible the next. Archived traces are in `docs/evidence/`.

---

## Reproduce it

Requires Python 3.11+ and a free Groq API key (console.groq.com).

```bash
git clone https://github.com/KrishanKVerma/bedrock && cd bedrock
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt && playwright install chromium
echo "GROQ_API_KEY=your_key" > .env
```

**Fastest path to the finding** — reproduces today:

```bash
BEDROCK_PROVIDER=groq python -m harness.sweep no_injection 20 element_count_tracking
```

Expect ~20/20 silent failures: the agent overshoots the target count and reports success
anyway, every time, with no honest failures.

**The login task**, which the retired model failed at 39% and current models pass:

```bash
BEDROCK_PROVIDER=groq python -m harness.sweep no_injection 20
```

Expect 0/20. This is the honest state of things: **the harness reproduces, the headline
rate does not.** For the original behaviour, read the archived traces —
`docs/evidence/mechanism_llama_selfundo.json` for the self-undo, and
`mechanism_mistral_stops.json` for the same observation producing the opposite action.

The model is set by `GROQ_MODEL` in `agent/plan.py`; providers are selected with
`BEDROCK_PROVIDER` (groq · mistral · gemini · openrouter · cerebras). There is no
fallback — a measurement must name its model.

Every sweep writes per-run evidence to `docs/evidence/`. A sweep halted by a rate limit
saves what it completed; one that completes zero runs writes nothing.

---

## Voice

```bash
BEDROCK_PROVIDER=mistral python -m voice.listen
```

Speech selects from a fixed set of registered tasks and reports the agent's claim
alongside the independent check. It never turns arbitrary speech into arbitrary browser
actions — given what the rest of this repo demonstrates, narrowing what an agent can be
asked to do is the defensible direction.

---

## Stack

Python 3 · Playwright · one model per measurement, provider and model recorded per run.
No agent framework — built directly on Playwright and an LLM so the failure modes are
visible rather than buried under abstraction.

---

## Depth

- [docs/failure-taxonomy.md](docs/failure-taxonomy.md) — every mode, every denominator,
  every retraction, in full
- [docs/generality.md](docs/generality.md) — where the mechanism did and didn't reproduce
- [docs/architecture.md](docs/architecture.md) — how the agent and harness fit together
- `docs/evidence/` — raw per-run data for every number on this page. Authoritative.
  `docs/sessions.json` covers early sessions only and is superseded by it.

---

## Status

| | |
|---|---|
| Silent failure | Measured — 33/85, mechanism verified N=17 |
| Weak-oracle pass | Documented, two instances |
| Non-determinism | Measured — 10%–67% across 8 sessions |
| DOM selector drift | Measured — 9/20, shown to be a **no-op** for this agent |
| Modal interruption | Measured — 0/20, self-undo attempted 3× and blocked |
| Rate-limit cliff | Documented |
| Session expiry | Measured — 2/20 silent, 18/20 honest |
| Weak-evidence verification | Measured — 20/20, 19/20 |
| State-tracking failure | Measured — 18/20, 20/20, 12/20, 2/20 |
| Cross-model replication | Done — 3 models |
| Voice control | Built |
| Irreversibility | **Not observed** — task surface didn't elicit it |
| Rate-limit recovery | **Not measured** — needs retry logic the agent lacks |
| Hardening before/after | **Not possible** — no live model exhibits the failure |
| Decision-time action scoring | **Not built** — next |

---

*Built by [Krishan Kumar Verma](https://github.com/KrishanKVerma).*