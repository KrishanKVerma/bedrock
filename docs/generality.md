# Generality test — does the silent-failure mechanism reproduce?

The login-task silent failure was hypothesized to follow from a structure:
the element proving success is also the element that undoes it. To test whether
this generalizes, tasks with the same structure on different sites were measured
at locked config (Groq, Llama-3.3-70B, 60 elements, n=10).

| Task | Site | Structure | Silent failures |
|---|---|---|---|
| quotes_login_form | quotes.toscrape.com | multi-step; post-login page transition; Logout at low ref | ~40–60% (4 sessions) |
| add_element_analog | the-internet.herokuapp.com | single click; no transition; Delete appears in place | **0/10** |

## Reading

The mechanism did **not** reproduce on the analog. The two tasks share the
surface structure (success evidence = undo control) but differ in a way that now
looks essential: the login task is multi-step and success triggers a **page
transition**, after which the agent re-perceives and can misfire onto the
evidence-destroying element at a tempting ref. The add-element task completes in a
single action with no transition — the agent clicks, sees success, and stops. There
is no second decision point at which to undo itself.

## Revised claim

Silent failure here is not a general property of "reachable evidence-destroying
elements." It requires a more specific structure: a **multi-step task where success
triggers a page transition, after which the evidence-destroying element appears at a
low ref and the agent takes one more action instead of stopping.**

One positive (login) and one negative (add-element) cannot support a general claim.
Establishing that the login result is not a one-off requires at least one more
*positive* reproduction on a different site. Until then the finding is: a specific,
reproducible task structure induces silent failure — not that agents silently fail
in general.