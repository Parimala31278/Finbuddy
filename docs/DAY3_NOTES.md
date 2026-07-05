# Day 3 — Streamlit UI

## What's built
- `agents/runner_utils.py` — one shared `run_agent(agent, message)` helper
  that runs any ADK agent and returns a plain text string. Used by the UI
  instead of each agent re-implementing session/event handling.
- `ui/app.py` — the dashboard: personality picker (sidebar) + 3 tabs
  (Spending Analysis, Forecast, Coach Check-in), each behind its own
  "Generate" button.

Verified: app boots cleanly with no import errors, server starts and serves
the page (checked in this sandbox with a dummy key — actual agent output
needs your real key, tested on your machine as before).

## Key design decisions
1. **Orchestrator Agent removed** (per your call) — this project no longer
   includes the "Should I Buy This?" feature. Flagged once for the record:
   this was the capstone's most distinctive feature and its removal means
   the project is now closer to "3 useful agents over financial data" than
   "flagship agentic decision-making," which may be worth weighing before
   final submission. Not raising it again after this note.
2. **No agent call happens automatically.** Every one of the 3 tabs requires
   an explicit button click. Given Gemini's free-tier daily quota can be as
   low as ~20 requests/day depending on the model/project, and Streamlit
   reruns the whole script on almost any interaction, auto-calling agents
   on page load or on every rerun would burn quota fast for no reason.
3. **Personality picker writes straight to SQLite** via a two-line
   update function in `app.py` — no new service/abstraction for a
   single-field setting.
4. **Results cached in `st.session_state`** so switching tabs doesn't
   silently re-trigger a paid... well, free but *quota-limited* API call.

## How to run
```bash
cd finbuddy
pip install -r requirements.txt
# .env already set up from Day 2 testing
cd ui
streamlit run app.py
```
It'll open in your browser automatically (usually http://localhost:8501).

## Next (Day 4 / wrap-up)
- README.md (setup, architecture, screenshots)
- Simple architecture diagram
- Optional: deploy to Streamlit Community Cloud (free, one click from GitHub)
