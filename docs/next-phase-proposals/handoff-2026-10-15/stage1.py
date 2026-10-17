"""Stage 1 documentation corrections. Usage: python stage1.py <root> [--with-experience]

<root> is the repository root or a scratch copy with the same relative paths.
Every replacement asserts its target occurs exactly once, so a drifted file aborts
before anything is written (all files are edited in memory first, then written).
Memlog lines are NOT written here: they go through `_bmad/scripts/memlog.py append`.
"""
import io
import re
import sys

root = sys.argv[1]
WITH_EXPERIENCE = "--with-experience" in sys.argv
PA = "_bmad-output/planning-artifacts"
F = {
    "prd": f"{PA}/prds/prd-AgentStudio-2026-10-08/prd.md",
    "exp": f"{PA}/ux-designs/ux-AgentStudio-2026-10-08/EXPERIENCE.md",
    "epics": f"{PA}/epics.md",
    "sprint": "_bmad-output/implementation-artifacts/sprint-status.yaml",
    "plan": "docs/next-phase-proposals/NEXT-PHASE-PLAN.md",
    "reg": "docs/next-phase-proposals/BMAD-DECISION-REGISTER.md",
    "handoff": "docs/next-phase-proposals/HANDOFF.md",
}
RESTORE_LF = "--restore-lf" in sys.argv
# Read without newline translation so line endings are seen as they are; edit with LF;
# write back in each file's own style.
CRLF, LF = "\r\n", "\n"
raw = {k: io.open(f"{root}/{v}", encoding="utf-8", newline="").read() for k, v in F.items()}
eol = {k: (CRLF if CRLF in r else LF) for k, r in raw.items()}
text = {k: r.replace(CRLF, LF) for k, r in raw.items()}
# Optional: the four planning docs whose LF endings an earlier session turned into CRLF go back to LF.
EXTRA = {"impl": "docs/next-phase-proposals/IMPLEMENTATION-STATE.md", "gate": "docs/next-phase-proposals/PROOF-GATE.md"}
if RESTORE_LF:
    for k in ("plan", "reg"):
        eol[k] = LF
    for k, v in EXTRA.items():
        r = io.open(f"{root}/{v}", encoding="utf-8", newline="").read()
        F[k], text[k], eol[k] = v, r.replace(CRLF, LF), LF


def rep(key, old, new):
    n = text[key].count(old)
    assert n == 1, (key, old[:80], n)
    text[key] = text[key].replace(old, new)


# ---------------------------------------------------------------- 1.1 PRD (A1-A3)
rep("prd", "updated: 2026-10-08\n---", "updated: 2026-10-08\namended: 2026-10-15\n---")
rep("prd", "\n>\n> Architecture is settled elsewhere.",
    "\n>\n> **Amended after finalization (§14).** Later approved decisions supersede or narrow a few statements below. "
    "Each keeps its original wording and carries an inline *[§14 An]* marker; where a marker appears, §14 governs.\n"
    ">\n> Architecture is settled elsewhere.")
rep("prd", "(FR8). Template-*defined behaviour* is not |",
    "(FR8). Template-*defined behaviour* is not *[Superseded for V1 — §14 A1]* |")
rep("prd", "It is a specification starting point, never a behaviour template. |",
    "It is a specification starting point, never a behaviour template. *[Superseded for V1 — §14 A1: not offered in V1]* |")
rep("prd", "**Why starting points are seeded rather than authored (FR8).** A per-vertical",
    "**Why starting points are seeded rather than authored (FR8).** *[Superseded for V1 — §14 A1]* A per-vertical")
rep("prd", "| **O1** | Who performs specification review, and with what competence |",
    "| **O1** | Who performs specification review, and with what competence *[Narrowed for V1 — §14 A3]* |")
rep("prd", "optional pre-filled specification starting points;",
    "optional pre-filled specification starting points *[superseded for V1 — §14 A1]*;")
rep("prd", "there is no alerting, and no metrics dashboard (§7.2).",
    "there is no alerting, and no metrics dashboard (§7.2). *[Amended — §14 A2]*")
