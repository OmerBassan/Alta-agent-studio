"""Stage 2 (gates D14, D15): additive amendments approved by the user on 2026-10-16.
Usage: python -I stage2.py <root>

Every replacement asserts its target occurs exactly once; all files are edited in memory
first and written only if every assertion passed, each in its own line-ending style.
Memlog entries are NOT written here: they go through `_bmad/scripts/memlog.py append`.
"""
import io
import sys

root = sys.argv[1]
PA = "_bmad-output/planning-artifacts"
F = {
    "spine": f"{PA}/architecture/architecture-AgentStudio-2026-10-07/ARCHITECTURE-SPINE.md",
    "prd": f"{PA}/prds/prd-AgentStudio-2026-10-08/prd.md",
    "exp": f"{PA}/ux-designs/ux-AgentStudio-2026-10-08/EXPERIENCE.md",
    "design": f"{PA}/ux-designs/ux-AgentStudio-2026-10-08/DESIGN.md",
    "epics": f"{PA}/epics.md",
    "sprint": "_bmad-output/implementation-artifacts/sprint-status.yaml",
    "plan": "docs/next-phase-proposals/NEXT-PHASE-PLAN.md",
    "reg": "docs/next-phase-proposals/BMAD-DECISION-REGISTER.md",
    "handoff": "docs/next-phase-proposals/HANDOFF.md",
}
CRLF, LF = "\r\n", "\n"
raw = {k: io.open(f"{root}/{v}", encoding="utf-8", newline="").read() for k, v in F.items()}
eol = {k: (CRLF if CRLF in r else LF) for k, r in raw.items()}
text = {k: r.replace(CRLF, LF) for k, r in raw.items()}


def rep(key, old, new):
    n = text[key].count(old)
    assert n == 1, (key, old[:90], n)
    text[key] = text[key].replace(old, new)


def row_append(key, prefix, addition):
    """Append text to the last cell of the one table row starting with `prefix`."""
    lines = text[key].split("\n")
    hits = [i for i, l in enumerate(lines) if l.startswith(prefix)]
    assert len(hits) == 1, (key, prefix, len(hits))
    l = lines[hits[0]]
    assert l.endswith(" |"), (key, prefix)
    lines[hits[0]] = l[:-2] + " " + addition + " |"
    text[key] = "\n".join(lines)


D = "2026-10-16"

# ================================================================ Spine: AD-26 to AD-29 (S1-S4)
rep("spine", "updated: '2026-10-08'\n", f"updated: '2026-10-08'\namended: '{D}'\n")
rep("spine", "# Architecture Spine — Agent Studio\n",
    "# Architecture Spine — Agent Studio\n\n"
    f"> **Amended after finalization ({D}).** AD-26 to AD-29 were added to answer UX contract gaps 4, 5, 12 and 14 "
    "(EXPERIENCE.md, Amendments and Upstream Gaps). No earlier AD was rewritten; AD-18 carries one inline cross-reference. "
    "Their wording was approved by the user; the decisions remain PROPOSED under program gate D14. Decision trail in `.memlog.md`.\n")
rep("spine", "No Core mechanism routes control anywhere else, chooses what follows a refusal, or selects a next step.\n",
    "No Core mechanism routes control anywhere else, chooses what follows a refusal, or selects a next step. "
    f"*[{D}: an operator suspension is a trigger of the declared safety halt — AD-26]*\n")
