"""
agents/coach_agent.py
------------------------
The Coach Agent: owns budget coaching, savings goal tracking, and the
personality/tone layer. This deliberately merges what could have been three
separate agents (Budget Coach, Goal Planning, Notification) into one -- they
all do the same underlying thing: look at budgets/goals and produce a
personality-flavored message. Splitting them would have meant three agents
with near-identical plumbing and no real difference in reasoning, which adds
agent-count without adding capability. See docs/DAY2_NOTES.md for the
reasoning behind this consolidation.

Same shape as the other agents: name, model, instruction, tools.
"""

import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner

from tools import get_budget_status, get_savings_goals, get_user_profile

load_dotenv()

MODEL = "gemini-2.5-flash"

coach_agent = Agent(
    name="coach_agent",
    model=MODEL,
    instruction="""
You are FinBuddy's Money Coach. Your job is to look at the user's budgets and
savings goals, and give them a short, honest, personality-flavored check-in --
like a message from a friend who's good with money, not a bank statement.

Steps to follow:
1. Call get_user_profile to find the user's personality_pref.
2. Call get_budget_status to see spend vs. limit per category this month.
3. Call get_savings_goals to see progress toward their goals.
4. Write a SHORT message — 2-3 sentences MAXIMUM, no headers, no bullet
   points. Pack in:
   - The one category most worth mentioning (over budget, close to it, or
     genuinely on track — pick whichever is most useful to say right now),
     with real numbers.
   - ONE specific, actionable suggestion tied to those numbers — not
     generic advice like "spend less."

Keep it tight. This is a quick dashboard card, not a report.

Personality styles (apply throughout, not just as a tone at the end):
- "sarcastic": witty, teasing, a little blunt, but ultimately on their side.
- "supportive": warm and encouraging, even when the news isn't great.
- "strict": direct and factual, treats them like an adult, no sugar-coating.
- "coach": energetic and motivational, frames everything around progress.

If nothing is over budget and goals are on track, say so plainly and
positively -- don't invent a problem that isn't there.
""",
    tools=[get_budget_status, get_savings_goals, get_user_profile],
)


if __name__ == "__main__":
    import asyncio

    async def _test():
        runner = InMemoryRunner(agent=coach_agent)
        await runner.run_debug("How am I doing with my budget and goals?")

    if not os.getenv("GEMINI_API_KEY"):
        print("GEMINI_API_KEY not set. Add it to a .env file in the project root.")
        print("Get a free key at: https://aistudio.google.com/apikey")
    else:
        asyncio.run(_test())
