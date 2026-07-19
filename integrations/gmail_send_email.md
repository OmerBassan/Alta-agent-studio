# Integration: Gmail — Send Email to a Lead

<!--
  Lifted from the proven implementation in
  Generated_CLI_Agents/NorthwindSDRConcierge_20260712_224830 (tools.py
  send_followup + gmail_auth.py), which passed selftest and ran the live
  Gmail path. Copy-adapt per client; never import across projects.
-->

## Metadata
- **id:** `gmail_send_email`
- **source system / API version:** Gmail API v1 (`users.messages.send`)
- **transport:** `vendor SDK` (`google-api-python-client` + `google-auth-oauthlib`)
- **auth:** OAuth 2.0 user consent, scope `https://www.googleapis.com/auth/gmail.send` — **client owns this; recipe ships none**
- **entity IDs:** Gmail message id (opaque string, returned as `message_id`)
- **stakes:** `confirm=True` — an email leaves the building in the lead's name; read back the address before sending
- **wiring last validated:** `2026-07-12` (selftest PASSED against the thin mock, NorthwindSDR build)
- **live-validation:** validated against a real Gmail account `2026-07-12` (NorthwindSDR)

## What it gives you
One flow/tool: `send_email` — composes a domain-tailored email (subject + body
derived from config, never free-typed by the caller) and sends it via the
client's Gmail account. Live when a token store exists; a labelled mock keeps
the selftest green until then. The interactive OAuth bootstrap is a separate
one-time script — the tool itself NEVER opens a browser mid-conversation.

