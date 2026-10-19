"""Story 1.9: the scenario runner can produce proof-gate evidence.

Runs are independent (a fresh store, Core and calendar each), the spend cap is
cumulative over the whole invocation, and every figure of the gate report is
computed from the recorded store files — credential-free throughout."""

import argparse
import asyncio
import json
from pathlib import Path

import pytest

from studio import proof_gate
from studio.__main__ import _scenarios, main
from studio.agent.deterministic import DeterministicAgent
from studio.config import ModelSettings, Settings
from studio.core.ports import ModelCall

TODAY = "2026-10-13"


def _args(**kw):
    base = dict(business=[], live=False, runs=1, max_cost=None, today=TODAY, record=None)
    base.update(kw)
    return argparse.Namespace(**base)


def _lines(directory: Path) -> list[dict]:
    return [json.loads(t) for t in (directory / proof_gate.RESULTS).read_text(encoding="utf-8").splitlines()]


def test_runs_are_independent_and_recorded(tmp_path, capsys):
    record = tmp_path / "rec"
    code = main(["scenarios", "dental", "--runs", "3", "--record", str(record), "--today", TODAY])
    out = capsys.readouterr().out
    assert code == 0, out
    lines = _lines(record)
    by_scenario: dict[str, list[dict]] = {}
    for line in lines:
        by_scenario.setdefault(line["scenario"], []).append(line)
    assert len(by_scenario) == 6 and all(len(v) == 3 for v in by_scenario.values())
    for scenario, runs in by_scenario.items():
        assert len({r["episode_id"] for r in runs}) == 3, scenario  # no replay of run 1
        assert all(r["passed"] for r in runs), runs
        for r in runs:
            assert (record / r["store"]).exists()
            assert len(r["turn_latency_ms"]) >= 1 and all(ms > 0 for ms in r["turn_latency_ms"])

    report = proof_gate.load_report(record)
    for run in report.runs:  # every run has its own steps and replies (the replay sent none on runs 2-3)
        assert run.turns >= 1  # D2 halts at a guard before any agent decision, so decisions may be 0
        from studio.core import EpisodeStore
        store = EpisodeStore(record / proof_gate.store_name(run.business, run.scenario, run.run))
        try:
            tenant = next(line["tenant"] for line in lines)
            replies = [o for e in run.episode_ids for o in store.outbox(tenant, e)]
        finally:
            store.close()
        assert replies, (run.scenario, run.run)


def test_record_and_report_round_trip_without_model_calls(tmp_path, capsys):
    record = tmp_path / "rec"
    assert main(["scenarios", "--record", str(record), "--today", TODAY]) == 0
    capsys.readouterr()
    assert main(["gate-report", str(record)]) == 0
    text = capsys.readouterr().out
    assert "Runs: 10, passed 10" in text
    assert "0.00 (0 calls / 13 turns)" in text
    # 1.38 (18 / 13) at the 2026-10-13 gate; since Story 2.5 (T12) the deterministic agent reads availability
    # before every booking proposal, so the credential-free decision count is higher by design.
    assert "1.85 (24 / 13)" in text
    latency = [line for line in text.splitlines() if "p50 / p95" in line]
    assert len(latency) == 2 and all("no model calls" in line for line in latency)
    assert not any(" 0 ms" in line or "0.00 s" in line.split("legacy")[0] for line in latency)
    report = proof_gate.load_report(record)
    assert report.call_latency() == (None, None, 0) and report.turn_latency() == (None, None, 0)
    assert text.splitlines()[1].startswith("Status: complete - 10/10 runs; agent ")
    # every denial and halt is counted, not only refusals
    assert "Halts by cause" in text and "guard" in text.split("Halts by cause")[1]
    assert "business_refusal:" in text.split("Denials (all")[1]
    assert "closed:halted" in text and "closed:resolved" in text


def test_a_used_record_directory_is_refused(tmp_path, capsys):
    record = tmp_path / "rec"
    assert main(["scenarios", "dental", "--record", str(record), "--today", TODAY]) == 0
    assert main(["scenarios", "dental", "--record", str(record), "--today", TODAY]) == 2
    assert "is not empty" in capsys.readouterr().err


