"""Execution-time authorization for gated tools. Generic — do not edit per
domain (engine file, see ENGINE_FILES in builder_core.py).

A Flow declares WHAT its action is, as a set of properties; the engine derives
WHICH gates that requires, and tool_exec refuses to run a gated tool unless a
platform-owned record proves every required gate was passed for exactly this
payload:

    state_changing -> confirm   (the end user says yes to a read-back)
    liability      -> hitl      (an operator approves via interrupt/resume)

Records live in the AuthorizationLedger, NOT in AgentState. State is written by
nodes that carry model output and by whoever invokes the graph, so a record in
state could be forged by either; the ledger is reachable only through the
engine code that build_pipeline hands it to. Each record is:

  * minted as an OFFER at the moment a human is shown the payload (think asks
    the confirm question; hitl_gate raises the operator interrupt);
  * GRANTED only by that human's own event (intent_detect's deterministic yes;
    an operator resume that names the offer id it approves);
  * CONSUMED once by tool_exec, all required gates together, and only if the
    payload about to run has the same binding digest as the one offered.

A binding is (conversation thread_id, agent id, effective-configuration
fingerprint, flow, tool, canonical args). Any difference — a modified
argument, another conversation, a config edit between the ask and the run —
is a different digest, and the run is refused.

Refusals are typed: `business_refusal` when a human with authority said no
(operator denial); `platform_error` when the platform could not establish
authorization (no record, replay, mismatch, expiry, missing conversation id).
A platform_error must never be phrased to the user as a decision.

Durability: the default ledger is in-process memory. A restart between a
grant and its consumption loses the grant, and the run is REFUSED (fail
closed) — the user is told nothing changed and can retry. A HITL approval
that must survive a restart needs a durable ledger with this interface.
"""

from __future__ import annotations

import hashlib
import json
import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Callable, Dict, FrozenSet, Iterable, Mapping, Optional

logger = logging.getLogger("agent.authz")

# The ONE mapping from a declared action property to the gate it requires.
PROPERTY_GATES: Dict[str, str] = {
    "state_changing": "confirm",
    "liability": "hitl",
}
GATES = frozenset(PROPERTY_GATES.values())

# How long an offered/granted record stays valid. A human answer slower than
# this is refused (platform_error) and the flow is re-asked; it also bounds
# the ledger's size to (records minted per second) x TTL.
DEFAULT_TTL_S = 3600.0

BUSINESS_REFUSAL = "business_refusal"
PLATFORM_ERROR = "platform_error"


class FlowDeclarationError(ValueError):
    """A flow's action properties are malformed or ambiguous. Raised at
    startup (build_pipeline), never at the first gated call."""


@dataclass(frozen=True)
class Refusal:
    kind: str     # BUSINESS_REFUSAL | PLATFORM_ERROR
    reason: str
    gate: str = ""

    def as_dict(self, tool: str = "") -> dict:
        return {"kind": self.kind, "reason": self.reason, "gate": self.gate, "tool": tool}


# ── declaration: properties -> gates ────────────────────────────────────────
def _declared(flow):
    """`properties` as written in the agent's config.py. Flow is defined per
    agent, so an agent whose config.py predates the field has none: that is
    "nothing declared", and its legacy booleans still set the gates."""
    return getattr(flow, "properties", frozenset())


def flow_properties(flow) -> FrozenSet[str]:
    """The flow's effective action properties. `confirm=True` / `hitl=True`
    are the legacy spelling of state_changing / liability; they are folded in
    here — the only place either spelling is read — so a mixed declaration
    can only ADD gates, never cancel one."""
    props = set(_declared(flow))
    if flow.confirm:
        props.add("state_changing")
    if flow.hitl:
        props.add("liability")
    return frozenset(props)


def required_gates(properties: Iterable[str]) -> FrozenSet[str]:
    return frozenset(PROPERTY_GATES[p] for p in properties)


def flow_gates(flow) -> FrozenSet[str]:
    return required_gates(flow_properties(flow))


def preflight_flows(flows: Mapping[str, object]) -> None:
    """Reject misdeclared flows before the agent takes a single call."""
    problems = []
    gated_owner: Dict[str, str] = {}
    tool_flows: Dict[str, list] = {}
    for name, flow in flows.items():
        tool_flows.setdefault(flow.tool, []).append(name)
        props = _declared(flow)
        if not isinstance(props, (set, frozenset)):
            problems.append(f"{name}: properties must be a set of names, "
                            f"got {type(props).__name__} {props!r}")
            continue
        unknown = sorted(p for p in props if p not in PROPERTY_GATES)
        if unknown:
            problems.append(f"{name}: unknown action properties {unknown}; "
                            f"known: {sorted(PROPERTY_GATES)}")
            continue
        if flow_gates(flow):
            gated_owner[flow.tool] = name
    # tool_exec derives the gates from the tool it is about to run, so a gated
    # tool must belong to exactly one flow — otherwise an ungated sibling flow
    # would be a way around the gate.
    for tool, owner in gated_owner.items():
        if len(tool_flows[tool]) > 1:
            problems.append(f"gated tool {tool} is declared by several flows "
                            f"{sorted(tool_flows[tool])}; a gated tool needs one owning flow")
    if problems:
        raise FlowDeclarationError("misdeclared flows: " + "; ".join(problems))


