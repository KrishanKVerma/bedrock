# Architecture

## The shape of the problem

A browser agent is a loop: look at the page, decide what to do, do it. That part is
solved — Playwright drives the browser, an LLM picks the action. What isn't solved is
knowing whether the loop actually worked.

So bedrock is two systems, not one:

1. **The agent** — the loop everyone builds.
2. **The harness** — the thing that wraps the loop, breaks it on purpose, and checks
   whether it lies about the result.

The second one is the point.

---

## The agent loop

```
task
 │
 ▼
PERCEIVE ──► page state (visible text + enumerated interactive elements)
 │
 ▼
PLAN ──────► next action (LLM reads state, returns one structured decision)
 │
 ▼
ACT ───────► execute via Playwright
 │
 └──► loop until the agent says done/fail, or the step budget runs out
```

**There is no verify step, and that is deliberate.** The agent acts and assumes, like
most agents. It decides when it is finished and reports what it thinks happened. Adding
per-step verification to the agent would make the agent better and the measurement
useless — the whole question is what an unverified loop does and whether its own account
of itself can be trusted.

Verification lives entirely in the harness, runs once at the end, and is never shown to
the agent.

**What is not built:** decision-time action scoring. Nothing enumerates the available
actions and scores them for reversibility *before* the agent acts. Every failure in this
repo was diagnosed post hoc from traces. Knowing that silent failures take one step past
success and click the same element does not mean anything in the loop notices at the
time. That gap is the obvious next thing to build, and the measured mechanism gives it a
narrow first target: flag actions that revert the postcondition the agent is working
toward.

---

## The harness

```
            ┌──────────────────────────┐
            │  task + expected outcome │
            └────────────┬─────────────┘
                         │
          ┌──────────────▼──────────────┐
          │  INJECT failure conditions  │
          │  (drift · index · modal ·   │
          │   session expiry)           │
          └──────────────┬──────────────┘
                         │
                ┌────────▼────────┐
                │   AGENT LOOP    │
                └────────┬────────┘
                         │
          ┌──────────────▼──────────────┐
          │  SILENT-FAILURE DETECTOR    │
          │  agent's claim vs page truth│
          └──────────────┬──────────────┘
                         │
               replayable run log
                         │
                ┌────────▼────────┐
                │  PASS / FAIL    │
                └─────────────────┘
```

### Silent-failure detection

The centrepiece. The agent reports "task complete." The harness independently checks the
final page state against a criterion defined before the run and never shown to the agent.
Disagreement = silent failure — the most dangerous category, because nothing errors and
nobody notices.

The criterion receives the final URL and the final page text. It does not re-fetch the
page, which matters for conditions that invalidate state without re-rendering: the
session-expiry injector reloads deliberately for exactly this reason.

### Failure-mode injection

Rather than hoping production chaos shows up, the harness manufactures it. Injections
fire on page state, not step number, and are recorded on the run log rather than passed
to the planner — both of those are fixes for measurement errors documented in
`failure-taxonomy.md`.

- **DOM selector drift** — rename class/id/data-test on every interactive element
- **Index shift** — insert decoy elements, shifting every positional ref
- **Modal interruption** — inject a blocking overlay
- **Session expiry** — clear cookies and reload, invalidating the session mid-task
- **Prepopulate** — seed the page with deletable elements before the agent starts

Two of these turned out to be **no-ops for this agent**: drift and modal change nothing
the perception layer passes to the planner. Probes in `tests/` verify that directly. They
are retained as controls, and in that role dom_drift is what detected the history-leak
bug.

### Per-run evidence

Every run writes a replayable log: every step's URL, element count, chosen action and
ref, the planner's stated reason, whether the action succeeded, and the provider *and
model string* that served each call. Sweeps write one JSON per provider/model/task/
condition to `docs/evidence/`.

Two of the five measurement errors this project caught were caught by fields added for
unrelated reasons — the clicked ref, and the per-run step count. Recording more than you
currently need is what makes an error findable later.

---

## Design decisions

- **No agent framework.** Built directly on Playwright and an LLM so the failure modes
  are visible, not buried under abstraction.
- **One model per measurement, never mixed.** There is no automatic provider fallback: if
  the locked provider fails, the run fails loudly rather than quietly continuing on a
  different model. Provider *and* model are recorded per run.
- **Free-tier throughout.** The research shouldn't require a budget. This has a cost —
  see the note on model retirement below.
- **Measure before hardening.** Baseline numbers first, fixes second, re-measure third.
- **Every run replayable.** A number nobody can reproduce isn't a result.

---

## Method, and where it broke

The intended method:

1. Build the baseline agent
2. Build the harness; measure the baseline honestly
3. Harden one failure mode at a time
4. Re-measure; report before/after
5. Publish what held and what didn't

Steps 1, 2, and 5 were completed. **Steps 3 and 4 are not possible.** Groq retired
`llama-3.3-70b-versatile` — the only model measured that exhibits the silent-failure
mechanism — partway through the work. There is no available model to harden against, so
there is no before/after to report.

That is a limitation of the result and also a finding about the method: a reliability
study built on a provider-hosted free-tier model is contingent on something the provider
can delete without notice. The archived traces remain; the arm is closed at 85 runs.