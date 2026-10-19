"""Shared builders for Core tests: a world with one or more businesses, a
scripted agent, a simulated calendar and an in-memory store."""

from __future__ import annotations

import asyncio
import itertools
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from studio.agent.scripted import ScriptedAgent
from studio.core import Core, CoreSettings, EpisodeStore, InboundMessage, SpecRegistry, TurnOutcome
from studio.core.types import (Argument, Claim, ClarifyRequest, ConfirmProposal, EffectRequest, EscalateRequest,
                               FactUpdate, ReadRequest, ResolutionClaim, RespondRequest)
from studio.extensions.simulated import SimulatedCalendar
from studio.spec import compile_specification, load_specification

BUSINESSES = Path(__file__).resolve().parents[1] / "businesses"
MONDAY = "2026-10-19"
SUNDAY = "2026-10-18"

DENTAL_FACTS = {"patient_name": "Ada Lovelace", "contact_email": "ada@example.com", "visit_type": "checkup",
                "preferred_date": MONDAY, "preferred_time": "09:00"}


def args(values: dict[str, Any]) -> tuple[Argument, ...]:
    return tuple(Argument(name=k, value=v) for k, v in values.items())


def facts(values: dict[str, Any]) -> tuple[FactUpdate, ...]:
    return tuple(FactUpdate(name=k, value=v) for k, v in values.items())


def ask_to_confirm(values: dict[str, Any] = DENTAL_FACTS, goal: str = "book_visit") -> ClarifyRequest:
    return ClarifyRequest(goal=goal, facts=facts(values), message="Shall I book that? (yes/no)",
                          confirm=ConfirmProposal(capability="book_visit", arguments=args(values)))


def check(values: dict[str, Any] = DENTAL_FACTS) -> ReadRequest:
    """The availability read the booking contract depends on (T12, Story 2.5)."""
    return ReadRequest(capability="check_availability", arguments=args(
        {k: values[k] for k in ("visit_type", "preferred_date")}))


def book(values: dict[str, Any] = DENTAL_FACTS, goal: str = "book_visit", with_facts: bool = False) -> EffectRequest:
    return EffectRequest(goal=goal, capability="book_visit", arguments=args(values),
                         facts=facts(values) if with_facts else ())


def booked_reply(view_or_evidence) -> RespondRequest:
    evidence = view_or_evidence if isinstance(view_or_evidence, str) else last_evidence(view_or_evidence)
    return RespondRequest(goal="book_visit", message="You're booked for Monday at 9.",
                          claims=(Claim(kind="action_taken", text="booked", evidence=evidence),),
                          resolution=ResolutionClaim(goal="book_visit", served=True, authority="capability:book_visit",
                                                     evidence=(evidence,)))


def last_evidence(view) -> str:
    for _, result in reversed(view.turn_results):
        if result.evidence_id:
            return result.evidence_id
    raise AssertionError("no evidence in this turn")


@dataclass
class World:
    core: Core
    agent: ScriptedAgent
    store: EpisodeStore
    calendar: SimulatedCalendar
    runner: asyncio.Runner
    tenants: dict[str, str] = field(default_factory=dict)
    _ids: Any = field(default_factory=lambda: itertools.count(1))

    def send(self, text: str, *, conversation: str = "c1", tenant: str = "bright-smile-dental",
             message_id: Optional[str] = None, script=()) -> TurnOutcome:
        self.agent.extend(script)
        message_id = message_id or f"m{next(self._ids)}"
        return self.runner.run(self.core.handle(InboundMessage(
            tenant=tenant, conversation_key=conversation, message_id=message_id, text=text)))

    def denials(self, tenant: str = "bright-smile-dental") -> list[tuple[str, str]]:
        return [(d["classification"], d["reason"]) for d in self.store.denials(tenant)]

    def results(self, outcome: TurnOutcome, tenant: str = "bright-smile-dental") -> list[dict]:
        return [s["payload"] for s in self.store.steps(tenant, outcome.episode_id) if s["kind"] == "result"]


def build_world(runner: asyncio.Runner, business_paths: list[Path], store: Optional[EpisodeStore] = None,
                settings: CoreSettings = CoreSettings(adapter_timeout_s=1.0), calendar=None) -> World:
    registry = SpecRegistry()
    for path in business_paths:
        registry.register(compile_specification(load_specification(path)))
    agent = ScriptedAgent()
    calendar = calendar or SimulatedCalendar()
    store = store or EpisodeStore()
    core = Core(registry, store, agent, {"calendar": calendar}, settings)
    return World(core=core, agent=agent, store=store, calendar=calendar, runner=runner)