text["prd"] = text["prd"].rstrip("\n") + (
    "\n\n## 14. Amendments after finalization\n\n"
    "Recorded 2026-10-15. Each row records a decision already taken in an approved BMAD run; no requirement text above was "
    "rewritten, and each affected statement carries an inline marker. Status is the decision's own, from its source.\n\n"
    "| # | Amendment | Affects | Source | Status |\n"
    "|---|---|---|---|---|\n"
    "| A1 | No vertical starter templates in V1. The Builder's only path is conversation plus the operator's material → "
    "Business Specification and Business Knowledge. Reconsiderable later purely as an onboarding optimisation. "
    "| §4.4, FR8, §8.1 note, §12 E2 | UX `.memlog.md` line 22 `(override)`; EXPERIENCE.md, Prohibitions carried from the sources | APPROVED |\n"
    "| A2 | A material divergence may ride the declared escalation email path (FR103) when it requires operator attention. "
    "Not authorised by this amendment: a generic notification system, a divergence-alerts product, an inbox, a digest, or any "
    "notification framework. What makes a divergence material is an upstream attention-policy question and remains open. "
    "| §13.2 | UX `.memlog.md` lines 58 `(override)`, 73, 74; EXPERIENCE.md Amendments item 1 and Open Question 3 | APPROVED (materiality OPEN) |\n"
    "| A3 | In V1 the business operator is the approver: no separate reviewer role, no approval hierarchy. Approval does not "
    "determine validity — the blocking validation suite does. Who may approve beyond V1, and with what competence, remains open. "
    "| O1, FR11 | UX `.memlog.md` line 37; EXPERIENCE.md Amendments item 7 | APPROVED |\n"
)

# ---------------------------------------------------------------- 1.2 EXPERIENCE (optional, Q1)
if WITH_EXPERIENCE:
    rep("exp", "| PRD §13.2 | **Explicit amendment.** A product decision taken in this UX discussion, not a reading of the existing PRD. |",
        "| PRD §13.2 | **Explicit amendment.** A product decision taken in this UX discussion, not a reading of the existing PRD. "
        "**Recorded upstream: PRD §14 A2 (2026-10-15).** |")
    rep("exp", "| PRD O1 | **Resolved here.** Confirm upstream. |",
        "| PRD O1 | **Resolved here.** Confirm upstream. **Recorded upstream: PRD §14 A3 (2026-10-15).** |")

# ---------------------------------------------------------------- 1.3-1.7 epics.md
rep("epics", "FR101 (surface). **UX-DRs:** 1–13, 18, 20–28, 30.", "FR101 (surface). **UX-DRs:** 1–12, 18, 20–28, 30.")
rep("epics", "- **Migration assessment** (PRD §7.4, §12) is distributed across E3–E9:",
    "- **Migration assessment** (PRD §7.4, §12) is distributed across E3–E9 and recorded once, by Story 1.9:")
routes = {
    3: "gate D10 (Story 8.6)", 4: "proposed Spine amendment S1, gate D14 (Story 7.1)",
    5: "proposed Spine amendment S2, gate D14 (Story 3.3)", 7: "recorded in PRD §14 A3",
    8: "gate D7 (Story 4.7)", 10: "proposed PRD amendment A4, gate D15 (Story 5.2)",
    11: "resolved in UX (Story 7.2)", 12: "proposed Spine amendment S3, gate D14 (Story 7.3)",
    13: "proposed PRD amendment A5, gate D15 (Story 3.3)", 14: "proposed Spine amendment S4, gate D14 (Story 7.3)",
    15: "gate D8 (Story 7.8)", 16: "gate D9 (Story 7.7)", 17: "proposed PRD amendment A6, gate D15 (Story 4.5)",
    18: "gate D10 (Story 8.6)", 19: "gate D12 (Story 8.5)",
}
for n, r in routes.items():
    pat = re.compile(rf"^(- Gap {n} .*)$", re.M)
    assert len(pat.findall(text["epics"])) == 1, n
    text["epics"] = pat.sub(lambda m: f"{m.group(1)} **Route:** {r}.", text["epics"])
rep("epics", "- Open question 3: what makes a divergence *material* (Amendment 1)",
    "- Open question 3 (gate D11, Story 8.7): what makes a divergence *material* (Amendment 1)")
rep("epics", "- Open question 4: whether the escalation address",
    "- Open question 4 (gate D10, Story 8.5): whether the escalation address")
rep("epics", "UX upstream contract gaps (EXPERIENCE.md, Amendments and Upstream Gaps — \"raise each with the owning document before implementation\"); each is owned by the story that first needs it:",
    "UX upstream contract gaps (EXPERIENCE.md, Amendments and Upstream Gaps — \"raise each with the owning document before implementation\"). "
    "Each is raised with its owning document; amendments marked *proposed* are not requirements until the user approves them under the named gate:")

