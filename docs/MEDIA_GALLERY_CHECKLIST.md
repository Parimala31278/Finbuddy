# FinBuddy — Media Gallery Checklist

I can't take these myself (I can't see your app running on your machine),
but here's exactly what to capture and why each one matters for the
evaluation criteria.

## Required screenshots

1. **Cover image** — the Streamlit app's title screen (`💸 FinBuddy` header
   + sidebar visible). This is the first thing judges see; make sure the
   personality picker in the sidebar is visible since it's a distinctive
   feature.
2. **Spending Analysis tab** — after clicking "Generate Analysis," with a
   real result showing. Crop so both the button and the response are visible.
3. **Forecast tab** — same, showing a generated forecast with a real number.
4. **Coach Check-in tab** — same, ideally showing at least one budget
   category flagged as over/near limit, since that's the most concrete
   demonstration of the agent reasoning over real numbers rather than
   giving generic advice.
5. **Personality switch, before/after** — two screenshots of the *same*
   tab's output under two different personalities (e.g. sarcastic vs.
   strict) side by side. This is a strong, easy way to visually prove the
   personality system actually changes behavior, not just a label.
6. **Terminal output of the MCP server running standalone**
   (`python mcp_server/server.py`) — proves the MCP server is a real,
   independently runnable artifact, not just internal plumbing. Judges
   evaluating the "MCP Server" criterion will want to see this exists.
7. **Code screenshot (optional but recommended)** — `agents/tools.py` or
   one agent file, showing the tool functions and docstrings ADK uses to
   build tool schemas. Useful for the "Technical Implementation" criterion.

## YouTube demo video (≤ 5 minutes)

See `docs/DEMO_VIDEO_SCRIPT.md` for the full script and timing. Record your
screen while narrating — OBS Studio (free, open-source) or Windows'
built-in Xbox Game Bar (Win+G) both work with zero cost.

## Cover image specifically

If you want something more polished than a plain screenshot, a simple
option: take the title-screen screenshot above and add a one-line caption
overlay like "FinBuddy — Your AI Financial Companion" using any free tool
(Canva free tier, or even PowerPoint/Google Slides export as an image).
Not required, but it noticeably improves first impressions in a gallery of
many submissions.

## Where these go in the submission

- Kaggle write-up: embed inline where they support this claim in the text
  (e.g. the personality before/after pair right after you describe that
  feature).
- README.md: has placeholder `![Screenshot description](path/to/image.png)`
  markdown syntax already in the Screenshots section — swap in your actual
  image files once captured, saved to a new `docs/screenshots/` folder.
