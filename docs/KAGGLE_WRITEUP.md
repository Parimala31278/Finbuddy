# FinBuddy: An AI Financial Companion Built on Specialized Agents

### Subtitle
Three specialized AI agents, one shared source of truth, and a personality
system that makes financial advice actually land.

---

## Problem Statement

Digital payments have made spending frictionless — a tap, a scan, a click,
and money moves. That same frictionlessness is exactly what makes
overspending invisible until it's already a problem. Traditional budgeting
apps are fundamentally passive: they log transactions after the fact,
render a pie chart, and stop there. They don't predict what's coming next
month. They don't understand how a purchase today affects a savings goal
three months out. And they communicate in the flattest possible voice —
a notification that says "You spent $340 on dining this month" carries no
judgment, no context, and no reason to change behavior.

The real problem isn't a lack of data. Every digital transaction is already
logged somewhere. The problem is a lack of *reasoning* over that data, and
a lack of a voice that makes the reasoning land emotionally, not just
informationally.

## Motivation

This capstone asked for a project that demonstrates genuine agentic
reasoning, planning, memory, and tool use — not a chatbot wrapper around an
existing feature. Personal finance is an unusually good fit for that brief,
because the reasoning involved is naturally decomposable: understanding
what happened (analysis), estimating what's likely to happen
(forecasting), and deciding what should happen next (coaching against
goals and budgets) are three genuinely different cognitive tasks. That
decomposition maps directly onto a multi-agent architecture rather than a
single do-everything prompt, which made this problem a natural fit for
demonstrating Google ADK's agent model rather than forcing it.

There's also a simpler, more personal motivation: most people already know
*that* they're overspending in some category. What they lack is a voice
that tells them in a way that actually changes behavior — which is why
FinBuddy's personality system (sarcastic, supportive, strict, coach) isn't
a cosmetic feature. It's a bet that tone is part of the intervention, not
decoration around it.

## Solution Overview

FinBuddy is an AI financial companion built around three specialized ADK
agents that share one financial dataset:

- **Analyst Agent** — reads recent transactions and 6-month spending trends,
  and produces a plain-language summary of what's actually happening:
  top categories, notable patterns, anything that stands out.
- **Forecaster Agent** — estimates next month's likely total spend by
  reasoning over recurring fixed costs and recent discretionary trends,
  with an explicit, explained range rather than a bare number.
- **Coach Agent** — checks current budget status against limits and
  savings goal progress, and delivers a short, personality-flavored
  check-in that calls out specific numbers rather than generic advice.

All three sit behind a Streamlit dashboard with a sidebar personality
picker. Every agent reads the user's chosen personality from the database
and adjusts its voice accordingly — the same underlying financial reasoning
delivered in four distinct tones.

Underneath all three agents is a single, real MCP (Model Context Protocol)
server that exposes the financial dataset through five tools:
`get_transactions`, `get_budget_status`, `get_savings_goals`,
`get_spending_summary`, and `get_user_profile`. This server is fully
standalone and independently runnable — it isn't internal-only plumbing,
it's a genuine MCP artifact that could be connected to any MCP-compatible
client. The three agents import the same underlying functions directly
rather than opening a live MCP connection at runtime, which keeps the
system simple without sacrificing correctness, since both paths execute
identical, tested logic.

Because no real bank API is free to use without eventual billing, all
transaction data is synthetically generated — but generated to be
*realistic*, not random. The generator models fixed recurring costs (rent,
subscriptions), variable recurring costs (utilities, groceries) with
believable fluctuation, weekend-weighted discretionary spending, a
deliberate seasonal spike month, and a gradual "lifestyle inflation" trend
across 6 months — so the Analyst and Forecaster agents have genuine
patterns to find, not noise.

## AI Agent Architecture

Each agent follows the same simple shape: a name, a Gemini 2.5 Flash model
backend, a system-prompt instruction defining its role and reasoning
steps, and a short list of tool functions. This consistency was a
deliberate design choice — once the pattern was proven correct for one
agent, extending it to the other two required no new architectural
decisions, only new prompts and tool lists.

The original design specified six agents (Spending Analysis, Prediction,
Budget Coach, Goal Planning, Notification, Behavioral Pattern) plus a
Decision Orchestrator for a "Should I Buy This?" feature. During
development, this was consolidated to three core agents: Behavioral
Pattern folded into the Analyst (both are the same underlying operation —
query transaction history and surface patterns), and Budget Coach, Goal
Planning, and Notification folded into a single Coach agent, since all
three reduce to "look at budgets/goals and say something in the right
tone." Splitting them further would have meant three agents with
near-identical plumbing and no additional reasoning capability — agent
count without agent capability.

