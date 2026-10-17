"""Proof-gate figures from a recorded scenario run (Story 1.9, PRD §7.5).

``python -m studio scenarios --record DIR`` leaves one SQLite episode store per
(business, scenario, run) and a ``results.jsonl`` line per run. Everything the
gate reports — model calls per turn, per-call and per-turn latency, resolution
refusals, spend — is computed here from those files alone, never from stdout,
so every figure written into PROOF-GATE.md can be reproduced with
``python -m studio gate-report DIR``.

"No model calls" is a distinct value, never 0 ms: a credential-free record has
no latency to report, and rendering it as zero would read as a perfect result.
"""

from __future__ import annotations

import json
import math
import os
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from studio.core import EpisodeStore

RESULTS = "results.jsonl"
STATUS = "status.json"

# Legacy figures (PROOF-GATE.md axes 3-4, from sprint CURRENT-STATE §3b).
LEGACY_CALLS_PER_TURN = 1.5
LEGACY_CALL_P50_MS = 1700.0
LEGACY_CALL_P95_MS = 3700.0

# Denial reasons the Core gives when it refuses a claimed resolution or an
# action claim (studio/core/harness.py `_check_resolution`, `_check_claims`).
REFUSAL_REASONS = ("undeclared_goal", "resolution_invalid", "action_without_evidence")


class RecordError(ValueError):
    """The record directory cannot be reported on."""


# --- writing (used by the scenarios command) ---------------------------------------------

def prepare_record_dir(directory: Path) -> None:
    """Create the directory; refuse anything already there, so a crashed run's
    leftover stores are never reopened and two runs never mix in one report."""
    if directory.exists() and not directory.is_dir():
        raise RecordError(f"{directory} exists and is not a directory")
    if directory.is_dir() and any(directory.iterdir()):
        raise RecordError(f"{directory} is not empty; choose an empty or new directory")
    directory.mkdir(parents=True, exist_ok=True)


def store_name(business: str, scenario: str, run: int) -> str:
    return f"{business}__{scenario}__run{run}.db"


def write_status(directory: Path, status: dict[str, Any]) -> None:
    """How the recorded invocation ended: planned and completed runs, outcome
    (complete | stopped_at_cap | error) and what ran. Temp file + replace."""
    tmp = directory / (STATUS + ".tmp")
    tmp.write_text(json.dumps(status, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")
    os.replace(tmp, directory / STATUS)


def append_result(directory: Path, line: dict[str, Any]) -> None:
    with (directory / RESULTS).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(line, ensure_ascii=False, sort_keys=True) + "\n")


def spend(calls: list[dict], price_in: Optional[float], price_out: Optional[float]) -> Optional[float]:
    """Estimated dollars for these model calls; None when no input price is set."""
    if price_in is None:
        return None
    return sum((c["input_tokens"] or 0) * price_in / 1e6 + (c["output_tokens"] or 0) * (price_out or 0) / 1e6
               for c in calls)


def store_model_calls(store: EpisodeStore, tenant: str) -> list[dict]:
    return [call for episode in store.episodes(tenant)
            for call in store.model_calls(tenant, episode.episode_id)]


# --- maths ---------------------------------------------------------------------------------

def percentile(values: list[float], q: float) -> Optional[float]:
    """Linear-interpolation percentile (the common 'type 7'); None for no data."""
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * q / 100.0
    low, high = math.floor(position), math.ceil(position)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


# --- reading -------------------------------------------------------------------------------

@dataclass
class Refusal:
    business: str
    scenario: str
    run: int
    episode_id: str
    reason: str
    detail: str
    source: str  # "resolution", "claim" (claims check) or "request" (goal check on any request)
    resolution: Optional[dict]


@dataclass
class RunFigures:
    business: str
    scenario: str
    run: int
    passed: bool
    failures: list[str]
    episode_ids: list[str]
    turns: int
    decisions: int
    calls: list[dict]
    turn_latency_ms: list[float]
    refusals: list[Refusal]
    spend: Optional[float]
    denials: list[str] = field(default_factory=list)  # every denial, as classification:reason
    closes: list[str] = field(default_factory=list)   # per episode: closed:<reason> or its open lifecycle
    halts: list[str] = field(default_factory=list)    # cause of every declared halt


@dataclass
class Report:
    directory: Path
    runs: list[RunFigures] = field(default_factory=list)
    status: Optional[dict] = None
    """status.json as written by the scenarios command; None when it is missing."""

    @property
    def complete(self) -> bool:
        return bool(self.status) and self.status.get("outcome") == "complete"

    @property
    def calls(self) -> list[dict]:
        return [c for r in self.runs for c in r.calls]

    @property
    def turns(self) -> int:
        return sum(r.turns for r in self.runs)

    @property
    def decisions(self) -> int:
        return sum(r.decisions for r in self.runs)

    @property
    def refusals(self) -> list[Refusal]:
        return [x for r in self.runs for x in r.refusals]

    def per_scenario(self) -> dict[tuple[str, str], list[RunFigures]]:
        out: dict[tuple[str, str], list[RunFigures]] = {}
        for r in self.runs:
            out.setdefault((r.business, r.scenario), []).append(r)
        return out

    def call_latency(self) -> tuple[Optional[float], Optional[float], int]:
        """(p50, p95, sample size) over every model call."""
        values = [c["latency_ms"] for c in self.calls]
        return percentile(values, 50), percentile(values, 95), len(values)

    def turn_latency(self) -> tuple[Optional[float], Optional[float], int]:
        """(p50, p95, sample size) of per-turn wall time; none without model calls."""
        if not self.calls:  # Core-only wall time is not the gate's latency
            return None, None, 0
        values = [ms for r in self.runs for ms in r.turn_latency_ms]
        return percentile(values, 50), percentile(values, 95), len(values)

    def spend(self) -> Optional[float]:
        priced = [r.spend for r in self.runs if r.spend is not None]
        if not self.calls:
            return 0.0
        return sum(priced) if len(priced) == len(self.runs) else None


def _refusal_source(request: dict, reason: str, detail: str) -> str:
    """'resolution' only when the refused decision is a respond request carrying
    a resolution and the denial is the resolution check's own (harness.py
    `_check_resolution`). The Core gives undeclared_goal and
    action_without_evidence from other checks too, so those are told apart by the
    resolution check's wording — pinned by a test that drives the real Core."""
    if request.get("kind") == "respond" and request.get("resolution") is not None:
        if reason == "resolution_invalid":
            return "resolution"
        if reason == "undeclared_goal" and detail.endswith("is not a declared goal"):
            return "resolution"
        if reason == "action_without_evidence" and detail.startswith("the resolution rests on"):
            return "resolution"
    return "claim" if reason == "action_without_evidence" else "request"


def _refusals(store: EpisodeStore, tenant: str, line: dict) -> list[Refusal]:
    out = []
    for episode in store.episodes(tenant):
        steps = {s["seq"]: s for s in store.steps(tenant, episode.episode_id)}
        for denial in store.denials(tenant, episode.episode_id):
            if denial["reason"] not in REFUSAL_REASONS:
                continue
            decision = steps.get(denial["step_seq"], {}).get("payload") or {}
            request = decision.get("request") or {}
            out.append(Refusal(business=line["business"], scenario=line["scenario"], run=line["run"],
                               episode_id=episode.episode_id, reason=denial["reason"], detail=denial["detail"],
                               source=_refusal_source(request, denial["reason"], denial["detail"]),
                               resolution=request.get("resolution")))
    return out


def _load_status(directory: Path) -> Optional[dict]:
    path = directory / STATUS
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"outcome": "unreadable", "message": f"{STATUS} is not valid JSON: {exc}"}