# Story 1.9 — migration assessment
rep("epics", "**Traces:** PRD §7.5 and §12; Spine Proof Gate",
    "**Traces:** PRD §7.5 and §12; PRD §7.4 migration assessment; Spine Proof Gate")
rep("epics", "**Given** the nine axes\n**When** the verdict is written",
    "**Given** the PRD §7.4 inventory of the shipped system\n**When** the gate report is written\n"
    "**Then** each item's disposition is recorded under the PRD's own postures — reusable largely as-is, concept transfers but code does not, "
    "not reusable, deliberately not carried forward — with its evidence\n"
    "**And** the report confirms that the fifteen-node pipeline was not ported.\n\n"
    "**Given** the nine axes\n**When** the verdict is written")

# 1.7 — the seven UX contract gaps wait on their owning documents
rep("epics", "UX gaps 5 (version lifecycle) and 13 (finding shape); UX-DR10, UX-DR12 (data) · **Depends on:** 3.1, 3.2 · **Verification:** contract tests on the finding and version-state types · **Status:** ready",
    "UX gaps 5 (version lifecycle; proposed Spine amendment S2) and 13 (finding shape; proposed PRD amendment A5); UX-DR10, UX-DR12 (data) · **Depends on:** 3.1, 3.2 · **decision gates D14 (S2), D15 (A5)** · **Verification:** contract tests on the finding and version-state types · **Status:** blocked (D14, D15)")
rep("epics", "**Then** they are recorded in the decision register as technical contracts answering UX gaps 5 and 13.",
    "**Then** they follow the version-state and finding contracts as approved under D14 (S2) and D15 (A5), and not a contract chosen in the code.")
rep("epics", "UX gap 17 (reference format: technical choice, recorded) · **Depends on:** 4.1 ·",
    "UX gap 17 (reference format; proposed PRD amendment A6) · **Depends on:** 4.1 · **decision gate D15 (A6), for the reference criterion only** ·")
rep("epics", "**Verification:** a test that fails if an operator-facing interface emits a status string outside the vocabulary · **Status:** ready",
    "**Verification:** a test that fails if an operator-facing interface emits a status string outside the vocabulary · **Status:** ready (the reference criterion waits on D15)")
rep("epics", "UX gap 10 (formats, size and duration limits — technical defaults chosen and recorded) · **Depends on:** 5.1, 2.1 · **Verification:** ingestion tests per format, including a corrupt file · **Status:** ready",
    "UX gap 10 (formats, size and duration limits; proposed PRD amendment A4) · **Depends on:** 5.1, 2.1 · **decision gate D15 (A4)** · **Verification:** ingestion tests per format, including a corrupt file · **Status:** blocked (D15)")
rep("epics", "**Given** the chosen limits\n**When** recorded\n**Then** they appear in the decision register as the technical answer to UX gap 10.",
    "**Given** the formats and limits approved under D15 (A4)\n**When** material falls outside them, or is only partly readable\n"
    "**Then** the operator is told which source, which limit and which parts were used, and nothing is silently truncated.")
rep("epics", "UX gap 4 (persistent suspended state) · **Depends on:** 6.1, Story 1.6 · **Verification:** UI tests including a forced suspend failure · **Status:** ready",
    "UX gap 4 (persistent suspended state; proposed Spine amendment S1) · **Depends on:** 6.1, Story 1.6 · **decision gate D14 (S1), for the persistence criterion only** · **Verification:** UI tests including a forced suspend failure · **Status:** ready (the persistence criterion waits on D14)")
rep("epics", "**Then** it persists, recorded under the technical answer to UX gap 4.",
    "**Then** it persists as the suspension state approved under D14 (S1).")
rep("epics", "UX-DR16; UX gaps 12, 14 · **Depends on:** 7.2, 2.2 · **Verification:** UI tests; a test asserting that viewing an interaction makes no model call · **Status:** ready",
    "UX-DR16, UX-DR21; UX gaps 12 (proposed Spine amendment S3) and 14 (S4) · **Depends on:** 7.2, 2.2 · **decision gate D14 (S3, S4), for the specification-link and label criteria** · **Verification:** UI tests; a test asserting that viewing an interaction makes no model call · **Status:** ready (the specification-link and label criteria wait on D14)")

