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

Urgent symptoms are classified by a keyword list in mock mode and in the fast
router, and by the model from `INTENT_DESCRIPTIONS` in live mode. Live
coverage is thin: one LIVE run (`gpt-6-luna`, 3 repetitions) handed off a
symptom described without any listed keyword (scenario PD2 in
`builder_platform/tests/live_scenarios/`). At the yes/no question only a bare
yes or no is an answer; anything else, an urgent symptom included, is
classified like any other message, and the booking is never made on it. Not covered: any channel or real
practice-management system.
