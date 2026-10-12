# -*- coding: utf-8 -*-
"""C7 live-model mode: run every cross-business scenario N times against a real
model and write a Markdown report of the results as rates.

Spends tokens. Never run by pytest (the file name does not start with test_).
The checker is the deterministic suite's own (test_cross_business_eval.check_turn).
By default the scenarios are too (eval_scenarios/, whose expectations were
written against the keyword-based mock); --scenarios points at another set,
such as live_scenarios/ (paraphrases with expectations fixed before any run).
Either way this script reports how a model does against them; it never adjusts
them.

    set OPENAI_API_KEY in the shell (never in a file), then:
    python builder_platform/tests/live_eval.py --model <id> \
        --price-in <usd per 1M input> --price-out <usd per 1M output> \
        [--runs 3] [--max-cost 0.50] [--probe]         [--token-param max_completion_tokens] [--reasoning-effort none]         [--scenarios builder_platform/tests/live_scenarios]

--model pins all three tiers (AGENT_INTENT/ANSWER/ENRICH_MODEL), so every
business runs on the same model. --probe runs only each business's first
scenario, once: a cheap check that the endpoint accepts the engine's requests.
--max-cost is the ceiling for the whole run, enforced turn by turn from the
usage the provider reports (pessimistic estimates where it reports none).
--token-param sets OPENAI_TOKEN_PARAM for the run (the output-cap field name the
endpoint accepts) and --reasoning-effort sets OPENAI_REASONING_EFFORT; both are
recorded in the report, and omitted flags leave the engine defaults.
--scenarios picks the scenario folder (default: the deterministic suite's
eval_scenarios/). live_scenarios/ holds paraphrases that only a model can
classify; pytest never reads it.
Writes <out>/<UTC stamp>-<model>.md and a .json with every raw driver reply.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from agent_driver import run_agent  # noqa: E402
from test_cross_business_eval import REPO, SCENARIO_DIR, SPECS, _observe, check_turn  # noqa: E402


def load_specs(directory: Path) -> dict:
    """{business: spec} from a folder of scenario files (same format as eval_scenarios/)."""
    return {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted(Path(directory).glob("*.json"))}

TIERS = ("AGENT_INTENT_MODEL", "AGENT_ANSWER_MODEL", "AGENT_ENRICH_MODEL", "OPENAI_MODEL")


def _git() -> str:
    try:
        rev = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO, capture_output=True,
                             text=True, timeout=5, check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=REPO, capture_output=True,
                               text=True, timeout=5, check=True).stdout.strip()
        return f"{rev}{' (uncommitted changes)' if dirty else ''}"
    except (OSError, subprocess.SubprocessError) as e:
        return f"unknown ({type(e).__name__})"


def run_live(model: str, runs: int, max_cost: float, price_in: float, price_out: float,
             probe: bool, token_param: str = "", reasoning_effort: str = "",
             specs: dict | None = None, scenario_set: str = "eval_scenarios") -> dict:
    """Every business × scenario, `runs` times, rep by rep so a budget stop
    leaves whole earlier repetitions. Returns the raw record the report reads."""
    specs = specs or SPECS
    for tier in TIERS:
        os.environ[tier] = model
    if token_param:
        os.environ["OPENAI_TOKEN_PARAM"] = token_param
    if reasoning_effort:
        os.environ["OPENAI_REASONING_EFFORT"] = reasoning_effort
    spent, replies, stopped = 0.0, [], False
    for rep in range(1, (1 if probe else runs) + 1):
        for biz, spec in specs.items():
            scenarios = spec["scenarios"][:1] if probe else spec["scenarios"]
            remaining = max_cost - spent
            if remaining <= 0:
                stopped = True
                break
            reply = run_agent(REPO / spec["agent_dir"],
                              {"conversations": [sc["turns"] for sc in scenarios],
                               "budget": {"max_cost_usd": remaining,
                                          "price_in_per_m": price_in, "price_out_per_m": price_out}},
                              timeout=1800, live=True)
            spent += reply["spend"]["cost_usd"]
            stopped = stopped or reply["spend"]["stopped"]
            print(f"[{datetime.now():%H:%M:%S}] rep {rep} {biz}: {len(scenarios)} scenarios done, "
                  f"estimated spend so far ${spent:.4f} of ${max_cost:.2f}", file=sys.stderr, flush=True)
            replies.append({"rep": rep, "business": biz,
                            "scenario_ids": [sc["id"] for sc in scenarios], "reply": reply})
        if stopped:
            break
    return {"model": model, "scenario_set": scenario_set, "runs_requested": 1 if probe else runs, "probe": probe,
            "token_param": os.environ.get("OPENAI_TOKEN_PARAM") or "max_tokens (engine default)",
            "reasoning_effort": os.environ.get("OPENAI_REASONING_EFFORT") or "not sent (model default)",
            "max_cost_usd": max_cost, "price_in_per_m": price_in, "price_out_per_m": price_out,
            "spent_usd": spent, "stopped_by_budget": stopped, "replies": replies,
            "git": _git(), "date_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}


def _pct(values: list, q: float):
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    return statistics.quantiles(values, n=100, method="inclusive")[int(q) - 1]


def summarize(raw: dict, specs: dict | None = None) -> dict:
    """Rates per scenario and per expectation, degraded calls, usage, latency."""
    specs = specs or SPECS
    scen = defaultdict(lambda: {"runs": 0, "passed": 0, "incomplete": 0,
                                "keys": defaultdict(lambda: {"pass": 0, "total": 0, "seen": Counter()})})
    degraded, parse_fallbacks, latencies = Counter(), Counter(), []
    error_messages = defaultdict(set)
    calls_total = calls_failed = 0
    modes, fingerprints = set(), {}
    for item in raw["replies"]:
        biz, reply = item["business"], item["reply"]
        modes.add(reply["llm_mode"])
        fingerprints[biz] = reply["config_sha256"]
        spec = {sc["id"]: sc for sc in specs[biz]["scenarios"]}
        for sid, turns in zip(item["scenario_ids"], reply["conversations"]):
            sc, s = spec[sid], scen[(biz, sid)]
            # Model calls count from EVERY turn that ran, including a
            # conversation the budget cut short: a failed call must never
            # drop out of the report because its scenario did not finish.
            for turn in turns:
                for entry in turn["trace"]:
                    for c in entry.get("model_calls") or ():
                        calls_total += 1
                        if c["ok"]:
                            latencies.append(c["latency_ms"])
                        else:
                            calls_failed += 1
                            degraded[(entry["node"], c["error"])] += 1
                            for msg in (c.get("error_message"), c.get("parse_error_message")):
                                if msg:
                                    error_messages[(entry["node"], c["error"])].add(msg)
                        if c.get("parse_error") and c["ok"]:
                            parse_fallbacks[(entry["node"], c["parse_error"])] += 1
            if len(turns) < len(sc["expect"]):
                s["incomplete"] += 1          # cut by the budget: no pass rate from it
                continue
            s["runs"] += 1
            ok_all = True
            for expect, turn in zip(sc["expect"], turns):
                seen = _observe(turn)
                ok_all = ok_all and not check_turn(expect, turn)
                for key, want in expect.items():
                    k = s["keys"][key]
                    k["total"] += 1
                    if not check_turn({key: want}, turn):
                        k["pass"] += 1
                    else:
                        k["seen"][repr(sorted(seen["facts"]) if key.startswith("facts") else seen[key])] += 1
            s["passed"] += ok_all
    return {"scenarios": scen, "degraded": degraded, "parse_fallbacks": parse_fallbacks,
            "error_messages": dict(error_messages),
            "calls_total": calls_total, "calls_failed": calls_failed,
            "latency_p50": _pct(latencies, 50), "latency_p95": _pct(latencies, 95),
            "modes": sorted(modes), "fingerprints": fingerprints}


def render(raw: dict, summary: dict, specs: dict | None = None) -> str:
    specs = specs or SPECS
    spend = [r["reply"]["spend"] for r in raw["replies"]]
    tin, tout = sum(s["input_tokens"] for s in spend), sum(s["output_tokens"] for s in spend)
    est = sum(s["estimated_calls"] for s in spend)
    scenario_set = raw.get("scenario_set", "eval_scenarios")
    origin = ("the expectations were written against the keyword-based mock and are reported unchanged"
              if scenario_set == "eval_scenarios" else
              f"the expectations are the pre-registered ones in `{scenario_set}/`, fixed before the run "
              "and reported unchanged")
    lines = [
        f"# C7 live evaluation — {raw['model']}{' (probe)' if raw['probe'] else ''}",
        "",
        f"**LIVE model results.** Not mock results, and not comparable to them one for one: {origin}.",
        "",
        "| | |", "| --- | --- |",
        f"| Date (UTC) | {raw['date_utc']} |",
        f"| Model (all three tiers) | `{raw['model']}` |",
        f"| Scenario set | `{raw.get('scenario_set', 'eval_scenarios')}` |",
        f"| Endpoint | {', '.join(summary['modes']) or 'none reached'} |",
        f"| Output-cap field | `{raw.get('token_param', 'unknown')}` |",
        f"| Reasoning effort | `{raw.get('reasoning_effort', 'unknown')}` |",
        f"| Repository | {raw['git']} |",
        f"| Runs per scenario | {raw['runs_requested']} requested |",
        f"| Spend | ${raw['spent_usd']:.4f} of ${raw['max_cost_usd']:.2f} ceiling "
        f"({tin} input / {tout} output tokens at ${raw['price_in_per_m']}/${raw['price_out_per_m']} per 1M; "
        f"{est} call(s) estimated, not reported) |",
        f"| Stopped by budget | {'YES — later runs missing' if raw['stopped_by_budget'] else 'no'} |",
        f"| Model calls | {summary['calls_total']} total, {summary['calls_failed']} failed "
        f"(node fell back to its heuristic) |",
        f"| Call latency p50 / p95 | {summary['latency_p50']} / {summary['latency_p95']} ms (successful calls) |",
        "",
        "Configuration fingerprints: " + ", ".join(f"{b} `{h[:12]}`" for b, h in sorted(summary["fingerprints"].items())),
        "",
        "## Scenario pass rates",
        "",
        "A scenario passes a run only if every expectation on every turn holds.",
        "",
        "| Business | Scenario | Behaviour | Passed | Cut by budget |",
        "| --- | --- | --- | --- | --- |",
    ]
    for (biz, sid), s in sorted(summary["scenarios"].items()):
        behaviour = next(sc["behaviour"] for sc in specs[biz]["scenarios"] if sc["id"] == sid)
        lines.append(f"| {biz} | {sid} | {behaviour} | {s['passed']}/{s['runs']} | {s['incomplete']} |")
    lines += ["", "## Expectations that did not always hold", "",
              "| Business | Scenario | Expectation | Held | Observed instead (count) |",
              "| --- | --- | --- | --- | --- |"]
    misses = 0
    for (biz, sid), s in sorted(summary["scenarios"].items()):
        for key, k in sorted(s["keys"].items()):
            if k["pass"] < k["total"]:
                misses += 1
                seen = ", ".join(f"{v} ×{n}" for v, n in k["seen"].most_common())
                lines.append(f"| {biz} | {sid} | {key} | {k['pass']}/{k['total']} | {seen} |")
    if not misses:
        lines.append("| — | — | — | — | every expectation held in every completed run |")
    lines += ["", "## Failed model calls", ""]
    if summary["degraded"]:
        lines += ["| Node | Error | Count |", "| --- | --- | --- |"]
        lines += [f"| {n} | {e} | {c} |" for (n, e), c in summary["degraded"].most_common()]
        lines += ["", "Provider error messages (truncated):", ""]
        for (n, e), msgs in sorted(summary["error_messages"].items()):
            lines += [f"- {n} / {e}: `{m}`" for m in sorted(msgs)]
    else:
        lines.append("None.")
    if summary["parse_fallbacks"]:
        lines += ["", "Structured calls that failed the native parse path and succeeded in JSON mode:", "",
                  "| Node | Parse error | Count |", "| --- | --- | --- |"]
        lines += [f"| {n} | {e} | {c} |" for (n, e), c in summary["parse_fallbacks"].most_common()]
    lines += ["", "## Reading this report", "",
              "- A failed model call means the node answered from the same keyword heuristic mock mode "
              "uses; a scenario that passed with failed calls is not evidence about the model.",
              "- Three runs per scenario show behaviour, not statistical reliability.",
              "- The raw driver output (traces, replies, per-call records) is in the .json file next to this report.",
              ""]
    return "\n".join(lines)


def _atomic_write(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--model", required=True)
    p.add_argument("--price-in", type=float, required=True, help="USD per 1M input tokens")
    p.add_argument("--price-out", type=float, required=True, help="USD per 1M output tokens")
    p.add_argument("--runs", type=int, default=3)
    p.add_argument("--max-cost", type=float, default=0.50)
    p.add_argument("--probe", action="store_true")
    p.add_argument("--scenarios", type=Path, default=SCENARIO_DIR)
    p.add_argument("--token-param", default="", choices=("", "max_tokens", "max_completion_tokens"))
    p.add_argument("--reasoning-effort", default="", help="e.g. none, low, medium (provider-defined)")
    p.add_argument("--out", type=Path, default=Path(__file__).resolve().parent / "live_reports")
    a = p.parse_args(argv)
    if not os.environ.get("OPENAI_API_KEY", "").strip():
        print("OPENAI_API_KEY is not set in this shell; refusing to start.", file=sys.stderr)
        return 2
    specs = load_specs(a.scenarios)
    raw = run_live(a.model, a.runs, a.max_cost, a.price_in, a.price_out, a.probe, a.token_param,
                   a.reasoning_effort, specs, a.scenarios.name)
    a.out.mkdir(parents=True, exist_ok=True)
    custom = "" if a.scenarios.resolve() == SCENARIO_DIR.resolve() else f"-{a.scenarios.name}"
    stem = f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{a.model.replace('/', '_')}{custom}{'-probe' if a.probe else ''}"
    _atomic_write(a.out / f"{stem}.json", json.dumps(raw, ensure_ascii=False, indent=1, default=str))
    _atomic_write(a.out / f"{stem}.md", render(raw, summarize(raw, specs), specs))
    print(f"spent ${raw['spent_usd']:.4f}; report: {a.out / (stem + '.md')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
