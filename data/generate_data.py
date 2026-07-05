"""
FinBuddy Synthetic Data Generator
----------------------------------
Generates 6 months of realistic transaction history for a demo user.

Design goals (why this isn't just random.randint everywhere):
1. Fixed recurring costs (rent, subscriptions) -> same day, same amount every month.
2. Variable recurring costs (utilities, groceries) -> same rough timing, amount
   fluctuates in a believable band.
3. Discretionary spending -> category-weighted, with weekend spikes for
   dining/entertainment, so overspending patterns are detectable.
4. A slow creeping increase in discretionary spend over the 6 months
   (a "lifestyle inflation" pattern) so the Analyst Agent has something
   real to catch.
5. One seasonal spike month (simulating a festive/holiday season) so the
   Forecaster Agent has a genuine anomaly to reason about, not just noise.
6. Two income deposits per month (salary split), consistent day-of-month.

Run: python generate_data.py
Produces: finbuddy.db (SQLite) in the same directory.
"""

import sqlite3
import random
from datetime import date, timedelta
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "finbuddy.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

random.seed(42)  # reproducible demo data -- important for judges re-running this

MONTHLY_INCOME = 65000.0  # e.g. INR, but currency-agnostic for the demo
MONTHS_OF_HISTORY = 6
SEASONAL_SPIKE_MONTH_OFFSET = 4  # the 5th month back gets a spending spike

FIXED_RECURRING = [
    # (category, merchant, amount, day_of_month)
    ("rent", "Skyline Apartments", 18000, 1),
    ("subscriptions", "Netflix", 649, 5),
    ("subscriptions", "Spotify", 119, 7),
    ("subscriptions", "Cloud Storage Plus", 299, 10),
    ("transport", "Metro Pass", 1200, 1),
]

VARIABLE_RECURRING = [
    # (category, merchant, base_amount, day_of_month, variance_pct)
    ("utilities", "PowerGrid Electric", 2200, 8, 0.25),
    ("utilities", "AquaCity Water", 450, 8, 0.15),
    ("utilities", "FiberNet Broadband", 999, 12, 0.05),
    ("groceries", "FreshMart", 6000, 15, 0.20),
]

DISCRETIONARY_CATEGORIES = [
    # (category, merchant_options, min_amt, max_amt, weekend_weight_multiplier)
    ("dining", ["Cafe Aroma", "Spice Route", "Burger Junction", "Sushi Bar"], 150, 1200, 2.5),
    ("entertainment", ["CineMax", "Game Lounge", "StreamPlay PPV", "Bowling Alley"], 200, 1500, 3.0),
    ("shopping", ["StyleHub", "QuickMart", "TechBazaar", "UrbanWear"], 300, 5000, 1.3),
    ("transport", ["RideNow Cab", "QuickAuto"], 80, 600, 1.5),
    ("health", ["MedPlus Pharmacy", "FitZone Gym Day Pass"], 200, 2000, 1.0),
    ("other", ["Misc Purchase"], 100, 1000, 1.0),
]


def build_schema(conn):
    with open(SCHEMA_PATH, "r") as f:
        conn.executescript(f.read())


def create_demo_user(conn):
    cur = conn.execute(
        "INSERT INTO users (name, monthly_income, personality_pref) VALUES (?, ?, ?)",
        ("Demo User", MONTHLY_INCOME, "sarcastic"),
    )
    conn.commit()
    return cur.lastrowid


def month_start_dates(months_back):
    today = date.today()
    starts = []
    year, month = today.year, today.month
    for i in range(months_back):
        m = month - i
        y = year
        while m <= 0:
            m += 12
            y -= 1
        starts.append(date(y, m, 1))
    return list(reversed(starts))  # oldest first


