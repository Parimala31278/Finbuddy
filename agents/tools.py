"""
agents/tools.py
-----------------
Thin pass-through wrappers around the MCP server's functions (mcp_server/server.py),
exposed as plain Python functions so ADK agents can use them as tools directly.

Why wrap instead of import raw: ADK reads each function's docstring and type hints
to build the tool schema the model sees. The MCP server's docstrings are written
for MCP tool discovery; keeping a thin wrapper layer here means we can tune each
tool's description for agent reasoning independently, without touching the server.

The underlying MCP server (mcp_server/server.py) remains a fully standalone,
runnable MCP server -- this file does not replace it, it reuses its logic.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp_server"))
import server as _mcp  # the actual MCP server module


def get_recent_transactions(days_back: int = 30, category: str = "") -> dict:
    """Get the user's individual transactions from the last N days.
    Use this for specific, detail-level questions.

    Args:
        days_back: number of days of history to fetch (1-1095).
        category: optional category filter (e.g. "dining", "shopping").
                  Pass an empty string for no filter.
    """
    cat = category.strip() or None
    return _mcp.get_transactions(days_back=days_back, category=cat)


def get_budget_status() -> dict:
    """Get the user's budget limits vs. actual spend for the current month,
    per category, including which categories are over budget."""
    return _mcp.get_budget_status()


def get_savings_goals() -> dict:
    """Get the user's active savings goals and progress toward each."""
    return _mcp.get_savings_goals()


def get_monthly_spending_trend(months_back: int = 6) -> dict:
    """Get monthly spending totals broken down by category, for trend analysis.
    Use this to answer questions about patterns over time, not single transactions.

    Args:
        months_back: how many months of history to summarize (1-24).
    """
    return _mcp.get_spending_summary(months_back=months_back)


def get_user_profile() -> dict:
    """Get the user's monthly income and preferred coaching personality
    (sarcastic, supportive, strict, or coach)."""
    return _mcp.get_user_profile()
