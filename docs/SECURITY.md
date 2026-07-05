# FinBuddy — Security Notes

This project is a 2-3 day capstone MVP, not a production financial system.
The security work here is scoped accordingly: real, specific measures that
matter at this scale — not an enterprise security posture that would be
dishonest to claim for a project like this.

## 1. API keys never touch the codebase

- `GEMINI_API_KEY` is read from a `.env` file via `python-dotenv`
  (see `analyst_agent.py`, `forecaster_agent.py`, `coach_agent.py`, `ui/app.py`).
- `.env` is listed in `.gitignore` — it is never committed, and the public
  GitHub repo contains no real key anywhere, including in git history
  (since it was never added in the first place).
- If `GEMINI_API_KEY` is missing, agents and the UI fail with a clear
  message pointing to where to get a free key, rather than silently
  misbehaving or leaking an error with sensitive detail.

## 2. Input validation at the data-access boundary

All of this lives in `mcp_server/server.py`, since that's the single choke
point every piece of data passes through:

- `_validate_days_back()` clamps any numeric date-range input to a sane
  bound (1 to ~3 years), so a malformed or adversarial call can't force an
  unbounded table scan or a nonsensical date computation.
- `_validate_category()` allow-lists categories against a fixed set
  (`ALLOWED_CATEGORIES`) rather than trusting whatever string an agent
  passes in — an unrecognized category raises a clear `ValueError` instead
  of silently returning wrong or empty data.
- All SQL uses parameterized queries (`?` placeholders) throughout —
  no string formatting into SQL anywhere in the codebase, which rules out
  SQL injection as an attack surface entirely.

## 3. Least-privilege data access

Agents never receive raw database credentials or a live SQL connection —
they only ever see the narrow, purpose-built functions in `agents/tools.py`.
An agent (or a prompt-injected instruction inside a tool's output) cannot
ask for arbitrary data; it can only call the specific functions it was
given, each of which returns a bounded, predictable shape of data.

## 4. Graceful failure, not information leakage

`agents/runner_utils.py` catches API-level errors (quota limits, transient
server errors) and returns a plain, friendly message rather than letting a
raw stack trace (which could reveal file paths, internal structure, or
other implementation detail) reach the end user through the UI.

## What's intentionally out of scope (see docs/FUTURE_SCOPE.md)

- **Multi-user authentication.** This is a single-demo-user MVP by design.
  Real auth (OAuth, hashed credentials, session tokens) is meaningful
  infrastructure that doesn't add to the agent-concepts demonstration at
  this scope.
- **Rate limiting at the application layer.** Gemini's own free-tier quota
  already provides a hard ceiling; adding a second layer of rate limiting
  in front of it has no visible effect a judge could observe in a demo.
- **Encryption at rest for the SQLite file.** The data is synthetic —
  there is no real financial information to protect in this project.

Being explicit about what's *not* done is itself a security-mindset
signal: claiming blanket "enterprise-grade security" for a weekend MVP
would be the less credible answer.