rep("spine", "this AD fixes only that the architecture must not foreclose them.\n",
    "this AD fixes only that the architecture must not foreclose them.\n\n"
    f"### AD-26 — Each deployed Agent has one operator-controlled suspension state `[ADDED {D} · PROPOSED]`\n\n"
    "- **Binds:** Core, Channel adapters, operator surface\n"
    "- **Prevents:** a suspend that fails silently or lapses on restart; a suspended Agent leaving a person mid-conversation in silence\n"
    "- **Rule:** Each deployed Agent has exactly one suspension state — not suspended, effects suspended, or suspended — which is durable, "
    "scoped to that Agent, and changed only by a recorded, attributable operator action, resume included. The Core enforces it on every request. "
    "The Core reads the state as a recorded step (AD-12). "
    "Under *effects suspended*, every `effect` is refused as a typed result classified `business_refusal` (AD-5), and replies continue. "
    "Under *suspended*, each episode in flight — active or pending — ends in a declared safety halt (AD-18) whose recorded reason is the operator's "
    "suspension, so the business's terminal notice is emitted; for an episode mid-turn, a request already authorized completes and its evidence "
    "stands, and the halt applies at its next request to the Core. A terminal notice that cannot be delivered is recorded as undelivered, and the halt "
    "stands. An inbound message or external system event that would start an episode while the Agent is suspended is recorded as an episode that "
    "closes without an Agent turn and without a reply, with the recorded outcome *arrived while suspended*; it never reaches the Agent, so it is not "
    "a Core exit (AD-18), it carries no resolution (AD-20), and it is never answered after resume. Such episodes stay in the operational record and "
    "are outside the denominator of Agent-quality evaluation; every report of those measures states the exclusion and the number excluded. "
    "Mailbox connection status is reported by the channel adapter and is not part of this state.\n\n"
    f"### AD-27 — Specification versions have four states, derived from records `[ADDED {D} · PROPOSED]`\n\n"
    "- **Binds:** Builder, Core, Specification, operator surface\n"
    "- **Prevents:** approving a version that failed validation; two live versions; a state field that drifts from what the records show\n"
    "- **Rule:** A specification version is exactly one of draft, validated, approved or live, derived from its records and never stored as a free "
    "field. Only a version whose validation suite passed can be approved; only an approved version can be promoted. Each Agent has at most one live "
    "version. A version replaced as live stays approved, keeps its promotion history, and remains eligible for rollback (AD-23).\n\n"
    f"### AD-28 — A specification reference names its item `[ADDED {D} · PROPOSED]`\n\n"
    "- **Binds:** Core, Specification, operator surface\n"
    "- **Prevents:** an interaction view that can quote source material but not the specification rule a reply relied on\n"
    "- **Rule:** Within the specification projection, a provenance reference's locator (AD-7) names the expression area and the item.\n\n"
    f"### AD-29 — Received time and display label are stored uninterpreted `[ADDED {D} · PROPOSED]`\n\n"
    "- **Binds:** Core, Channel adapters\n"
    "- **Prevents:** channel semantics leaking into episode state through an interaction label\n"
    "- **Rule:** A normalised inbound turn may carry the received time (UTC) and a channel-neutral display label supplied by the channel adapter. "
    "The Core stores both uninterpreted and never reasons on them; they carry no channel semantics (AD-16) and are removable with the evidence (AD-25).\n")

# ================================================================ PRD: §14 A4-A7 and markers
rep("prd", "amended: 2026-10-15\n", f"amended: {D}\n")
rep("prd", "Recorded 2026-10-15. Each row records a decision already taken in an approved BMAD run;",
    f"Recorded 2026-10-15 (A1–A3) and {D} (A4–A7); rows are cited as \"§14 An\", distinct from the assumption tags A1–A4 of §11.1, and "
    "\"program gate\" means a gate of NEXT-PHASE-PLAN §6. Rows A1–A3 record decisions already taken in an approved BMAD run; rows A4–A7 record wording the user approved, and their decisions stay PROPOSED until the user confirms them;")
rep("prd", "- Share of inbound episodes resolved without a human.\n",
    "- Share of inbound episodes resolved without a human. *[Specified — §14 A7]*\n")
rep("prd", "published FAQs, prior customer correspondence. |",
    "published FAQs, prior customer correspondence. *[Specified for V1 — §14 A4]* |")
rep("prd", "Where a business lacks the shape a check assumes, the check adapts or skips rather than failing. |",
    "Where a business lacks the shape a check assumes, the check adapts or skips rather than failing. *[Narrowed — §14 A5]* |")
rep("prd", "Evidence vocabulary follows established GenAI telemetry naming where it exists | Qualitative |",
    "Evidence vocabulary follows established GenAI telemetry naming where it exists *[Narrowed for V1 — §14 A6]* | Qualitative |")
rep("prd", "episodes in flight when it happens end in a recorded outcome rather than silently. |",
    "episodes in flight when it happens end in a recorded outcome rather than silently. *[Specified — §14 A7]* |")