# ── binding ─────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Binding:
    thread_id: str
    agent_id: str
    fingerprint: str
    flow: str
    tool: str
    args_json: str
    digest: str = field(compare=False)


def canonical_args(args: Mapping) -> str:
    """Key-order-independent, whitespace-free JSON. Non-JSON values raise
    TypeError: two payloads that only stringify alike must not share a digest."""
    return json.dumps(dict(args), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass
class _Record:
    offer_id: str
    binding: Binding
    created: float
    granted: bool = False


# ── the ledger ──────────────────────────────────────────────────────────────
class AuthorizationLedger:
    """Platform-owned gate records, one outstanding record per (thread, gate).

    Shared by every conversation the process serves; all mutation happens
    under one lock. Size is bounded by expiry: expired records are pruned on
    every offer."""

    def __init__(self, agent_id: str, fingerprint: str, ttl_s: float = DEFAULT_TTL_S,
                 clock: Callable[[], float] = time.monotonic) -> None:
        self.agent_id = agent_id
        self.fingerprint = fingerprint
        self._ttl_s = ttl_s
        self._clock = clock
        self._lock = threading.Lock()
        self._records: Dict[tuple, _Record] = {}

    def binding(self, thread_id: str, flow: str, tool: str, args: Mapping) -> Binding:
        args_json = canonical_args(args)
        fields = {"thread_id": thread_id, "agent_id": self.agent_id,
                  "fingerprint": self.fingerprint, "flow": flow, "tool": tool,
                  "args": args_json}
        digest = hashlib.sha256(json.dumps(fields, sort_keys=True).encode("utf-8")).hexdigest()
        return Binding(thread_id, self.agent_id, self.fingerprint, flow, tool, args_json, digest)

    def _expired(self, rec: _Record) -> bool:
        return self._clock() - rec.created > self._ttl_s

    def offer(self, gate: str, binding: Binding) -> str:
        """Record that a human is being shown this payload for this gate.
        Idempotent for an identical binding (hitl_gate re-runs on resume and
        must find the SAME offer id it showed); a different binding replaces
        the thread's outstanding offer for the gate."""
        key = (binding.thread_id, gate)
        with self._lock:
            for k in [k for k, r in self._records.items() if self._expired(r)]:
                del self._records[k]
            rec = self._records.get(key)
            if rec is not None and not rec.granted and rec.binding.digest == binding.digest:
                return rec.offer_id
            rec = _Record(uuid.uuid4().hex, binding, self._clock())
            self._records[key] = rec
            return rec.offer_id

    def grant(self, gate: str, thread_id: str, offer_id: Optional[str] = None) -> Optional[Refusal]:
        """The human said yes. `offer_id`, when the gate's channel carries one
        (the operator resume), must name the outstanding offer exactly."""
        with self._lock:
            rec = self._records.get((thread_id, gate))
            if rec is None or rec.granted:
                return Refusal(PLATFORM_ERROR, "no outstanding offer to grant", gate)
            if self._expired(rec):
                del self._records[(thread_id, gate)]
                return Refusal(PLATFORM_ERROR, "offer expired", gate)
            if offer_id is not None and offer_id != rec.offer_id:
                return Refusal(PLATFORM_ERROR, "approval names a different offer", gate)
            rec.granted = True
            return None

    def revoke(self, gate: str, thread_id: str) -> None:
        with self._lock:
            self._records.pop((thread_id, gate), None)

    def consume(self, gates: FrozenSet[str], binding: Binding) -> Optional[Refusal]:
        """All-or-nothing, one-time. Every record touched by the attempt is
        removed whether it succeeds or not: a refused execution burns its
        grants, and the flow must be re-asked."""
        with self._lock:
            refusal = None
            for gate in sorted(gates):
                rec = self._records.pop((binding.thread_id, gate), None)
                if refusal is not None:
                    continue
                if rec is None or not rec.granted:
                    refusal = Refusal(PLATFORM_ERROR, "no granted authorization", gate)
                elif self._expired(rec):
                    refusal = Refusal(PLATFORM_ERROR, "authorization expired", gate)
                elif rec.binding.digest != binding.digest:
                    refusal = Refusal(PLATFORM_ERROR, "authorization is for a different payload", gate)
            return refusal
