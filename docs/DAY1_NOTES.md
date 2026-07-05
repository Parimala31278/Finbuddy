# Day 1 — Data Layer + MCP Server

## What's built
- `data/schema.sql` — 4-table SQLite schema (users, transactions, goals, budgets)
- `data/generate_data.py` — synthetic data generator producing 6 months of
  realistic transaction history: fixed recurring costs, variable recurring
  costs, weekend-weighted discretionary spend, a seasonal spike month, and a
  gradual lifestyle-inflation trend. Seeded (42) for reproducible demo data.
- `mcp_server/server.py` — MCP server (FastMCP) exposing 5 tools:
  `get_transactions`, `get_budget_status`, `get_savings_goals`,
  `get_spending_summary`, `get_user_profile`.

## Design decisions worth remembering
1. **All DB access goes through the MCP server.** Agents never touch SQLite
   directly. This keeps agent code focused on reasoning and gives us one
   place to validate/secure inputs (see `_validate_days_back`,
   `_validate_category`, category allow-listing).
2. **Data realism over data volume.** 6 months / ~180 transactions was a
   deliberate choice — enough for genuine trend detection, small enough to
   eyeball and sanity-check by hand.
3. **Current month is generated as a partial month** (only up to today's
   date) so the demo never shows future-dated transactions.
4. **Month-window math in `get_spending_summary` uses exact calendar-month
   arithmetic**, not day-count approximation — matters for the Forecaster
   Agent's trend windows being trustworthy.

## How to re-run / verify
```bash
cd data && python3 generate_data.py     # regenerates finbuddy.db
cd ../mcp_server && python3 server.py   # starts MCP server on stdio
```

## Known simplifications (intentional, for MVP scope)
- Single demo user (`DEFAULT_USER_ID = 1`) — multi-user auth is a stretch
  goal, not required for the capstone's core demonstration.
- Currency is unlabeled/generic — cosmetic, easy to localize later.

## Next (Day 2)
Build the 4 ADK agents (Analyst, Forecaster, Coach, Decision Orchestrator)
wired to these MCP tools, starting with the Analyst Agent end-to-end.