text["prd"] = text["prd"].rstrip("\n") + "\n" + (
    "| A4 | Material intake. In V1 the Builder accepts plain text, Markdown, PDF with a text layer, DOCX, CSV, XLSX and pasted text. There is no OCR: "
    "a PDF without a text layer is reported as \"Could not be read. Nothing from it has been used.\" Size and duration limits are recorded and stated "
    "to the operator, never applied silently; partly readable material states which parts were used. Ingestion never blocks a Builder turn. Fetching "
    "web pages is deferred until the operator conversations (FR94) show where businesses keep their published FAQs. Unverified premise (program "
    "handoff U3, 2026-10-15): that these formats cover what small-business operators hold; FR94 tests it. "
    f"| FR2, FR117 | EXPERIENCE.md Material intake (\"unspecified upstream\") and Amendments item 10; user decision {D} (program gate D15) | PROPOSED (wording approved by the user {D}; decision pending) |\n"
    "| A5 | Validation findings. FR22 governs: platform-owned checks block, and a business's declared criteria warn unless the business declares one "
    "blocking. A business-declared blocking criterion can only add a block; it never waives, weakens or overrides a platform check. FR95's \"only "
    "platform-owned checks may block\" is narrowed accordingly; the suite itself stays platform-owned and is never authored by the Builder it gates. "
    "Every finding states whether it blocks, its origin (platform check or business-declared criterion), a plain-language statement, the expression "
    "area it concerns, and the item where there is one. A check that did not run is not a finding; a check skipped under FR95 is recorded in the "
    "validation record, so a skip stays auditable (FR96). "
    f"| FR22, FR95, FR24 | PRD `.memlog.md` line 53; EXPERIENCE.md Validation result and Amendments item 13; user decision {D} (program gate D15) | PROPOSED (wording approved by the user {D}; decision pending) |\n"
    "| A6 | Error references. Every unit of work has one correlation identity: an episode, a Builder session, or an operator action (approval, "
    "promotion, rollback, suspend, resume). Every platform error the operator sees shows that identity, or a code resolving to exactly one unit of "
    "work and its records. In V1 references are shown to the operator only: a requester never sees one, and the business's terminal notice and "
    "disclosure wording never carry one. Known limit: a requester can report a problem only through the business, and the V1 operator surface "
    "cannot find an interaction that is not an Activity item, so for requesters NFR16's \"reportable by a person who experienced a problem\" is met "
    f"only in part. | NFR16 | EXPERIENCE.md \"Something on our side failed. Reference: {{code}}\" and Amendments item 17; user decision {D} (program gate D15) | PROPOSED (wording approved by the user {D}; decision pending) |\n"
    "| A7 | Suspension outcomes. When the operator fully suspends an Agent, every interaction in flight (active or pending) ends in a declared safety "
    "halt whose recorded reason is the operator's suspension, and the requester receives the business's terminal notice (FR111); a notice that "
    "cannot be delivered is recorded as undelivered. An inbound message that arrives while the Agent is suspended is recorded as an interaction with "
    "the outcome \"arrived while suspended\", receives no reply, is shown to the operator in Activity, and is not answered after resume. Effects-only "
    "suspension refuses every effect as a typed result, classified as a business refusal (FR77), while replies continue. Evaluation (FR76, §10.1–10.2): "
    "interactions that arrived while suspended stay in the record but are outside the denominators of Agent-quality measures, because the Agent "
    "never handled them; every report of those measures states this exclusion and the number excluded, beside the measures, so the exclusion cannot "
    "improve a figure unseen. Interactions the suspension halted stay inside the denominators, recorded as halts with the reason operator suspension. "
    f"| FR110, FR111, FR76, §10.1–10.2 | Architecture Spine AD-26; EXPERIENCE.md Amendments item 20; user decision {D} (program gate D14) | PROPOSED (wording approved by the user {D}; decision pending) |\n")

