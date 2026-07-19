# Integration: Google Calendar — Event Booking & Cancellation

<!-- Promoted 2026-07-12. Wiring validated selftest-green (hook + structural +
     filler gates) + happy/failure path through the real graph. Live path is
     proven per-client at implement-time once prerequisites validate. -->

## Metadata
- **id:** `google_calendar_booking`
- **source system / API version:** Google Calendar API **v3** (`events.insert`, `events.delete`)
- **transport:** `MCP` (a Google Calendar MCP server)  |  `vendor SDK` (`google-api-python-client`)
- **auth:** OAuth 2.0 user consent, scope `https://www.googleapis.com/auth/calendar.events` — **client owns this; recipe ships none**
- **entity IDs:** event id = Google's **opaque** id (base32hex, `[A-Za-z0-9_-]{5,1024}`); calendar id = `primary` or an email-like id
- **stakes:** `confirm=True` on BOTH flows (creating and deleting an event are real-world changes; not money → confirm, not `hitl`)
- **wiring last validated:** 2026-07-12 (selftest-green: hook + structural + filler gates + happy/failure path)
- **live-validation:** per-client at implement-time (needs the client's OAuth)

## What it gives you
Two flows on the user's primary Google Calendar: **`schedule_event`** (create an
event from a title, start time, and duration) and **`cancel_event`** (delete by
event id). Both confirm before acting; `schedule_event` caches the returned
`event_id` into `session_facts` so a follow-up cancel can reference it.

## 1. Prerequisites (the Validate gate — confirm BEFORE implementing live)
Block here if any are missing; hand the client these exact steps. Do NOT ship the
mock as if it were real.
- [ ] A Google Cloud project with the **Calendar API enabled**.
- [ ] An **OAuth 2.0 client** (Desktop or Web) and a completed consent granting scope
      `https://www.googleapis.com/auth/calendar.events` (use `.../auth/calendar` if you also read).
- [ ] A stored **authorized-user token** the process can load at startup (the SDK refreshes it).
- [ ] Transport ready: EITHER a running **Google Calendar MCP server**, OR
      `pip install google-api-python-client google-auth google-auth-oauthlib`.
- [ ] Account config: `GCAL_CALENDAR_ID` (default `primary`) and `GCAL_TIMEZONE` (IANA, e.g. `America/New_York`).

**Credential files this recipe puts on disk** — confirm each is in the generated agent's
`.gitignore` (Step 4.3): the OAuth client (`credentials.json` / `client_secret*.json`) and
the refreshed authorized-user token at `GCAL_TOKEN_PATH` (`token.json` by default). If the
client points `GCAL_TOKEN_PATH` somewhere else, that exact path must be added.

## 2. config.py — FLOWS  *(paste into `FLOWS`)*
```python
"schedule_event": Flow(
    tool="create_event",
    slots=("summary", "start_time", "duration_min"),
    slot_prompts={
        "summary": "what the event is (a short title)",
        "start_time": "what day and time it should start",
        "duration_min": "how long it should run (in minutes)",
    },
    confirm=True,
    confirm_template="Just to confirm — schedule \"{summary}\" starting {start_time} for {duration_min} minutes? (yes/no)",
    validators={"start_time": _validate_start_time, "duration_min": _validate_duration},
    cache_keys=("event_id",),
),
"cancel_event": Flow(
    tool="delete_event",
    slots=("event_id",),
    slot_prompts={"event_id": "the event id to cancel (from the booking confirmation)"},
    confirm=True,
    confirm_template="Just to confirm — cancel event {event_id}? (yes/no)",
    validators={"event_id": _validate_event_id},
),
```

## config.py — validators  *(paste; no ENTITY_RESOLVERS — no catalog to ground against)*
```python
from datetime import datetime  # (config already imports datetime/timedelta)

def _validate_start_time(value: str, _slots: dict) -> tuple[bool, str]:
    """Well-formed ISO-8601/RFC3339, not in the past. In LIVE mode the ANSWER
    tier produces this from natural language with the current date injected — the
    validator grounds format + past, it does not parse NL itself. Idempotent."""
    v = (value or "").strip()
    try:
        dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
    except ValueError:
        return False, "What day and time should I set it for? (e.g. tomorrow at 3pm)"
    ref = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
    if dt < ref:
        return False, "That time is in the past — what upcoming day and time works?"
    return True, dt.isoformat()

def _validate_duration(value: str, _slots: dict) -> tuple[bool, str]:
    import re
    digits = re.sub(r"\D", "", str(value or ""))
    if not digits:
        return False, "How long should it run — 30 minutes, an hour?"
    mins = int(digits)
    if 15 <= mins <= 480:
        return True, str(mins)
    return False, "Events can run 15 minutes to 8 hours — how long should this one be?"

def _validate_event_id(value: str, _slots: dict) -> tuple[bool, str]:
    """Accepts Google's opaque base32hex event ids (and the mock's EVT-#####)."""
    import re
    v = (value or "").strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{5,1024}", v):
        return True, v
    return False, "What's the event id to cancel? (from the confirmation when it was booked)"
```

## config.py — NEXT_STEP_HINTS / FILLERS_BY_TOOL  *(paste; [CUSTOMIZE tone])*
```python
# NEXT_STEP_HINTS entries:
"create_event": "You can cancel it any time with its event id.",
"delete_event": "",

# FILLERS_BY_TOOL entries — reword in THIS agent's voice:
"create_event": ["Let me add that to your calendar…", "Setting that up now…", "One sec — putting that on the calendar…"],
"delete_event": ["Let me cancel that for you…", "Taking that off your calendar now…", "One moment while I clear that…"],
```

