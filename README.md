# bedrock

**A browser agent built to survive the real web — and prove it with numbers.**

Browser agents score 78% on benchmarks and finish ~30% of real tasks. Worse, they often report success when they silently failed. Bedrock is built the other way around: measured against the failure modes that break agents in production, hardened against each, with reproducible before/after numbers.

---

## What this investigates

The agent loop is commoditized. Reliability isn't. Every browser agent can click and type; almost none can tell you whether it *actually* completed the task, or whether it just claimed to. This project treats that as the real problem: build the agent, then build the harness that catches it lying, and measure the gap.

**Thesis: the hard part isn't making an agent act. It's knowing whether to trust what it says it did.**

---

## Status

v1 in progress — building the baseline agent.

---

## The six failure modes

Production breaks browser agents in ways benchmarks never test:

| Mode | What it is | Status |
|---|---|---|
| **Silent failure** | Agent claims success; task didn't complete | v1 |
| **DOM selector drift** | The button moved or the class changed | v1 |
| **Modal interruption** | A cookie banner eats the click | v1 |
| **Login / session state** | Session expires mid-task | v2 |
| **Rate-limit cliffs** | 429 at action 17 | v2 |
| **Irreversibility** | Submit Order has no undo | v2 |

---

## Architecture

See [docs/architecture.md](docs/architecture.md).

---

## Stack

- **Python 3** · **Playwright** (browser control) · **Groq** (LLM)
- Custom eval harness — no framework, built to study the problem directly

---

## Roadmap

- [ ] Baseline agent (perceive → plan → act)
- [ ] Reliability harness + silent-failure detection
- [ ] Baseline measurement
- [ ] Hardening + before/after numbers
- [ ] Hands-free voice control (accessibility)
- [ ] v2 — remaining three failure modes

---

*Built by [Krishan Kumar Verma](https://github.com/KrishanKVerma) — building AI agents that ship.*