# ================================================================ EXPERIENCE: status cells, item 20
rep("exp", "updated: 2026-10-10\n", f"updated: 2026-10-10\namended: {D}\n")
up = lambda where: f"**Recorded upstream: {where} ({D}; wording approved, decision PROPOSED).**"
row_append("exp", "| 4 | **Persistent suspended state.**", up("Spine AD-26; PRD §14 A7"))
row_append("exp", "| 5 | **Specification version lifecycle**", up("Spine AD-27"))
row_append("exp", "| 10 | **Material intake limits**", up("PRD §14 A4"))
row_append("exp", "| 12 | **Linking a reply to the specification item it relied on.**", up("Spine AD-28"))
row_append("exp", "| 13 | **Validation result shape.**", up("PRD §14 A5"))
row_append("exp", "| 14 | **Email subject and received time in the interaction record.**",
           up("Spine AD-29") + " The premise that the Spine lists channel identity as not stored is an inference in "
           "`.working/extract-architecture.md` (lines 406–412), not Spine text.")
row_append("exp", "| 17 | **Platform error reference.**", up("PRD §14 A6"))
rep("exp", "| 19 | **Undeliverable escalation email.** What happens, and what the operator sees, when the escalation email bounces. | PRD FR103 / FR114 | **Gap.** |\n",
    "| 19 | **Undeliverable escalation email.** What happens, and what the operator sees, when the escalation email bounces. | PRD FR103 / FR114 | **Gap.** |\n"
    "| 20 | **Email that arrives while the Agent is suspended.** It is recorded and not answered, and it appears in Activity under its own group, "
    "*Arrived while suspended. Not answered.*, which is not a divergence class. It is not answered after resume, and its items stay in Activity after "
    "resume like any other item. *Nothing has come apart since {time}* refers to divergences only and may appear beside this group; no counts are shown. "
    "Interactions in flight when Suspend applies end, and each customer receives the business's terminal notice. If resume does not apply, "
    "*Resume did not apply. The Agent is still suspended. Try again.* is shown only after the platform has confirmed that the resume failed and the "
    "Agent is still suspended; while that is unconfirmed the status line shows the recorded state, and a failure that cannot be confirmed either way "
    "is shown as *Something on our side failed. Reference: {code}*. | PRD FR110 (§14 A7); Spine AD-26 | "
    f"**Explicit amendment**: wording approved by the user {D}; decision PROPOSED (program gate D14). Visual treatment: DESIGN.md refinement item 6. |\n")
rep("exp", "The list contains **divergences only**. It is not",
    f"The list contains **divergences only**. *[Amended {D} — item 20: while the Agent is suspended, Activity also lists email that arrived and was not answered, in its own group.]* It is not")
rep("exp", "| Empty Activity | Nothing has come apart since {time}. *(always shown with the Agent status line)* |\n",
    "| Empty Activity | Nothing has come apart since {time}. *(always shown with the Agent status line)* |\n"
    "| Arrived while suspended *(Amendments item 20)* | Arrived while suspended. Not answered. |\n"
    "| Resume failed *(Amendments item 20; shown only once the failure is confirmed)* | Resume did not apply. The Agent is still suspended. Try again. |\n")
rep("exp", "- **Let the Agent act again** resumes. It is a secondary action and never looks like Suspend.\n",
    "- **Let the Agent act again** resumes. It is a secondary action and never looks like Suspend.\n"
    f"- *(Amendments item 20, {D}.)* Interactions in flight when Suspend applies end, and each customer receives the business's terminal notice. "
    "Email that arrives while suspended is kept, not answered, and listed in Activity under *Arrived while suspended. Not answered.*\n")
rep("exp", "This document states the operator-visible need; it does not invent the field. Raise with architecture before implementation.\n",
    "This document states the operator-visible need; it does not invent the field. Raise with architecture before implementation. "
    f"**Recorded upstream: Spine AD-26 ({D}; wording approved, decision PROPOSED).**\n")

# ================================================================ DESIGN: open refinement item 6
rep("design", "updated: 2026-10-10\n", f"updated: 2026-10-10\namended: {D}\n")
text["design"] = text["design"].rstrip("\n") + "\n" + (
    f"6. **The *Arrived while suspended* group in Activity** (EXPERIENCE.md Amendments item 20, {D}). It is not a divergence class, so it must not "
    "borrow a class shape or colour; its non-colour cue is undecided.\n")

