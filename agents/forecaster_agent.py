"""
agents/forecaster_agent.py
-----------------------------
The Forecaster Agent: predicts next month's likely spending based on recent
trends and known recurring costs.

Design note: this is intentionally an LLM-reasoning forecast, not a statistical
/ ML time-series model. For a 2-3 day agentic-AI capstone, a proper ARIMA/Prophet
pipeline would be scope creep that doesn't demonstrate agent concepts any better
-- the point here is the agent reasoning over structured data and producing a
grounded, explained estimate, which is exactly what "Prediction Agent" means in
the context of this capstone. A real statistical model is listed in
docs/FUTURE_SCOPE.md as a stretch goal, not attempted here.

Same shape as analyst_agent.py: name, model, instruction, tools.
"""

import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner

from tools import get_monthly_spending_trend, get_recent_transactions

load_dotenv()

MODEL = "gemini-2.5-flash"

forecaster_agent = Agent(
    name="forecaster_agent",
    model=MODEL,
    instruction="""
You are FinBuddy's Forecaster. Your job is to estimate the user's likely total
spending for the NEXT calendar month, with a short explanation of how you got there.

Steps to follow:
1. Call get_monthly_spending_trend (use months_back=6) to see spend by month
   and by category.
2. Call get_recent_transactions (days_back=30) to see what's recurring vs
   one-off in the most recent month.
3. Reason step by step:
   - Identify which costs are recurring/fixed (rent, subscriptions, utilities)
     and will almost certainly repeat.
   - Look at the trend in discretionary categories (dining, shopping,
     entertainment, etc.) across months -- is it rising, falling, or stable?
   - Note if the most recent month looks unusually high or low compared to
     the trend (a possible one-off spike, not necessarily indicative of next month).
4. Give your answer in 2 SHORT sentences total, no headers, no bullet points:
   one sentence with the number/range (e.g. "₹52,000-₹58,000"), one sentence
   naming the single biggest driver of that estimate.

Be honest about uncertainty, but stay brief -- this is a quick dashboard
card, not a report. Do not give buy/don't-buy advice; that's a different
agent's job.
""",
    tools=[get_monthly_spending_trend, get_recent_transactions],
)


if __name__ == "__main__":
    import asyncio

    async def _test():
        runner = InMemoryRunner(agent=forecaster_agent)
        await runner.run_debug("What am I likely to spend next month?")

    if not os.getenv("GEMINI_API_KEY"):
        print("GEMINI_API_KEY not set. Add it to a .env file in the project root.")
        print("Get a free key at: https://aistudio.google.com/apikey")
    else:
        asyncio.run(_test())