## 3. tools.py — LIVE tool body  *(the ship target)*
```python
import os
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials

# Build the authorized service ONCE at startup from the client's stored token.
_SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
_creds = Credentials.from_authorized_user_file(os.environ["GCAL_TOKEN_PATH"], _SCOPES)
_service = build("calendar", "v3", credentials=_creds, cache_discovery=False)
_CAL_ID = os.getenv("GCAL_CALENDAR_ID", "primary")
_TZ = os.getenv("GCAL_TIMEZONE", "UTC")

def create_event(summary: str = "", start_time: str = "", duration_min: str = "", **_) -> dict:
    start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
    end_dt = start_dt + timedelta(minutes=int(duration_min))
    body = {"summary": summary,
            "start": {"dateTime": start_dt.isoformat(), "timeZone": _TZ},
            "end":   {"dateTime": end_dt.isoformat(),   "timeZone": _TZ}}
    try:
        ev = _service.events().insert(calendarId=_CAL_ID, body=body).execute()
    except HttpError as e:
        return {"tool": "create_event", "error": str(e), "summary": "I couldn't create that event."}
    return {"tool": "create_event", "event_id": ev["id"], "html_link": ev.get("htmlLink"),
            "start": ev["start"]["dateTime"], "status": ev.get("status"),
            "summary": f'Scheduled "{summary}" for {start_time} ({duration_min} min). Event id {ev["id"]}.'}

def delete_event(event_id: str = "", **_) -> dict:
    try:
        _service.events().delete(calendarId=_CAL_ID, eventId=event_id).execute()
    except HttpError as e:
        if getattr(getattr(e, "resp", None), "status", None) == 404:
            return {"tool": "delete_event", "event_id": event_id, "error": "event not found",
                    "summary": "I couldn't find an event with that id."}
        return {"tool": "delete_event", "event_id": event_id, "error": str(e),
                "summary": "I couldn't cancel that event."}
    return {"tool": "delete_event", "event_id": event_id, "cancelled": True,
            "summary": f"Cancelled event {event_id}."}
# TOOL_REGISTRY["create_event"] = create_event ; TOOL_REGISTRY["delete_event"] = delete_event
#
# --- OR, MCP transport (server exposes create_event/delete_event with these arg names): ---
# await tools.register_mcp_tools(session, ["create_event", "delete_event"])
```

## tools.py — thin mock stub  *(selftest substrate ONLY — not the product)*
```python
import hashlib
from datetime import datetime, timedelta

def _stable_id(*parts: str) -> str:
    h = int(hashlib.md5(":".join(p or "" for p in parts).encode()).hexdigest(), 16)
    return f"EVT-{h % 100000:05d}"

def create_event(summary: str = "", start_time: str = "", duration_min: str = "", **_) -> dict:
    try:
        end = (datetime.fromisoformat((start_time or "").replace("Z", "+00:00"))
               + timedelta(minutes=int(duration_min or 0))).isoformat()
    except (ValueError, TypeError):
        end = ""
    eid = _stable_id(summary, start_time)
    return {"tool": "create_event", "event_id": eid,
            "html_link": f"https://www.google.com/calendar/event?eid={eid}",
            "start": start_time, "end": end, "status": "confirmed",
            "summary": f'Scheduled "{summary}" for {start_time} ({duration_min} min). Event id {eid}.'}

def delete_event(event_id: str = "", **_) -> dict:
    digits = "".join(c for c in (event_id or "") if c.isdigit())
    if digits and set(digits) == {"0"}:      # all-zeros id => simulate a 404
        return {"tool": "delete_event", "event_id": event_id, "error": "event not found (simulated 404)",
                "summary": "I couldn't find an event with that id."}
    return {"tool": "delete_event", "event_id": event_id, "cancelled": True,
            "summary": f"Cancelled event {event_id}."}
```

## selftest.py — HOOK_CHECKS additions  *(REQUIRED — keeps structural_preflight green)*
```python
# every validator this recipe adds must be exercised with a raw value:
("validator", "schedule_event", "start_time", "2020-01-01T09:00:00", {}, False, "past"),
("validator", "schedule_event", "duration_min", "45 minutes", {}, True, "45"),
("validator", "schedule_event", "duration_min", "600", {}, False, "8 hours"),
("validator", "cancel_event", "event_id", "??", {}, False, "event id"),
```
Also add the mock SLOT_EXTRACTORS for `summary` / `start_time` / `duration_min` /
`event_id` (see the harness config) so a mock SCRIPT can drive the flows.

## Customize per client (the "little modification")
- `GCAL_CALENDAR_ID`, `GCAL_TIMEZONE` (IANA), the OAuth scope, `GCAL_TOKEN_PATH`.
- The `FILLERS_BY_TOOL` tone — reword in the agent's voice.
- A live-vs-mock env flag if the client wants a credential-less demo mode.

## Gotchas / limits
- **Opaque event ids.** Live ids are Google's base32hex, NOT `EVT-#####`; `_validate_event_id` already accepts both, so live and mock share the validator.
- **Timezones.** Pass IANA `timeZone`; naive `dateTime` values are interpreted in `_TZ`. **All-day** events (a `date` field instead of `dateTime`) are not covered — extend the body if needed.
- **Idempotency.** `events.insert` is not idempotent — a blind retry double-books. The `confirm=True` gate + `MAX_TOOL_CALLS_PER_TURN` breaker mitigate; add an idempotency key only if you automate retries.
- **Attendees/invites** are intentionally out of scope. To add: an `attendee_email` slot (with an email-format validator) → an `attendees:[{ "email": ... }]` field in the body + the `sendUpdates` param.
- **Rate limits.** Standard Calendar API quotas apply; batch for bulk operations.
- **Mock coverage.** The thin stub exercises graph logic + the not-found failure path only; real HTTP errors, auth expiry, and timezone edge cases are proven only on the live path (step 3).