# ================================================================ epics.md (stays status: draft)
rep("epics", "amendments marked *proposed* are not requirements until the user approves them under the named gate:",
    "amendments marked *proposed* are not requirements until the user approves them under the named gate. "
    f"Gaps 4, 5, 10, 12, 13, 14 and 17 received user-approved wording on {D} (Spine AD-26–AD-29; PRD §14 A4–A7); the decisions stay PROPOSED, so gates D14 and D15 remain open:")
for old, new in [
    ("proposed Spine amendment S1, gate D14 (Story 7.1)", "Spine AD-26 and PRD §14 A7 (Story 7.1)"),
    ("proposed Spine amendment S2, gate D14 (Story 3.3)", "Spine AD-27 (Story 3.3)"),
    ("proposed PRD amendment A4, gate D15 (Story 5.2)", "PRD §14 A4 (Story 5.2)"),
    ("proposed Spine amendment S3, gate D14 (Story 7.3)", "Spine AD-28 (Story 7.3)"),
    ("proposed PRD amendment A5, gate D15 (Story 3.3)", "PRD §14 A5 (Story 3.3)"),
    ("proposed Spine amendment S4, gate D14 (Story 7.3)", "Spine AD-29 (Story 7.3)"),
    ("proposed PRD amendment A6, gate D15 (Story 4.5)", "PRD §14 A6 (Story 4.5)"),
]:
    rep("epics", f"**Route:** {old}.", f"**Route:** {new}, wording applied {D}; decision PROPOSED (gate {'D14' if 'Spine' in new else 'D15'}).")
rep("epics", "the empty state \"Nothing has come apart since {time}\" only alongside the status line.\n",
    "the empty state \"Nothing has come apart since {time}\" only alongside the status line. While the Agent is suspended, email that arrived "
    "and was not answered is listed under its own group, \"Arrived while suspended. Not answered.\", which is not a divergence class; its items "
    "stay after resume, carry no count, and the empty-state sentence refers to divergences only (EXPERIENCE.md Amendments item 20).\n")

# Story 3.3
rep("epics", "UX gaps 5 (version lifecycle; proposed Spine amendment S2) and 13 (finding shape; proposed PRD amendment A5); UX-DR10, UX-DR12 (data) · **Depends on:** 3.1, 3.2 · **decision gates D14 (S2), D15 (A5)** · **Verification:** contract tests on the finding and version-state types · **Status:** blocked (D14, D15)",
    "FR95, FR26; UX gaps 5 (version lifecycle; Spine AD-27) and 13 (finding shape; PRD §14 A5); UX-DR10, UX-DR12 (data) · **Depends on:** 3.1, 3.2 · **decision gates D14 (AD-27), D15 (A5)** · **Verification:** contract tests on the finding and version-state types · **Status:** blocked (D14, D15)")
rep("epics", "**Then** it carries an identifier, whether it blocks, a plain-language message, the expression area it concerns, and the item it points at where there is one.",
    "**Then** it carries an identifier, whether it blocks, its origin (platform check or business-declared criterion), a plain-language message, the expression area it concerns, and the item it points at where there is one\n"
    "**And** a check that did not run produces no finding, and a check skipped under FR95 is recorded in the validation record.")
rep("epics", "**Then** it is exactly one of draft, validated, approved, live, derived from records rather than stored as a free field.",
    "**Then** it is exactly one of draft, validated, approved, live, derived from records rather than stored as a free field\n"
    "**And** only a validated version can be approved, only an approved version can be promoted, each Agent has at most one live version, and a version replaced as live stays approved and eligible for rollback.")
rep("epics", "**Then** they follow the version-state and finding contracts as approved under D14 (S2) and D15 (A5), and not a contract chosen in the code.",
    "**Then** they follow Spine AD-27 and PRD §14 A5, and not a contract chosen in the code.\n\n"
    "**Given** a business-declared criterion marked blocking\n**When** the suite runs\n"
    "**Then** it can add a blocking finding but never waives, weakens or overrides a platform check.")
# Story 4.5
rep("epics", "UX gap 17 (reference format; proposed PRD amendment A6) · **Depends on:** 4.1 · **decision gate D15 (A6), for the reference criterion only** ·",
    "UX gap 17 (reference format; PRD §14 A6) · **Depends on:** 4.1 · **decision gate D15 (A6), for the reference criterion only** ·")
