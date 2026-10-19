"""Command line: ``python -m studio <command>``.

    validate <business>            run the validation suite on a business specification
    scenarios [<business> ...]     run scenario files end to end (credential-free by default)
    gate-report <dir>              proof-gate figures from a ``scenarios --record <dir>`` run
    chat <business>                talk to a business's Agent in the terminal (developer tool)

``<business>`` is a folder under ``studio/businesses`` or a path to a
``specification.toml``. Live model runs need ``--live`` *and* a configured
endpoint (see ``studio.config``); they stop once the estimated spend reaches
``--max-cost`` dollars. This entry point is thin: everything it does is
importable and tested elsewhere.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import date, datetime, timezone
from pathlib import Path

from studio import proof_gate
from studio.agent.deterministic import DeterministicAgent
from studio.channels.harness import HarnessChannel, load_scenarios, run_scenario
from studio.config import ConfigurationError, Settings
from studio.core import Core, CoreSettings, EpisodeStore, SpecRegistry
from studio.extensions.simulated import SimulatedCalendar
from studio.spec import SpecificationError, compile_specification, load_specification, validate

BUSINESSES = Path(__file__).resolve().parent / "businesses"
SIMULATED_TIMES = {"hopfield-brewery": ("12:00", "15:00", "18:00")}


def _spec_path(name: str) -> Path:
    path = Path(name)
    if path.suffix == ".toml":
        return path
    folder = path if path.is_dir() else BUSINESSES / name
    return folder / "specification.toml"


def _agent(settings: Settings, live: bool, today: date):
    if not live:
        return DeterministicAgent(today=lambda: today), None
    if not settings.live:
        raise ConfigurationError("--live needs OPENAI_API_KEY (or OPENAI_BASE_URL) and STUDIO_AGENT_MODEL")
    from studio.agent.llm_agent import LLMAgent
    from studio.agent.model_port import ModelPort
    port = ModelPort(settings.model)
    return LLMAgent(port), port


def _spend(core: Core, settings: Settings) -> float:
    """Estimated spend recorded in one Core's store (one run); the caller sums runs."""
    if not settings.live or settings.model.price_in_per_mtok is None:
        return 0.0
    calls = [c for tenant in core.registry.tenants() for c in proof_gate.store_model_calls(core.store, tenant)]
    return proof_gate.spend(calls, settings.model.price_in_per_mtok, settings.model.price_out_per_mtok) or 0.0


def cmd_validate(args) -> int:
    try:
        loaded = load_specification(_spec_path(args.business))
    except SpecificationError as exc:
        for f in exc.findings:
            print(f"BLOCKING {f.code}: {f.message}")
        return 1
    report = validate(loaded)
    for f in report.findings:
        print(f"{f.severity.upper():8s} {f.area or '':4s} {f.code}: {f.message}")
    print(f"{loaded.spec.business.name} - version {loaded.version} - "
          + ("passes the validation suite" if report.passed else "BLOCKED"))
    return 0 if report.passed else 1


async def _scenarios(args, settings: Settings, agent_factory=_agent) -> int:
    """Run every scenario ``args.runs`` times. Each run is independent: its own
    registry, store, Core and simulated calendar, so message ids that restart
    per run never collide with an earlier run's record. Spend is summed over
    every run so far and checked against ``--max-cost`` after each run."""
    names = args.business or sorted(p.parent.name for p in BUSINESSES.glob("*/scenarios.toml"))
    record = Path(args.record) if getattr(args, "record", None) else None
    plan = []
    for name in names:
        compiled = compile_specification(load_specification(_spec_path(name)))
        plan.append((name, _spec_path(name).parent.name, compiled,
                     load_scenarios(_spec_path(name).parent / "scenarios.toml")))
    if record is not None:
        proof_gate.prepare_record_dir(record)
    today = date.fromisoformat(args.today)
    agent, port = agent_factory(settings, args.live, today)

    def clock() -> datetime:  # the recorded clock reads --today, so the Agent's view carries it (AD-12)
        return datetime.combine(today, datetime.now(timezone.utc).timetz())

    prices = settings.model if settings.live else None
    failed = completed = 0
    spent = 0.0
    outcome, message = "error", "interrupted before the first run finished"
    try:
        for name, label, compiled, scenarios in plan:
            for scenario in scenarios:
                for run in range(1, args.runs + 1):
                    registry = SpecRegistry()
                    registry.register(compiled)
                    calendar = SimulatedCalendar(tenant_times=dict(SIMULATED_TIMES))
                    store_file = proof_gate.store_name(label, scenario["id"], run)
                    store = EpisodeStore(record / store_file if record is not None else ":memory:", clock=clock)
                    # One generic simulated system of record stands in for each business's own systems until
                    # one is connected: a calendar for bookings, a records system for claims.
                    core = Core(registry, store, agent, {"calendar": calendar, "records": calendar},
                                CoreSettings(context_assembly=settings.context_assembly))
                    try:
                        result = await run_scenario(core, compiled.tenant, scenario,
                                                    effects_counter=lambda: sum(calendar.executions.values()))
                        status = "PASS" if result.passed else "FAIL"
                        failed += not result.passed
                        calls = store.model_calls(compiled.tenant, result.episode_id) if result.episode_id else []
                        print(f"{status} {name}/{scenario['id']}  model calls: {len(calls)}")
                        for failure in result.failures:
                            print(f"     {failure}")
                        if record is not None:
                            proof_gate.append_result(record, {
                                "business": label, "tenant": compiled.tenant, "scenario": scenario["id"],
                                "run": run, "passed": result.passed, "failures": result.failures,
                                "episode_id": result.episode_id, "episode_ids": result.transcript.episode_ids,
                                "turn_latency_ms": result.turn_latency_ms, "store": store_file,
                                "agent": agent.name,
                                "price_in_per_mtok": prices.price_in_per_mtok if prices else None,
                                "price_out_per_mtok": prices.price_out_per_mtok if prices else None})
                        completed += 1
                    finally:
                        spent += _spend(core, settings)  # counted even when the run raised
                        store.close()
                    if args.max_cost is not None and spent >= args.max_cost:
                        outcome, message = "stopped_at_cap", f"estimated spend ${spent:.4f} reached ${args.max_cost}"
                        print(f"Stopping: estimated spend ${spent:.4f} reached --max-cost ${args.max_cost}")
                        return 2
        outcome, message = "complete", None
    except BaseException as exc:
        outcome, message = "error", f"{type(exc).__name__}: {exc}"
        raise
    finally:
        if port:
            await port.aclose()
        if record is not None:
            proof_gate.write_status(record, {
                "planned_runs": sum(len(s) for *_, s in plan) * args.runs, "completed_runs": completed,
                "outcome": outcome, "message": message, "agent": agent.name,
                "model": settings.model.agent_model if settings.live else None, "today": args.today, "context_assembly": settings.context_assembly})
        if settings.live:
            cap = f" (cap ${args.max_cost})" if args.max_cost is not None else ""
            print(f"Estimated spend: ${spent:.4f}{cap}")
    return 1 if failed else 0


