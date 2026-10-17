"""End-to-end: channel harness → Core → credential-free agent → simulated
system of record, for every business's scenario file. Expectations are about
the episode record (FR76), never about wording, and are never edited to fit an
outcome: a failing scenario means the product is wrong."""

import asyncio
from datetime import date

import pytest

from studio.agent.deterministic import DeterministicAgent
from studio.channels.harness import load_scenarios, run_scenario
from studio.core import Core, EpisodeStore, SpecRegistry
from studio.extensions.simulated import SimulatedCalendar
from studio.spec import compile_specification, load_specification
from studio.tests.helpers import BUSINESSES

TODAY = date(2026, 10, 13)  # a Tuesday, so "Monday" is 2026-10-19
TIMES = {"hopfield-brewery": ("12:00", "15:00", "18:00")}


def cases():
    for business in sorted(p.parent.name for p in BUSINESSES.glob("*/scenarios.toml")):
        for scenario in load_scenarios(BUSINESSES / business / "scenarios.toml"):
            yield pytest.param(business, scenario, id=scenario["id"])


@pytest.mark.parametrize("business,scenario", cases())
def test_scenario(business, scenario):
    compiled = compile_specification(load_specification(BUSINESSES / business / "specification.toml"))
    registry = SpecRegistry()
    registry.register(compiled)
    calendar = SimulatedCalendar(tenant_times=dict(TIMES))
    core = Core(registry, EpisodeStore(), DeterministicAgent(today=lambda: TODAY), {"calendar": calendar})
    result = asyncio.run(run_scenario(core, compiled.tenant, scenario,
                                      effects_counter=lambda: sum(calendar.executions.values())))
    transcript = "\n".join(f"> {text}\n" + "\n".join(f"< [{m.kind}] {m.text}" for m in out)
                           for text, out in result.transcript.exchanges)
    assert result.passed, "\n".join(result.failures) + "\n\n" + transcript