rep("epics", "**Then** it carries a reference code that resolves to the episode and its records.",
    "**Then** it carries a reference that is the correlation identity of its unit of work — an episode, a Builder session or an operator action — or a code resolving to exactly one of them and its records\n"
    "**And** no message to a requester ever carries a reference.")
# Story 5.2
rep("epics", "UX gap 10 (formats, size and duration limits; proposed PRD amendment A4) · **Depends on:** 5.1, 2.1 · **decision gate D15 (A4)** · **Verification:** ingestion tests per format, including a corrupt file · **Status:** blocked (D15)",
    "UX gap 10 (formats, size and duration limits; PRD §14 A4) · **Depends on:** 5.1, 2.1 · **decision gate D15 (A4)** · **Verification:** ingestion tests per format, including a corrupt file and a PDF without a text layer · **Status:** blocked (D15)")
rep("epics", "**Given** plain text, Markdown or a PDF with extractable text\n",
    "**Given** plain text, Markdown, a PDF with a text layer, DOCX, CSV, XLSX or pasted text\n")
rep("epics", "**Then** the outcome is stated to the operator and nothing from it is used.",
    "**Then** the outcome is stated to the operator and nothing from it is used\n"
    "**And** a PDF without a text layer is reported as \"Could not be read. Nothing from it has been used.\" (no OCR).")
rep("epics", "**Given** the formats and limits approved under D15 (A4)\n",
    "**Given** the size and duration limits the platform sets, recorded with this story and stated to the operator (PRD §14 A4)\n")
rep("epics", "**Then** the operator is told which source, which limit and which parts were used, and nothing is silently truncated.",
    "**Then** the operator is told which source, which limit and which parts were used, and nothing is silently truncated.\n\n"
    "**Given** material being ingested\n**When** the operator keeps talking\n**Then** the Builder conversation continues; ingestion never blocks a Builder turn.")
# Story 7.1
rep("epics", "UX gap 4 (persistent suspended state; proposed Spine amendment S1) · **Depends on:** 6.1, Story 1.6 · **decision gate D14 (S1), for the persistence criterion only** · **Verification:** UI tests including a forced suspend failure · **Status:** ready (the persistence criterion waits on D14)",
    "FR111; UX gap 4 (persistent suspended state; Spine AD-26; PRD §14 A7); UX Amendments item 20 · **Depends on:** 6.1, Story 1.6 · **decision gate D14 (AD-26, A7), for the persistence and suspension-outcome criteria** · **Verification:** UI tests including a forced suspend failure; Core tests with an injection test and a mutation proof for the in-flight halt and for the unanswered inbound · **Status:** ready (the persistence and suspension-outcome criteria wait on D14)")
rep("epics", "**Then** it persists as the suspension state approved under D14 (S1).",
    "**Then** it persists, and only a recorded, attributable operator action changes it (Spine AD-26).\n\n"
    "**Given** interactions in flight when the operator fully suspends the Agent\n**When** the suspension applies\n"
    "**Then** each, active or pending, ends in a declared safety halt whose recorded reason is the operator's suspension, and each customer receives the business's terminal notice\n"
    "**And** for an interaction mid-turn, a request already authorized completes with its evidence and the halt applies at its next request\n"
    "**And** a terminal notice that cannot be delivered is recorded as undelivered, and the halt stands.\n\n"
    "**Given** an email, or an external system event, that would start an interaction while the Agent is suspended\n**When** received\n"
    "**Then** it is recorded as an interaction with the outcome \"arrived while suspended\", closed with no Agent turn and no reply, shown in Activity (Story 7.2), and not answered after resume.\n\n"
    "**Given** Stop actions only\n**When** the Agent requests an effect\n"
    "**Then** the effect is refused as a typed result classified as a business refusal, and replies continue.\n\n"
    "**Given** Let the Agent act again\n**When** the resume fails\n"
    "**Then** \"Resume did not apply. The Agent is still suspended. Try again.\" is shown only after the platform has confirmed the resume failed and the Agent is still suspended; until then the status line shows the recorded state, and a failure that cannot be confirmed is shown as \"Something on our side failed. Reference: {code}\".")
