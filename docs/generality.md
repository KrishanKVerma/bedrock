# Generality test - does the silent-failure mechanism reproduce?

The login-task silent failure was hypothesized to follow from a structure:
the element proving success is also the element that undoes it. To test whether
this generalizes, tasks with the same structure on different sites were measured
at locked config (Groq, Llama-3.3-70B, 60 elements, n=10).

| Task | Site | Structure | Silent failures |
|---|---|---|---|
| quotes_login_form | quotes.toscrape.com | multi-step; post-login transition; Logout at low ref; accepts any credentials | ~40-60% (4 sessions) |
| add_element_analog | the-internet.herokuapp.com | single click; no transition; Delete appears in place | **0/10** |
| herokuapp_login_analog | the-internet.herokuapp.com | multi-step; post-login transition to secure area; Logout on new page; validates credentials | **0/10** |

## Reading

Two structural analogs were built to reproduce the login silent failure. Both
returned zero.

The first analog (add_element) was too simple - a single click, no page transition -
so its negative result only ruled out the simplest structure. The second analog
(herokuapp_login) was designed to match the original closely: multi-step, a page
transition to a secure area after success, and a Logout control on the new page at a
reachable ref. It also returned 0/10.

Two negatives on two different structures mean the silent failure is **not** explained
by the structural story we proposed ("multi-step task + post-success transition +
evidence-destroying element at a low ref"). Something specific to the
`quotes_login_form` task is producing it, and our structural hypotheses do not
capture what.

## Candidate differences (unresolved)

- **Credential validation.** quotes.toscrape.com accepts any credentials (a scraping
  sandbox); herokuapp validates them. The quotes "login" is trivially permissive,
  which may change agent behaviour.
- **Exact element layout.** On the quotes post-login page the Logout link sits at a
  very low ref in a short element list. This points back to the earlier
  perception-config finding - that the failure is driven by the *index position* of
  the evidence-destroying element - rather than task structure. The herokuapp page
  may simply place its Logout control where the agent is less likely to select it.

## Revised claim (smaller, and honest)

We have a **single reproducible instance** of silent failure - `quotes_login_form` -
that we have not reproduced on any other task despite two purpose-built analogs.

The finding is therefore not "browser agents silently fail" and not "here is a general
mechanism." It is narrower, and the narrowness is itself the point:

> Silent failure was reliably reproducible on one specific task and did not transfer
> to two deliberately similar tasks. Whatever causes it is contingent on details we
> have not yet isolated - most likely the exact element layout of one page, not a
> structural property of the task. Failures this contingent are hard to predict and
> hard to test for, which is precisely why an independent post-hoc check - rather than
> anticipating the failure mode in advance - is the oversight approach that caught it.

Establishing anything more general requires isolating which specific factor
(credential permissiveness, element layout/ref position, page-transition timing)
drives the quotes result - by varying them one at a time - before any mechanism can be
claimed.