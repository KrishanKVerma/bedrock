# bedrock

**A browser agent, and a harness that checks whether it actually did the task.**

The agent loop is commoditized. Knowing whether the loop worked is not. Bedrock builds
both, then measures the gap between what an agent reports and what actually happened.

---

## The claim

A browser agent completes its task, takes one more locally reasonable action that
invalidates it, and reports success.

On a login task the agent enters credentials, submits, and succeeds. It then observes
the "Logout" link — correct evidence that it succeeded — and clicks it, logging itself
out. It reports success. Nothing errors. The only thing that catches it is an
independent check against the real end state, defined before the run and never shown to
the agent.

The reasoning on that final step is *correct*:

```
1 type  2  | need to enter username
2 type  3  | need to enter password
3 click 4  | Login button is now ready to be clicked
4 click 1  | Logout link is present, indicating a successful login
```

The agent identifies the right evidence and draws the right conclusion. Then it clicks
the evidence away. This is not a perception failure or a capability failure. It is a
**stop-condition failure**: a correct inference that terminates in an action instead of
a stop.

---

## Results

**Mechanism, verified by prediction (N=17).** Every silent failure took exactly one step
past the terminal action and clicked the same element: 4 steps, ref[1]. Every passing run
stopped *on* the terminal action: 3 steps, ref[4]. 17/17, with 0/36 in the contrast
class — though that contrast is partly definitional, since a pass by construction ends at
the step that creates success.

**Rate: 33/85 (39%) across 8 sessions, spread 10%–67%.** Same model, same task, same
config, temperature 0. Per session: 4/10, 4/10, 3/13, 4/10, 1/10, 5/10, 8/12, 8/20.

**The rate moves; the mechanism doesn't.** Across 112 instrumented runs there is not one
exception to the 3-step/4-step, ref[4]/ref[1] split. A benchmark reporting only the rate
would read a deterministic failure as noise.

**Step budget ruled out.** Raising `max_steps` from 8 to 12 changed nothing — the agent
never used more than 4 of its 12 steps. It is not running until it hits a ceiling; it
takes exactly one step past the terminal action and halts on its own.

**One intervention removes it.** Inserting three decoy links, which moves Logout from
ref[1] to ref[4] and changes nothing else, takes the rate to 0/26. The element is still
present, visible, labelled, and clickable. Only its position in an enumerated list
changed. Verified by a direct probe with no model calls
(`tests/probe_logout_ref.py`).

**Not universal across models.** Same task, same harness, same config:

| Model | Silent failures |
|---|---|
| Llama-3.3-70B (Groq) | 33/85 (39%) |
| Mistral Small | 0/20 |
| gpt-oss-120b | 0/20 |

Mistral, seeing the identical element list with Logout at the identical ref[1], reports:
*"The page shows 'Logout' in the visible text, indicating successful login"* — and stops.
The same observation, the opposite action. That contrast is what rules out positional
bias as the cause: a low-ref pull would pull on both models.

**But "reliable model" is not a thing.** On a second task — click a button until exactly
two elements exist — the two models that score 0/20 on login score 18/20 and 20/20 silent.
Zero honest failures across 40 runs on that task. Reliability is a property of the
task/model pair, not the model.

---

## Walk-backs

Four claims retracted, publicly, with the data kept in the repo.

**1. A variance figure that belonged to the instrument.** Early sessions read 80%, 33%,
30%, 50% and looked like dramatic non-determinism. The perception config had been tuned
between runs — element count moved between 30 and 60, which re-indexed the list and moved
the destructive element out of easy reach. The instability was mine, not the agent's.
Retracted, config locked, re-measured.

**2. A generalisation claim that failed its own test.** The mechanism was claimed to
generalise. Two purpose-built analogs — a single-click task and a multi-step task with a
page transition — both returned 0/10. It reproduced on one task only. The
non-reproducibility is itself the argument for post-hoc checks: you cannot enumerate the
failure modes in advance well enough to check for them specifically.

**3. Injection results measured against the wrong page.** The injection trigger matched
`quotes.toscrape.com/`, which also matches `quotes.toscrape.com/login`. Every injection
fired on the login page and was spent before the agent reached the page the failure lives
on. Two full conditions measured a perturbation that never arrived. Caught only because
per-run evidence recorded which element was clicked.

**4. The harness told the agent it had been tampered with.** After fixing (3), the runner
still appended the injection's own description to the planner's prompt: *"[harness
injected dom_drift: renamed class/id/data-test on 41 attributes]"*. So under every
injection the agent was warned, in plain English, on exactly the step where the failure
would otherwise occur. Three conditions returned zero silent failures because of it. With
the leak closed, one of them returned straight to baseline.

**The harness has caught five of its own measurement errors before any of them reached a
claim.** The fifth: the original mechanism-verification script evaluated the
success-signature only inside the silent-failure branch, so it could only ever print
100%. A verification that cannot return a negative is not a verification.

Every error made the numbers *more* interesting, not less. That is the pattern worth
noticing.