# Story 7.2
rep("epics", "· **Depends on:** 7.1, Epic 4 · **Verification:** UI tests over seeded divergences of all three classes and three sources · **Status:** ready",
    "· **Depends on:** 7.1, Epic 4 · **decision gate D14 (item 20), for the suspended-arrivals criterion only** · **Verification:** UI tests over seeded divergences of all three classes and three sources · **Status:** ready (the suspended-arrivals criterion waits on D14)")
rep("epics", "**Traces:** FR79, FR81, FR77, FR78, FR108, FR115 (sources); UX-DR15, UX-DR21 ·",
    "**Traces:** FR79, FR81, FR77, FR78, FR108, FR115 (sources); UX-DR15, UX-DR21; UX Amendments item 20 ·")
rep("epics", "**Then** \"Nothing has come apart since {time}\" appears, and only together with the status line.",
    "**Then** \"Nothing has come apart since {time}\" appears, and only together with the status line.\n\n"
    "**Given** email that arrived while the Agent was suspended\n**When** Activity renders\n"
    "**Then** it is listed under \"Arrived while suspended. Not answered.\", a group that is not a divergence class and uses no class shape\n"
    "**And** its items stay after resume like any Activity item, no count is shown, and \"Nothing has come apart since {time}\" refers to divergences only, so it may appear beside this group.")
# Story 4.1 (evaluation denominators, PRD §14 A7)
rep("epics", "· **Depends on:** Epics 1–3 · **Verification:** new `studio/evaluation/` tests over recorded scenario episodes · **Status:** ready",
    "· **Depends on:** Epics 1–3 · **decision gate D14 (A7), for the suspension-exclusion criterion only** · **Verification:** new `studio/evaluation/` tests over recorded scenario episodes · **Status:** ready (the suspension-exclusion criterion waits on D14)")
rep("epics", "**Traces:** FR20 (evaluated), FR67, FR72, FR73 (cost), FR76, PRD §10.1–10.2 and §10.4 guards, NFR13, NFR14 ·",
    "**Traces:** FR20 (evaluated), FR67, FR72, FR73 (cost), FR76, PRD §10.1–10.2 and §10.4 guards, PRD §14 A7, NFR13, NFR14 ·")
rep("epics", "**Then** it gives the §10.2 shares, with Agent failures reported separately from blocks by the business's own rules, and never reads lifecycle as success or failure.",
    "**Then** it gives the §10.2 shares, with Agent failures reported separately from blocks by the business's own rules, and never reads lifecycle as success or failure.\n\n"
    "**Given** interactions that arrived while the Agent was suspended, and interactions the suspension halted\n**When** the per-episode and per-business measures are computed\n"
    "**Then** the first stay in the record but are outside the Agent-quality denominators, and the report states that exclusion and the number excluded beside the measures\n"
    "**And** the second stay inside the denominators, as halts with the reason operator suspension.")
# Story 7.3
rep("epics", "UX gaps 12 (proposed Spine amendment S3) and 14 (S4) · **Depends on:** 7.2, 2.2 · **decision gate D14 (S3, S4), for the specification-link and label criteria** · **Verification:** UI tests; a test asserting that viewing an interaction makes no model call · **Status:** ready (the specification-link and label criteria wait on D14)",
    "UX gaps 12 (Spine AD-28) and 14 (Spine AD-29) · **Depends on:** 7.2, 2.2 · **decision gate D14 (AD-28, AD-29), for the specification-link and label criteria** · **Verification:** UI tests; a test asserting that viewing an interaction makes no model call · **Status:** ready (the specification-link and label criteria wait on D14)")
rep("epics", "**Then** the label is \"Customer email · {received date and time}\".",
    "**Then** the label is \"Customer email · {received date and time}\".\n\n"
    "**Given** a reply that relied on a specification rule\n**When** shown\n"
    "**Then** the rule is quoted and linked to its item in Understanding through the reference's locator, which names the expression area and the item.\n\n"
    "**Given** an interaction whose adapter supplied a display label and received time\n**When** labelled\n"
    "**Then** the label uses them as stored, and the Core never interprets them (Spine AD-29).")