A fourth agent, the Decision Orchestrator, was built and verified working
— it used ADK's `AgentTool` pattern to delegate to the other three agents
and synthesize a "Buy it / Wait / Skip it" verdict grounded in real budget,
forecast, and goal data. It was removed from the final submission after
testing revealed that delegating to three sub-agents multiplies API calls
per single user action, which repeatedly exhausted Gemini's free-tier
daily quota during iterative testing. This is documented transparently in
the project's Future Scope notes rather than silently dropped, since it
represents a genuine architecture trade-off between demonstrating richer
multi-agent orchestration and staying reliably within a $0 budget.

## Technical Implementation

**Data layer:** a 4-table SQLite schema (users, transactions, goals,
budgets) populated by a synthetic data generator that produces 6 months
of history with intentional realism: recurring costs land on consistent
days, discretionary spending is weekend-weighted, and the current month is
generated only up to today's actual date rather than filling in
future-dated transactions.

**MCP server:** built with the official `mcp` Python SDK (FastMCP),
exposing five tools. Every tool validates its inputs — numeric ranges are
clamped to sane bounds, and category filters are checked against an
allow-list — so malformed or adversarial calls fail predictably rather
than causing unbounded queries or silent wrong answers. All database
access uses parameterized queries throughout, ruling out SQL injection as
an attack surface.

**Agents:** built with Google ADK, backed by `gemini-2.5-flash` —
confirmed free-tier, no billing required, as of mid-2026 (notably, Gemini
2.0 Flash was deprecated and Pro-tier models became paid-only earlier this
year, which shaped this model choice directly). Tool schemas are generated
automatically by ADK from Python type hints and docstrings, which was
verified structurally during development rather than assumed.

**Reliability:** a shared `run_agent()` helper distinguishes between
transient server errors (retried automatically, since these usually clear
within seconds) and quota errors (not retried, since retrying against a
rate limit only wastes more of the same limited quota) — failing with a
clear, friendly message in either case rather than a raw stack trace
reaching the user.

**Security:** API keys are read from a `.env` file excluded via
`.gitignore`, never touching the committed codebase. Input validation and
allow-listing happen at the single data-access boundary (the MCP server),
so every agent's data access is bounded and predictable regardless of what
an agent or a malformed prompt asks for.

**UI:** a single-file Streamlit dashboard. No agent call happens
automatically on page load or on UI rerun — every generation is behind an
explicit button click, a deliberate choice given how easily Streamlit's
constant rerunning could exhaust a limited free-tier daily quota.

## Challenges

The most significant challenge was Gemini's free-tier quota being tighter
than expected — as low as 20 requests/day on `gemini-2.5-flash` for some
projects, following a policy tightening in late 2025, discovered only
through live testing rather than documentation. This directly shaped two
architecture decisions: switching viable testing to `gemini-2.5-flash-lite`
for its more generous quota, and removing the multi-agent Decision
Orchestrator, which multiplied API calls per interaction beyond what
reliable iterative testing could sustain on the free tier.

A second challenge was keeping the synthetic data genuinely realistic
rather than obviously random — early generator versions produced spending
trends too noisy for the Forecaster agent to find a real signal in, fixed
by applying trend effects (lifestyle inflation, seasonal spikes) at the
per-month level rather than per-transaction, so the underlying pattern
survives natural transaction-level noise.

A third was verifying ADK's fast-moving API surface directly rather than
relying on potentially stale documentation — confirming the exact
`Agent` constructor fields, the `AgentTool` delegation pattern, and the
tool-schema generation behavior through direct introspection before
writing agent code against assumed APIs.

## Results

All three core agents (Analyst, Forecaster, Coach) run end-to-end against
live Gemini calls, producing personality-flavored, data-grounded output
verified against real synthetic transaction data — not placeholder text.
The MCP server runs standalone and independently, exposing all five tools
correctly with verified input validation. The Streamlit dashboard connects
all three agents behind a working personality-switching UI. The complete
project — data generator, MCP server, three agents, and UI — runs locally
with a single free API key and zero paid infrastructure.

## Future Scope

The Decision Orchestrator ("Should I Buy This?") is the clearest next
step: the `AgentTool`-based delegation pattern is already proven and can
be reintroduced directly, ideally paired with a lighter-quota model.
Beyond that: a genuine statistical forecasting model (ARIMA/Prophet-style)
alongside the current LLM-reasoning approach; multi-user authentication;
scheduled/push notifications rather than on-demand check-ins; and optional
deployment to Streamlit Community Cloud for a live, shareable demo beyond
the GitHub repository.