def _run_figures(store: EpisodeStore, line: dict) -> RunFigures:
    tenant = line["tenant"]
    episodes = store.episodes(tenant)
    steps = [s for e in episodes for s in store.steps(tenant, e.episode_id)]
    calls = store_model_calls(store, tenant)
    denials = [d for e in episodes for d in store.denials(tenant, e.episode_id)]
    return RunFigures(
        business=line["business"], scenario=line["scenario"], run=line["run"], passed=line["passed"],
        failures=line["failures"], episode_ids=[e.episode_id for e in episodes],
        turns=sum(1 for s in steps if s["actor"] == "requester" and s["kind"] == "inbound"),
        decisions=sum(1 for s in steps if s["actor"] == "agent" and s["kind"] == "decision"),
        calls=calls, turn_latency_ms=line["turn_latency_ms"], refusals=_refusals(store, tenant, line),
        spend=spend(calls, line.get("price_in_per_mtok"), line.get("price_out_per_mtok")),
        denials=[f"{d['classification']}:{d['reason']}" for d in denials],
        closes=[f"closed:{e.close_reason}" if e.lifecycle == "closed" else e.lifecycle for e in episodes],
        halts=[s["payload"].get("cause", "?") for s in steps if s["kind"] == "halt"])


def load_report(directory: str | Path) -> Report:
    directory = Path(directory)
    results = directory / RESULTS
    if not directory.is_dir():
        raise RecordError(f"{directory} does not exist")
    if not results.exists():
        raise RecordError(f"{directory} holds no record ({RESULTS} is missing)")
    lines = []
    for number, text in enumerate(results.read_text(encoding="utf-8").splitlines(), start=1):
        if not text.strip():
            continue
        try:
            lines.append(json.loads(text))
        except json.JSONDecodeError as exc:
            raise RecordError(f"{RESULTS} line {number} is not valid JSON ({exc})") from None
    if not lines:
        raise RecordError(f"{results} is empty")
    report = Report(directory=directory, status=_load_status(directory))
    for number, line in enumerate(lines, start=1):
        try:
            path = directory / line["store"]
            if not path.exists():
                raise RecordError(f"{line['store']} is named in {RESULTS} but is missing")
            store = EpisodeStore(path)
            try:
                report.runs.append(_run_figures(store, line))
            finally:
                store.close()
        except (KeyError, TypeError) as exc:
            raise RecordError(f"{RESULTS} record {number} is incomplete or malformed ({type(exc).__name__}: {exc})") \
                from None
    return report