---

## Built vs not built

**Built.** An independent postcondition checker. It evaluates a criterion defined in
advance against the real page state after the run, never shown to the agent, and never
trusts the agent's own report. Replayable per-run traces recording the element clicked,
step count, planner reasoning, and the model that served each call.

**Not built.** Decision-time action scoring. Nothing in the loop enumerates the available
actions and scores them for reversibility *before* the agent acts. Every failure here was
diagnosed post hoc from traces. Knowing that silent failures take one step past success
and click the same element does not mean anything in the loop notices that at the time.

That gap is the obvious next thing to build, and the observed mechanism gives it a narrow
first target: flag actions that revert the postcondition the agent is working toward.

---

## Status

| Mode | Status |
|---|---|
| Silent failure | Measured — 33/85, mechanism verified N=17 |
| Weak-oracle pass | Documented, one instance |
| Non-determinism | Measured — 10%–67% across 8 sessions |
| DOM selector drift | Measured — 9/20, and shown to be a **no-op** for this agent |
| Modal interruption | Measured — 0/20, self-undo attempted 3 times and physically blocked |
| Rate-limit cliff | Documented, hit repeatedly |
| Login / session expiry | Measured on Mistral — 2/20 silent, 18/20 honest |
| Element-count tracking | Measured — 18/20 (Mistral), 20/20 (gpt-oss) |
| Rate-limit recovery | Not measured |
| Irreversibility | Not measured |

Two results worth reading closely. **DOM drift changes nothing the agent can see** — a
probe confirms the perceived element list and page text are byte-identical before and
after 41 attributes are renamed. It breaks agents that key on selectors; this one keys on
text and position. **Modal blocks the consequence, not the decision** — in 3 of 20 runs
the agent still chose to click Logout and the overlay intercepted the click. On one of
those it then reported failure on a run that had actually succeeded. The self-report is
decoupled from reality in both directions.

---

## The instrument was retired mid-study

Groq removed `llama-3.3-70b-versatile` from its API while this project was running. Every
headline number above was measured on it. **That arm is closed at 85 runs and cannot be
extended.** The planned hardening phase — add a fix, measure before and after — is no
longer possible, because no available model exhibits the failure to fix.

This is worth stating rather than hiding. A reliability study whose substrate was deleted
by the provider mid-measurement is the sharpest available illustration of what this repo
argues: agent reliability numbers are contingent on a moving base, and a benchmark
published one month may be unreproducible the next. The archived traces remain in
`docs/evidence/`.

---

## Reproduce it

Requires Python 3.11+ and a free Groq API key (console.groq.com).

```bash
git clone https://github.com/KrishanKVerma/bedrock && cd bedrock
python -m venv venv && source venv/bin/activate
pip install -e . && playwright install chromium
echo "GROQ_API_KEY=your_key" > .env
```

**Fastest path to the finding** — the element-count task, which reproduces today:

```bash
BEDROCK_PROVIDER=groq python -m harness.sweep no_injection 20 element_count_tracking
```

Expect ~20/20 silent failures: the agent overshoots the target count and reports success
anyway, every time, with no honest failures.

**The login task**, which the archived model failed at 39% and current models pass:

```bash
BEDROCK_PROVIDER=groq python -m harness.sweep no_injection 20
```

Expect 0/20. This is the honest state of things: **the harness reproduces, the headline
rate does not.** The original traces are in `docs/evidence/` — see
`mechanism_llama_selfundo.json` for the self-undo and `mechanism_mistral_stops.json` for
the same observation producing the opposite action.

Every sweep writes per-run evidence to `docs/evidence/`, including the model string that
served it. A sweep halted by a rate limit saves what it completed; a sweep that completes
zero runs writes nothing.

---

## Stack

Python 3 · Playwright · single-model-per-measurement, provider and model recorded per run
(Groq, Mistral, Gemini, OpenRouter, Cerebras wired). No agent framework — built directly
on Playwright and an LLM so the failure modes are visible rather than buried under
abstraction.

---

## Depth

- [docs/failure-taxonomy.md](docs/failure-taxonomy.md) — every mode, every denominator,
  every retraction, in full
- [docs/architecture.md](docs/architecture.md) — how the agent and harness fit together
- [docs/generality.md](docs/generality.md) — where the mechanism did not reproduce
- `docs/evidence/` — raw per-run data for every number on this page

---

## Roadmap

- [x] Baseline agent (perceive → plan → act)
- [x] Reliability harness + silent-failure detection
- [x] Baseline measurement, mechanism verification
- [x] Cross-model replication
- [ ] Decision-time action scoring (reversibility at plan time)
- [ ] Hands-free voice control (accessibility)
- [ ] Remaining v2 modes — rate-limit recovery, irreversibility
- [ ] ~~Hardening + before/after numbers~~ — blocked: no available model exhibits the
      failure

---

*Built by [Krishan Kumar Verma](https://github.com/KrishanKVerma).*
