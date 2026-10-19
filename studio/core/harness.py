"""The Core — validate, authorize, execute, observe, persist (AD-1).

The Agent decides what to do next. The Core decides whether that is permitted,
does it, and records what happened. Nothing in this module selects the Agent's
next step: every mechanism either returns a typed ``Result`` to the Agent or
ends the episode in a declared safety halt — the Core's only two exits (AD-18).

Per inbound message:

1. A re-sent message is recognised and not processed twice (FR87).
2. The episode is found or created; a new episode pins the specification and
   compiler versions and receives its provenance references (AD-7, AD-11).
3. If an operator has suspended the Agent, the message is recorded and the
   episode ends in a recorded outcome, unanswered (FR110).
4. A pending confirmation is granted or declined only by the requester's own
   bare yes or no (DL-015, DL-008).
5. Guards are evaluated before the Agent sees the message (FR44, AD-21).
6. The Agent is asked for one request at a time; each is authorized, executed
   and journaled, and its typed result returned, until the Agent emits a
   request that speaks to the requester — or the per-turn budget or the stall
   detector ends the episode in a declared halt (FR107).

Every agent request, Core decision, effect and message is a step in the
journal, and every denial is classified exactly once (AD-2, AD-5).
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import re
import sqlite3
import weakref
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Optional

from studio.core.consent import bare_answer
from studio.core.policy import (ArgumentError, canonical_arguments, coerce, denying_rule, idempotency_key,
                                payload_digest)
from studio.core.ports import (Adapter, AdapterResult, AgentDecision, AgentRuntime, AgentView, ConversationEntry,
                               InboundMessage, ObligationView, OfferView, OutboundMessage, ProvenanceRef)
from studio.core.store import Episode, EpisodeStore, parse_instant
from studio.core.types import (TURN_ENDING_KINDS, Argument, ClarifyRequest, Denial, EffectRequest, EscalateRequest,
                               ReadRequest, Result, RespondRequest, RetrieveRequest, SuspendRequest)
from studio.core.vocabulary import REASON_CLASS
from studio.config import CONTEXT_ASSEMBLY_MODES, ConfigurationError
from studio.knowledge.retrieval import LexicalRetriever, Retriever
from studio.spec.compile import CapabilityPolicy, CompiledSpecification, ContextItem

logger = logging.getLogger("studio.core")

EPISODE_LINK = "studio://episode/{tenant}/{episode_id}"


@dataclass(frozen=True)
class CoreSettings:
    """Platform-owned limits. Never business configuration (AD-15)."""

    max_requests_per_turn: int = 8
    stall_repeats: int = 3
    adapter_timeout_s: float = 10.0
    agent_timeout_s: float = 90.0
    context_assembly: str = "standing"
    """``standing``: every item's reference is issued at episode start and its text is in view.
    ``on_demand``: only the specification projection is; source material is reached through retrieve
    (T9, approved 2026-10-19: both modes, the default chosen by measurement — Story 2.3)."""



class UnknownTenant(LookupError):
    pass


@dataclass
class _Entry:
    compiled: CompiledSpecification
    items: dict[str, ContextItem]


class SpecRegistry:
    """Compiled specifications by tenant and version. An episode always runs
    on the version pinned at its start (AD-11, FR27); ``live`` is only used to
    start new episodes. Promotion and rollback (Phase 3) move ``live``."""

    def __init__(self) -> None:
        self._versions: dict[tuple[str, str], _Entry] = {}
        self._live: dict[str, str] = {}

    def register(self, compiled: CompiledSpecification, live: bool = True) -> None:
        self._versions[(compiled.tenant, compiled.spec_version)] = _Entry(
            compiled, {i.item_id: i for i in compiled.context.items})
        if live:
            self._live[compiled.tenant] = compiled.spec_version

    def tenants(self) -> tuple[str, ...]:
        return tuple(sorted(self._live))

    def live(self, tenant: str) -> CompiledSpecification:
        if tenant not in self._live:
            raise UnknownTenant(tenant)
        return self._versions[(tenant, self._live[tenant])].compiled

    def entry(self, tenant: str, version: str) -> _Entry:
        try:
            return self._versions[(tenant, version)]
        except KeyError:
            raise UnknownTenant(f"{tenant}@{version}") from None


@dataclass
class TurnOutcome:
    episode_id: str
    messages: list[OutboundMessage] = field(default_factory=list)
    lifecycle: str = "active"
    duplicate: bool = False
    halted: Optional[str] = None


def _refused(kind: str, reason: str, detail: str) -> Result:
    return Result(kind=kind, status="refused",
                  denial=Denial(classification=REASON_CLASS[reason], reason=reason, detail=detail))


def _failed(kind: str, reason: str, detail: str, **extra) -> Result:
    return Result(kind=kind, status="failed",
                  denial=Denial(classification=REASON_CLASS[reason], reason=reason, detail=detail), **extra)


def _signature(request) -> str:
    return hashlib.sha256(request.model_dump_json().encode()).hexdigest()


DEADLINE_EXPIRED = "deadline_expired"


def _describe_event(payload: dict) -> str:
    """How an external-system event reads in the Agent's conversation."""
    if payload.get("kind") == DEADLINE_EXPIRED:
        return (f"The deadline {payload.get('deadline')} passed while waiting for {payload.get('awaiting')}; "
                "nothing has arrived.")
    return f"An external system reported: {payload}"


def _due(deadline: Optional[str], now: str) -> bool:
    return deadline is not None and parse_instant(deadline) <= parse_instant(now)


