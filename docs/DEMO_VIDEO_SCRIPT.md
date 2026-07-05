# FinBuddy — Demo Video Script (Target: ~4:30)

Speak at a natural, unhurried pace (~130-140 words/minute). Each section
below has an approximate word count and timestamp so you can rehearse
against a stopwatch. Practice once before recording — you'll naturally
compress the slower parts on a second pass.

---

## [0:00–0:25] Introduction (~55 words)

> "Hi, I'm [your name], and this is FinBuddy — an AI financial companion I
> built for the Google times Kaggle AI Agents Intensive Vibe Coding
> Capstone. Most budgeting apps just show you numbers after the fact.
> FinBuddy uses a team of specialized AI agents to actually reason about
> your spending and talk to you like a friend who's good with money —
> not a spreadsheet."

## [0:25–1:00] Problem statement (~75 words)

> "Here's the problem: digital payments make spending frictionless, but
> that same convenience makes overspending invisible until the damage is
> done. Traditional budgeting apps are passive — they log what already
> happened. They don't predict what's coming, they don't understand your
> goals, and they definitely don't talk to you in a way that actually
> lands. People don't need another expense tracker. They need something
> that reasons about their money the way a smart friend would."

## [1:00–1:35] Why AI agents (~70 words)

> "This is where agents matter, not just an LLM wrapper. A single chatbot
> can answer questions, but it can't independently analyze trends, run a
> forecast, and check your goals in a coordinated way. FinBuddy uses three
> specialized ADK agents — an Analyst, a Forecaster, and a Coach — each
> with its own reasoning role and its own tools, all working from the same
> underlying financial data."

## [1:35–2:15] Architecture overview (~85 words)

> "Under the hood, all financial data lives in SQLite, accessed through a
> real MCP server I built — that's the single source of truth every agent
> reads from, which keeps the whole system auditable. Each agent — Analyst,
> Forecaster, Coach — is a Google ADK agent backed by Gemini 2.5 Flash,
> with its own narrow set of tools. The Coach Agent also owns something I
> think matters a lot for adoption: a personality system. You can pick
> sarcastic, supportive, strict, or coach mode, and every agent adjusts its
> tone accordingly."

*(Show the architecture diagram from docs/ARCHITECTURE.md on screen here.)*

## [2:15–4:00] Live demonstration (~215 words spoken + live interaction)

> "Let me show you it running."

*(Screen-record the actual Streamlit app here. Suggested flow:)*

1. Show the sidebar personality picker — switch it to "sarcastic."
2. Click "Generate Analysis" — narrate what's happening while it loads:
   > "This is a live call to Gemini right now — the agent is calling real
   > tool functions to pull my actual transaction history and spending
   > trends before it says anything."
3. Read a sentence or two of the result aloud, pointing out that it
   references specific real numbers, not generic advice.
4. Switch to the Forecast tab, click "Generate Forecast":
   > "Same pattern — this agent looks at 6 months of spending trends and
   > gives a grounded estimate for next month, with its reasoning, not
   > just a number."
5. Switch to Coach Check-in:
   > "And this one checks my actual budget limits and savings goals — if
   > I'm over budget somewhere, it'll call that out by name, with the real
   > numbers."
6. Switch personality to "strict" and re-click one button to show the tone
   changing on the same underlying data:
   > "Same data, same agent — just a different voice. That's a config
   > value, not a different codebase."

## [4:00–4:20] Technologies used (~45 words)

> "This runs entirely on free tools: Google ADK for the agents, Gemini
> 2.5 Flash's free tier for reasoning, a custom MCP server for data access,
> SQLite for storage, and Streamlit for the interface. No paid APIs, no
> credit card, anywhere in this stack."

## [4:20–4:30] Conclusion (~35 words)

> "FinBuddy shows that a small team of purpose-built agents can do more
> than one big chatbot — real reasoning, real tools, real personality.
> Thanks for watching — the full code is on GitHub, linked below."

---

## Recording tips

- Record the screen and voice separately if your tool allows it — much
  easier to redo a flubbed sentence without re-recording the whole demo.
- Test your personality-switch demo moment beforehand — pick an example
  where the tone difference is obvious, not subtle.
- If you hit a Gemini quota error live, don't panic — pause the recording,
  wait a minute, resume. Nobody needs to see the raw take.
