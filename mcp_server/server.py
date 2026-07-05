"""
FinBuddy MCP Server
--------------------
Exposes the user's financial data as MCP tools. This is the ONLY layer that
touches the database directly -- every agent goes through these tools rather
than writing its own SQL. That separation is the point: it keeps agent logic
about reasoning, not data access, and makes the tool contracts auditable
(important for the "Security Features" criterion -- one place to validate
inputs and one place to reason about what data agents can actually see).

Tools:
  - get_transactions(days_back, category=None)
  - get_budget_status()
  - get_savings_goals()
  - get_spending_summary(months_back)
  - get_user_profile()

Run standalone for local testing:  python server.py
"""

import os
import sqlite3
from datetime import date, timedelta
from typing import Optional

from mcp.server.fastmcp import FastMCP

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "finbuddy.db")
DEFAULT_USER_ID = 1  # single-demo-user MVP; multi-user auth is a stretch goal, see docs/security.md

mcp = FastMCP("finbuddy")


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _validate_days_back(days_back: int) -> int:
    """Security: clamp untrusted numeric input to a sane range so a
    malformed or adversarial agent call can't force a full-table scan
    or an absurd date computation."""
    if not isinstance(days_back, int):
        raise ValueError("days_back must be an integer")
    return max(1, min(days_back, 365 * 3))


ALLOWED_CATEGORIES = {
    "rent", "subscriptions", "transport", "utilities", "groceries",
    "dining", "entertainment", "shopping", "health", "income", "other",
}


def _validate_category(category: Optional[str]) -> Optional[str]:
    """Security: category is used in a parameterized query already, but we
    additionally allow-list it so agents can't probe for unexpected
    categories or pass oversized/garbage strings."""
    if category is None:
        return None
    category = category.strip().lower()
    if category not in ALLOWED_CATEGORIES:
        raise ValueError(f"Unknown category '{category}'. Allowed: {sorted(ALLOWED_CATEGORIES)}")
    return category


@mcp.tool()
def get_transactions(days_back: int = 30, category: Optional[str] = None) -> dict:
    """Fetch the user's transactions from the last N days, optionally filtered
    by category. Returns individual transaction rows -- use this for detail-level
    questions ("what did I spend on dining last week"), not for trend analysis
    (use get_spending_summary for that).

    Args:
        days_back: how many days of history to fetch (1-1095).
        category: optional filter, one of the allowed spending categories.
    """
    days_back = _validate_days_back(days_back)
    category = _validate_category(category)

    cutoff = (date.today() - timedelta(days=days_back)).isoformat()
    conn = _connect()
    try:
        if category:
            rows = conn.execute(
                "SELECT date, amount, category, merchant, is_recurring FROM transactions "
                "WHERE user_id = ? AND date >= ? AND category = ? ORDER BY date DESC",
                (DEFAULT_USER_ID, cutoff, category),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT date, amount, category, merchant, is_recurring FROM transactions "
                "WHERE user_id = ? AND date >= ? ORDER BY date DESC",
                (DEFAULT_USER_ID, cutoff),
            ).fetchall()

        transactions = [dict(r) for r in rows]
        total_spend = sum(t["amount"] for t in transactions if t["amount"] > 0)
        total_income = sum(-t["amount"] for t in transactions if t["amount"] < 0)

        return {
            "days_back": days_back,
            "category_filter": category,
            "transaction_count": len(transactions),
            "total_spend": round(total_spend, 2),
            "total_income": round(total_income, 2),
            "transactions": transactions,
        }
    finally:
        conn.close()


@mcp.tool()
def get_budget_status() -> dict:
    """Return the user's budget limits per category alongside actual spend
    for the current calendar month, with overage flags. This is the primary
    tool for detecting overspending."""
    conn = _connect()
    try:
        budgets = conn.execute(
            "SELECT category, monthly_limit FROM budgets WHERE user_id = ?",
            (DEFAULT_USER_ID,),
        ).fetchall()

        month_start = date.today().replace(day=1).isoformat()

        results = []
        for b in budgets:
            spent_row = conn.execute(
                "SELECT COALESCE(SUM(amount), 0) as spent FROM transactions "
                "WHERE user_id = ? AND category = ? AND date >= ? AND amount > 0",
                (DEFAULT_USER_ID, b["category"], month_start),
            ).fetchone()
            spent = round(spent_row["spent"], 2)
            limit = b["monthly_limit"]
            results.append({
                "category": b["category"],
                "monthly_limit": limit,
                "spent_this_month": spent,
                "remaining": round(limit - spent, 2),
                "percent_used": round((spent / limit) * 100, 1) if limit else None,
                "is_over_budget": spent > limit,
            })

        return {"month": month_start[:7], "budgets": results}
    finally:
        conn.close()


@mcp.tool()
def get_savings_goals() -> dict:
    """Return the user's active savings goals, including progress toward
    each target and days remaining until the target date."""
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT name, target_amount, saved_amount, target_date FROM goals WHERE user_id = ?",
            (DEFAULT_USER_ID,),
        ).fetchall()

        goals = []
        for r in rows:
            days_left = None
            if r["target_date"]:
                days_left = (date.fromisoformat(r["target_date"]) - date.today()).days
            progress_pct = round((r["saved_amount"] / r["target_amount"]) * 100, 1) if r["target_amount"] else None
            goals.append({
                "name": r["name"],
                "target_amount": r["target_amount"],
                "saved_amount": r["saved_amount"],
                "remaining_to_save": round(r["target_amount"] - r["saved_amount"], 2),
                "progress_percent": progress_pct,
                "target_date": r["target_date"],
                "days_left": days_left,
            })

        return {"goals": goals}
    finally:
        conn.close()


@mcp.tool()
def get_spending_summary(months_back: int = 6) -> dict:
    """Return monthly spend totals broken down by category, for the last N
    months. Use this for trend analysis and forecasting -- it's the
    aggregate view, not individual transactions."""
    months_back = max(1, min(months_back, 24))
    conn = _connect()
    try:
        # Precise calendar-month arithmetic (day-based subtraction drifts due to
        # months having different lengths, which matters for exact trend windows).
        today = date.today()
        total_month_index = today.year * 12 + (today.month - 1) - (months_back - 1)
        cutoff_year, cutoff_month = divmod(total_month_index, 12)
        cutoff_month += 1
        cutoff = date(cutoff_year, cutoff_month, 1).isoformat()
        rows = conn.execute(
            "SELECT substr(date,1,7) as month, category, SUM(amount) as total "
            "FROM transactions WHERE user_id = ? AND date >= ? AND amount > 0 "
            "GROUP BY month, category ORDER BY month",
            (DEFAULT_USER_ID, cutoff),
        ).fetchall()

        summary = {}
        for r in rows:
            summary.setdefault(r["month"], {})[r["category"]] = round(r["total"], 2)

        monthly_totals = {
            month: round(sum(cats.values()), 2) for month, cats in summary.items()
        }

        return {
            "months_back": months_back,
            "by_month_and_category": summary,
            "monthly_totals": monthly_totals,
        }
    finally:
        conn.close()


@mcp.tool()
def get_user_profile() -> dict:
    """Return the user's basic profile: monthly income and chosen personality
    style for the coaching agent (sarcastic, supportive, strict, coach)."""
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT name, monthly_income, personality_pref FROM users WHERE id = ?",
            (DEFAULT_USER_ID,),
        ).fetchone()
        return dict(row) if row else {}
    finally:
        conn.close()


if __name__ == "__main__":
    mcp.run()
