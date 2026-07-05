"""
ui/app.py
-----------
FinBuddy's Streamlit dashboard. Wires together the 3 agents
(Analyst, Forecaster, Coach) behind simple "Generate" buttons, plus an
instant, LLM-free charts section for at-a-glance spending/savings insight.

Design decisions:
1. NOTHING calls an agent automatically on page load. Every agent call is
   behind an explicit button click, since Gemini's free-tier daily quota
   can be tight and Streamlit reruns the script constantly.
2. Charts use REAL numbers pulled directly from the database via the same
   tool functions the agents use -- zero LLM calls, zero cost, instant.
   Visual, glanceable insight shouldn't have to wait on an API round-trip.
3. Each agent result comes with an expandable "What the AI actually looked
   at" trace, showing the exact tool calls and real data the model used --
   the clearest way to demonstrate (including on camera, for a demo video)
   that the agent is grounded in real data, not generating plausible text.
4. Results are cached in st.session_state so switching tabs doesn't
   silently re-trigger an API call.

Run: streamlit run app.py   (from inside the ui/ folder)
"""

import os
import sys
import sqlite3
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agents"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp_server"))

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from runner_utils import run_agent
from analyst_agent import analyst_agent
from forecaster_agent import forecaster_agent
from coach_agent import coach_agent
from tools import get_monthly_spending_trend, get_budget_status, get_savings_goals

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "finbuddy.db")
PERSONALITIES = ["sarcastic", "supportive", "strict", "coach"]

st.set_page_config(page_title="FinBuddy", page_icon="💸", layout="centered")

# ---------------------------------------------------------------------------
# Styling -- a classier look without pulling in a heavy design system.
# Streamlit's default theme is functional but plain; this nudges typography,
# spacing, and card styling toward something closer to a real product.
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    h1 { font-weight: 700; letter-spacing: -0.5px; }
    h2, h3 { font-weight: 600; }
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 10px 18px;
        font-weight: 500;
    }
    div[data-testid="stMetric"] {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 14px 16px;
    }
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        padding: 6px 20px;
    }
    div[data-testid="stExpander"] {
        border-radius: 10px;
        border: 1px solid rgba(255,255,255,0.08);
    }
    .fb-caption {
        color: rgba(250,250,250,0.55);
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)


def get_current_personality() -> str:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT personality_pref FROM users WHERE id = 1").fetchone()
    conn.close()
    return row[0] if row else "sarcastic"


def set_personality(value: str) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE users SET personality_pref = ? WHERE id = 1", (value,))
    conn.commit()
    conn.close()


def render_trace(trace: list) -> None:
    """Show exactly which tools the agent called and what real data came
    back -- proof the answer is grounded, not hallucinated. This is the
    single best thing to point a camera at in a demo video."""
    if not trace:
        return
    with st.expander(f"🔍 What the AI actually looked at ({len(trace)} data calls)"):
        for i, call in enumerate(trace, 1):
            args_str = ", ".join(f"{k}={v}" for k, v in call["args"].items()) or "no arguments"
            st.markdown(f"**{i}. `{call['tool']}({args_str})`**")
            st.json(call["result"], expanded=False)


def render_result(session_key: str) -> None:
    if session_key not in st.session_state:
        return
    text, trace = st.session_state[session_key]
    (st.error if text.startswith("⚠️") else st.success)(text)
    render_trace(trace)


if not os.getenv("GEMINI_API_KEY"):
    st.error(
        "GEMINI_API_KEY not found. Add it to a `.env` file in the project root "
        "(same folder as requirements.txt), then restart this app.\n\n"
        "Get a free key at: https://aistudio.google.com/apikey"
    )
    st.stop()

st.title("💸 FinBuddy")
st.markdown(
    '<p class="fb-caption">Your AI financial companion — analysis, forecasting, '
    'and coaching, powered by three specialized agents.</p>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.subheader("Personality")
    current = get_current_personality()
    choice = st.selectbox(
        "How should FinBuddy talk to you?",
        PERSONALITIES,
        index=PERSONALITIES.index(current) if current in PERSONALITIES else 0,
    )
    if choice != current:
        set_personality(choice)
        st.success(f"Personality set to '{choice}'.")

    st.divider()

# ---------------------------------------------------------------------------
# Instant charts -- zero LLM calls, computed directly from the database.
# ---------------------------------------------------------------------------
st.subheader("📊 At a Glance")

summary = get_monthly_spending_trend(months_back=6)
budget = get_budget_status()
goals = get_savings_goals()

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Monthly spend trend**")
    monthly_totals = summary.get("monthly_totals", {})
    if monthly_totals:
        df_trend = pd.DataFrame(
            {"Total Spend": list(monthly_totals.values())},
            index=list(monthly_totals.keys()),
        )
        st.line_chart(df_trend, height=220)
    else:
        st.caption("No spending history yet.")

with col2:
    st.markdown("**This month by category**")
    by_month = summary.get("by_month_and_category", {})
    latest_month = max(by_month.keys()) if by_month else None
    if latest_month:
        cat_data = by_month[latest_month]
        df_cat = pd.DataFrame({"Amount": list(cat_data.values())}, index=list(cat_data.keys()))
        st.bar_chart(df_cat, height=220)
    else:
        st.caption("No category data yet.")

st.markdown("**Budget usage this month**")
budgets_list = budget.get("budgets", [])
if budgets_list:
    for b in budgets_list:
        pct = min(b["percent_used"] or 0, 100) / 100
        label = f"{b['category'].title()} — ₹{b['spent_this_month']:,.0f} / ₹{b['monthly_limit']:,.0f}"
        st.progress(pct, text=label)
        if b["is_over_budget"]:
            st.caption(f"⚠️ Over budget by ₹{-b['remaining']:,.0f}")
else:
    st.caption("No budgets set.")

st.markdown("**Savings goals progress**")
goals_list = goals.get("goals", [])
if goals_list:
    for g in goals_list:
        pct = min(g["progress_percent"] or 0, 100) / 100
        label = f"{g['name']} — ₹{g['saved_amount']:,.0f} / ₹{g['target_amount']:,.0f} ({g['progress_percent']}%)"
        st.progress(pct, text=label)
else:
    st.caption("No savings goals set.")

st.divider()

# ---------------------------------------------------------------------------
# Agent-powered tabs -- each one makes a live Gemini call, on demand only.
# ---------------------------------------------------------------------------
st.subheader("🤖 Ask Your AI Agents")

tab1, tab2, tab3 = st.tabs(["📊 Spending Analysis", "🔮 Forecast", "🎯 Coach Check-in"])

with tab1:
    st.write("A plain-language summary of your recent spending patterns.")
    if st.button("Generate Analysis", key="analyst_btn"):
        with st.spinner("Analyzing your spending..."):
            st.session_state["analysis_result"] = run_agent(
                analyst_agent, "Give me a summary of my recent spending."
            )
    render_result("analysis_result")

with tab2:
    st.write("An estimate of your likely total spend next month, and why.")
    if st.button("Generate Forecast", key="forecast_btn"):
        with st.spinner("Working out your forecast..."):
            st.session_state["forecast_result"] = run_agent(
                forecaster_agent, "What am I likely to spend next month?"
            )
    render_result("forecast_result")

with tab3:
    st.write("How your budgets and savings goals are looking right now.")
    if st.button("Get Check-in", key="coach_btn"):
        with st.spinner("Checking your budgets and goals..."):
            st.session_state["coach_result"] = run_agent(
                coach_agent, "How am I doing with my budget and goals?"
            )
    render_result("coach_result")
