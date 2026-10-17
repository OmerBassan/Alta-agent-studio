"""Command line: ``python -m studio <command>``.

    validate <business>            run the validation suite on a business specification
    scenarios [<business> ...]     run scenario files end to end (credential-free by default)
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
from datetime import date
from pathlib import Path

from studio.agent.deterministic import DeterministicAgent
from studio.channels.harness import HarnessChannel, load_scenarios, run_scenario
from studio.config import ConfigurationError, Settings
from studio.core import Core, EpisodeStore, SpecRegistry
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
    if not settings.live or settings.model.price_in_per_mtok is None:
        return 0.0
    total = 0.0
    for tenant in {e.tenant for e in _all_episodes(core)}:
        for episode in core.store.episodes(tenant):
            for call in core.store.model_calls(tenant, episode.episode_id):
                total += (call["input_tokens"] or 0) * settings.model.price_in_per_mtok / 1e6
                total += (call["output_tokens"] or 0) * (settings.model.price_out_per_mtok or 0) / 1e6
    return total


def _all_episodes(core: Core):
    for tenant in core.registry.tenants():
        yield from core.store.episodes(tenant)


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


async def _scenarios(args, settings: Settings) -> int:
    names = args.business or sorted(p.parent.name for p in BUSINESSES.glob("*/scenarios.toml"))
    agent, port = _agent(settings, args.live, date.fromisoformat(args.today))
    failed = 0
    try:
        for name in names:
            compiled = compile_specification(load_specification(_spec_path(name)))
            for scenario in load_scenarios(_spec_path(name).parent / "scenarios.toml"):
                registry = SpecRegistry()
                registry.register(compiled)
                calendar = SimulatedCalendar(tenant_times=dict(SIMULATED_TIMES))
                core = Core(registry, EpisodeStore(), agent, {"calendar": calendar})
                for _ in range(args.runs):
                    result = await run_scenario(core, compiled.tenant, scenario,
                                                effects_counter=lambda: sum(calendar.executions.values()))
                    status = "PASS" if result.passed else "FAIL"
                    failed += not result.passed
                    calls = core.store.model_calls(compiled.tenant, result.episode_id) if result.episode_id else []
                    print(f"{status} {name}/{scenario['id']}  model calls: {len(calls)}")
                    for failure in result.failures:
                        print(f"     {failure}")
                    spent = _spend(core, settings)
                    if args.max_cost is not None and spent >= args.max_cost:
                        print(f"Stopping: estimated spend ${spent:.4f} reached --max-cost ${args.max_cost}")
                        return 2
    finally:
        if port:
            await port.aclose()
    return 1 if failed else 0


async def _chat(args, settings: Settings) -> int:
    loaded = load_specification(_spec_path(args.business))
    registry = SpecRegistry()
    registry.register(compile_specification(loaded))
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    store = EpisodeStore(settings.data_dir / f"{loaded.tenant}.db")
    agent, port = _agent(settings, args.live, date.today())
    core = Core(registry, store, agent, {"calendar": SimulatedCalendar(tenant_times=dict(SIMULATED_TIMES))})
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
    c = sub.add_parser("chat")
    c.add_argument("business")
    c.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)
    try:
        settings = Settings.from_env()
        if args.command == "validate":
            return cmd_validate(args)
        if args.command == "scenarios":
            if args.live and args.max_cost is None:
                raise ConfigurationError("--live needs --max-cost so spend is bounded")
            return asyncio.run(_scenarios(args, settings))
        return asyncio.run(_chat(args, settings))
    except ConfigurationError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
