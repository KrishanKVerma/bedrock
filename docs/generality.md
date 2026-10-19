# Generality

Where the findings hold, where they don't, and what the boundaries turned out to be.

This document exists because the first version of it was wrong. An early claim that the
silent-failure mechanism generalised was retracted when two purpose-built analogs both
returned 0/10. What follows is the version that survived being tested.

Every rate here carries an interval, and every comparison carries a test. Interval
overlap is a crude and conservative way to compare two rates; where a claim rests on a
difference, a two-sample Fisher exact test is reported instead.

---

## The claim being tested

The headline mechanism — an agent completes a task, takes one step past the terminal
action, clicks the element that proves its own success, and reports success anyway — was
characterised on one task (`quotes_login_form`) with one model (Llama-3.3-70B, Groq).

Two questions follow. Does it appear on other tasks? Does it appear on other models?

The answers are **no** and **no** — and the interesting part is what replaced it.

---

## Across tasks: the mechanism did not reproduce

Two analogs were built specifically to reproduce the self-undo, each isolating a different
suspected ingredient.

**`add_element_analog`** — single click, a Delete control appearing at a low ref
immediately afterward. Tests whether a destructive element at a reachable position is
sufficient. **0/10** (95% Clopper-Pearson 0–30.9%).

**`herokuapp_login_analog`** — multi-step, credentials, a page transition on success, and
a Logout control on the destination page at a reachable ref. A structural match for the
original in every way identified as relevant at the time. **0/10** (0–30.9%).

The self-undo mechanism has been reproduced on exactly one task out of three attempts.

**How strong is that, given n=10 per analog?** Stronger than the intervals suggest. A
single 0/10 has an upper bound of 30.9%, which overlaps the baseline's lower bound of
28.8% — so by interval overlap alone a single analog is marginal. But interval overlap is
a conservative test. Compared directly against the 34/89 baseline, a single analog gives
Fisher exact **p = 0.0141**, and the two analogs pooled (0/20, 0–16.8%) give
**p = 0.0003**. The non-reproduction is real; it is not an artifact of small n. Stating
both the weak check and the strong one, because the first is what a reader will run in
their head.

**The non-reproducibility is the argument.** If a mechanism this specific — same failure
shape, same element class, same page structure — does not transfer to a task built
deliberately to elicit it, then enumerating failure modes in advance and checking for them
is not a viable oversight strategy. You cannot write the check before you have seen the
failure. That is the case for post-hoc verification against real end state, which catches
the failure without needing to have predicted its shape.

---

## Across models: the mechanism is not universal

Same task, same harness, same config, same postcondition:

| Model | Silent failures, login task | 95% interval |
|---|---|---|
| Llama-3.3-70B (Groq) | 34/89 (38%) | 28.8–48.6% (Wilson) |
| Mistral Small | 0/20 | 0–16.8% (Clopper-Pearson) |
| gpt-oss-120b | 0/20 | 0–16.8% (Clopper-Pearson) |

**Read the zero cells correctly.** 0/20 does not mean the model does not do this. It means
that at twenty runs I did not observe it, and the data are consistent with a true rate as
high as 16.8%. A model that silently failed one run in twenty would have produced 0/20
here more than a third of the time (0.95²⁰ = 36%). The rule of three gives roughly
3/20 = 15% as a quick bound for a zero numerator at this n, slightly under the exact
Clopper-Pearson figure of 16.8% — which is how the rule generally behaves.

**The comparison survives the intervals, and the test.** Both zero cells have upper bounds
(16.8%) below Llama's lower bound (28.8%), so the difference is not an artifact of
reporting point estimates without uncertainty. Fisher exact against the Llama baseline
gives p = 0.0003 for each. That is the claim: a difference that survives the caveats, not
a table with caveats bolted on.

Three bare point estimates in a comparison table would have been the exact error this
project exists to document. I made it in the first version of this table.

Both live models see an identical element list, with the destructive Logout link at the
same ref[1] that Llama clicked in 34 runs. Neither ever clicks it.

The traces show why, and they show it is not a perception difference. Mistral's stopping
reason is:

> The page shows 'Logout' in the visible text, indicating successful login.

Llama's final action, on a silent-failure run, is:

> click 1 | Logout link is present, indicating a successful login

The same observation, from the same list, in almost the same words. One treats it as
evidence and stops; the other treats it as an action and clicks. The difference is not in
what the models see, and not in where the element sits — it is in whether a correct
conclusion about task completion becomes a decision to terminate.

---

