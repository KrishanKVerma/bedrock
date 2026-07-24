# Failure taxonomy

A catalog of the ways a browser agent fails, built from Bedrock's own runs - not
from a checklist. Each entry records what the failure is, how it shows up, how the
harness detects it, and the one column that matters most: **does the agent's own
report reveal the failure?**

That last column is the thesis. Where the answer is "no," the agent's self-report
is worse than useless - it is confidently wrong - and no oversight method that
trusts the agent can catch it. Only an independent check against real state can.

All rates below are from single-provider (Groq, Llama-3.3-70B), single-config
(1500-char page text, 60 elements) runs. Rates are non-deterministic across
sessions and are reported as ranges with denominators, never averaged.

---

## 1. Silent failure

**What it is.** The agent completes its loop, reports success, and the task was not
accomplished. No error, no exception, no crash.

**How it manifests.** In the login task: the agent enters credentials, submits,
login genuinely succeeds, the agent observes the "Logout" link (correct evidence),
then clicks that link - logging itself out - and reports *"Login was successful as
indicated by the presence of the Logout link."* It reasoned correctly about
evidence it then destroyed.

**How it's detected.** An independent postcondition check evaluated against the
final page, defined in advance and never shown to the agent:
`text_contains("Logout")`. The agent's claim is recorded as data, not trusted as a
result.

**Does the agent's report reveal it?** **No.** The agent reports success. This is
the core case: the self-report and reality point in opposite directions.

**Rate.** Non-deterministic across sessions: observed 30%-50% (no injection, 60
elements) so far, with earlier unlocked observations as high as 80%. Not a stable
percentage - a moving target. See `docs/sessions.json`.

---

## 2. Weak-oracle pass

**What it is.** The agent's claim of success is *true*, but the task was not
performed the way it was meant to be - and a success criterion that is too loose
accepts it anyway. This is a failure of the *check*, not the agent.

**How it manifests.** Asked to search Wikipedia for a term and open the article, the
agent tried the search UI, failed, then navigated directly to the guessed URL. It
reached the right page without ever searching. A criterion of
`url_contains("Alan_Turing")` passed it.

**How it's detected.** Only by a stronger criterion that checks the *process*, not
just the endpoint. A weak oracle cannot distinguish "did the task" from "reached the
same place by another route."

**Does the agent's report reveal it?** **No - and neither does a naive check.** The
claim is technically true, so both the agent and a loose oracle agree. This is a
distinct class from silent failure: there the claim is false; here the claim is
true but unearned.

**Why it's separate.** Conflating this with silent failure would be a mistake. Silent
failure = the agent lies. Weak-oracle pass = the agent tells the truth and the
measurement is too weak to notice the task was sidestepped. Both defeat naive
oversight, for opposite reasons.

---

## 3. DOM selector drift

**What it is.** The page's structure changes between deployments - classes, ids, and
data attributes are renamed - while the page looks identical to a human.

**How it manifests.** The harness renames class/id/data-test on every interactive
element mid-run, simulating a site redeploy. The visible page is unchanged; every
structural hook is different.

**How it's detected.** Compared against the no-injection baseline for the same task,
same config, same session where possible.

**Does the agent's report reveal it?** **No.** Under clean single-provider runs,
injected drift produced 10/10 silent failures - worse than the no-injection baseline
(30-50%). The agent did not report confusion; it reported success. Drift did not
announce itself.

**Note.** An earlier provider-mixed run suggested drift might *reduce* silent failure
by shifting the evidence-destroying element out of reach. That result did not survive
a clean single-provider re-run for class/id drift. Whether *index-shift* drift (a
different injector) is protective is not yet settled - it must not be conflated with
class/id drift.

---

## 4. Non-determinism

**What it is.** The same agent, same task, same configuration produces different
outcomes across runs and - more strongly - across sessions.

**How it manifests.** The login task's silent-failure rate has been measured at 30%,
50%, and (unlocked) ~80% and ~33% in different sessions. Same code, same model, same
config. Temperature is 0; this variance is not from sampling temperature.

**How it's detected.** Multi-run sweeps, repeated across sessions, with denominators
kept visible. A single run - or a single session - cannot reveal it.

**Does the agent's report reveal it?** **No.** Each individual run reports a
confident outcome. The instability is only visible in aggregate, across many runs.

**Why it matters most.** If a reliability number swings this much on nothing, then any
benchmark reporting a single figure is reporting one sample from a wide distribution.
Reliability is not a fixed property of the agent; it is a distribution, and most
published numbers show one draw from it.

