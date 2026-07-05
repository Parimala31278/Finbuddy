"""
agents/analyst_agent.py
-------------------------
The Analyst Agent: looks at the user's transaction history and spending
trends, and produces a clear, plain-language summary -- top categories,
notable patterns, anything that stands out (e.g. a category creeping up,
an unusually large one-off purchase).

This is deliberately the simplest of the four agents. It's built first and
used as the template for Forecaster, Coach, and the Decision Orchestrator --
same shape every time: a name, a model, an instruction (role + personality),
and a short list of tool functions.

Run directly for a quick manual test:  python analyst_agent.py
(Requires GEMINI_API_KEY in your environment / .env file.)
"""

import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner

from tools import get_recent_transactions, get_monthly_spending_trend, get_user_profile

load_dotenv()

MODEL = "gemini-2.5-flash"  # free-tier model as of mid-2026; see README.md Setup section

analyst_agent = Agent(
    name="analyst_agent",
    model=MODEL,
    instruction="""
You are FinBuddy's Spending Analyst. Your only job is to look at the user's
transaction history and spending trends and summarize what's actually going on
-- in plain, everyday language, not financial jargon.

Steps to follow:
1. Call get_user_profile to see the user's income and preferred personality style.
2. Call get_monthly_spending_trend to see spending trends over recent months.
3. Call get_recent_transactions (last 30 days) to see recent detail.
4. Write a SHORT summary — 2-3 sentences maximum, no bullet points, no headers.
   Cover only:
   - Their top 1-2 spending categories recently.
   - One clear trend or specific observation worth mentioning.

Keep it tight. This is a quick dashboard card, not a report.

Match your tone to the user's personality_pref from their profile:
- "sarcastic": witty, teasing, a little blunt, but never mean.
- "supportive": warm, encouraging, gentle even when flagging a problem.
- "strict": direct, no-nonsense, treats the user like an adult who needs facts.
- "coach": energetic, motivational, framed around progress and goals.

Do NOT give buy/don't-buy advice here -- that's a different agent's job.
Just report what the data shows, clearly and honestly.
""",
    tools=[get_recent_transactions, get_monthly_spending_trend, get_user_profile],
)


if __name__ == "__main__":
    import asyncio

    async def _test():
        runner = InMemoryRunner(agent=analyst_agent)
        await runner.run_debug("Give me a summary of my recent spending.")

    if not os.getenv("GEMINI_API_KEY"):
        print("GEMINI_API_KEY not set. Add it to a .env file in the project root.")
        print("Get a free key at: https://aistudio.google.com/apikey")
    else:
        asyncio.run(_test())
