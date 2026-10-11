# -*- coding: utf-8 -*-
"""Cross-business evaluation suite (C7, deterministic mode).

One engine, three businesses. Each business has a scenario file in
eval_scenarios/<business>.json: a list of conversations (inbound turns) with
per-turn EXPECTATIONS about the trace — never about reply wording. Scenarios
whose id starts with "X" send the identical input to every business, so the
differences in expected behaviour come from each business's declarations.

Run just this suite:
    python -m pytest builder_platform/tests/test_cross_business_eval.py -v

Mock mode only (OPENAI_API_KEY blanked by agent_driver): zero model calls,
zero tokens. Each business runs in its own subprocess, once per session.

Expectation keys (all optional, per turn):
  intent                 intent_detect's intent
  tools_run              exact list of tools that executed this turn ([] = none)
  pending_confirmation   a yes/no question is pending after the turn
  interrupted            the turn ended suspended at the operator gate
  outcome                execution_validator outcome (verified/unchecked/failed/unverified)
  refusal                kind of a typed refusal (business_refusal/platform_error)
  handoff                handoff_requested after the turn
  facts_have / facts_lack  session_facts keys present / absent
File-level: registry_lacks — tools that must not be registered at all.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from agent_driver import run_agent  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
SCENARIO_DIR = Path(__file__).resolve().parent / "eval_scenarios"
SPECS = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted(SCENARIO_DIR.glob("*.json"))}
CASES = [(biz, sc["id"]) for biz, spec in SPECS.items() for sc in spec["scenarios"]]
_KNOWN = {"intent", "tools_run", "pending_confirmation", "interrupted", "outcome",
          "refusal", "handoff", "facts_have", "facts_lack"}


def _observe(turn: dict) -> dict:
    """The trace properties an expectation can name, read from one driver turn."""
    def last(node, key):
        vals = [e.get(key) for e in turn["trace"] if e["node"] == node]
        return vals[-1] if vals else None
    refusals = [e["refusal"]["kind"] for e in turn["trace"]
                if e["node"] in ("tool_exec", "hitl_gate") and e.get("refusal")]
    return {
        "intent": last("intent_detect", "intent"),
        "tools_run": [c[0] for c in turn["tool_calls"]],
        "pending_confirmation": bool(turn["pending_confirmation"]),
        "interrupted": turn["interrupted"],
        "outcome": last("execution_validator", "outcome"),
        "refusal": refusals[-1] if refusals else None,
        "handoff": turn["handoff_requested"],
        "facts": set(turn["session_facts"]),
    }


def check_turn(expect: dict, turn: dict) -> list:
    """Every mismatch between an expectation and an observed turn, as text."""
    unknown = set(expect) - _KNOWN
    if unknown:
        return [f"unknown expectation key(s) {sorted(unknown)}"]
    seen = _observe(turn)
    problems = []
    for key, want in expect.items():
        if key == "facts_have":
            missing = set(want) - seen["facts"]
            if missing:
                problems.append(f"facts_have: missing {sorted(missing)} (facts={sorted(seen['facts'])})")
        elif key == "facts_lack":
            present = set(want) & seen["facts"]
            if present:
                problems.append(f"facts_lack: present {sorted(present)}")
        elif seen[key] != want:
            problems.append(f"{key}: expected {want!r}, observed {seen[key]!r}")
    return problems


@pytest.fixture(scope="session")
def runs():
    """One driver subprocess per business: every scenario's conversation."""
    out = {}
    for biz, spec in SPECS.items():
        reply = run_agent(REPO / spec["agent_dir"],
                          {"conversations": [sc["turns"] for sc in spec["scenarios"]]})
        out[biz] = {"registry": reply["tool_registry"],
                    "conversations": dict(zip((sc["id"] for sc in spec["scenarios"]),
                                              reply["conversations"]))}
    return out


@pytest.mark.parametrize("business, scenario", CASES, ids=[f"{b}/{s}" for b, s in CASES])
def test_scenario(runs, business, scenario):
    spec = SPECS[business]
    sc = next(s for s in spec["scenarios"] if s["id"] == scenario)
    turns = runs[business]["conversations"][scenario]
    assert len(sc["expect"]) == len(turns), f"{business}/{scenario}: one expectation per turn"
    failures = []
    for i, (expect, turn) in enumerate(zip(sc["expect"], turns), start=1):
        failures += [f"turn {i} ({turn['message']!r}): {p}" for p in check_turn(expect, turn)]
    assert not failures, (f"{business}/{scenario} — {sc['behaviour']}\n  "
                          + "\n  ".join(failures))


@pytest.mark.parametrize("business", sorted(SPECS))
def test_registry_lacks(runs, business):
    lacks = set(SPECS[business].get("registry_lacks", ())) & set(runs[business]["registry"])
    assert not lacks, f"{business}: must not register {sorted(lacks)}"


def test_cross_business_scenarios_send_identical_input():
    """An X scenario is only a comparison if every business got the same turns."""
    xs = {}
    for biz, spec in SPECS.items():
        for sc in spec["scenarios"]:
            if sc["id"].startswith("X"):
                xs.setdefault(sc["id"], {})[biz] = sc["turns"]
    assert xs, "no cross-business scenarios"
    for sid, by_biz in xs.items():
        assert set(by_biz) == set(SPECS), f"{sid} missing for {sorted(set(SPECS) - set(by_biz))}"
        first = next(iter(by_biz.values()))
        assert all(t == first for t in by_biz.values()), f"{sid}: inputs differ across businesses"


def test_checker_reports_a_wrong_expectation():
    """The checker is not vacuous: a wrong expectation is reported precisely."""
    turn = {"trace": [{"node": "intent_detect", "intent": "book_visit"},
                      {"node": "execution_validator", "outcome": "verified"}],
            "tool_calls": [["book_dental_visit", {}]], "pending_confirmation": {},
            "interrupted": False, "handoff_requested": False,
            "session_facts": {"confirmation": "BSD-00001"}, "message": "yes"}
    assert check_turn({"tools_run": ["book_dental_visit"], "outcome": "verified",
                       "facts_have": ["confirmation"]}, turn) == []
    wrong = check_turn({"tools_run": [], "outcome": "unverified", "handoff": True,
                        "facts_lack": ["confirmation"], "intnet": "x"}, turn)
    assert wrong == ["unknown expectation key(s) ['intnet']"]
    wrong = check_turn({"tools_run": [], "outcome": "unverified", "handoff": True,
                        "facts_lack": ["confirmation"]}, turn)
    assert len(wrong) == 4, wrong
