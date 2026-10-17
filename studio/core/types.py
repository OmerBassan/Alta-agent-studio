"""The closed request taxonomy and the typed results the Core returns.

The Agent emits exactly one of seven request kinds (AD-2, FR40): ``retrieve``,
``read``, ``effect``, ``clarify``, ``respond``, ``escalate``, ``suspend``. The set
is closed in both directions: a business grants capabilities *over* these kinds
and can never add one. The kinds carry no precedence and no order.

Every request is authorized and journaled, reads included. Every outcome
returns to the Agent as a typed ``Result`` — or the episode ends in a declared
safety halt (AD-18). Requests carry no channel information (AD-16, FR83).

Model output is untrusted input: requests are parsed and validated here before
the Core looks at them, and a request that does not parse is itself a typed
result, never an exception that escapes the loop.
"""

from __future__ import annotations

from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from studio.core.vocabulary import Classification, Reason

Scalar = Union[str, int, float, bool, None]


class _Req(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Argument(_Req):
    """A named value. Lists of pairs, never free-keyed objects, so the schema
    stays valid for strict structured output (DL-037)."""

    name: str
    value: Scalar


class FactUpdate(_Req):
    """A fact the Agent reports having established from the requester. The
    Core validates the name and type and records it with the step it came
    from; the Core is the only writer of episode state (AD-13)."""

    name: str
    value: Scalar


class _Common(_Req):
    goal: Optional[str] = Field(default=None, description="The declared goal this request pursues (FR49, FR50).")
    facts: tuple[FactUpdate, ...] = ()


class RetrieveRequest(_Common):
    kind: Literal["retrieve"] = "retrieve"
    query: str


class ReadRequest(_Common):
    kind: Literal["read"] = "read"
    capability: str
    arguments: tuple[Argument, ...] = ()


class EffectRequest(_Common):
    kind: Literal["effect"] = "effect"
    capability: str
    arguments: tuple[Argument, ...] = ()


class ConfirmProposal(_Req):
    """The exact payload the Agent is asking the requester to confirm. The Core
    records an offer bound to it; only the requester's own reply grants it."""

    capability: str
    arguments: tuple[Argument, ...] = ()


class ClarifyRequest(_Common):
    kind: Literal["clarify"] = "clarify"
    message: str
    asks_for: tuple[str, ...] = ()
    confirm: Optional[ConfirmProposal] = None


ClaimKind = Literal["business_fact", "general_knowledge", "conclusion", "action_taken"]


class Claim(_Req):
    """Something the reply asserts, typed so the Core can check it (AD-7).

    * ``business_fact`` names a provenance reference the Core issued to this
      episode. The Agent can neither mint nor alter one.
    * ``general_knowledge`` is allowed only if the business permits it, and is
      marked as such in the record (FR34).
    * ``conclusion`` names a declared conclusion; forbidden ones are refused (FR17).
    * ``action_taken`` names Core evidence of a verified effect (FR71).
    """

    kind: ClaimKind
    text: str
    reference: Optional[str] = None
    conclusion: Optional[str] = None
    evidence: Optional[str] = None


class ResolutionClaim(_Req):
    """The fixed resolution envelope (AD-20, FR68): which goal, whether it was
    served, under which authority, on what evidence, plus a business payload.
    The enumeration of resolution kinds is deliberately not fixed (O4)."""

    goal: str
    served: bool
    authority: str
    evidence: tuple[str, ...] = ()
    payload: tuple[Argument, ...] = ()


class RespondRequest(_Common):
    kind: Literal["respond"] = "respond"
    message: str
    claims: tuple[Claim, ...] = ()
    resolution: Optional[ResolutionClaim] = None


class EscalateRequest(_Common):
    kind: Literal["escalate"] = "escalate"
    reason_class: str
    summary: str
    message: str = Field(description="What the requester is told.")


class SuspendRequest(_Common):
    kind: Literal["suspend"] = "suspend"
    awaiting: str = Field(description="The named external input the episode waits for (FR60).")
    message: str
    deadline: Optional[str] = None


AgentRequest = Annotated[
    Union[RetrieveRequest, ReadRequest, EffectRequest, ClarifyRequest, RespondRequest, EscalateRequest,
          SuspendRequest],
    Field(discriminator="kind"),
]

TURN_ENDING_KINDS = frozenset({"clarify", "respond", "escalate", "suspend"})
"""Kinds that, once accepted, produce a message to the requester. This is a
property of what the request *is*, not an order the Core imposes: the Agent
chooses which kind to emit, and when."""


class Denial(BaseModel):
    model_config = ConfigDict(frozen=True)

    classification: Classification
    reason: Reason
    detail: str
    rule: Optional[str] = None
    """The specification rule that refused it, when a rule did (EX6)."""


class Result(BaseModel):
    """The typed result of one request — the Core's first exit (AD-18)."""

    model_config = ConfigDict(frozen=True)

    kind: str
    status: Literal["ok", "refused", "failed"]
    capability: Optional[str] = None
    denial: Optional[Denial] = None
    data: tuple[Argument, ...] = ()
    items: tuple[dict, ...] = ()
    evidence_id: Optional[str] = None
    verified: Optional[bool] = None
    offer_id: Optional[str] = None
    note: Optional[str] = None