---

## 5. Rate-limit cliff

**What it is.** The model provider refuses further requests mid-task once a quota is
hit.

**How it manifests.** Encountered repeatedly in Bedrock's own build: the free-tier
daily token cap (100k) is reached partway through a measurement sweep, and further
calls return HTTP 429.

**How it's detected.** The provider raises a hard error; the harness surfaces it and
stops rather than silently switching providers (which would mix models and confound
the measurement).

**Does the agent's report reveal it?** **Yes.** This is the exception. A rate-limit
cliff is a hard, loud failure - the one failure mode in this list that announces
itself. It is included precisely because it contrasts with the others: the dangerous
failures are the quiet ones.

---

## Roadmap (v2)

Not yet measured, planned for v2: **login/session-state expiry**, **rate-limit
recovery** (as an agent-handled condition rather than an infrastructure stop), and
**irreversibility** (actions with no undo, e.g. submitting an order). Each will be
added here with the same columns - and, critically, the same question: does the
agent's own report reveal the failure?

---

---

## Measurement artifact: when the instrument moves

Not a failure of the agent - a failure of the harness, and worth documenting as
carefully as the rest, because it produced a result we nearly believed.

**What we thought we found.** Early sessions measured the login task's
silent-failure rate at roughly 80%, then 33%, then 30%, then 50%. Same code, same
model, same task. The obvious reading was dramatic session-to-session
non-determinism - an agent whose reliability swung by a factor of two on nothing.
That is a striking claim, and it was nearly published.

**What actually drifted.** The perception layer has two settings that control how
much of the page the planner sees: `max_text` (characters of visible page text) and
`max_elements` (interactive elements listed). Across those sessions, both moved -
1500 characters in some runs, 600 in others; 60 elements in some, 30 in others -
because they were being tuned to fit a token budget while measurements were running.
The session log compounded it: entries were tagged `30el` while the code was running
at 60.

**Why that produced the artifact.** Element refs are positional. At 60 elements the
Logout link - the element whose click destroys the agent's own success evidence -
sat at a low, frequently-chosen ref. At 30 elements the list re-indexed and that
element moved out of easy reach. So the "rate" was not the agent behaving
differently; it was the target moving between measurements.

**How it was resolved.** The distribution was discarded, the config locked
(`max_text=1500`, `max_elements=60`), and the log tagged with the real config. Three
clean sessions then measured 60%, 60%, 50% - a range fully consistent with ordinary
sampling noise around a stable rate near 55% at n=10. No non-determinism required.

**The finding.** The instability was in the instrument, not the agent. This is worth
stating plainly because it generalizes: an agent benchmark whose configuration is
adjusted between runs will report differences that belong to the harness. The
apparent result was more dramatic than the truth, which is exactly the direction such
errors tend to run.

---

## Methodology: two errors the harness caught on itself

Both of the measurement errors in this project were found by the harness before they
reached a claim. Recording them is not throat-clearing - a measurement apparatus that
has never caught itself being wrong has not been tested.

**1. Injection fired at a step the agent never reached.** Failure-mode injections were
triggered by step number ("inject before step 4"). The agent completes the login task
in three steps about half the time, so the injection frequently never fired at all,
and the run recorded a clean result for the wrong reason. Detected by reading a trace
and noticing the `injected` field named a step that did not exist in the step list.
Fixed by triggering on page state - the injection fires when the post-login page
appears, regardless of step count. All injection results measured under the old
trigger were discarded.

**2. Perception config drifted between sessions.** Documented above.

The pattern in both: the error made the numbers *more* interesting, not less. A
non-firing injection produced conditions that looked protective; a drifting config
produced dramatic variance. Neither would have announced itself in a summary
statistic - both were only visible in the raw traces and the config history. This is
the argument for keeping every run replayable and every config recorded, and it is
the same argument this project makes about agents: a system's own report of what it
did is not evidence that it did it.

## The pattern

Read down the "does the agent's report reveal it?" column:

| Failure | Agent's report reveals it? |
|---|---|
| Silent failure | No |
| Weak-oracle pass | No |
| DOM drift | No |
| Non-determinism | No |
| Rate-limit cliff | Yes |

Every dangerous failure is invisible in the agent's own account of itself. The only
one the agent reliably reports is the one that was never subtle. This is the case for
independent, enforced, postcondition-based oversight - and against trusting an
agent's narrative of its own success.