## 1. Prerequisites (the Validate gate — confirm BEFORE implementing live)
- [ ] Google Cloud project with the **Gmail API enabled**
- [ ] OAuth consent screen with scope `gmail.send`; the sending address added as a test user while the app is in "Testing"
- [ ] OAuth client ID of type **"Desktop app"**, downloaded as `credentials.json` into the agent folder
- [ ] `pip install google-api-python-client google-auth-oauthlib`
- [ ] One-time interactive mint: `python gmail_auth.py` (copy that bootstrap script from this recipe's source agent) → writes `token.json`

**Credential files this recipe puts on disk** (append to the generated agent's
`.gitignore` — the boilerplate already covers the common names):

- `credentials.json` (the OAuth client), `token.json` (the refreshed authorized-user token)

## 2. config.py — FLOWS  *(paste into `FLOWS`; fill `[CUSTOMIZE]`)*
```python
"send_email": Flow(
    tool="send_email",
    slots=("email",),                      # [CUSTOMIZE] add "company" etc. if the body tailors on them
    slot_prompts={"email": "the email address to send it to"},
    validators={"email": _validate_email},
    confirm=True,                          # real-world side effect — read back before sending
    confirm_template="Just to confirm — send the recap to {email}? (yes/no)",
    cache_keys=("message_id",),
),
```

## config.py — ENTITY_RESOLVERS / validators / NEXT_STEP_HINTS / FILLERS_BY_TOOL
```python
def _validate_email(value: str, _slots: dict) -> tuple[bool, str]:
    v = value.strip().lower().replace(" at ", "@").replace(" dot ", ".")  # voice-transcript repair
    if re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", v):
        return True, v
    return False, "Could you spell out that email address for me one more time?"

# NEXT_STEP_HINTS
"send_email": "",        # the send summary is complete; no upsell line

# FILLERS_BY_TOOL — [CUSTOMIZE tone]: reword in THIS agent's voice.
"send_email": ["Sending that over now…", "One sec — getting that email out…",
               "Putting that in your inbox…"],
```

## 3. tools.py — LIVE tool body  *(the ship target — paste + wire to real creds)*
```python
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def _gmail_token_path() -> str:
    return os.getenv("GMAIL_TOKEN_PATH") or os.path.join(_HERE, "token.json")

def _gmail_credentials_path() -> str:
    return os.getenv("GMAIL_CREDENTIALS_PATH") or os.path.join(_HERE, "credentials.json")

def _gmail_ready() -> bool:
    """LIVE only when a token store already exists AND the google libs import.
    NEVER launch interactive OAuth from a tool call (it would open a browser
    mid-conversation) — the token is minted once by gmail_auth.py."""
    if not os.path.exists(_gmail_token_path()):
        return False
    try:
        import google.oauth2.credentials  # noqa: F401
        import googleapiclient.discovery   # noqa: F401
        return True
    except ImportError:
        return False

def _compose_email(**slots) -> tuple:
    # [CUSTOMIZE] subject + body from config/domain facts — content is
    # design-time, the caller never dictates arbitrary text (prompt-injection
    # surface + brand control). Tailor on slots like company.
    subject = "..."
    body = "..."
    return subject, body

def _live_send_email(email: str, **slots) -> dict:
    import base64
    from email.mime.text import MIMEText
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    token_path = _gmail_token_path()
    creds = Credentials.from_authorized_user_file(token_path, GMAIL_SCOPES)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())                     # silent refresh
            with open(token_path, "w") as f:
                f.write(creds.to_json())
        else:
            return {"tool": "send_email", "to": email,
                    "error": "gmail token invalid; re-run `python gmail_auth.py`",
                    "summary": "I couldn't send that email just now."}
    service = build("gmail", "v1", credentials=creds)
    subject, body = _compose_email(email=email, **slots)
    msg = MIMEText(body)
    msg["to"] = email
    msg["subject"] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    try:
        sent = service.users().messages().send(userId="me", body={"raw": raw}).execute()
    except Exception as e:
        return {"tool": "send_email", "to": email, "error": str(e),
                "summary": "I couldn't send that email just now."}
    return {"tool": "send_email", "sent": True, "to": email,
            "subject": subject, "message_id": sent.get("id", ""),
            "summary": f"Sent — it's on its way to {email}.", "mode": "live"}

def send_email(email: str = "", **slots) -> dict:
    addr = (email or "").strip().lower()
    if addr.startswith("fail@"):                          # simulated failure path
        return {"tool": "send_email", "to": addr,
                "error": "email send failed (simulated)",
                "summary": "I couldn't send that email just now."}
    if _gmail_ready():
        return _live_send_email(addr, **slots)
    return _mock_send_email(addr, **slots)

# TOOL_REGISTRY["send_email"] = send_email
```

## tools.py — thin mock stub  *(selftest substrate ONLY — not the product)*
```python
def _mock_send_email(email: str, **slots) -> dict:
    subject, _ = _compose_email(email=email, **slots)
    message_id = f"MSG-{_stable_hash('mail', email) % 1000000:06d}"
    return {"tool": "send_email", "sent": True, "to": email, "subject": subject,
            "message_id": message_id, "mode": "mock",
            "summary": f"Sent — it's on its way to {email}."}
```

## selftest.py — HOOK_CHECKS additions  *(REQUIRED — keeps structural_preflight green)*
```python
("validator", "send_email", "email", "dana at example dot com", {}, True, "dana@example.com"),
("validator", "send_email", "email", "not-an-address", {}, False, "spell"),
```
SCRIPT: exercise the confirm gate (ask → address → "yes" → `_tool: "send_email"`)
and the `fail@` failure path (graceful summary, session alive).

## Customize per client
- `_compose_email` — the whole point: subject/body in the client's voice, tailored on collected slots.
- `GMAIL_TOKEN_PATH` / `GMAIL_CREDENTIALS_PATH` env overrides if creds live outside the agent folder.
- Filler + confirm phrasing in the agent's spoken voice (voice style pass applies).

## Gotchas / limits
- **Never OAuth mid-call**: the tool only reads `token.json`; minting is `gmail_auth.py`, once, interactive. A missing token silently degrades to the labelled mock — the operator must check `mode` before demoing live.
- Consent screen in "Testing" mode: tokens expire after 7 days unless the app is published or the user re-mints.
- Gmail send quotas (per-user daily limits) — fine for SDR follow-ups, not for bulk.
- Body content is design-time composed, never caller-dictated free text (injection + brand safety).
- The thin mock does NOT cover: auth refresh, quota errors, malformed-address rejection by the API — live path only.