# 1.7b — Story 5.3 must not depend on a later epic (BMAD: no forward dependencies)
rep("epics", "**Depends on:** 5.1, 5.2 · soft prerequisite Story 9.8 ·",
    "**Depends on:** 5.1, 5.2 · recommended input, not a dependency: notes from the operator conversations (Story 9.8), if held ·")
rep("epics", "**Soft prerequisite:** the 2–3 operator conversations of Story 9.8 (FR94) should precede Story 5.3,",
    "**Recommended, not a dependency:** the 2–3 operator conversations of Story 9.8 (FR94) should be held before Story 5.3,")

rep("epics", "30/30 UX-DRs; no forward dependencies). Awaiting user approval",
    "30/30 UX-DRs; no forward dependencies). 2026-10-15 re-check: that check missed one forward dependency (Story 5.3 named Story 9.8 as a soft prerequisite); corrected to a recommendation, all checks re-run. Awaiting user approval")

# 1.4 — UX-DR21 on the other product-voice surfaces
rep("epics", "FR108, FR115 (sources); UX-DR15 ·", "FR108, FR115 (sources); UX-DR15, UX-DR21 ·")
rep("epics", "**Traces:** FR46, FR52, NFR16; UX-DR19, UX-DR20 ·", "**Traces:** FR46, FR52, NFR16; UX-DR19, UX-DR20, UX-DR21 ·")
rep("epics", "**Traces:** FR103, FR74, FR69; UX-DR29;", "**Traces:** FR103, FR74, FR69; UX-DR21, UX-DR29;")

# 1.6 — Epic 9: the Builder never receives the hand-written specifications
GUARD = ("\n\n**Given** any hand-written specification of this business from Epics 1–2 (for example "
         "`studio/businesses/<business>/specification.toml`), or any earlier Builder output for it\n"
         "**When** the Builder session runs\n"
         "**Then** none of those is among the Builder's inputs, and the session record lists every input it was given "
         "(the business's material and the operator's answers only)\n"
         "**And** a test fails if a hand-written specification is among the inputs.")
for sid, nxt in [("9.2", "9.3"), ("9.3", "9.4"), ("9.4", "9.5"), ("9.5", "9.6")]:
    head = f"### Story {sid}:"
    i = text["epics"].index(head)
    j = text["epics"].index(f"### Story {nxt}:", i)
    block = text["epics"][i:j].rstrip("\n")
    assert block.count("**Acceptance Criteria:**") == 1, sid
    text["epics"] = text["epics"][:i] + block + GUARD + "\n\n" + text["epics"][j:]

# ---------------------------------------------------------------- sprint-status comments
for key, note in [
    ("3-3-readable-validation-findings-and-version-states", "blocked: D14 (S2), D15 (A5)"),
    ("4-5-a-closed-vocabulary-and-reportable-error-references", "reference criterion waits on D15 (A6)"),
    ("5-2-take-in-the-operator-s-own-material", "blocked: D15 (A4)"),
    ("7-1-the-agent-status-line-and-suspend", "persistence criterion waits on D14 (S1)"),
    ("7-3-the-interaction-viewer", "spec-link and label criteria wait on D14 (S3, S4)"),
]:
    rep("sprint", f"  {key}: backlog\n", f"  {key}: backlog  # {note}\n")

rep("sprint", "# human track, owner: user; start now; soft prerequisite of 5.3", "# human track, owner: user; start now; recommended before 5.3 (not a dependency)")
rep("plan", "| 9.7, 9.8 (and 5.3 softly) |", "| 9.7, 9.8 (and recommended before 5.3) |")

# ---------------------------------------------------------------- program, register, handoff
rep("plan", "| 3 | Epic 3 — Safe change; Epic 4 — Evaluation and backlog | 3.1–3.4; 4.1–4.7 | 4.7 blocked on D7 (O11) |",
    "| 3 | Epic 3 — Safe change; Epic 4 — Evaluation and backlog | 3.1–3.4; 4.1–4.7 | 4.7 blocked on D7 (O11); 3.3 on D14, D15; 4.5's reference criterion on D15 |")
rep("plan", "| 4 | Epic 5 — Builder | 5.1–5.9 | Soft prerequisite: 9.8 operator conversations |",
    "| 4 | Epic 5 — Builder | 5.1–5.9 | Recommended before 5.3, not a dependency: 9.8 operator conversations; 5.2 blocked on D15 |")