def test_leftovers_and_non_directories_are_refused(tmp_path, capsys):
    crashed = tmp_path / "crashed"
    crashed.mkdir()
    (crashed / "dental__D1-book-a-checkup__run1.db").write_bytes(b"")  # no results.jsonl
    assert main(["scenarios", "dental", "--record", str(crashed), "--today", TODAY]) == 2
    assert "is not empty" in capsys.readouterr().err
    a_file = tmp_path / "a_file"
    a_file.write_text("x", encoding="utf-8")
    assert main(["scenarios", "dental", "--record", str(a_file), "--today", TODAY]) == 2
    assert "is not a directory" in capsys.readouterr().err


def test_runs_below_one_are_refused(capsys):
    assert main(["scenarios", "dental", "--runs", "0", "--today", TODAY]) == 2
    assert "--runs must be at least 1" in capsys.readouterr().err


def test_live_without_an_input_price_is_refused_at_startup(monkeypatch, capsys):
    monkeypatch.setenv("OPENAI_API_KEY", "not-a-real-key")
    monkeypatch.setenv("STUDIO_AGENT_MODEL", "stub")
    monkeypatch.delenv("STUDIO_PRICE_IN", raising=False)
    assert main(["scenarios", "dental", "--live", "--max-cost", "0.25", "--today", TODAY]) == 2
    err = capsys.readouterr().err
    assert "STUDIO_PRICE_IN" in err and "not-a-real-key" not in err


@pytest.mark.parametrize("content,expect", [
    ('{"business": "b", "tenant": "t"\n', "not valid JSON"),
    ('{"business": "b"}\n', "incomplete or malformed"),
])
def test_a_malformed_results_line_fails_loudly(tmp_path, capsys, content, expect):
    record = tmp_path / "rec"
    record.mkdir()
    (record / proof_gate.RESULTS).write_text(content, encoding="utf-8")
    assert main(["gate-report", str(record)]) == 1
    assert expect in capsys.readouterr().err


def test_a_missing_status_is_reported_as_incomplete(tmp_path, capsys):
    record = tmp_path / "rec"
    assert main(["scenarios", "dental", "--record", str(record), "--today", TODAY]) == 0
    (record / proof_gate.STATUS).unlink()
    capsys.readouterr()
    assert main(["gate-report", str(record)]) == 0
    assert "Status: INCOMPLETE" in capsys.readouterr().out


def test_a_run_that_raises_leaves_an_error_status(tmp_path, capsys, monkeypatch):
    import studio.__main__ as cli
    real = cli.run_scenario
    calls = {"n": 0}

    async def flaky(*a, **kw):
        calls["n"] += 1
        if calls["n"] == 2:
            raise RuntimeError("adapter exploded")
        return await real(*a, **kw)

    monkeypatch.setattr(cli, "run_scenario", flaky)
    record = tmp_path / "rec"
    args = _args(business=["dental"], live=True, runs=1, max_cost=100.0, record=str(record))
    with pytest.raises(RuntimeError):
        asyncio.run(_scenarios(args, _priced_settings(), agent_factory=lambda *a: (PricedAgent(), None)))
    out = capsys.readouterr().out
    assert "Estimated spend: $" in out  # spend already incurred is still printed
    status = json.loads((record / proof_gate.STATUS).read_text(encoding="utf-8"))
    assert status["outcome"] == "error" and "adapter exploded" in status["message"]
    assert status["completed_runs"] == 1 and status["planned_runs"] == 6
    assert status["model"] == "stub" and status["today"] == TODAY
    text = proof_gate.render(proof_gate.load_report(record))
    assert "Status: INCOMPLETE (error: RuntimeError: adapter exploded) - 1/6 runs" in text


@pytest.mark.parametrize("make", ["missing", "empty_dir", "empty_file"])
def test_gate_report_on_nothing_fails_loudly(tmp_path, capsys, make):
    target = tmp_path / "rec"
    if make != "missing":
        target.mkdir()
    if make == "empty_file":
        (target / proof_gate.RESULTS).write_text("", encoding="utf-8")
    assert main(["gate-report", str(target)]) == 1
    assert "gate-report:" in capsys.readouterr().err


