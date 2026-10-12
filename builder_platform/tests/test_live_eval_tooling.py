"""The live-evaluation tooling (agent_driver live mode, live_eval.py) without
spending a token.

The end-to-end case runs the driver in LIVE mode against a closed local port:
every model call fails at connect time, which is exactly the degraded path a
live report must expose, and it drives the budget stop with real per-call
records instead of a hand-made trace.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import live_eval  # noqa: E402
from agent_driver import run_agent, turn_spend  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
ACME = REPO / "boilerplate"


def _call(**kw):
    base = {"model": "m", "kind": "structured", "path": "parse", "ok": True, "error": None,
            "input_tokens": 1000, "output_tokens": 100, "input_chars": 3000, "latency_ms": 5.0}
    return {**base, **kw}


def test_turn_spend_uses_reported_usage_and_overestimates_the_rest():
    trace = [{"node": "intent_detect", "model_calls": [_call()]},
             {"node": "think", "model_calls": [
                 _call(ok=False, error="APIConnectionError", input_tokens=None, output_tokens=None,
                       input_chars=301),
                 _call(path="json_mode", parse_error="BadRequestError", input_chars=30)]},
             {"node": "router"}]
    s = turn_spend(trace, price_in_per_m=1.0, price_out_per_m=10.0)
    # reported 1000+1000, estimated ceil(301/3)=101 and ceil(30/3)=10 for the failed parse attempt
    assert s["input_tokens"] == 1000 + 101 + 1000 + 10
    assert s["output_tokens"] == 100 + 400 + 100 + 400
    assert s["estimated_calls"] == 2
    assert s["cost_usd"] == pytest.approx((2111 * 1.0 + 1000 * 10.0) / 1e6)


def test_live_run_without_a_key_refuses_to_start(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY is not set"):
        run_agent(ACME, {"conversations": [["hello"]]}, live=True)


def test_live_eval_refuses_to_start_without_a_key(monkeypatch, capsys):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert live_eval.main(["--model", "m", "--price-in", "1", "--price-out", "1"]) == 2


@pytest.fixture
def dead_endpoint(monkeypatch):
    """A live configuration whose every call fails fast: no tokens, no network."""
    monkeypatch.setenv("OPENAI_API_KEY", "not-a-real-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "http://127.0.0.1:9/v1")
    for tier in live_eval.TIERS:
        monkeypatch.setenv(tier, "dead-model")


def test_failed_live_calls_are_reported_and_the_budget_stops_the_run(dead_endpoint):
    reply = run_agent(ACME, {"conversations": [["hello", "what are your hours?"], ["hello"]],
                             "budget": {"max_cost_usd": 1e-9, "price_in_per_m": 1.0,
                                        "price_out_per_m": 1.0}},
                      timeout=300, live=True)
    assert reply["llm_mode"].startswith("LIVE")
    first, second = reply["conversations"]
    assert len(first) == 1 and second == [], "the budget did not stop the run before the next turn"
    assert reply["spend"]["stopped"] is True and reply["spend"]["estimated_calls"] >= 1
    calls = [c for e in first[0]["trace"] for c in e.get("model_calls") or ()]
    assert calls and not any(c["ok"] for c in calls)
    assert next(e for e in first[0]["trace"] if e["node"] == "intent_detect")["degraded"] is True

    raw = {"model": "dead-model", "runs_requested": 1, "probe": True, "max_cost_usd": 1e-9,
           "price_in_per_m": 1.0, "price_out_per_m": 1.0, "spent_usd": reply["spend"]["cost_usd"],
           "stopped_by_budget": True, "git": "test", "date_utc": "2026-10-12T00:00:00+00:00",
           "replies": [{"rep": 1, "business": "acme",
                        "scenario_ids": [s["id"] for s in live_eval.SPECS["acme"]["scenarios"][:2]],
                        "reply": reply}]}
    summary = live_eval.summarize(raw)
    assert summary["calls_failed"] == summary["calls_total"] > 0
    report = live_eval.render(raw, summary)
    assert "**LIVE model results.**" in report and "YES — later runs missing" in report
    assert "| intent_detect |" in report, "failed calls missing from the report"


def test_mock_driver_reply_summarizes_with_no_model_calls():
    reply = run_agent(ACME, {"conversations": [live_eval.SPECS["acme"]["scenarios"][0]["turns"]]})
    assert reply["llm_mode"].startswith("MOCK") and reply["spend"]["cost_usd"] == 0
    raw = {"model": "mock", "runs_requested": 1, "probe": True, "max_cost_usd": 0.5,
           "price_in_per_m": 0, "price_out_per_m": 0, "spent_usd": 0.0, "stopped_by_budget": False,
           "git": "test", "date_utc": "x",
           "replies": [{"rep": 1, "business": "acme",
                        "scenario_ids": [live_eval.SPECS["acme"]["scenarios"][0]["id"]], "reply": reply}]}
    summary = live_eval.summarize(raw)
    (s,) = summary["scenarios"].values()
    assert (s["runs"], s["passed"], summary["calls_total"]) == (1, 1, 0)


def test_parse_fallback_table_counts_only_json_mode_successes():
    """Bug: the probe report listed calls whose JSON-mode retry ALSO failed under
    'failed the native parse path and succeeded in JSON mode'."""
    turn = {"message": "hi", "trace": [{"node": "think", "model_calls": [
        _call(path="json_mode", parse_error="BadRequestError"),
        _call(path="json_mode", ok=False, error="BadRequestError", parse_error="BadRequestError",
              error_message="Unsupported parameter: 'x'")]}],
        "tool_calls": [], "pending_confirmation": {}, "interrupted": False,
        "handoff_requested": False, "session_facts": {}}
    sid = live_eval.SPECS["acme"]["scenarios"][0]["id"]
    raw = {"replies": [{"rep": 1, "business": "acme", "scenario_ids": [sid],
                        "reply": {"llm_mode": "LIVE", "config_sha256": "x", "conversations": [[turn]]}}]}
    summary = live_eval.summarize(raw)
    assert summary["parse_fallbacks"] == {("think", "BadRequestError"): 1}
    assert summary["error_messages"] == {("think", "BadRequestError"): {"Unsupported parameter: 'x'"}}
