# Bright Smile Dental — inbound front-desk agent

A copy of `boilerplate/` with only the domain files edited (`config.py`,
`tools.py`, this README). Engine files are byte-identical to `boilerplate/`
(enforced by `builder_platform/tests/test_engine_drift.py`).

What it does: answers hours and services questions and books a cleaning,
checkup, or consultation. The booking asks the patient to confirm, and the
engine reads it back from the practice calendar before calling it booked.

Boundaries, each enforced in code:

| Boundary | Where |
| --- | --- |
| Urgent symptoms go to a person (`human_handoff`), never triage — including when they arrive mid-booking or at the yes/no question | `INTENT_KEYWORDS["human_handoff"]` (ranked first) |
| The agent never asks about symptoms | `SYMPTOM_QUESTION_RE` in `BLOCKED_PATTERNS`, applied to every outgoing reply |
| No refund or billing authority | no refund flow, no refund tool in `TOOL_REGISTRY`; money questions get the fixed `faq_billing` answer |
| A booking is reported only after read-back | `tools.VERIFIERS["book_dental_visit"]` |

Run it in mock mode (no keys, no tokens):

```text
python selftest.py         # must print SELF-TEST PASSED
python agent_sandbox.py    # text REPL for a developer
```

Behaviour tests: `python -m pytest builder_platform/tests/test_dental_agent.py`
from the repo root.

Not covered: live-model classification of urgent symptoms (the keyword list is
what mock mode and the fast router use; a live model classifies from
`INTENT_DESCRIPTIONS`), and any channel or real practice-management system.