class PricedAgent:
    """The credential-free agent, with each decision charged as one model call."""

    name = "priced-stub"

    def __init__(self):
        self.inner = DeterministicAgent(today=lambda: __import__("datetime").date.fromisoformat(TODAY))

    async def decide(self, view):
        decision = await self.inner.decide(view)
        call = ModelCall(model="stub", ok=True, path="stub", input_tokens=1_000_000, output_tokens=0,
                         latency_ms=250.0)
        return decision.model_copy(update={"model_calls": (call,)})


def _priced_settings() -> Settings:
    return Settings(data_dir=Path("unused"), model=ModelSettings(
        base_url="http://unused", api_key="unused", agent_model="stub",
        price_in_per_mtok=0.01, price_out_per_mtok=0.0))


def test_spend_cap_is_cumulative_across_runs(tmp_path, capsys):
    # Each decision costs $0.01; one D1 run is a handful of decisions, so no
    # single run reaches $0.10 and only the running total can stop the loop.
    record = tmp_path / "rec"
    args = _args(business=["dental"], live=True, runs=3, max_cost=0.10, record=str(record))
    code = asyncio.run(_scenarios(args, _priced_settings(), agent_factory=lambda *a: (PricedAgent(), None)))
    out = capsys.readouterr().out
    assert code == 2, out
    stop = [line for line in out.splitlines() if line.startswith("Stopping:")]
    assert len(stop) == 1 and stop[0].endswith("reached --max-cost $0.1")
    spent = float(stop[0].split("$")[1].split()[0])
    lines = _lines(record)
    report = proof_gate.load_report(record)
    assert spent == pytest.approx(report.spend())  # the printed spend is the whole run's, from the record
    per_run = [r.spend for r in report.runs]
    assert max(per_run) < 0.10 <= sum(per_run)
    assert sum(per_run[:-1]) < 0.10  # stopped at the first run that reached the cap
    assert len(lines) == len(report.runs) > 1
    status = json.loads((record / proof_gate.STATUS).read_text(encoding="utf-8"))
    assert status["outcome"] == "stopped_at_cap" and status["completed_runs"] == len(lines) < status["planned_runs"]
    assert "Status: INCOMPLETE (stopped_at_cap" in proof_gate.render(report)


def test_report_figures_with_model_calls(tmp_path, capsys):
    record = tmp_path / "rec"
    args = _args(business=["dental"], live=True, runs=1, max_cost=100.0, record=str(record))
    assert asyncio.run(_scenarios(args, _priced_settings(),
                                  agent_factory=lambda *a: (PricedAgent(), None))) == 0
    capsys.readouterr()
    report = proof_gate.load_report(record)
    assert len(report.calls) == report.decisions > 0
    assert report.call_latency() == (250.0, 250.0, len(report.calls))
    t50, t95, n_turns = report.turn_latency()
    assert t50 is not None and t95 >= t50 and n_turns == report.turns
    text = proof_gate.render(report)
    assert f"0.25 s / 0.25 s (n={len(report.calls)})" in text
    assert f"(n={report.turns})" in text
    assert f"Spend: ${report.spend():.4f}" in text
    assert "Status: complete - 6/6 runs; agent priced-stub, model stub" in text


def test_spend_without_prices_is_not_priced_rather_than_zero(tmp_path, capsys):
    record = tmp_path / "rec"
    unpriced = Settings(data_dir=Path("unused"), model=ModelSettings(
        base_url="http://unused", api_key="unused", agent_model="stub"))
    args = _args(business=["dental"], live=True, runs=1, max_cost=None, record=str(record))
    assert asyncio.run(_scenarios(args, unpriced, agent_factory=lambda *a: (PricedAgent(), None))) == 0
    capsys.readouterr()
    report = proof_gate.load_report(record)
    assert report.spend() is None
    spend_line = next(line for line in proof_gate.render(report).splitlines() if line.startswith("Spend:"))
    assert spend_line == f"Spend: not priced ({1_000_000 * len(report.calls)} input, 0 output tokens)"
    assert "$" not in spend_line