# --- rendering -----------------------------------------------------------------------------

def _ms(value: Optional[float]) -> str:
    return "no model calls" if value is None else f"{value / 1000:.2f} s"


def _status_line(report: Report) -> str:
    status = report.status
    if status is None:
        return f"Status: INCOMPLETE - {STATUS} is missing; the invocation may have been interrupted"
    done = f"{status.get('completed_runs', '?')}/{status.get('planned_runs', '?')} runs"
    what = (f"agent {status.get('agent', '?')}, model {status.get('model') or 'none'}, "
            f"today {status.get('today', '?')}")
    if report.complete:
        return f"Status: complete - {done}; {what}"
    message = f": {status['message']}" if status.get("message") else ""
    return f"Status: INCOMPLETE ({status.get('outcome', '?')}{message}) - {done}; {what}"


def render(report: Report) -> str:
    out = [f"Proof gate report - {report.directory}", _status_line(report)]
    passed = sum(r.passed for r in report.runs)
    out.append(f"Runs: {len(report.runs)}, passed {passed}")
    out.append("")
    out.append("Per scenario                                  pass       episodes")
    for (business, scenario), runs in report.per_scenario().items():
        ok = sum(r.passed for r in runs)
        episodes = len({e for r in runs for e in r.episode_ids})
        out.append(f"  {business + '/' + scenario:44s} {ok}/{len(runs)} {100 * ok / len(runs):5.1f}%  {episodes}")
    failing = [r for r in report.runs if not r.passed]
    if failing:
        out.append("")
        out.append("Failures")
        for r in failing:
            out.append(f"  {r.business}/{r.scenario} run {r.run} ({', '.join(r.episode_ids)})")
            out.extend(f"     {f}" for f in r.failures)
    calls = report.calls
    turns = report.turns
    out.append("")
    out.append("Axis 3 - model calls                 candidate                 legacy")
    per_turn = f"{len(calls) / turns:.2f} ({len(calls)} calls / {turns} turns)" if turns else "no turns"
    out.append(f"  calls per turn                     {per_turn:25s} {LEGACY_CALLS_PER_TURN}")
    decisions = f"{report.decisions / turns:.2f} ({report.decisions} / {turns})" if turns else "no turns"
    out.append(f"  agent decisions per turn           {decisions}")
    failed_calls = sum(1 for c in calls if not c["ok"])
    out.append(f"  failed model calls                 {failed_calls}")
    p50, p95, n_calls = report.call_latency()
    t50, t95, n_turns = report.turn_latency()

    def pair(lo, hi, n):
        return f"{_ms(lo)} / {_ms(hi)} (n={n})" if calls else "no model calls"

    out.append("")
    out.append("Axis 4 - latency                     candidate                      legacy")
    out.append(f"  per call p50 / p95                 {pair(p50, p95, n_calls):30s} "
               f"{_ms(LEGACY_CALL_P50_MS)} / {_ms(LEGACY_CALL_P95_MS)}")
    out.append(f"  per turn p50 / p95 (wall)          {pair(t50, t95, n_turns):30s} not measured")
    for title, counts in (
            ("Denials (all, classification:reason)", Counter(d for r in report.runs for d in r.denials)),
            ("Episode outcomes", Counter(c for r in report.runs for c in r.closes)),
            ("Halts by cause", Counter(h for r in report.runs for h in r.halts))):
        out.append("")
        out.append(title)
        out.extend(f"  {key:50s} {count}" for key, count in sorted(counts.items()))
        if not counts:
            out.append("  none")
    refusals = report.refusals
    out.append("")
    out.append(f"Resolution and action-claim refusals: {len(refusals)} "
               f"({sum(x.source == 'resolution' for x in refusals)} from the resolution check)")
    for x in refusals:
        out.append(f"  {x.business}/{x.scenario} run {x.run} {x.episode_id} [{x.source}] {x.reason}: {x.detail}")
        if x.resolution:
            out.append(f"     resolution: {json.dumps(x.resolution, sort_keys=True)}")
    out.append("")
    total = report.spend()
    if not calls:
        out.append("Spend: $0.0000 (no model calls)")
    elif total is None:
        tokens_in = sum(c["input_tokens"] or 0 for c in calls)
        tokens_out = sum(c["output_tokens"] or 0 for c in calls)
        out.append(f"Spend: not priced ({tokens_in} input, {tokens_out} output tokens)")
    else:
        out.append(f"Spend: ${total:.4f} (estimated from recorded tokens and prices)")
    return "\n".join(out)