def cmd_gate_report(args) -> int:
    try:
        report = proof_gate.load_report(args.directory)
    except proof_gate.RecordError as exc:
        print(f"gate-report: {exc}", file=sys.stderr)
        return 1
    print(proof_gate.render(report))
    return 0


async def _chat(args, settings: Settings) -> int:
    loaded = load_specification(_spec_path(args.business))
    registry = SpecRegistry()
    registry.register(compile_specification(loaded))
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    store = EpisodeStore(settings.data_dir / f"{loaded.tenant}.db")
    agent, port = _agent(settings, args.live, date.today())
    calendar = SimulatedCalendar(tenant_times=dict(SIMULATED_TIMES))
    core = Core(registry, store, agent, {"calendar": calendar, "records": calendar},
                CoreSettings(context_assembly=settings.context_assembly))
    channel = HarnessChannel(core, loaded.tenant)
    conversation = f"terminal-{date.today().isoformat()}"
    print(f"{loaded.spec.business.name} - agent: {agent.name}. Empty line to quit.")
    try:
        while True:
            text = input("you> ").strip()
            if not text:
                return 0
            outcome = await channel.send(conversation, text)
            for message in outcome.messages:
                print(f"\n{message.text}\n")
            if outcome.lifecycle == "closed":
                print(f"(conversation closed: {store.get_episode(loaded.tenant, outcome.episode_id).close_reason})")
                conversation += "+"
    finally:
        if port:
            await port.aclose()
        store.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m studio")
    sub = parser.add_subparsers(dest="command", required=True)
    v = sub.add_parser("validate")
    v.add_argument("business")
    s = sub.add_parser("scenarios")
    s.add_argument("business", nargs="*")
    s.add_argument("--live", action="store_true")
    s.add_argument("--runs", type=int, default=1)
    s.add_argument("--max-cost", type=float, default=None)
    s.add_argument("--today", default=date.today().isoformat(), help="the date relative weekdays resolve against")
    s.add_argument("--record", metavar="DIR", default=None,
                   help="keep each run's episode store and a results.jsonl line in DIR (for gate-report)")
    g = sub.add_parser("gate-report")
    g.add_argument("directory")
    c = sub.add_parser("chat")
    c.add_argument("business")
    c.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            return cmd_validate(args)
        if args.command == "gate-report":  # reads stored records only; needs no model settings
            return cmd_gate_report(args)
        settings = Settings.from_env()
        if args.command == "scenarios":
            if args.runs < 1:
                raise ConfigurationError("--runs must be at least 1")
            if args.live and args.max_cost is None:
                raise ConfigurationError("--live needs --max-cost so spend is bounded")
            if args.live and settings.live and settings.model.price_in_per_mtok is None:
                raise ConfigurationError("--live needs STUDIO_PRICE_IN (dollars per million input tokens), "
                                         "or --max-cost cannot bound spend")
            return asyncio.run(_scenarios(args, settings))
        return asyncio.run(_chat(args, settings))
    except ConfigurationError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2
    except proof_gate.RecordError as exc:
        print(f"Record error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