# ================================================================ sprint-status comments
for k, old, new in [
    ("3-3-readable-validation-findings-and-version-states", "blocked: D14 (S2), D15 (A5)", f"blocked: D14 (AD-27), D15 (A5); wording applied {D}"),
    ("4-5-a-closed-vocabulary-and-reportable-error-references", "reference criterion waits on D15 (A6)", f"reference criterion waits on D15 (A6); wording applied {D}"),
    ("5-2-take-in-the-operator-s-own-material", "blocked: D15 (A4)", f"blocked: D15 (A4); wording applied {D}"),
    ("7-1-the-agent-status-line-and-suspend", "persistence criterion waits on D14 (S1)", f"persistence and suspension-outcome criteria wait on D14 (AD-26, A7); wording applied {D}"),
    ("7-3-the-interaction-viewer", "spec-link and label criteria wait on D14 (S3, S4)", f"spec-link and label criteria wait on D14 (AD-28, AD-29); wording applied {D}"),
]:
    rep("sprint", f"  {k}: backlog  # {old}\n", f"  {k}: backlog  # {new}\n")
rep("sprint", "  4-1-evaluate-every-interaction-from-its-record: backlog\n", "  4-1-evaluate-every-interaction-from-its-record: backlog  # suspension-exclusion criterion waits on D14 (A7)\n")
rep("sprint", "  7-2-activity-the-divergence-list: backlog\n", "  7-2-activity-the-divergence-list: backlog  # suspended-arrivals criterion waits on D14 (item 20)\n")

# ================================================================ program, register, handoff
rep("plan", "3.3 on D14, D15; 4.5's reference criterion on D15 |", "3.3 on D14, D15; 4.5's reference criterion on D15; 4.1's suspension-exclusion criterion on D14 |")
rep("plan", "criteria of 7.1 and 7.3 on D14 |", "criteria of 7.1, 7.2 and 7.3 on D14 |")
rep("plan", "| PROPOSED (architecture) | 3.3, 7.1 (one criterion), 7.3 (two criteria) | No | Wording under review — prepared, not applied (review of 2026-10-15) | — |",
    f"| PROPOSED (architecture) | 3.3, 4.1, 7.1, 7.2, 7.3 (criteria) | No | Wording approved by the user and applied {D}: Spine AD-26–AD-29 (S1 as an operator-triggered declared safety halt) and PRD §14 A7; decision status pending the user's confirmation | — |")
rep("plan", "| PROPOSED (product) | 3.3, 4.5 (one criterion), 5.2 | No | Wording under review — prepared, not applied; A4 is a product choice | — |",
    f"| PROPOSED (product) | 3.3, 4.5 (one criterion), 5.2 | No | Wording approved by the user and applied {D}: PRD §14 A4–A6; decision status pending the user's confirmation | — |")
rep("plan", "they go to their owning documents through gates D14 and D15 (2026-10-15).",
    f"they go to their owning documents through gates D14 and D15 (2026-10-15); their wording was approved and applied on {D}, and both gates stay PROPOSED until the user confirms the decisions.")
rep("reg", "all PROPOSED (2026-10-15).",
    f"all PROPOSED (2026-10-15). {D}: the user approved the wording (not the decisions, which stay PROPOSED); applied as Spine AD-26–AD-29 and PRD §14 A4–A7, with EXPERIENCE.md "
    "Amendments item 20. B-16's status column is unchanged: gaps 3, 15, 16, 18 and 19 remain open.")
rep("handoff", "Stories 3.3 and 5.2 are blocked on them; 4.5, 7.1 and 7.3 have one or two criteria waiting.",
    f"Stories 3.3 and 5.2 are blocked on them; 4.5, 7.1 and 7.3 have one or two criteria waiting. *({D}: wording approved by the user and applied as "
    "Spine AD-26–AD-29 and PRD §14 A4–A7; the decisions stay PROPOSED, so the gates and the stories' gate markers remain.)*")

for k, v in F.items():
    io.open(f"{root}/{v}", "w", encoding="utf-8", newline="").write(text[k].replace(LF, eol[k]))
print("stage 2 applied to", root)
