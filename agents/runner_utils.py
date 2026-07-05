"""
agents/runner_utils.py
--------------------------
One small shared helper: run an ADK agent with a message and get back a
plain text string. The UI needs to *display* an agent's answer, not just
print it to a console (which is all InMemoryRunner.run_debug does), so this
wraps the lower-level session + event-loop mechanics in a single function.

Kept in one place so every agent (and the Streamlit UI) uses the exact same
pattern -- no copy-pasted session/event handling per agent.

Retry behavior (kept deliberately simple, not a generic retry framework):
- Transient server errors (Gemini overloaded, 503/500-range) are retried a
  few times with a short wait -- these usually clear up on their own within
  seconds.
- Quota errors (429) are NOT retried automatically. Retrying immediately
  against a rate/quota limit just wastes more of the same limited quota.
  Instead we fail fast with a clear, friendly message.
- Any other unexpected error is also surfaced as a friendly message rather
  than letting a raw traceback crash the Streamlit page.
"""

import asyncio
import time
import uuid
from google.genai import types
from google.genai import errors as genai_errors
from google.adk.runners import InMemoryRunner

MAX_RETRIES = 3
RETRY_WAIT_SECONDS = 5


async def _run_agent_async(agent, message: str):
    runner = InMemoryRunner(agent=agent)
    user_id = "demo_user"
    session_id = str(uuid.uuid4())

    await runner.session_service.create_session(
        app_name=runner.app_name, user_id=user_id, session_id=session_id
    )

    content = types.Content(role="user", parts=[types.Part(text=message)])

    final_text = ""
    trace = []  # list of {"tool": name, "args": {...}, "result": {...}} -- the proof trail

    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=content
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.function_call:
                    trace.append({
                        "tool": part.function_call.name,
                        "args": dict(part.function_call.args or {}),
                        "result": None,
                    })
                if part.function_response:
                    # attach the result to the matching most-recent call of that tool
                    for t in reversed(trace):
                        if t["tool"] == part.function_response.name and t["result"] is None:
                            t["result"] = part.function_response.response
                            break

        if event.is_final_response() and event.content and event.content.parts:
            final_text = "".join(p.text or "" for p in event.content.parts)

    await runner.close()
    return final_text, trace


def run_agent(agent, message: str):
    """Synchronous entry point -- call this from Streamlit code.

    Args:
        agent: an ADK Agent instance (e.g. analyst_agent).
        message: the prompt to send it.

    Returns:
        A (text, trace) tuple. `text` is the agent's final response, or a
        friendly error message if the call ultimately failed (never raises
        -- the UI can always just display the returned string). `trace` is
        a list of {"tool", "args", "result"} dicts showing exactly which
        tools were called and what real data came back -- useful for
        demonstrating that the agent is grounded in real data, not just
        generating plausible-sounding text. `trace` is an empty list on error.
    """
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return asyncio.run(_run_agent_async(agent, message))

        except genai_errors.ClientError as e:
            # 429 = quota/rate limit. Don't retry -- it won't help, and it
            # burns more of the same limited quota. Fail fast and clearly.
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                return (
                    "⚠️ Free-tier quota reached — please wait a bit and try again.",
                    [],
                )
            last_error = e

        except genai_errors.ServerError as e:
            # 503/500-range = Google's servers are temporarily overloaded.
            # Usually clears up within seconds -- worth a short retry.
            last_error = e
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_WAIT_SECONDS)
                continue

        except Exception as e:  # noqa: BLE001 -- last-resort safety net for the UI
            last_error = e
            break

    return (
        f"⚠️ Couldn't get a response after {MAX_RETRIES} attempts. Please try again shortly.\n\nDetails: {last_error}",
        [],
    )
