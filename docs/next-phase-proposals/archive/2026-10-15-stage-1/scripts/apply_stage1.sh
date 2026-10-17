#!/usr/bin/env bash
# Apply the approved Stage 1 to <root> (a scratch copy or the repository). Stops on the first failure.
set -euo pipefail
ROOT="$1"
S="C:/Users/OMERBA~1/AppData/Local/Temp/claude/c--Users-Omer-Bassan-Desktop-Projects-AgentStudio/db5b62e0-3deb-4b0a-aa65-89e47aeda91a/scratchpad"
REPO="C:/Users/Omer Bassan/Desktop/Projects/AgentStudio"
python -I "$S/stage1_approved.py" "$ROOT" --with-experience --restore-lf
python -I "$S/regen_trace.py" "$ROOT" "$REPO/docs/next-phase-proposals/tools/trace_epics.py"
uv run --quiet "$REPO/_bmad/scripts/memlog.py" append \
  --path "$ROOT/_bmad-output/planning-artifacts/prds/prd-AgentStudio-2026-10-08/.memlog.md" --type change --by user \
  --text "2026-10-15 POST-FINAL AMENDMENT RECORD: §14 A1–A3 with inline markers at §2 (Specification reviewer), §4.4, FR8, FR11, §8.1, O1, §12 E2, §13.2; no requirement text rewritten; each records a decision already taken in the UX run (UX memlog lines 22, 37, 58, 73, 74). Decision statuses unchanged."
uv run --quiet "$REPO/_bmad/scripts/memlog.py" append \
  --path "$ROOT/_bmad-output/planning-artifacts/ux-designs/ux-AgentStudio-2026-10-08/.memlog.md" --type change --by user \
  --text "2026-10-15 UPSTREAM CONFIRMATION RECORDED: Amendments item 1 (divergence on the escalation email) is recorded in PRD §14 A2 and item 7 (operator is the approver; approval is not validity) in PRD §14 A3; the two Status cells gain 'Recorded upstream'; original text unchanged; materiality (Open Question 3) stays open; decision statuses unchanged."
