# FinBuddy — Future Scope

Everything below was deliberately excluded from the MVP to keep the 2-3 day
build achievable, not because it wasn't considered. Listed here so the
reasoning is visible rather than silently dropped.

## "Should I Buy This?" Decision Orchestrator
Originally planned as the project's flagship feature: a 4th agent that would
delegate to Analyst, Forecaster, and Coach (via ADK's `AgentTool`) to
reason through a purchase decision — "Buy it / Wait / Skip it" — grounded in
real budget, forecast, and goal data. It was built and confirmed working
end-to-end in development, then removed to stay within Gemini's free-tier
daily quota during testing (delegating to 3 sub-agents multiplies API calls
per single user action). Re-adding it is straightforward: the original
implementation pattern (agents-as-tools via `AgentTool`) is proven and can
be reintroduced directly, ideally paired with `gemini-2.5-flash-lite` to
stay comfortably inside free-tier limits.

## Statistical forecasting model
The current Forecaster Agent produces estimates via LLM reasoning over
aggregated spending trends, not a dedicated time-series model. A real
ARIMA/Prophet-style pipeline would improve numerical precision but doesn't
demonstrate agent concepts any better, so it was left out of MVP scope.

## Multi-user support & authentication
The app currently serves a single demo user (`DEFAULT_USER_ID = 1`) with no
login system. Real multi-user support would need account creation, session
handling, and per-user data isolation — meaningful infrastructure with no
bearing on the agent-concepts the capstone is judged on.

## Push/scheduled notifications
The brief's original "Notification Agent" concept — proactive alerts sent
without the user opening the app — was folded into the Coach Agent's
on-demand check-in instead. A true push/notification system would need a
scheduler and a delivery channel (email, SMS, mobile push), all of which
are real infrastructure additions outside a 2-3 day scope.

## Live deployment
The project currently runs locally via `streamlit run app.py`. Streamlit
Community Cloud deployment (free, no card) is documented as an option in
the README but treated as optional per the project's own constraints — a
well-documented public GitHub repo is an accepted alternative.

## Rate limiting / application-layer quota management
Not implemented since Gemini's own free-tier quota already imposes a hard
ceiling; a second layer of application-side limiting wouldn't be visible or
demonstrable in a short demo.

## Real bank data integration
All transaction data is synthetically generated (see `data/generate_data.py`).
Real bank API integration (e.g. Plaid or a regional equivalent) was ruled
out from the start per the "free tools only, no billing" constraint most
such APIs require paid tiers for production use.