## What replaced it: the failure is a property of the pair

Extending to four tasks across the two models that remain available:

| Task | Mistral Small | gpt-oss-120b |
|---|---|---|
| `quotes_login_form` | 0/20 | 0/20 |
| `element_count_tracking` | 18/20 | 20/20 |
| `herokuapp_dynamic_controls` | 20/20 | 19/20 |
| `irreversible_delete` | 12/20 | 2/20 |

Each cell is n=20, so a zero cell bounds at 0–16.8% and a 20/20 cell at 83.2–100%
(Clopper-Pearson). Mid-range cells carry intervals roughly ±20 points wide: 19/20 is
75.1–99.9%, 18/20 is 68.3–98.8%, 12/20 is 36.1–80.9%, 2/20 is 1.2–31.7%. Read the table
with that in mind — it distinguishes the extremes cleanly (0/20 against 20/20 gives
Fisher exact p = 1.5e-11) and the middle poorly.

**77 silent failures in 80 runs** on the two tasks where both models fail. **Zero honest
failures on any of the four tasks, on either model** — across 160 runs, not one instance
of an agent reporting that it could not do the job.

Three things follow.

**1. The login task is the outlier, not the archetype.** Most of this project's effort
went into characterising a mechanism on the one task these models reliably pass. On the
other three, silent failure is the normal case rather than an edge case that had to be
hunted for.

**2. There is no reliability ordering between the models.** gpt-oss is worse than Mistral
on `element_count_tracking` (20/20 vs 18/20) and dramatically better on
`irreversible_delete` (2/20 vs 12/20). Neither dominates. "Which model is more reliable"
has no answer that survives changing the task. Note that the first of those two contrasts
is well inside the noise — 20/20 against 18/20 at n=20 gives Fisher exact p = 0.49, which
is no difference at all — while the second (2/20 against 12/20, p = 0.002) is real. The
non-ordering claim rests on the second contrast, not the first, and the first should never
have been stated as though it carried weight.

**3. So reliability looks like a property of the task/model pair.** Not of the model, not
of the task. A number measured on one pair is evidence about that pair.

This cuts against this project's own headline result as much as anyone else's. The 38%
figure is a fact about Llama-3.3-70B on `quotes_login_form`, and nothing more. It was
never a fact about browser agents, and the temptation to read it as one is exactly what
this section exists to block.

---

## What generalised instead

Three things did hold across every task and model measured:

**The self-report is never reliable.** Zero honest failures in 160 runs. Whatever the
failure mode, the agent's account of it was either wrong or absent.

**The independent check always caught it.** A postcondition defined in advance against
real end state caught every failure class in the taxonomy — self-undo, weak-evidence
verification, state-tracking — without needing to know which one it was looking for.

**Failure shape is stable even where rate isn't.** On the login task, across 81
unperturbed instrumented runs, a pass is always 3 steps ending on ref 4 and a silent
failure is always 4 steps ending on ref 1. (An earlier figure of 112 was a running tally
that did not match the evidence files; 81 is the count derived from `docs/evidence/`.) The
pooled rate is 34/89 with a wide interval, 28.8–48.6%; the shape never varied once. A
benchmark reporting only the rate would read a deterministic failure as noise.

Note that the per-session spread behind that rate — 10% to 60% across eight sessions — is
within binomial noise at these session sizes and does **not** support a between-session
effect. A chi-square test of homogeneity gives p = 0.371. An earlier version of
`docs/failure-taxonomy.md` presented that spread as instability in its own right; it is
retracted there.

---

## Boundaries of everything above

- **Two live models.** Mistral Small and gpt-oss-120b. The third, Llama-3.3-70B, was
  retired by the provider mid-study; that arm is closed at 89 runs and cannot be extended.
- **Four tasks**, all on two public test sites. All are short — three to ten steps.
- **n=20 per cell.** Enough to distinguish 0/20 from 20/20 (Fisher exact p < 0.0001); not
  enough to resolve 12/20 from 14/20, and not enough to resolve 18/20 from 20/20. Intervals
  on mid-range cells are roughly ±20 points.
- **n=10 per analog**, which is why the across-tasks section reports a direct test rather
  than leaning on intervals.
- **English-language, single-session, no authentication beyond a test login.**
- **The pair-dependence claim itself rests on 4 tasks × 2 models.** It is the strongest
  thing in this document and it is still a claim from eight cells. Widening that matrix is
  the obvious next thing to do, and until it is done this section should be read as a
  hypothesis with supporting evidence rather than an established result.
