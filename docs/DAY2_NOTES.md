# Day 2 — The 4 Agents

## What's built
- `agents/tools.py` — thin wrappers around the MCP server's functions, used
  as ADK tool functions.
- `agents/analyst_agent.py` — spending patterns & trends.
- `agents/forecaster_agent.py` — next-month spend estimate.
- `agents/coach_agent.py` — budget status, savings goals, personality.
- `agents/orchestrator_agent.py` — "Should I Buy This?", delegates to the
  other 3 agents via `AgentTool`.

All four constructed and verified structurally (tool schemas generate
correctly, `AgentTool` delegation wiring is valid). Live Gemini calls need a
`GEMINI_API_KEY` — not testable inside this sandbox (no network access to
Google's API domains here), first live run happens on your machine.

## Key design decisions
1. **6 agents consolidated to 4.** Behavioral Pattern folded into Analyst
   (same underlying operation: query + look for patterns). Budget Coach,
   Goal Planning, and Notification folded into one Coach agent (all three
   were "look at budgets/goals, say something in the right tone" — splitting
   them would've meant duplicate plumbing, not more capability).
2. **Forecaster uses LLM reasoning over aggregated trend data, not a
   statistical time-series model.** A real ARIMA/Prophet pipeline is listed
   in `docs/FUTURE_SCOPE.md`, not built here — it wouldn't demonstrate agent
   concepts any better and is genuine scope creep for a 2-3 day build.
3. **Orchestrator delegates to sub-agents via `AgentTool`, not raw tool
   calls.** This is the actual multi-agent demonstration: one agent planning
   a sequence of sub-agent calls and synthesizing their output, which is a
   stronger capstone signal than one agent with a long flat tool list.
4. **No live MCP client/server round-trip at runtime.** The MCP server
   (`mcp_server/server.py`) is a real, standalone, independently runnable
   artifact for the "MCP Server" criterion. Agents import the same
   underlying functions directly — no subprocess/connection management,
   which would be infrastructure with no demo value at this scope.
5. **Model: `gemini-2.5-flash`.** Confirmed via web search (July 2026) that
   this is still free-tier, no card required. Gemini 2.0 Flash was
   deprecated June 1, 2026; Pro models became paid-only in April 2026 —
   both ruled out for this reason.

## How to test live (on your machine, once you have a key)
```bash
pip install -r requirements.txt
echo "GEMINI_API_KEY=your_key_here" > .env
cd agents
python3 analyst_agent.py       # or forecaster_agent.py, coach_agent.py
python3 orchestrator_agent.py  # the flagship "Should I Buy This?" demo
```

## Next (Day 3)
Streamlit UI: personality picker, dashboard (Analyst + Forecaster + Coach
output), and the "Should I Buy This?" input form wired to the Orchestrator.
Then README, architecture diagram, and optional deployment.