class Core:
    def __init__(self, registry: SpecRegistry, store: EpisodeStore, agent: AgentRuntime,
                 adapters: dict[str, Adapter], settings: CoreSettings = CoreSettings(),
                 retriever: Optional[Retriever] = None):
        if settings.context_assembly not in CONTEXT_ASSEMBLY_MODES:
            raise ConfigurationError(f"context_assembly must be one of {CONTEXT_ASSEMBLY_MODES}, "
                                     f"got {settings.context_assembly!r}")
        self.retriever = retriever or LexicalRetriever()
        self.registry = registry
        self.store = store
        self.agent = agent
        self.adapters = adapters
        self.settings = settings
        # Weak values: a lock lives exactly as long as some turn holds or awaits
        # it, so the map cannot grow with the number of conversations ever seen.
        self._locks: weakref.WeakValueDictionary[tuple[str, str], asyncio.Lock] = weakref.WeakValueDictionary()

    # ==============================================================================
    # Ingress
    # ==============================================================================

    async def handle(self, inbound: InboundMessage) -> TurnOutcome:
        compiled = self.registry.live(inbound.tenant)  # raises UnknownTenant
        # One lock per conversation serialises every inbound message that could
        # touch the same episode, including the one that creates it (AD-13).
        async with self._lock(inbound.tenant, inbound.conversation_key):
            known = self.store.seen_message(inbound.tenant, inbound.message_id)
            if known:
                return self._duplicate(inbound.tenant, known)
            episode = self.store.open_episode(inbound.tenant, inbound.conversation_key) \
                or self._start_episode(compiled, inbound.conversation_key)
            try:
                with self.store.transaction():
                    self.store.record_inbound(episode.tenant, inbound.message_id, episode.episode_id)
                    seq = self.store.append_step(episode.tenant, episode.episode_id, "requester", "inbound",
                                                 {"message_id": inbound.message_id, "text": inbound.text})
            except sqlite3.IntegrityError:
                return self._duplicate(inbound.tenant, episode.episode_id)
            return await self._turn(episode, inbound, seq)

    def _lock(self, tenant: str, conversation_key: str) -> asyncio.Lock:
        key = (tenant, conversation_key)
        lock = self._locks.get(key)
        if lock is None:
            lock = self._locks[key] = asyncio.Lock()
        return lock

    def _duplicate(self, tenant: str, episode_id: str) -> TurnOutcome:
        episode = self.store.get_episode(tenant, episode_id)
        return TurnOutcome(episode_id=episode_id, lifecycle=episode.lifecycle if episode else "closed",
                           duplicate=True)

    def _start_episode(self, compiled: CompiledSpecification, conversation_key: str) -> Episode:
        """Episode creation is the Core's, on an adapter's request (AD-13). The
        versions in force are pinned now and read from the episode thereafter."""
        with self.store.transaction():
            self._pin(compiled)
            episode = self.store.create_episode(compiled.tenant, conversation_key, compiled.spec_version,
                                                compiled.compiler_version)
            seq = self.store.append_step(episode.tenant, episode.episode_id, "core", "episode_started", {
                "spec_version": compiled.spec_version, "compiler_version": compiled.compiler_version})
            standing = [i for i in compiled.context.items
                        if self.settings.context_assembly == "standing" or i.origin == "specification"]
            for item in standing:
                self.store.issue_reference(episode.tenant, episode.episode_id, item.item_id, item.source_id,
                                           item.source_version, item.locator)
            self.store.append_step(episode.tenant, episode.episode_id, "core", "references_issued",
                                   {"count": len(standing), "after": seq,
                                    "context_assembly": self.settings.context_assembly})
        return episode

    def _pin(self, compiled: CompiledSpecification) -> None:
        """Make the version an episode starts on durable (Story 2.1, AD-11): each
        source's sections once under its content hash, and the compiled
        specification with those texts stripped. Both are written once and never
        rewritten, so a leaflet edited tomorrow cannot change what this episode
        was told, even after a restart."""
        sources: dict[str, tuple[str, list[dict]]] = {}
        for item in compiled.context.items:
            if item.origin == "source":
                sources.setdefault(item.source_version, (item.source_id, []))[1].append(
                    {"locator": item.locator, "title": item.title, "text": item.text})
        for content_hash, (source_id, sections) in sources.items():
            self.store.put_source_snapshot(content_hash, source_id, sections)
        stripped = compiled.model_copy(update={"context": compiled.context.model_copy(update={"items": tuple(
            i.model_copy(update={"text": ""}) if i.origin == "source" else i for i in compiled.context.items)})})
        self.store.put_spec_snapshot(compiled.tenant, compiled.spec_version, stripped.model_dump_json())

    def _entry(self, tenant: str, version: str) -> _Entry:
        """The pinned version an episode runs on. After a restart that followed
        an edit, the registry no longer holds it: rebuild it from the store."""
        try:
            return self.registry.entry(tenant, version)
        except UnknownTenant:
            raw = self.store.spec_snapshot(tenant, version)
            if raw is None:
                raise
        stripped = CompiledSpecification.model_validate_json(raw)
        texts: dict[tuple[str, str], str] = {}
        loaded: set[str] = set()
        items = []
        for item in stripped.context.items:
            if item.origin == "source":
                if item.source_version not in loaded:
                    loaded.add(item.source_version)
                    for section in self.store.source_snapshot(item.source_version) or ():
                        texts[(item.source_version, section["locator"])] = section["text"]
                text = texts.get((item.source_version, item.locator))
                if text is None:
                    raise UnknownTenant(f"{tenant}@{version}: source {item.source_id} was never pinned")
                item = item.model_copy(update={"text": text})
            items.append(item)
        compiled = stripped.model_copy(update={"context": stripped.context.model_copy(update={"items": tuple(items)})})
        self.registry.register(compiled, live=False)
        return self.registry.entry(tenant, version)

    async def _turn(self, episode: Episode, inbound: InboundMessage, seq: int) -> TurnOutcome:
        tenant, eid = episode.tenant, episode.episode_id
        entry = self._entry(tenant, episode.spec_version)
        compiled = entry.compiled
        agent_suspended, effects_suspended = self.store.flags(tenant)
        if agent_suspended:
            await self._reconcile_started_effects(episode, compiled)  # no orphan survives into a closed episode
            self.store.append_step(tenant, eid, "core", "suspended_unanswered", {"message_id": inbound.message_id})
            self.store.set_lifecycle(tenant, eid, "closed", close_reason="suspended")
            return TurnOutcome(episode_id=eid, lifecycle="closed")
        if episode.lifecycle == "pending":
            self.store.append_step(tenant, eid, "core", "resumed", {"awaiting": episode.awaiting})
            self.store.set_lifecycle(tenant, eid, "active")
        self._resolve_consent(episode, inbound)

        constraints: list[str] = []
        text = inbound.text.lower()
        for guard in compiled.policy.guards:
            hit = next((k for k in guard.keywords if k in text), None)
            if hit is None:
                continue
            gseq = self.store.append_step(tenant, eid, "core", "guard_verdict",
                                          {"guard": guard.id, "verdict": guard.verdict, "matched": hit})
            self.store.add_evidence(tenant, eid, "guard_verdict",
                                    {"guard": guard.id, "family": guard.family, "verdict": guard.verdict}, gseq)
            if guard.verdict == "halt":
                await self._reconcile_started_effects(episode, compiled)  # no orphan survives into a closed episode
                return self._halt(episode, compiled, "guard", f"guard {guard.id} ({guard.family})")
            constraints.append(f"[{guard.id}] {guard.constraint}")
        return await self._agent_loop(episode, entry, tuple(constraints), effects_suspended)

    # ==============================================================================
    # Consent — only the requester's own bare answer grants or declines
    # ==============================================================================

    def _resolve_consent(self, episode: Episode, inbound: InboundMessage) -> None:
        tenant, eid = episode.tenant, episode.episode_id
        open_offers = [o for o in self.store.offers(tenant, eid, "confirmation") if o["state"] == "offered"]
        if not open_offers:
            return
        answer = bare_answer(inbound.text)
        if not answer:
            return
        state = "granted" if answer == "yes" else "declined"
        for offer in open_offers:
            self.store.decide_offer(offer["offer_id"], state, f"requester:{inbound.message_id}")
            seq = self.store.append_step(tenant, eid, "core", f"confirmation_{state}",
                                         {"offer_id": offer["offer_id"], "message_id": inbound.message_id})
            self.store.add_evidence(tenant, eid, f"confirmation_{state}",
                                    {"offer_id": offer["offer_id"], "capability": offer["capability"],
                                     "message_id": inbound.message_id}, seq)

    # ==============================================================================
    # The loop — the Agent chooses; the Core constrains
    # ==============================================================================

    async def _agent_loop(self, episode: Episode, entry: _Entry, constraints: tuple[str, ...],
                          effects_suspended: bool) -> TurnOutcome:
        tenant, eid = episode.tenant, episode.episode_id
        results: list[tuple[str, Result]] = await self._reconcile_started_effects(episode, entry.compiled)
        signatures: Counter[str] = Counter()
        budget = self.settings.max_requests_per_turn
        for used in range(budget):
            view = self._view(episode, entry, constraints, results, budget - used)
            decision = await self._decide(view)
            seq = self.store.append_step(tenant, eid, "agent", "decision", {
                "request": decision.request.model_dump(mode="json") if decision.request else None,
                "error": decision.error})
            for call in decision.model_calls:
                self.store.add_model_call(tenant, eid, seq, call.model_dump())
            if decision.request is None:
                result = _failed("unknown", "agent_failed", decision.error or "the agent produced no request")
                self._record_result(episode, entry.compiled, seq, result)
                results.append(("unknown", result))
                continue
            request = decision.request
            signatures[_signature(request)] += 1
            if signatures[_signature(request)] >= self.settings.stall_repeats:
                return self._halt(episode, entry.compiled, "stall",
                                  f"the same {request.kind} request was made {self.settings.stall_repeats} times")
            result, reply = await self._handle(episode, entry, request, seq, effects_suspended)
            self._record_result(episode, entry.compiled, seq, result)
            results.append((request.kind, result))
            if reply is not None:
                return reply
        return self._halt(episode, entry.compiled, "budget_exhausted",
                          f"no reply after {budget} requests in one turn")

    async def _decide(self, view: AgentView) -> AgentDecision:
        try:
            return await asyncio.wait_for(self.agent.decide(view), timeout=self.settings.agent_timeout_s)
        except asyncio.TimeoutError:
            return AgentDecision(error=f"the agent did not decide within {self.settings.agent_timeout_s}s")
        except Exception as exc:  # the runtime is outside the Core; its failure is a typed result
            logger.exception("agent runtime %s failed", getattr(self.agent, "name", "?"))
            return AgentDecision(error=f"{type(exc).__name__}: {exc}")

    def _record_result(self, episode: Episode, compiled: CompiledSpecification, seq: int, result: Result) -> None:
        self.store.append_step(episode.tenant, episode.episode_id, "core", "result", result.model_dump(mode="json"))
        if result.denial:
            self.store.add_denial(episode.tenant, episode.episode_id, seq, result.denial.classification,
                                  result.denial.reason, result.denial.detail, compiled.spec_version)

    # ==============================================================================
    # Request handling — one function per kind; each authorizes and executes
    # ==============================================================================

    async def _handle(self, episode: Episode, entry: _Entry, request, seq: int,
                      effects_suspended: bool) -> tuple[Result, Optional[TurnOutcome]]:
        compiled = entry.compiled
        common = self._apply_common(episode, compiled, request, seq)
        if common is not None:
            return common, None
        if isinstance(request, RetrieveRequest):
            return self._retrieve(episode, entry, request, seq), None
        if isinstance(request, ReadRequest):
            return await self._read(episode, compiled, request, seq), None
        if isinstance(request, EffectRequest):
            return await self._effect(episode, compiled, request, seq, effects_suspended), None
        if isinstance(request, ClarifyRequest):
            return self._clarify(episode, compiled, request, seq)
        if isinstance(request, RespondRequest):
            return self._respond(episode, entry, request, seq)
        if isinstance(request, EscalateRequest):
            return self._escalate(episode, compiled, request, seq)
        if isinstance(request, SuspendRequest):
            return self._suspend(episode, compiled, request, seq)
        return _refused(getattr(request, "kind", "unknown"), "malformed_request", "unknown request kind"), None

    def _apply_common(self, episode: Episode, compiled: CompiledSpecification, request, seq: int) -> Optional[Result]:
        """Goal and facts carried by any request. Validated as a whole before
        anything is recorded, so a bad request changes nothing."""
        policy, kind = compiled.policy, request.kind
        if request.goal is not None and request.goal not in policy.goals:
            return _refused(kind, "undeclared_goal",
                            f"'{request.goal}' is not one of this business's goals; goals come only from the "
                            "declared set (FR49)")
        values: dict[str, Any] = {}
        for update in request.facts:
            if update.name not in policy.facts:
                return _refused(kind, "undeclared_fact", f"'{update.name}' is not a declared fact")
            try:
                values[update.name] = coerce(policy.facts[update.name], update.value)
            except ArgumentError as exc:
                return _refused(kind, "invalid_fact_value", f"'{update.name}' {exc}")
        with self.store.transaction():
            for name, value in values.items():
                self.store.set_fact(episode.tenant, episode.episode_id, name, value, seq)
            if request.goal is not None:
                goals = self.store.goals(episode.tenant, episode.episode_id)
                if goals.get(request.goal) != "active":
                    self.store.set_active_goal(episode.tenant, episode.episode_id, request.goal, seq)
        return None

    # --- retrieve ---------------------------------------------------------------------

    def _retrieve(self, episode: Episode, entry: _Entry, request: RetrieveRequest, seq: int) -> Result:
        """Retrieval over the episode's pinned material (Story 2.3). In standing
        mode every item was issued at episode start; on demand, a retrieval
        issues references for exactly the items it returns, so the Agent can
        only cite what it has retrieved (FR32, FR38)."""
        tenant, eid = episode.tenant, episode.episode_id
        issued = {r["item_id"]: r["ref"] for r in self.store.references(tenant, eid)}
        if self._assembly(episode) == "on_demand":
            pool = list(entry.items.values())
        else:
            pool = [entry.items[i] for i in issued if i in entry.items]
        if not pool:
            return _refused("retrieve", "nothing_to_retrieve", "this business has no authoritative material")
        found, records = [], []
        with self.store.transaction():
            for item in self.retriever.search(request.query, pool, 4):
                ref = issued.get(item.item_id) or self.store.issue_reference(
                    tenant, eid, item.item_id, item.source_id, item.source_version, item.locator)
                found.append({"reference": ref, "title": item.title, "text": item.text})
                records.append({"reference": ref, "source_id": item.source_id,
                                "source_version": item.source_version, "locator": item.locator})
            self.store.add_evidence(tenant, eid, "retrieval", {
                "query": request.query, "references": [r["reference"] for r in records], "items": records}, seq)
        found = tuple(found)
        return Result(kind="retrieve", status="ok", items=found,
                      note=None if found else "Nothing in the business's material matches this.")

    # --- read -------------------------------------------------------------------------

    def _capability(self, compiled: CompiledSpecification, kind: str, name: str,
                    expected: str) -> tuple[Optional[CapabilityPolicy], Optional[Result]]:
        cap = compiled.policy.capabilities.get(name)
        if cap is None:
            return None, _refused(kind, "not_granted", f"'{name}' is not a capability this business has granted")
        if cap.kind != expected:
            return None, _refused(kind, "wrong_kind", f"'{name}' is a {cap.kind}, not a {expected}")
        return cap, None

    async def _reconcile_started_effects(self, episode: Episode,
                                         compiled: CompiledSpecification) -> list[tuple[str, Result]]:
        """A crash between starting an effect and recording its outcome leaves
        it 'started': the system of record may or may not hold it (Story 1.11).
        Before the Agent decides anything, settle each one by read-back only —
        never by executing it again — so no effect stays an orphan. An
        unreachable read-back proves nothing, so the effect is 'unverified'.
        Each outcome is returned as the effect's own typed result, so the Agent
        sees it exactly as if the effect had just run.

        Limits: the read-back is keyed by the idempotency key (the adapter's
        reference was never recorded), and the conversation lock is per
        process, so this assumes the single-writer store (T3)."""
        tenant, eid = episode.tenant, episode.episode_id
        results: list[tuple[str, Result]] = []
        for row in self.store.started_effects(tenant, eid):
            cap = compiled.policy.capabilities.get(row["capability"])
            adapter = self.adapters.get(cap.adapter) if cap else None
            verified, reference, problem = False, None, None
            if adapter is None:
                problem = "adapter missing"
            else:
                try:
                    check = await self._call_adapter(adapter.read_back, tenant, cap.operation, row["arguments"],
                                                     row["idempotency_key"], None)
                    verified, reference = bool(check.ok), check.reference
                except Exception as exc:
                    problem = f"read-back unreachable: {type(exc).__name__}: {exc}"
                    logger.warning("reconciling %s: %s", row["capability"], problem)
            state = "verified" if verified else "unverified"
            with self.store.transaction():
                seq = self.store.append_step(tenant, eid, "core", "effect_reconciled", {
                    "capability": row["capability"], "idempotency_key": row["idempotency_key"], "state": state})
                evidence_id = self.store.finish_effect(
                    tenant, eid, row["idempotency_key"], state, reference, f"effect_{state}", {
                        "capability": row["capability"], "arguments": row["arguments"], "reference": reference,
                        "idempotency_key": row["idempotency_key"], "adapter_problem": problem, "reconciled": True}, seq)
            if verified:
                results.append(("effect", Result(kind="effect", status="ok", capability=row["capability"],
                                                 verified=True, evidence_id=evidence_id,
                                                 note="Settled after an interruption: it is done.")))
            else:
                escalate = cap is not None and cap.on_unverified == "inform_and_escalate"
                results.append(("effect", _failed(
                    "effect", "adapter_failed",
                    f"{row['capability']} was interrupted and could not be confirmed by reading it back. It may or "
                    "may not have happened. Do not tell the requester it is done." +
                    (" The business wants this handed to a person." if escalate else ""),
                    evidence_id=evidence_id, verified=False, capability=row["capability"])))
        return results

    async def _call_adapter(self, fn, *args) -> AdapterResult:
        return await asyncio.wait_for(asyncio.to_thread(fn, *args), timeout=self.settings.adapter_timeout_s)

    async def _read(self, episode: Episode, compiled: CompiledSpecification, request: ReadRequest,
                    seq: int) -> Result:
        cap, refusal = self._capability(compiled, "read", request.capability, "read")
        if refusal:
            return refusal
        try:
            args = canonical_arguments(cap, request.arguments)
        except ArgumentError as exc:
            return _refused("read", "invalid_arguments", str(exc))
        adapter = self.adapters.get(cap.adapter)
        if adapter is None:
            return _failed("read", "adapter_missing", f"no adapter '{cap.adapter}' is connected")
        try:
            out = await self._call_adapter(adapter.read, episode.tenant, cap.operation, args)
        except asyncio.TimeoutError:
            return _failed("read", "adapter_timeout", f"{cap.name} did not answer in {self.settings.adapter_timeout_s}s")
        except Exception as exc:
            logger.exception("adapter %s read failed", cap.adapter)
            return _failed("read", "adapter_failed", f"{type(exc).__name__}: {exc}")
        if not out.ok:
            return _failed("read", "adapter_failed", out.error or "the system returned an error")
        evidence_id = self.store.add_evidence(episode.tenant, episode.episode_id, "read_result", {
            "capability": cap.name, "arguments": args, "data": dict(out.data), "freshness": cap.freshness}, seq)
        return Result(kind="read", status="ok", capability=cap.name, evidence_id=evidence_id,
                      data=tuple(Argument(name=k, value=v if isinstance(v, (str, int, float, bool)) or v is None
                                          else str(v)) for k, v in out.data))

    # --- shared effect checks (used by effect and by a confirmation proposal) ------------

    def _check_payload(self, episode: Episode, compiled: CompiledSpecification, kind: str, capability: str,
                       arguments: tuple[Argument, ...]) -> tuple[Optional[CapabilityPolicy], dict, Optional[Result]]:
        cap, refusal = self._capability(compiled, kind, capability, "effect")
        if refusal:
            return None, {}, refusal
        try:
            args = canonical_arguments(cap, arguments)
        except ArgumentError as exc:
            return None, {}, _refused(kind, "invalid_arguments", str(exc))
        facts = self.store.facts(episode.tenant, episode.episode_id)
        for inp in cap.inputs:
            if inp.name not in args:
                continue
            if inp.fact not in facts:
                return None, {}, _refused(kind, "arguments_not_established",
                                          f"'{inp.name}' has not been established in this conversation")
            if str(facts[inp.fact]).lower() != str(args[inp.name]).lower():
                return None, {}, _refused(kind, "arguments_not_established",
                                          f"'{inp.name}' is {args[inp.name]!r} but the conversation established "
                                          f"{facts[inp.fact]!r}")
        rule = denying_rule(cap.deny_rules, {**facts, **args})
        if rule is not None:
            return None, {}, Result(kind=kind, status="refused", capability=cap.name, denial=Denial(
                classification="business_refusal", reason="rule_denied", detail=f"{rule.rule_id}: {rule.text}",
                rule=rule.rule_id))
        return cap, args, None

    # --- effect -----------------------------------------------------------------------

    async def _effect(self, episode: Episode, compiled: CompiledSpecification, request: EffectRequest, seq: int,
                      effects_suspended: bool) -> Result:
        tenant, eid = episode.tenant, episode.episode_id
        if effects_suspended:
            return _refused("effect", "effects_suspended", "the operator has stopped this agent from acting")
        cap, args, refusal = self._check_payload(episode, compiled, "effect", request.capability, request.arguments)
        if refusal:
            return refusal
        digest = payload_digest(tenant, eid, episode.spec_version, cap.name, args)
        key = idempotency_key(tenant, eid, cap.name, args)
        existing = self.store.get_effect(tenant, eid, key)
        if existing and existing["state"] == "verified":
            return Result(kind="effect", status="ok", capability=cap.name, verified=True,
                          evidence_id=existing["evidence_id"], note="Already done; not repeated.")

        if cap.authority_basis == "verified_identity" and not any(
                e["kind"] == "identity_verified" for e in self.store.evidence(tenant, eid)):
            return _refused("effect", "authority_not_established",
                            f"'{cap.name}' needs the requester's identity verified; a sender address is not an identity")
        approval = None
        if cap.authority_basis == "operator_approval":
            offers = [o for o in self.store.offers(tenant, eid, "operator_approval") if o["digest"] == digest]
            approval = next((o for o in offers if o["state"] == "granted"), None)
            if approval is None:
                if any(o["state"] == "declined" for o in offers):
                    return _refused("effect", "operator_denied", f"the operator declined '{cap.name}' for this request")
                offer_id = self.store.create_offer(tenant, eid, "operator_approval", cap.name, digest,
                                                   episode.spec_version, seq)
                return Result(kind="effect", status="refused", offer_id=offer_id,
                              denial=Denial(classification="business_refusal", reason="operator_approval_required",
                                            detail=f"'{cap.name}' waits for operator approval (offer {offer_id})"))
        confirmation = None
        if cap.confirmation:
            confirmation = next((o for o in self.store.offers(tenant, eid, "confirmation")
                                 if o["digest"] == digest and o["state"] == "granted"), None)
            if confirmation is None:
                return _refused("effect", "confirmation_missing",
                                f"'{cap.name}' needs the requester to confirm exactly these details first")

        if existing is None:
            self.store.start_effect(tenant, eid, key, cap.name, args)
        for gate in (confirmation, approval):
            if gate is not None:
                self.store.decide_offer(gate["offer_id"], "consumed", f"core:step{seq}")

        adapter = self.adapters.get(cap.adapter)
        if adapter is None:
            evidence_id = self.store.finish_effect(tenant, eid, key, "failed", None, "effect_failed",
                                                   {"capability": cap.name, "error": "adapter missing"}, seq)
            return _failed("effect", "adapter_missing", f"no adapter '{cap.adapter}' is connected",
                           evidence_id=evidence_id, verified=False)
        outcome: Optional[AdapterResult] = None
        problem: Optional[str] = None
        try:
            outcome = await self._call_adapter(adapter.effect, tenant, cap.operation, args, key)
        except asyncio.TimeoutError:
            problem = "timeout"
        except Exception as exc:
            logger.exception("adapter %s effect failed", cap.adapter)
            problem = f"{type(exc).__name__}: {exc}"
        if outcome is not None and not outcome.ok and problem is None:
            evidence_id = self.store.finish_effect(tenant, eid, key, "failed", None, "effect_failed",
                                                   {"capability": cap.name, "arguments": args,
                                                    "error": outcome.error}, seq)
            return _failed("effect", "adapter_failed", outcome.error or f"{cap.name} was rejected by the system",
                           evidence_id=evidence_id, verified=False)

        # Success is never the adapter's say-so: it is a read-back (FR51, AD-6).
        verified = False
        reference = outcome.reference if outcome else None
        try:
            check = await self._call_adapter(adapter.read_back, tenant, cap.operation, args, key, reference)
            verified = bool(check.ok)
            reference = check.reference or reference
        except Exception as exc:  # an unreachable read-back proves nothing either way
            logger.warning("read-back for %s failed: %s", cap.name, exc)
        state = "verified" if verified else "unverified"
        evidence_id = self.store.finish_effect(tenant, eid, key, state, reference, f"effect_{state}", {
            "capability": cap.name, "arguments": args, "reference": reference, "idempotency_key": key,
            "adapter_problem": problem}, seq)
        if verified:
            return Result(kind="effect", status="ok", capability=cap.name, verified=True, evidence_id=evidence_id,
                          data=(Argument(name="reference", value=reference),) if reference else ())
        return _failed("effect", "adapter_timeout" if problem == "timeout" else "adapter_failed",
                       f"{cap.name} could not be confirmed by reading it back. It may or may not have happened. "
                       "Do not tell the requester it is done." +
                       (" The business wants this handed to a person." if cap.on_unverified == "inform_and_escalate"
                        else ""),
                       evidence_id=evidence_id, verified=False, capability=cap.name)

    # --- clarify ----------------------------------------------------------------------

    def _clarify(self, episode: Episode, compiled: CompiledSpecification, request: ClarifyRequest,
                 seq: int) -> tuple[Result, Optional[TurnOutcome]]:
        policy = compiled.policy
        for fact in request.asks_for:
            if fact not in policy.facts:
                return _refused("clarify", "undeclared_fact", f"'{fact}' is not a declared fact"), None
            if fact in policy.never_ask_facts:
                return _refused("clarify", "never_ask", f"this business never asks for '{fact}'"), None
        offer_id = None
        if request.confirm is not None:
            cap, args, refusal = self._check_payload(episode, compiled, "clarify", request.confirm.capability,
                                                     request.confirm.arguments)
            if refusal:
                return refusal, None
            digest = payload_digest(episode.tenant, episode.episode_id, episode.spec_version, cap.name, args)
            offer_id = self.store.create_offer(episode.tenant, episode.episode_id, "confirmation", cap.name, digest,
                                               episode.spec_version, seq)
        self._expire_confirmations(episode, keep=offer_id)
        return Result(kind="clarify", status="ok", offer_id=offer_id), self._reply(episode, compiled, request.message)

    def _expire_confirmations(self, episode: Episode, keep: Optional[str] = None) -> None:
        """A confirmation is valid only while it is the question the requester
        was last asked. Anything else said to them expires it."""
        for offer in self.store.offers(episode.tenant, episode.episode_id, "confirmation"):
            if offer["state"] == "offered" and offer["offer_id"] != keep:
                self.store.decide_offer(offer["offer_id"], "expired", "core")

    # --- respond ----------------------------------------------------------------------

    def _check_claims(self, episode: Episode, entry: _Entry, request: RespondRequest) -> Optional[Result]:
        policy = entry.compiled.policy
        tenant, eid = episode.tenant, episode.episode_id
        for claim in request.claims:
            if claim.kind == "business_fact":
                row = self.store.lookup_reference(claim.reference or "")
                if row is None:
                    return _refused("respond", "provenance_invalid",
                                    f"'{claim.reference}' was never issued; a business fact must cite material "
                                    "the platform supplied")
                if row["tenant"] != tenant:
                    return _refused("respond", "provenance_invalid",
                                    f"'{claim.reference}' belongs to another business")
                if row["episode_id"] != eid:
                    return _refused("respond", "provenance_invalid",
                                    f"'{claim.reference}' was issued to another conversation")
                item = entry.items.get(row["item_id"])
                if item is None or item.source_version != row["source_version"]:
                    return _refused("respond", "provenance_invalid",
                                    f"'{claim.reference}' does not match the version of the material in force")
            elif claim.kind == "general_knowledge":
                if not policy.general_knowledge_allowed:
                    return _refused("respond", "general_knowledge_disabled",
                                    "this business does not allow answers from general knowledge")
            elif claim.kind == "conclusion":
                if claim.conclusion not in policy.conclusions:
                    return _refused("respond", "conclusion_undeclared",
                                    f"the specification does not say whether '{claim.conclusion}' may be concluded")
                if not policy.conclusions[claim.conclusion]:
                    return _refused("respond", "conclusion_forbidden",
                                    f"this business does not permit the conclusion '{claim.conclusion}'")
            elif claim.kind == "action_taken":
                evidence = self.store.get_evidence(claim.evidence or "")
                if (evidence is None or evidence["tenant"] != tenant or evidence["episode_id"] != eid
                        or evidence["kind"] != "effect_verified"):
                    return _refused("respond", "action_without_evidence",
                                    "the reply says something was done, but there is no verified record that it was")
        return None

    def _check_resolution(self, episode: Episode, compiled: CompiledSpecification,
                          request: RespondRequest) -> Optional[Result]:
        res = request.resolution
        policy = compiled.policy
        if res.goal not in policy.goals:
            return _refused("respond", "undeclared_goal", f"'{res.goal}' is not a declared goal")
        tenant, eid = episode.tenant, episode.episode_id
        evidence = {}
        for evidence_id in res.evidence:
            row = self.store.get_evidence(evidence_id)
            if row is None or row["tenant"] != tenant or row["episode_id"] != eid:
                return _refused("respond", "resolution_invalid", f"'{evidence_id}' is not evidence from this conversation; resolution "
                                "evidence takes only evidence ids from results (never a reference id), or none")
            evidence[evidence_id] = row
        if res.served:
            facts = self.store.facts(tenant, eid)
            waived = self.store.waivers(tenant, eid).get(res.goal, set())
            outstanding = [o for o in policy.goals[res.goal].obligations if o not in facts and o not in waived]
            if outstanding:
                return _refused("respond", "resolution_invalid",
                                f"goal '{res.goal}' cannot be served while these are outstanding: "
                                f"{', '.join(outstanding)}")
        if res.authority.startswith("capability:"):
            capability = res.authority.split(":", 1)[1]
            if not any(r["kind"] == "effect_verified" and r["payload"].get("capability") == capability
                       for r in evidence.values()):
                return _refused("respond", "action_without_evidence",
                                f"the resolution rests on '{capability}' but cites no verified record of it")
        return None

    def _respond(self, episode: Episode, entry: _Entry, request: RespondRequest,
                 seq: int) -> tuple[Result, Optional[TurnOutcome]]:
        compiled = entry.compiled
        refusal = self._check_claims(episode, entry, request)
        if refusal is None and request.resolution is not None:
            refusal = self._check_resolution(episode, compiled, request)
        if refusal:
            return refusal, None
        tenant, eid = episode.tenant, episode.episode_id
        self.store.add_evidence(tenant, eid, "reply_claims", {
            "claims": [c.model_dump(mode="json") for c in request.claims],
            "general_knowledge_used": any(c.kind == "general_knowledge" for c in request.claims)}, seq)
        self._expire_confirmations(episode)
        close = False
        if request.resolution is not None:
            res = request.resolution
            with self.store.transaction():
                self.store.set_resolution(tenant, eid, res.goal, res.served, res.authority, list(res.evidence),
                                          {a.name: a.value for a in res.payload})
                self.store.mark_goal_resolved(tenant, eid, res.goal, seq)
            close = not any(state in ("active", "parked") for state in self.store.goals(tenant, eid).values())
        outcome = self._reply(episode, compiled, request.message)
        if close:
            self.store.set_lifecycle(tenant, eid, "closed", close_reason="resolved")
            outcome.lifecycle = "closed"
        return Result(kind="respond", status="ok"), outcome

    # --- escalate ---------------------------------------------------------------------

    def _escalate(self, episode: Episode, compiled: CompiledSpecification, request: EscalateRequest,
                  seq: int) -> tuple[Result, Optional[TurnOutcome]]:
        """The Agent escalates; the Core never does it on the Agent's behalf
        (FR47). An escalation is always delivered — but a reason the
        specification does not declare, or an escalation because the rules are
        silent, is recorded as a specification defect (FR48)."""
        policy = compiled.policy
        tenant, eid = episode.tenant, episode.episode_id
        if request.reason_class == "rules_silent":
            self.store.add_denial(tenant, eid, seq, "spec_defect", "rules_silent", request.summary,
                                  compiled.spec_version)
        elif request.reason_class not in policy.escalation_reasons:
            self.store.add_denial(tenant, eid, seq, "spec_defect", "escalation_reason_undeclared",
                                  f"escalated for '{request.reason_class}', which the specification does not declare",
                                  compiled.spec_version)
        success = policy.escalation_reasons.get(request.reason_class, False)
        goal = request.goal or self.store.get_episode(tenant, eid).active_goal or "unassigned"
        with self.store.transaction():
            evidence_id = self.store.add_evidence(tenant, eid, "escalation", {
                "reason_class": request.reason_class, "summary": request.summary, "is_success": success}, seq)
            self.store.add_outbox(tenant, eid, "escalation", policy.escalation_destination,
                                  f"Handed to a human — reason: {request.reason_class}\n\n{request.summary}\n\n"
                                  f"Interaction: {EPISODE_LINK.format(tenant=tenant, episode_id=eid)}")
            self.store.set_resolution(tenant, eid, goal, success, f"escalation:{request.reason_class}",
                                      [evidence_id], {})
        self._expire_confirmations(episode)
        outcome = self._reply(episode, compiled, request.message)
        self.store.set_lifecycle(tenant, eid, "closed", close_reason="escalated")
        outcome.lifecycle = "closed"
        return Result(kind="escalate", status="ok", evidence_id=evidence_id), outcome

    # --- suspend ----------------------------------------------------------------------

    def _suspend(self, episode: Episode, compiled: CompiledSpecification, request: SuspendRequest,
                 seq: int) -> tuple[Result, Optional[TurnOutcome]]:
        if not request.awaiting.strip():
            return _refused("suspend", "awaiting_unnamed", "a pending episode must name what it is waiting for"), None
        deadline = None
        if request.deadline is not None:
            # Refused now, so a malformed deadline never sits as one that
            # silently never fires. Stored as a UTC instant (a naive one is UTC).
            try:
                instant = parse_instant(request.deadline)
            except ValueError:
                return _refused("suspend", "invalid_deadline",
                                f"{request.deadline!r} is not an ISO 8601 date-time (YYYY-MM-DDTHH:MM, with an "
                                "optional offset; without one it is read as UTC)"), None
            if instant <= parse_instant(self.store.now()):
                return _refused("suspend", "invalid_deadline",
                                f"the deadline has already passed ({request.deadline!r}, now {self.store.now()})"), None
            deadline = instant.isoformat()
        self._expire_confirmations(episode)
        outcome = self._reply(episode, compiled, request.message)
        self.store.set_lifecycle(episode.tenant, episode.episode_id, "pending", awaiting=request.awaiting,
                                 deadline=deadline)
        outcome.lifecycle = "pending"
        return Result(kind="suspend", status="ok"), outcome

    # ==============================================================================
    # Egress and the second exit
    # ==============================================================================

    def _first_message(self, episode: Episode) -> bool:
        return not any(s["kind"] == "egress" for s in self.store.steps(episode.tenant, episode.episode_id))

    def _reply(self, episode: Episode, compiled: CompiledSpecification, text: str,
               kind: str = "reply") -> TurnOutcome:
        """Everything said to the requester leaves through here. The first
        message of every episode carries the business's disclosure (FR112)."""
        body = text.strip()
        if self._first_message(episode):
            body = f"{compiled.policy.disclosure}\n\n{body}"
        tenant, eid = episode.tenant, episode.episode_id
        with self.store.transaction():
            self.store.append_step(tenant, eid, "core", "egress", {"kind": kind, "text": body})
            self.store.add_outbox(tenant, eid, kind, episode.conversation_key, body)
        lifecycle = self.store.get_episode(tenant, eid).lifecycle
        return TurnOutcome(episode_id=eid, lifecycle=lifecycle, messages=[OutboundMessage(
            kind=kind, episode_id=eid, conversation_key=episode.conversation_key, text=body)])

    def _halt(self, episode: Episode, compiled: CompiledSpecification, cause: str, detail: str) -> TurnOutcome:
        """The declared safety halt — the Core's second and only other exit
        (AD-18). The requester is told it has ended, with the business's own
        terminal notice (FR111); the business is told at its escalation
        destination, so the halt is never a database record nobody sees."""
        tenant, eid = episode.tenant, episode.episode_id
        with self.store.transaction():
            seq = self.store.append_step(tenant, eid, "core", "halt", {"cause": cause, "detail": detail})
            self.store.add_evidence(tenant, eid, "halt", {"cause": cause, "detail": detail}, seq)
            self.store.add_outbox(tenant, eid, "halt_notice", compiled.policy.escalation_destination,
                                  f"Conversation ended by the platform — {cause}: {detail}\n\n"
                                  f"Interaction: {EPISODE_LINK.format(tenant=tenant, episode_id=eid)}")
        self._expire_confirmations(episode)
        outcome = self._reply(episode, compiled, compiled.policy.terminal_notice, kind="terminal_notice")
        self.store.set_lifecycle(tenant, eid, "closed", close_reason="halted")
        outcome.lifecycle = "closed"
        outcome.halted = cause
        return outcome

    # ==============================================================================
    # The Agent's view
    # ==============================================================================

    def _assembly(self, episode: Episode) -> str:
        """The context-assembly mode is pinned at episode start, like the specification version (AD-11): a
        restart under a different setting does not change what an episode can reach."""
        for step in self.store.steps(episode.tenant, episode.episode_id):
            if step["kind"] == "references_issued":
                return step["payload"].get("context_assembly", "standing")
        return self.settings.context_assembly

    def _view(self, episode: Episode, entry: _Entry, constraints: tuple[str, ...],
              results: list[tuple[str, Result]], requests_left: int) -> AgentView:
        tenant, eid = episode.tenant, episode.episode_id
        compiled = entry.compiled
        conversation = []
        egressed = False
        for step in self.store.steps(tenant, eid):
            if step["kind"] == "inbound":
                conversation.append(ConversationEntry(role="requester", text=step["payload"]["text"]))
            elif step["kind"] == "egress":
                egressed = True
                conversation.append(ConversationEntry(role="agent", text=step["payload"]["text"]))
            elif step["kind"] == "external_event":
                conversation.append(ConversationEntry(role="external", text=_describe_event(step["payload"])))
        facts = self.store.facts(tenant, eid)
        goals = self.store.goals(tenant, eid)
        waivers = self.store.waivers(tenant, eid)
        obligations = tuple(
            ObligationView(goal=g.id,
                           outstanding=tuple(o for o in g.obligations if o not in facts and o not in waivers.get(g.id, ())),
                           established=tuple(o for o in g.obligations if o in facts),
                           waived=tuple(sorted(waivers.get(g.id, ()))))
            for g in compiled.policy.goals.values())
        references = []
        for row in self.store.references(tenant, eid):
            item = entry.items.get(row["item_id"])
            if item is not None:
                references.append(ProvenanceRef(ref=row["ref"], item_id=item.item_id, title=item.title,
                                                text=item.text))
        current = self.store.get_episode(tenant, eid)
        context, index = compiled.context, ()
        if self._assembly(episode) == "on_demand":
            # The boundary itself holds only the specification projection and what was retrieved; the rest of
            # the material is named by title only, so the Agent knows what it can retrieve (Story 2.3).
            issued = {r.item_id for r in references}
            context = context.model_copy(update={"items": tuple(
                i for i in context.items if i.origin == "specification" or i.item_id in issued)})
            index = tuple(sorted({i.title for i in compiled.context.items
                                  if i.origin == "source" and i.item_id not in issued}))
        return AgentView(
            episode_id=eid, context=context, surface=compiled.surface, references=tuple(references),
            material_index=index,
            conversation=tuple(conversation), facts=tuple(sorted(facts.items())),
            active_goal=current.active_goal,
            parked_goals=tuple(sorted(g for g, s in goals.items() if s == "parked")),
            obligations=obligations,
            offers=tuple(OfferView(offer_id=o["offer_id"], capability=o["capability"], state=o["state"])
                         for o in self.store.offers(tenant, eid)),
            constraints=constraints, turn_results=tuple(results), requests_left=requests_left,
            first_message=not egressed, today=self.store.now()[:10])

    # ==============================================================================
    # Operator actions — recorded, attributable, and never the Agent's
    # ==============================================================================

    def set_suspension(self, tenant: str, *, agent: bool, effects: bool, by: str) -> None:
        """FR110: stop the Agent replying and acting, or only acting. Takes
        effect on the next request; needs no promotion and no deployment."""
        self.registry.live(tenant)
        self.store.set_flags(tenant, agent_suspended=agent, effects_suspended=effects or agent, by=by)

    def decide_approval(self, tenant: str, offer_id: str, *, approve: bool, by: str) -> None:
        """An operator's approval of exactly one payload (FR16 liability gate)."""
        offer = self.store.get_offer(offer_id)
        if offer is None or offer["tenant"] != tenant or offer["gate"] != "operator_approval":
            raise LookupError(f"no operator approval {offer_id} for {tenant}")
        if offer["state"] != "offered":
            raise ValueError(f"approval {offer_id} is already {offer['state']}")
        state = "granted" if approve else "declined"
        self.store.decide_offer(offer_id, state, f"operator:{by}")
        seq = self.store.append_step(tenant, offer["episode_id"], "operator", f"approval_{state}",
                                     {"offer_id": offer_id, "by": by})
        self.store.add_evidence(tenant, offer["episode_id"], f"approval_{state}",
                                {"offer_id": offer_id, "capability": offer["capability"], "by": by}, seq)

    def waive(self, tenant: str, episode_id: str, goal: str, obligation: str, *, by: str) -> None:
        """FR106: an explicit, attributable waiver under a declared authority."""
        episode = self.store.get_episode(tenant, episode_id)
        if episode is None:
            raise LookupError(f"no episode {episode_id} for {tenant}")
        policy = self._entry(tenant, episode.spec_version).compiled.policy
        if goal not in policy.goals or obligation not in policy.goals[goal].waivable:
            raise PermissionError(f"'{obligation}' of '{goal}' is not declared waivable")
        with self.store.transaction():
            self.store.add_waiver(tenant, episode_id, goal, obligation, "operator", by)
            seq = self.store.append_step(tenant, episode_id, "operator", "waiver",
                                         {"goal": goal, "obligation": obligation, "by": by})
            self.store.add_evidence(tenant, episode_id, "waiver",
                                    {"goal": goal, "obligation": obligation, "by": by}, seq)

    def record_external_result(self, tenant: str, episode_id: str, payload: dict) -> str:
        """A result from an external system. After close it is a late result and
        never touches the resolution (FR63)."""
        episode = self.store.get_episode(tenant, episode_id)
        if episode is None:
            raise LookupError(f"no episode {episode_id} for {tenant}")
        if episode.lifecycle == "closed":
            self.store.add_late_result(tenant, episode_id, payload)
            return "late"
        seq = self.store.append_step(tenant, episode_id, "core", "external_result", payload)
        self.store.add_evidence(tenant, episode_id, "external_result", payload, seq)
        return "recorded"

    # ==============================================================================
    # The expiry source — a passed deadline is an external event (FR60, FR61, FR63)
    # ==============================================================================

    @staticmethod
    def _last_wait(steps: list[dict]) -> Optional[tuple[int, Optional[str], Optional[str]]]:
        """``(result seq, awaiting, deadline)`` of the episode's latest
        successful suspend, read from the journal (closing an episode clears
        the episode row's own awaiting and deadline). None if it never waited."""
        decision = None
        wait = None
        for s in steps:
            if s["kind"] == "decision":
                decision = (s["payload"] or {}).get("request") or {}
            elif (s["kind"] == "result" and s["payload"].get("kind") == "suspend"
                  and s["payload"].get("status") == "ok" and decision is not None):
                deadline = decision.get("deadline")
                if deadline is not None:
                    try:
                        deadline = parse_instant(deadline).isoformat()
                    except ValueError:  # a wait recorded before deadlines were validated: kept as written
                        logger.warning("a recorded wait has an unreadable deadline %r", deadline)
                wait = (s["seq"], decision.get("awaiting"), deadline)
        return wait

    def _already_expired(self, tenant: str, episode_id: str, steps: list[dict]) -> bool:
        """Whether the deadline of the episode's latest wait has already been
        delivered — as an event since the wait began, or as a late result."""
        wait = self._last_wait(steps)
        waited = wait[0] if wait else 0
        if any(s["kind"] == "external_event" and s["payload"].get("kind") == DEADLINE_EXPIRED and s["seq"] > waited
               for s in steps):
            return True
        return any(r["payload"].get("kind") == DEADLINE_EXPIRED for r in self.store.late_results(tenant, episode_id))

    async def record_expiry(self, tenant: str, episode_id: str) -> TurnOutcome | str:
        """Deliver the expiry of a pending episode's deadline, read against the
        recorded clock (AD-12). It is recorded as an external-system event and
        the episode resumes: the Agent receives the expiry as its input and its
        request is the next step. The Core itself never replies, escalates or
        closes because of an expiry.

        Returns the turn's outcome when the expiry was delivered, otherwise:
        ``"duplicate"`` (this expiry was already delivered; nothing recorded),
        ``"late"`` (the episode closed after waiting with a deadline; recorded
        as a late result that changes nothing), ``"not_due"`` (no passed
        deadline is outstanding; nothing recorded), ``"unreadable_deadline"``
        (a stored deadline that does not parse; logged, nothing recorded) or
        ``"agent_suspended"`` (an operator has stopped the Agent; nothing
        recorded, so the episode stays pending and due).
        """
        episode = self.store.get_episode(tenant, episode_id)
        if episode is None:
            raise LookupError(f"no episode {episode_id} for {tenant}")
        async with self._lock(tenant, episode.conversation_key):
            episode = self.store.get_episode(tenant, episode_id)  # re-read under the lock
            steps = self.store.steps(tenant, episode_id)
            if self._already_expired(tenant, episode_id, steps):
                return "duplicate"
            if episode.lifecycle == "closed":
                wait = self._last_wait(steps)
                if wait is None or wait[2] is None:
                    return "not_due"
                self.store.add_late_result(tenant, episode_id,
                                           {"kind": DEADLINE_EXPIRED, "awaiting": wait[1], "deadline": wait[2]})
                return "late"
            if episode.lifecycle != "pending":
                return "not_due"
            event = {"kind": DEADLINE_EXPIRED, "awaiting": episode.awaiting, "deadline": episode.deadline}
            try:
                due = _due(episode.deadline, self.store.now())
            except ValueError:
                logger.warning("episode %s/%s has an unreadable deadline %r", tenant, episode_id, episode.deadline)
                return "unreadable_deadline"
            if not due:
                return "not_due"
            entry = self._entry(tenant, episode.spec_version)  # raises UnknownTenant
            agent_suspended, effects_suspended = self.store.flags(tenant)
            if agent_suspended:
                return "agent_suspended"
            with self.store.transaction():
                seq = self.store.append_step(tenant, episode_id, "core", "external_event", event)
                self.store.add_evidence(tenant, episode_id, "external_event", event, seq)
                self.store.append_step(tenant, episode_id, "core", "resumed", {"awaiting": episode.awaiting})
                self.store.set_lifecycle(tenant, episode_id, "active")
            return await self._agent_loop(self.store.get_episode(tenant, episode_id), entry, (), effects_suspended)

    async def expire_due(self) -> list[tuple[str, str, TurnOutcome | str]]:
        """Deliver every passed deadline, across every tenant, once. A method a
        caller invokes — a scenario or a CLI decides when — never a timer.
        Returns ``(tenant, episode_id, outcome)`` per due episode; an episode
        this process holds no specification for is reported as
        ``"unknown_tenant"`` and one whose delivery raised as ``"failed"``,
        never skipped silently."""
        delivered = []
        for episode in self.store.due_pending(self.store.now()):
            try:
                outcome = await self.record_expiry(episode.tenant, episode.episode_id)
            except UnknownTenant:
                logger.warning("expiry for %s/%s: no specification %s is registered", episode.tenant,
                               episode.episode_id, episode.spec_version)
                outcome = "unknown_tenant"
            except Exception:  # one episode's failure must not abort the sweep; it is reported, not hidden
                logger.exception("expiry for %s/%s failed", episode.tenant, episode.episode_id)
                outcome = "failed"
            delivered.append((episode.tenant, episode.episode_id, outcome))
        return delivered