def test_percentile_on_fixed_data():
    data = [5.0, 1.0, 4.0, 2.0, 3.0]
    assert proof_gate.percentile(data, 50) == 3.0
    assert proof_gate.percentile(data, 95) == pytest.approx(4.8)
    assert proof_gate.percentile(data, 0) == 1.0 and proof_gate.percentile(data, 100) == 5.0
    assert proof_gate.percentile([7.0], 95) == 7.0
    assert proof_gate.percentile([], 50) is None


def test_resolution_refusals_from_the_real_core_are_labelled(tmp_path, capsys):
    """Pins the report's coupling to the Core's wording: the real Core's
    resolution check produces resolution_invalid and action_without_evidence,
    and the goal check on a non-respond request produces undeclared_goal; only
    the first two are counted as resolution-check refusals."""
    from studio.core import EpisodeStore
    from studio.core.types import ClarifyRequest, ResolutionClaim, RespondRequest
    from studio.tests.helpers import BUSINESSES, build_world
    record = tmp_path / "rec"
    proof_gate.prepare_record_dir(record)
    tenant = "bright-smile-dental"
    with asyncio.Runner() as runner:
        world = build_world(runner, [BUSINESSES / "dental" / "specification.toml"],
                            store=EpisodeStore(record / "real.db"))
        world.send("info", script=[
            ClarifyRequest(goal="not_a_goal", message="Which?"),
            RespondRequest(message="Done.", resolution=ResolutionClaim(goal="book_visit", served=True,
                                                                       authority="agent")),
            RespondRequest(message="Not booked.", resolution=ResolutionClaim(
                goal="book_visit", served=False, authority="capability:book_visit")),
            RespondRequest(message="What name?")])
        world.store.close()
    proof_gate.append_result(record, {"business": "dental", "tenant": tenant, "scenario": "s", "run": 1,
                                      "passed": True, "failures": [], "turn_latency_ms": [1.0], "store": "real.db"})
    report = proof_gate.load_report(record)
    assert [(r.reason, r.source) for r in report.refusals] == [("undeclared_goal", "request"),
                                                               ("resolution_invalid", "resolution"),
                                                               ("action_without_evidence", "resolution")]
    assert "(2 from the resolution check)" in proof_gate.render(report)


def test_refusals_are_read_from_the_record(tmp_path):
    """A resolution refusal journaled by the Core is reported with its detail
    and the resolution the agent claimed."""
    from studio.core import EpisodeStore
    record = tmp_path / "rec"
    proof_gate.prepare_record_dir(record)
    store = EpisodeStore(record / "x.db")
    episode = store.create_episode("t1", "c1", "v1", "c1")
    eid = episode.episode_id
    store.append_step("t1", eid, "requester", "inbound", {"message_id": "m1", "text": "hi"})
    resolution = {"goal": "book", "served": True, "authority": "capability:book", "evidence": []}
    seq = store.append_step("t1", eid, "agent", "decision", {"request": {"kind": "respond", "resolution": resolution},
                                                             "error": None})
    store.add_denial("t1", eid, seq, "platform_error", "resolution_invalid", "goal 'book' cannot be served", "v1")
    store.add_denial("t1", eid, seq, "platform_error", "action_without_evidence",
                     "the reply says something was done, but there is no verified record that it was", "v1")
    store.close()
    proof_gate.append_result(record, {"business": "b", "tenant": "t1", "scenario": "s", "run": 1, "passed": False,
                                      "failures": ["x"], "turn_latency_ms": [1.0], "store": "x.db"})
    report = proof_gate.load_report(record)
    refusals = report.refusals
    assert [(r.reason, r.source) for r in refusals] == [("resolution_invalid", "resolution"),
                                                        ("action_without_evidence", "claim")]
    assert refusals[0].resolution == resolution
    assert "goal 'book' cannot be served" in proof_gate.render(report)
