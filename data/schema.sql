-- FinBuddy Database Schema
-- Kept intentionally simple so each MCP tool maps to a clear, obvious query.

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    monthly_income REAL NOT NULL,
    personality_pref TEXT DEFAULT 'sarcastic'  -- sarcastic | supportive | strict | coach
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    date TEXT NOT NULL,           -- ISO format YYYY-MM-DD
    amount REAL NOT NULL,         -- positive = expense, negative = income credit
    category TEXT NOT NULL,       -- rent, groceries, dining, entertainment, utilities, subscriptions, transport, shopping, health, income, other
    merchant TEXT,
    is_recurring INTEGER DEFAULT 0  -- 1 if this is a fixed/recurring line item
);

CREATE TABLE IF NOT EXISTS goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    name TEXT NOT NULL,
    target_amount REAL NOT NULL,
    saved_amount REAL DEFAULT 0,
    target_date TEXT   -- ISO format YYYY-MM-DD
);

CREATE TABLE IF NOT EXISTS budgets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    category TEXT NOT NULL,
    monthly_limit REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tx_user_date ON transactions(user_id, date);
CREATE INDEX IF NOT EXISTS idx_tx_category ON transactions(user_id, category);
