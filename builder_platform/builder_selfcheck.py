# -*- coding: utf-8 -*-
"""Standalone proof of the Day 2 AM builder (real LLM, no UI).

Modes:
  python builder_selfcheck.py --smoke   two cheap turns: proves SDK auth, the
                                        system-prompt injection, and that the
                                        builder opens the Step 1 design
                                        conversation in character.
  python builder_selfcheck.py           the full scripted design conversation:
                                        brief -> approvals -> implementation.
                                        PASSES only if a project exists in the
                                        workspace AND its selftest gate PASSed.

The driver is intentionally dumb: it walks a fixed script, then nudges with an
approval line until the build completes or the turn budget runs out — the
budget is the loop bound (never unbounded).
"""

from __future__ import annotations

import asyncio
import sys
import time
import uuid

from ask_protocol import format_card, parse_ask_block, visible_text
from builder import BuilderSession

# The transcript is LLM prose (em-dashes, curly quotes) rendered to whatever the
# console encoding happens to be; on a non-UTF-8 Windows console that raises
# UnicodeEncodeError mid-drive and kills a token-costing proof run.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SMOKE_TURNS = [
    "Hi! What can you help me build?",
]

# The wizard drives the rest via alta:ask cards; we answer per phase in the
# client's own plain language (never in platform jargon).
PHASE_ANSWERS = {
    "mission": (
        "BrightDesk is a help-desk SaaS for small IT teams — we resolve tickets "
        "40% faster with AI triage. The agent calls people who just signed up "
        "for a free trial, and its job is to see if they're a fit and book them "
        "a 30-minute demo with an account executive."
    ),
    "qualification": (
        "Before I'd book a meeting I need to know their team size (we serve 1 to "
        "500 agents), what help-desk tool they use today, and whether they're "
        "looking to switch this quarter or later. Their email is needed for the "
        "invite. Nice to know: whether they're on Slack or Teams."
    ),
    "objections": (
        "Two big ones. 'We already use Zendesk' — BrightDesk migrates every "
        "ticket in one click and costs half as much. 'It's too expensive' — the "
        "average team saves 11 hours per agent per month, so the Starter plan at "
        "$49 a seat pays for itself."
    ),
    "close": (
        "Success is a booked 30-minute demo. Read their email back to them "
        "before booking, and get a clear yes before it goes in the calendar. If "
        "they say no to a meeting, ask to send a short overview by email "
        "instead, thank them, and end politely."
    ),
    "boundaries": (
        "Don't quote custom or discounted pricing, don't promise a feature we "
        "don't have, and don't give technical migration or security advice "
        "beyond saying we're SOC 2 Type II certified. If someone is angry, asks "
        "for a human, or has a live support problem, hand them to a human SDR."
    ),
}

FULL_TURNS = [
    # One rich opener so the design conversation converges fast. The builder
    # should still run its steps; we've simply pre-answered most of Step 1.
    (
        "I want a voice SDR agent for 'BrightDesk', a help-desk SaaS for small "
        "IT teams (pitch: resolve tickets 40% faster with AI triage; plans: "
        "Starter $49/seat/month, Pro $99/seat/month, annual billing gets two "
        "months free; SOC 2 Type II certified; integrates with Slack and "
        "Teams). It calls inbound trial signups. Qualification is BANT-lite: "
        "team size (1-500 agents), current tooling (free text is fine), and "
        "timeline (this quarter / later). CTA: book a 30-minute demo with an "
        "account executive — collect their email for the invite and read it "
        "back before booking; booking needs a yes/no confirm. Mock the "
        "booking and lead-log tools (no live systems yet, the lead log just "
        "stores name/company/BANT answers). Top objections: 'we already use "
        "Zendesk' (rebuttal: BrightDesk migrates tickets in one click and "
        "costs half as much) and 'too expensive' (rebuttal: average team "
        "saves 11 hours/agent/month — the Starter plan pays for itself). "
        "Escalation goes to a human SDR via the platform's handoff flag. "
        "English only, no cross-session memory, standard tool budgets are "
        "fine, and use whatever model tiering you recommend for voice. "
        "You have my approval to make sensible default choices; please don't "
        "block on minor details."
    ),
]

NUDGE = ("Approved — proceed with your best judgment and sensible defaults. "
         "Finish the implementation and run the selftest.")

# The wizard spine costs ~8 turns (opener + 5 phase cards + review + build);
# the bound leaves slack for a re-ask without ever running unbounded.
MAX_DRIVER_TURNS = 14


FATAL_MARKERS = ("hit your session limit", "usage limit", "credit balance")


def reply_for(block: dict | None, nudge: str | None) -> str | None:
    """The client's next line, chosen from the builder's last ask-card."""
    if block is None:
        return nudge
    if block.get("kind") == "approve":
        return block.get("approve_label") or "Approved — please build it."
    answer = PHASE_ANSWERS.get(block.get("phase") or "")
    return answer or nudge


async def drive(turns: list[str], nudge: str | None, session: BuilderSession) -> None:
    sent = 0
    queue = list(turns)
    block: dict | None = None
    while sent < MAX_DRIVER_TURNS:
        if queue:
            msg = queue.pop(0)
        elif session.project_dir and session.selftest_passed:
            break
        else:
            msg = reply_for(block, nudge)
            if msg is None:
                break
        sent += 1
        print(f"\n>>> CLIENT [{sent}]: {msg[:120]}{'…' if len(msg) > 120 else ''}")
        t0 = time.time()
        turn_error = False
        turn_text = ""
        async for event in session.send(msg):
            if event["type"] == "text":
                turn_text += event["text"]
                if any(m in event["text"].lower() for m in FATAL_MARKERS):
                    turn_error = True
            elif event["type"] == "tool":
                print(f"    [tool: {event['name']}]")
            elif event["type"] == "result":
                print(f"    [turn done in {time.time() - t0:.0f}s | "
                      f"error={event['is_error']} "
                      f"project={event['project_dir']} "
                      f"selftest_passed={event['selftest_passed']}]")
                turn_error = turn_error or event["is_error"]
        # Render the turn the way the UI would: prose bubble, then the card.
        block = parse_ask_block(turn_text)
        said = visible_text(turn_text)
        if said:
            print(said)
        if block:
            print(format_card(block))
        if turn_error:
            print("\nFATAL TURN (quota/API failure) — aborting the drive; "
                  "nudging a dead session is waste.")
            break
        if session.project_dir and session.selftest_passed:
            break


async def main() -> int:
    smoke = "--smoke" in sys.argv
    session = BuilderSession(f"selfcheck_{uuid.uuid4().hex[:8]}")
    await session.start()
    try:
        if smoke:
            await drive(SMOKE_TURNS, nudge=None, session=session)
            print("\nSMOKE OK — builder responded; check the transcript above "
                  "for in-character Step 1 behavior.")
            return 0
        await drive(FULL_TURNS, nudge=NUDGE, session=session)
        ok = bool(session.project_dir) and session.selftest_passed
        print(f"\n{'BUILDER PROOF PASSED' if ok else 'BUILDER PROOF FAILED'} — "
              f"project={session.project_dir} selftest_passed={session.selftest_passed}")
        return 0 if ok else 1
    finally:
        await session.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