rep("plan", "| 5 | Epic 6 — Teaching workspace; Epic 7 — Run surfaces | 6.1–6.6; 7.1–7.8 | 7.7 blocked on D9; 7.8 on D8 |",
    "| 5 | Epic 6 — Teaching workspace; Epic 7 — Run surfaces | 6.1–6.6; 7.1–7.8 | 7.7 blocked on D9; 7.8 on D8; criteria of 7.1 and 7.3 on D14 |")
rep("plan", "| Defer: the Builder is designed against no real operator |",
    "| Defer: the Builder is designed against no real operator |\n"
    "| **D14** | Architecture Spine amendments S1–S4 answering UX contract gaps 4, 5, 12, 14 (EXPERIENCE.md: \"raise each with the owning document\") | PROPOSED (architecture) | 3.3, 7.1 (one criterion), 7.3 (two criteria) | No | Wording under review — prepared, not applied (review of 2026-10-15) | — |\n"
    "| **D15** | PRD amendments A4–A6 answering UX contract gaps 10, 13, 17 | PROPOSED (product) | 3.3, 4.5 (one criterion), 5.2 | No | Wording under review — prepared, not applied; A4 is a product choice | — |")
rep("plan", "The **web stack** for Epics 6–7, the **build order** of the four exemplars (Story 9.2) and the **contracts** answering UX gaps 4, 5, 10, 12, 13, 14 and 17 are technical choices, recorded in the register when made.",
    "The **web stack** for Epics 6–7 and the **build order** of the four exemplars (Story 9.2) are technical choices, recorded in the register when made. The UX contract gaps 4, 5, 10, 12, 13, 14 and 17 are **not** technical choices: they go to their owning documents through gates D14 and D15 (2026-10-15).")
rep("plan", "| UX gaps 3–19 | not scheduled |",
    "| UX-DR21 | traced to 6.1 only | also 7.2, 7.3, 7.5, 8.5 (product voice on Run surfaces and the escalation email) | EXPERIENCE.md Voice and Tone |\n"
    "| PRD §7.4 migration assessment | no story | Story 1.9 records every asset's disposition | PRD §12 |\n"
    "| Epic 6 header | claimed UX-DR13 | UX-DR13 belongs to Story 8.6 | EXPERIENCE.md Surface inventory |\n"
    "| Epic 9 builds | no rule on inputs | 9.2–9.5 forbid the hand-written specifications as Builder input | PRD review F4.3; FR88 |\n"
    "| UX gaps 3–19 | not scheduled |")
rep("reg", "**B-16** (UX contract gaps) → each gap owned by a story or a gate (NEXT-PHASE-PLAN §6; `epics.md` Additional Requirements).",
    "**B-16** (UX contract gaps) → each gap owned by a story or a gate (NEXT-PHASE-PLAN §6; `epics.md` Additional Requirements); gaps 4, 5, 12, 14 go to the Spine (gate D14) and 10, 13, 17 to the PRD (gate D15), all PROPOSED (2026-10-15).")
rep("reg", "- **T9–T12 remain PROPOSED** (gates D2, D4, D5, D6).",
    "- **CX-06** (clerical, 2026-10-15): the PRD now records the two approved amendments in §14 (A1 templates, A2 divergence alerting) plus A3 (O1 narrowed for V1), with inline markers and no rewritten text. Status column unchanged.\n"
    "- **T9–T12 remain PROPOSED** (gates D2, D4, D5, D6).")
rep("handoff", "3. UX contract gaps 4, 5, 10, 12, 13, 14, 17 are to be answered as technical contracts recorded in the register by the stories that need them (3.3, 4.5, 5.2, 7.1, 7.3), not as amendments to the Spine; the UX spine asked for them to be raised with the owning document. If the user wants the Spine amended, that is a `bmad-architecture` update.",
    "3. *(Revised 2026-10-15.)* UX contract gaps 4, 5, 12, 14 go to the Spine (gate D14) and 10, 13, 17 to the PRD (gate D15), as the UX spine instructs; the wording is prepared for the user's review and not applied. Stories 3.3 and 5.2 are blocked on them; 4.5, 7.1 and 7.3 have one or two criteria waiting.")

for k, v in F.items():
    io.open(f"{root}/{v}", "w", encoding="utf-8", newline="").write(text[k].replace(LF, eol[k]))
print("stage 1 applied to", root, "(EXPERIENCE included)" if WITH_EXPERIENCE else "(EXPERIENCE skipped)")
