# Integration: <Human Name>  (e.g. Google Calendar — Appointment Booking)

<!--
  Recipe skeleton. Copy to a new file named for the integration (snake_case,
  e.g. google_calendar_booking.md) when a new integration is proven. Fill every
  section. The integration lifecycle is Detect → Validate prerequisites →
  Implement LIVE; the mock is only a thin selftest substrate. See README.md.
-->

## Metadata
- **id:** `<snake_case_id>`                     <!-- matches the filename -->
- **source system / API version:** <e.g. Google Calendar API v3>
- **transport:** `MCP` (server: `<name / how to run it>`)  |  `vendor SDK` (`<pip pkg>`)
- **auth:** <e.g. OAuth 2.0 user consent, scope `...`> — **client owns this; recipe ships none**
- **entity IDs:** <formats the tools emit/consume, e.g. event id = opaque base32hex>
- **stakes:** <`confirm=True` end-user gate | `hitl=True` operator gate | none> — and why
- **wiring last validated:** `<YYYY-MM-DD>` (selftest PASSED against the thin mock)
- **live-validation:** `<per-client at implement-time>` | `<validated against a real account YYYY-MM-DD>`

## What it gives you
<One short paragraph: which flow(s)/tool(s), what the agent can do live.>

## 1. Prerequisites (the Validate gate — confirm BEFORE implementing live)
Block here if any are missing; hand the client these exact steps, do not ship a
mock as if it were real.
- [ ] <cloud project / app registration with the API enabled>
- [ ] <OAuth client (id+secret) or service account; the granted scopes: `...`>
- [ ] <a token store / refresh token the process can load at startup>
- [ ] <transport ready: a running MCP server, OR `pip install <sdk>` + creds>
- [ ] <any account-level config: calendar id, tenant, region, timezone>

**Credential files this recipe puts on disk** (append every one to the generated
agent's `.gitignore` — Step 4.3; the boilerplate already covers the common names):

- `<credentials.json — the OAuth client>`, `<token.json — the refreshed authorized-user token>`, `<any key/service-account file or local cache DB>`

## 2. config.py — FLOWS  *(paste into `FLOWS`; fill `[CUSTOMIZE]`)*
```python
"<intent_name>": Flow(
    tool="<tool_name>",
    slots=(...),
    slot_prompts={...},
    # confirm=True / confirm_template=... / hitl=True / enrich=... per the stakes
    cache_keys=(...),   # hard identifiers this flow produces for downstream steps
),
```

## config.py — ENTITY_RESOLVERS / validators / NEXT_STEP_HINTS / FILLERS_BY_TOOL
```python
# resolvers (only for slots that key into a catalog); validators (format/bounds):
def _validate_<slot>(value: str, _slots: dict) -> tuple[bool, str]: ...

"<tool_name>": "<one NEXT_STEP_HINTS sentence>",

# FILLERS_BY_TOOL entry — [CUSTOMIZE tone]: reword in THIS agent's voice.
"<tool_name>": ["<natural spoken ack 1>", "<ack 2>", "<ack 3>"],
```

## 3. tools.py — LIVE tool body  *(the ship target — paste + wire to real creds)*
```python
# Build the authorized client ONCE at startup (from the client's creds), then:
def <tool_name>(**args) -> dict:
    resp = <sdk call OR MCP forwards this>       # faithful to the published API
    return {"tool": "<tool_name>", "<id_field>": resp["..."], ...,
            "summary": "<one plain-English sentence>"}
# TOOL_REGISTRY["<tool_name>"] = <tool_name>
# — OR, MCP transport: await tools.register_mcp_tools(session, ["<tool_name>", ...])
```

## tools.py — thin mock stub  *(selftest substrate ONLY — not the product)*
```python
def <tool_name>(**args) -> dict:
    # deterministic minimal stand-in: enough to exercise graph logic + the
    # failure path; NOT a re-simulation of the vendor API.
    return {"tool": "<tool_name>", ..., "summary": "..."}
```

## selftest.py — HOOK_CHECKS additions  *(REQUIRED — keeps structural_preflight green)*
```python
("validator", "<flow>", "<slot>", "<raw/bad input>", "<expected or None>"),
```

## Customize per client (the "little modification")
- <calendar/tenant/account id, timezone, scopes, live-vs-mock env flag>
- <the filler tone — reword FILLERS in the agent's voice>

## Gotchas / limits
- <rate limits, pagination, tz/all-day handling, idempotency keys, error semantics>
- <what the thin mock does NOT cover — only the live path exercises it>