def safe_day(year, month, day):
    """Clamp day to a valid date for that month (handles Feb, 30-day months)."""
    next_month = date(year + (month // 12), (month % 12) + 1, 1)
    last_day = (next_month - timedelta(days=1)).day
    return min(day, last_day)


def insert_tx(conn, user_id, d, amount, category, merchant, is_recurring):
    conn.execute(
        "INSERT INTO transactions (user_id, date, amount, category, merchant, is_recurring) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, d.isoformat(), round(amount, 2), category, merchant, int(is_recurring)),
    )


def generate_month(conn, user_id, month_start, month_index, total_months, is_spike_month):
    y, m = month_start.year, month_start.month
    today = date.today()
    is_current_month = (y == today.year and m == today.month)

    # --- Income: salary split into two deposits (skip if the pay date hasn't happened yet) ---
    pay_day_1 = date(y, m, safe_day(y, m, 1))
    if not is_current_month or pay_day_1 <= today:
        insert_tx(conn, user_id, pay_day_1, -MONTHLY_INCOME * 0.6, "income", "Employer Payroll", True)
    pay_day_2 = date(y, m, safe_day(y, m, 16))
    if not is_current_month or pay_day_2 <= today:
        insert_tx(conn, user_id, pay_day_2, -MONTHLY_INCOME * 0.4, "income", "Employer Payroll", True)

    # --- Fixed recurring costs (only if the due date has already occurred, for the current month) ---
    for category, merchant, amount, day in FIXED_RECURRING:
        d = date(y, m, safe_day(y, m, day))
        if not is_current_month or d <= today:
            insert_tx(conn, user_id, d, amount, category, merchant, True)

    # --- Variable recurring costs (same rule) ---
    for category, merchant, base_amount, day, variance in VARIABLE_RECURRING:
        d = date(y, m, safe_day(y, m, day))
        if not is_current_month or d <= today:
            amt = base_amount * random.uniform(1 - variance, 1 + variance)
            insert_tx(conn, user_id, d, amt, category, merchant, True)

    # --- Lifestyle inflation factor: discretionary spend creeps up over time ---
    # month_index 0 = oldest month, increases toward present. Applied as a per-month
    # multiplier (not per-transaction) so the trend reads clearly across months
    # instead of being drowned out by per-transaction randomness.
    inflation_factor = 1.0 + (month_index / max(total_months - 1, 1)) * 0.65  # up to +65%

    # --- Seasonal spike multiplier (one specific month simulates festive spending) ---
    spike_multiplier = 1.9 if is_spike_month else 1.0

    # --- Discretionary spending: random days across the month, weekend-weighted ---
    next_month_date = date(y + (m // 12), (m % 12) + 1, 1)
    days_in_month = (next_month_date - month_start).days
    # If this is the current (partial) month, only generate up to today.
    max_day_offset = min(days_in_month, (today - month_start).days + 1) if is_current_month else days_in_month

    base_tx_count = random.randint(20, 24)  # number of discretionary transactions this month
    # Scale expected tx count down proportionally for a partial current month.
    if is_current_month:
        base_tx_count = max(1, int(base_tx_count * max_day_offset / days_in_month))
    tx_count = int(base_tx_count * (1.0 + (inflation_factor - 1.0) * 0.4))  # count grows a little, amount grows more

    for _ in range(tx_count):
        day_offset = random.randint(0, max_day_offset - 1)
        tx_date = month_start + timedelta(days=day_offset)
        is_weekend = tx_date.weekday() >= 5

        category, merchants, min_amt, max_amt, weekend_mult = random.choice(DISCRETIONARY_CATEGORIES)
        merchant = random.choice(merchants)

        weight = weekend_mult if is_weekend else 1.0
        # tighter per-transaction randomness (0.85x-1.15x) so the month-level
        # inflation_factor trend is visible rather than swamped by noise
        amount = random.uniform(min_amt, max_amt) * weight * inflation_factor * spike_multiplier
        amount *= random.uniform(0.9, 1.1)

        insert_tx(conn, user_id, tx_date, amount, category, merchant, False)


def generate_goals_and_budgets(conn, user_id):
    conn.execute(
        "INSERT INTO goals (user_id, name, target_amount, saved_amount, target_date) VALUES (?, ?, ?, ?, ?)",
        (user_id, "Emergency Fund", 100000, 32000, (date.today() + timedelta(days=240)).isoformat()),
    )
    conn.execute(
        "INSERT INTO goals (user_id, name, target_amount, saved_amount, target_date) VALUES (?, ?, ?, ?, ?)",
        (user_id, "New Laptop", 75000, 18000, (date.today() + timedelta(days=90)).isoformat()),
    )

    budgets = [
        ("dining", 4000),
        ("entertainment", 3000),
        ("shopping", 5000),
        ("groceries", 7000),
        ("transport", 2500),
    ]
    for category, limit in budgets:
        conn.execute(
            "INSERT INTO budgets (user_id, category, monthly_limit) VALUES (?, ?, ?)",
            (user_id, category, limit),
        )
    conn.commit()


def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    build_schema(conn)
    user_id = create_demo_user(conn)

    months = month_start_dates(MONTHS_OF_HISTORY)
    spike_index = max(len(months) - 1 - SEASONAL_SPIKE_MONTH_OFFSET, 0)

    for i, month_start in enumerate(months):
        generate_month(
            conn, user_id, month_start,
            month_index=i, total_months=len(months),
            is_spike_month=(i == spike_index),
        )

    generate_goals_and_budgets(conn, user_id)
    conn.commit()

    tx_count = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    print(f"Generated {tx_count} transactions for user_id={user_id} across {len(months)} months.")
    print(f"Database written to: {DB_PATH}")
    conn.close()


if __name__ == "__main__":
    main()
