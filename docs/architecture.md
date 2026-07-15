# Architecture

## The shape of the problem

A browser agent is a loop: look at the page, decide what to do, do it. That part is solved — Playwright drives the browser, an LLM picks the action. What isn't solved is knowing whether the loop actually worked.

So bedrock is two systems, not one:

1. **The agent** — the loop everyone builds.
2. **The harness** — the thing that wraps the loop, breaks it on purpose, and checks whether it lies about the result.

The second one is the point.

---

## The agent loop

```
task
 │
 ▼
PERCEIVE ──► page state (DOM + screenshot → structured, LLM-readable)
 │
 ▼
PLAN ──────► next action (LLM reads state, picks click/type/navigate)
 │
 ▼
ACT ───────► execute via Playwright
 │
 ▼
VERIFY ────► did the page actually change the way the plan expected?
 │
 └──► loop until task complete or budget exhausted
```

**VERIFY is the non-standard step.** Most agents act and assume. Bedrock checks its own work at every step — that's the difference between "I clicked" and "the thing I wanted to happen happened."

---

## The harness
            ┌──────────────────────────┐
            │  task + expected outcome │
            └────────────┬─────────────┘
                         │
          ┌──────────────▼──────────────┐
          │  INJECT failure conditions  │
          │  (drift · modals · ...)     │
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

### Silent-failure detection
The centerpiece. The agent reports "task complete." The harness independently checks the final page state against the task's expected outcome. Disagreement = silent failure — the most dangerous category, because nothing errors and nobody notices.

### Failure-mode injection
Rather than hoping production chaos shows up, the harness manufactures it:

- **DOM selector drift** — mutate selectors/classes mid-run
- **Modal interruption** — inject an overlay before a click lands
- **(v2)** session expiry, 429 responses, irreversible actions

---

## Design decisions

- **No agent framework.** Built directly on Playwright and an LLM so the failure modes are visible, not buried under abstraction.
- **Free-tier throughout.** Groq for inference, local Chromium — the research shouldn't require a budget.
- **Measure before hardening.** Baseline numbers first, fixes second, re-measure third. Any claim of improvement has a before to compare against.
- **Every run replayable.** A number nobody can reproduce isn't a result.

---

## Method

1. Build the baseline agent
2. Build the harness; measure the baseline honestly
3. Harden one failure mode at a time
4. Re-measure; report before/after
5. Publish what held and what didn't
