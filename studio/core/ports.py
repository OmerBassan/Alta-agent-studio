"""The Core's ports. Everything outside the Core plugs in here (AD-9).

Dependencies point inward: the agent runtime, the adapters and the channel
adapters implement these protocols; the Core imports none of them.

* ``AgentRuntime`` — the runtime boundary we own (AD-14). The Agent receives a
  read-only ``AgentView`` and returns one request. It never receives the store,
  an adapter, or anything it could use to reach outside the Core (FR41).
* ``Adapter`` — Core contract → adapter → extension (FR56). Adapters receive a
  Core-issued idempotency key (AD-10) and expose a read-back so success is
  evidenced, not asserted (FR51, AD-6).
* ``InboundMessage`` / ``OutboundMessage`` — what a channel adapter hands the
  Core and receives back. Neither carries a channel field (AD-16, FR83).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional, Protocol

from pydantic import BaseModel, ConfigDict

from studio.core.types import AgentRequest, Result
from studio.spec.compile import AgentContext, CapabilitySurface


class _F(BaseModel):
    model_config = ConfigDict(frozen=True)


# --- channel ---------------------------------------------------------------------

class InboundMessage(_F):
    tenant: str
    conversation_key: str
    """The channel's own correlation key (an email thread id, a chat id). The
    Core maps it to an episode; it never learns what channel it came from."""
    message_id: str
    """Unique per logical message, so a re-send is processed once (FR87)."""
    text: str
    received_at: Optional[datetime] = None


class OutboundMessage(_F):
    kind: Literal["reply", "terminal_notice"]
    episode_id: str
    conversation_key: str
    text: str


# --- agent runtime ---------------------------------------------------------------

class ConversationEntry(_F):
    role: Literal["requester", "agent"]
    text: str


class ProvenanceRef(_F):
    """A Core-issued reference to one authoritative context item, valid only
    for the episode it was issued to (AD-7)."""

    ref: str
    item_id: str
    title: str
    text: str


class ObligationView(_F):
    goal: str
    outstanding: tuple[str, ...]
    established: tuple[str, ...]
    waived: tuple[str, ...]


class OfferView(_F):
    offer_id: str
    capability: str
    state: Literal["offered", "granted", "declined", "consumed", "expired"]


class AgentView(_F):
    """Everything the Agent may read for one decision. Built by the Core."""

    episode_id: str
    context: AgentContext
    surface: CapabilitySurface
    references: tuple[ProvenanceRef, ...]
    conversation: tuple[ConversationEntry, ...]
    facts: tuple[tuple[str, Any], ...]
    active_goal: Optional[str]
    parked_goals: tuple[str, ...]
    obligations: tuple[ObligationView, ...]
    offers: tuple[OfferView, ...]
    constraints: tuple[str, ...]
    """Typed constraints returned by guards this turn (AD-21)."""
    turn_results: tuple[tuple[str, Result], ...]
    """``(request kind, result)`` for every request already handled this turn."""
    requests_left: int
    first_message: bool
    """True when nothing has yet been sent to the requester in this episode."""
    today: Optional[str] = None
    """The Core's recorded date (AD-12), so the Agent can resolve "Monday"."""


class ModelCall(_F):
    model: str
    ok: bool
    path: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    latency_ms: float = 0.0
    error: Optional[str] = None


class AgentDecision(_F):
    """One request, or the reason none could be produced.

    ``request`` is None only when the runtime could not produce a valid request
    (for example the model's output failed validation); ``error`` says why. The
    Core turns that into a typed result rather than letting it escape."""

    request: Optional[AgentRequest] = None
    error: Optional[str] = None
    model_calls: tuple[ModelCall, ...] = ()


class AgentRuntime(Protocol):
    name: str

    async def decide(self, view: AgentView) -> AgentDecision: ...


# --- extensions ------------------------------------------------------------------

class AdapterResult(_F):
    ok: bool
    data: tuple[tuple[str, Any], ...] = ()
    reference: Optional[str] = None
    """The external system's own identifier for what was done — the join key
    into the system of record (FR86, CONV seam 1)."""
    error: Optional[str] = None


class Adapter(Protocol):
    """A leaf behind a declared contract (FR59). Adapter code may block; the
    Core runs it off the request loop and bounds it by a timeout (FR97)."""

    name: str

    def read(self, tenant: str, operation: str, arguments: dict[str, Any]) -> AdapterResult: ...

    def effect(self, tenant: str, operation: str, arguments: dict[str, Any], idempotency_key: str) -> AdapterResult: ...

    def read_back(self, tenant: str, operation: str, arguments: dict[str, Any], idempotency_key: str,
                  reference: Optional[str]) -> AdapterResult: ...
