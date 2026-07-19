# Integrations Catalog — validated, copy-adapt recipes for external systems

This folder is the **reusable toolkit**: for each external system an agent can
connect to (a calendar, CRM, ticketing system, payment gateway, or a specific
MCP server), a **recipe** captures everything needed to wire that integration
into a build with little-to-no modification — and, critically, to wire it
**live**, not as a throwaway mock.

It is the ONE **read-WRITE** shared folder in this repo:

- **READ it** before hand-authoring any external-system tool (SKILL.md Step 1
  item 4 → applied in Step 5). If a recipe matches the client's system of
  record, you follow its lifecycle instead of re-deriving the tool.
- **APPEND to it** after a new integration is proven (SKILL.md Step 4).

Contrast with `references/*.txt` (read-only architectural theory) and
`boilerplate/` (read-only engine skeleton). Those never change per build; this
one accumulates validated integrations over time.

## Integration lifecycle — Detect → Validate → Implement (live-first)

For a **catalog integration the contract is already known**, so re-mocking it
per client is wasted effort. Mock-first is for *bespoke* client tools (unknown
contract, no credentials). A catalog integration follows three steps instead:

1. **Detect** — recognize that a known, worth-using connection fits the client's
   need ("they want booking → Google Calendar is a validated recipe"). Offer it.
2. **Validate prerequisites** — a real GATE. Confirm the client actually has
   what the live integration needs: credentials/OAuth client, granted consent
   and the exact scopes, a token store, and a transport (a running MCP server OR
   the vendor SDK). The recipe's **Prerequisites** section is this checklist. If
   anything is missing, hand the client the precise setup steps and **block on
   it** — do NOT ship a mock dressed up as the real thing.
3. **Implement live** — wire the recipe's **live tool body** against the
   client's credentials. This is the ship target.

**The mock is not the product.** Each recipe still carries a *thin* mock stub,
but its only jobs are (a) to let `selftest.py` exercise the graph/Flow logic
without credentials (the gate stays green), and (b) to stand in TEMPORARILY,
clearly labeled, if the client wants to demo flow logic before their credentials
are ready. It is a stub, never an elaborate re-simulation of the vendor API.

## Copy-adapt, NOT import (why)

A generated agent copies `boilerplate/` **wholesale** and is fully
self-contained — shipping it never depends on this repo (the Isolation Rule).
Recipes preserve that: their code blocks are **pasted** into the generated
agent's `config.py` / `tools.py` / `selftest.py`, never imported from a shared
package. The only edits are the `[CUSTOMIZE]` placeholders (calendar/tenant IDs,
timezone, scopes, and the filler tone, reworded in the agent's own voice).

## Recipe format

Every recipe is one Markdown file named for its integration
(`google_calendar_booking.md`, `stripe_refund.md`, `zendesk_ticket.md`, …) and
follows `_TEMPLATE.md` exactly: a metadata header; a **Prerequisites** checklist
(the step-2 gate — the auth/OAuth/scopes/server the client must have; recipes
never ship credentials); paste-ready blocks for `FLOWS`, `ENTITY_RESOLVERS`,
slot `validators`, `NEXT_STEP_HINTS`, `FILLERS_BY_TOOL`; the **live tool body**
(the ship target — MCP registration or the vendor SDK call, faithful to the
published API contract); a **thin mock stub** (selftest substrate only); the
`HOOK_CHECKS` additions **required** so the generated agent's
`structural_preflight()` still passes; then "Customize per client" and
"Gotchas / limits".

## Promotion discipline (what keeps this trustworthy)

A recipe enters the catalog ONLY when ALL of these hold — otherwise the folder
rots into unmaintained snippets nobody trusts:

1. **Contract-faithful to the published API.** The live tool body and the entity
   ID / field formats mirror the vendor's real, documented contract and API
   version — not a guess, not the mock's convenience shapes.
2. **Wiring is selftest-green.** The recipe's `FLOWS` / validators / `HOOK_CHECKS`
   pass `selftest.py` against its thin mock stub — so pasting it into a new build
   keeps the gate green. (This validates the graph wiring; the LIVE path is
   proven per-client at implement-time, step 3, once prerequisites validate.)
3. **Generalizable, not client-proprietary.** It integrates a system many
   clients share (Google Calendar, Stripe, Zendesk, a public MCP server), not
   one client's bespoke internal API or business logic.

Each recipe records its API version, the last date its wiring passed selftest,
and its live-validation status. When a vendor API changes, re-check the contract
and re-run the wiring selftest, then bump those.

## Index

| Recipe | System | Transport | Stakes | API ver / validated |
|--------|--------|-----------|--------|---------------------|
| [google_calendar_booking](google_calendar_booking.md) | Google Calendar | MCP or `google-api-python-client` | `confirm` (both flows) | v3 / wiring 2026-07-12 |
| [tavily_search](tavily_search.md) | Tavily (web search) | local `tavily-python` (keyed REST) | none (read-only) | search API / wiring 2026-07-12 |
| [gmail_send_email](gmail_send_email.md) | Gmail (send to a lead) | `google-api-python-client` (OAuth `gmail.send`) | `confirm` (email leaves the building) | v1 / wiring + live 2026-07-12 |
