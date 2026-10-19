"""The Business Specification schema — what a business can express.

One artifact per business (FR13). It is declarative about *the business*, not
about an agent: identity, goals, obligations, rules, authorities, capabilities,
guards, escalation, refusals, what may and may not be asked, sources, evidence
expectations, evaluation criteria and data lifecycle — the seventeen expression
areas EX1–EX17 of the PRD.

Two properties are enforced by the *shape* of this schema, not by checks run
afterwards:

* **Ordering is unexpressible (FR18).** Every model forbids unknown fields, and
  no field carries a sequence, step, precedence-of-actions or transition. The
  order of entries in any list has no meaning: the canonical form used for the
  version hash sorts them (``studio.spec.loader``), so reordering a file cannot
  change behaviour. The validator's prose check (FR24) is the backstop, not the
  mechanism.
* **An empty area is a recorded absence, never a default (FR14).** Every area
  is optional at the top level; an area that is not written is reported as
  *not established* by the validation suite, and nothing in the Core substitutes
  a default for it.

Nothing here is executable: rules are predicates over named facts in a closed
operator set, so business configuration can never change Core semantics
(FR58, AD-15) or become a programming language (the declared anti-goal).
"""

from __future__ import annotations

import re
from typing import Annotated, Literal, Optional, Union

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, field_validator

_ID = re.compile(r"^[a-z][a-z0-9_]*$")
_TENANT = re.compile(r"^[a-z][a-z0-9-]{1,62}$")

AuthorityClass = Literal["informational", "liability", "state_changing"]
"""FR16 decision authority classes, each gated separately by the Core."""

AuthorityBasis = Literal["requester_self", "verified_identity", "operator_approval"]
"""FR109: how the authority to execute a consequential capability is
established. Never assumed from the channel. ``requester_self`` means the
requester acts only on their own behalf and no existing account is mutated."""

InputType = Literal["string", "integer", "number", "boolean", "date", "time"]
PredicateOp = Literal["eq", "ne", "in", "not_in", "lt", "le", "gt", "ge", "present", "absent", "weekday_in"]
GuardFamily = Literal[
    "urgency", "authorization_failure", "policy_violation",
    "unsupported_request", "identity_problem", "other",
]
CriterionCheck = Literal[
    "no_effect_without_confirmation",
    "every_business_fact_grounded",
    "disclosure_sent_first",
    "escalation_reason_recorded",
    "declared_resolution_or_pending",
]
"""Closed set of machine checks a business criterion may name (EX16).
Criteria without a check are recorded for human judgement only."""


def _check_id(value: str) -> str:
    if not _ID.match(value):
        raise ValueError(f"{value!r} must be lower_snake_case (letters, digits, underscores)")
    return value


Id = Annotated[str, AfterValidator(_check_id)]
"""A lower_snake_case identifier."""


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Business(_Strict):
    tenant: str = Field(description="Tenant identity carried by every record (AD-17).")
    name: str

    @field_validator("tenant")
    @classmethod
    def _tenant(cls, v: str) -> str:
        if not _TENANT.match(v):
            raise ValueError("tenant must be lower-case letters, digits and hyphens, 2-63 characters")
        return v


class Identity(_Strict):
    """EX1 — what the business is, how it speaks, and what it will not say.
    The platform has no default voice: nothing here is ever filled in for a
    business that leaves it empty."""

    description: str
    voice: Optional[str] = None
    will_not_say: tuple[str, ...] = ()
    disclosure: str = Field(description="FR112: told to the requester in the first message.")
    terminal_notice: str = Field(description="FR111: emitted by the Core when an episode is halted.")


class Fact(_Strict):
    """A named piece of information a goal or capability depends on."""

    name: Id
    description: str
    type: InputType = "string"
    sensitive: bool = False


class Goal(_Strict):
    """EX2 — a request the business supports, and what resolving it means.
    EX4 obligations must be established before the goal can resolve; EX5
    diagnostic inputs help the Agent reason and have no fixed sufficient set
    (FR15)."""

    id: Id
    description: str
    resolution: str
    obligations: tuple[str, ...] = ()
    diagnostic_inputs: tuple[str, ...] = ()


class NeverGoal(_Strict):
    """EX3 — what may never become a goal."""

    id: Id
    text: str


class Predicate(_Strict):
    """One condition over a named fact or capability input. Closed operator set:
    a rule can never express computation."""

    fact: str
    op: PredicateOp
    value: Union[str, int, float, bool, tuple[Union[str, int, float], ...], None] = None


class Rule(_Strict):
    """EX6 — eligibility, pricing, timing, policy and constraints.

    ``text`` is what the Agent reads. ``deny_when`` is what the Core enforces:
    when every predicate holds for an effect's arguments (or the episode's
    established facts), the effect is refused as a business refusal. A rule
    with no ``deny_when`` is informational and is enforced by nothing — the
    validator reports it, because prompt text alone is advisory (AD-3)."""

    id: Id
    text: str
    applies_to: tuple[str, ...] = ()
    deny_when: tuple[Predicate, ...] = ()
    always_deny: bool = False


class Conclusion(_Strict):
    """EX7 — a conclusion the Agent may (or may not) draw, and on whose
    authority. FR17: inferring a cause and determining fault are separate
    conclusions, permitted separately."""

    id: Id
    text: str
    authority_class: AuthorityClass = "informational"
    permitted: bool


class CapabilityInput(_Strict):
    name: Id
    type: InputType = "string"
    required: bool = True
    description: str = ""
    fact: Optional[str] = Field(
        default=None,
        description="The fact this input is drawn from; defaults to a fact of the same name.",
    )


class Consequence(_Strict):
    """FR52 — what an operator is actually bounding."""

    reversible: bool
    costs_money: bool
    reaches_customer: bool


class ReadBasis(_Strict):
    """EX8 + T12 (approved 2026-10-19): the read an effect depends on, and how old that read may be when the
    effect is taken (FR35). Declared per contract — never globally."""

    read: Id
    max_age_seconds: int = Field(gt=0)


class Capability(_Strict):
    """EX8 — a granted capability and its contract (FR51).

    ``kind`` maps onto the closed request taxonomy: a ``read`` capability is
    used through a ``read`` request, an ``effect`` capability through an
    ``effect`` request. Nothing here says *when* to use it: that is the
    Agent's decision (FR38)."""

    name: Id
    description: str
    kind: Literal["read", "effect"]
    adapter: str
    operation: str
    inputs: tuple[CapabilityInput, ...] = ()
    authority_class: AuthorityClass = "informational"
    confirmation: bool = False
    consequence: Optional[Consequence] = None
    authority_basis: Optional[AuthorityBasis] = None
    success_evidence: Optional[Literal["read_back"]] = None
    idempotency: Literal["episode", "none"] = "episode"
    on_unverified: Literal["inform_and_escalate", "inform_only"] = "inform_and_escalate"
    freshness: Literal["fresh", "bounded"] = "fresh"
    depends_on: Optional[ReadBasis] = None


class Guard(_Strict):
    """EX9 — a condition that overrides the ordinary path, evaluated before
    the Agent recognises a goal (FR44). Detection may be keyword or model
    based; the verdict binds with exactly two outcomes and never composes a
    reply (AD-21)."""

    id: Id
    family: GuardFamily
    description: str
    detect_keywords: tuple[str, ...] = ()
    verdict: Literal["halt", "constrain"]
    constraint: Optional[str] = Field(
        default=None, description="Typed constraint returned to the Agent when verdict is 'constrain'.")


class EscalationCondition(_Strict):
    id: Id
    text: str
    reason_class: Id
    is_success: bool = Field(default=False, description="FR69: escalation may be a declared success.")


class Escalation(_Strict):
    """EX10 — what this business will not let an Agent decide, and where a
    handed-off episode is delivered (FR103)."""

    destination: str
    conditions: tuple[EscalationCondition, ...] = ()


class Refusal(_Strict):
    """EX11 — refusal conditions."""

    id: Id
    text: str
    reason_class: Id


class NeverAsk(_Strict):
    """EX12 — something that must never be asked. ``facts`` names the facts a
    ``clarify`` request may not ask for; the Core refuses such a request."""

    id: Id
    text: str
    facts: tuple[str, ...] = ()


class Questions(_Strict):
    """EX12 — what may be asked, and what must never be asked."""

    may_ask: tuple[str, ...] = ()
    never_ask: tuple[NeverAsk, ...] = ()


class Prohibition(_Strict):
    """EX13 — what the Agent must not infer or do."""

    id: Id
    text: str
    conclusions: tuple[str, ...] = ()


class Source(_Strict):
    """EX14 — an authoritative source, pinned by content at load (FR30)."""

    id: Id
    path: str
    description: str = ""
    precedence: int = Field(default=100, description="Lower wins when sources conflict (FR31).")


class Grounding(_Strict):
    """EX14 — the knowledge policy: authoritative sources, and whether general
    domain knowledge from the model may be used at all (FR34)."""

    sources: tuple[Source, ...] = ()
    general_knowledge_allowed: bool = False


class EvidencePolicy(_Strict):
    """EX15 — what evidence is required, and what happens when it is absent.
    Per-capability ``success_evidence``/``on_unverified`` carry the detail;
    this records the business-wide statement."""

    statement: str


class Criterion(_Strict):
    """EX16 — what good looks like here."""

    id: Id
    text: str
    blocking: bool = False
    check: Optional[CriterionCheck] = None


class Evaluation(_Strict):
    criteria: tuple[Criterion, ...] = ()
    refusal_sample_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="FR115.")


class DataLifecycle(_Strict):
    """EX17 — captured in V1; the executor is deferred (AD-25, NFR10)."""

    retention_days: Optional[int] = Field(default=None, ge=1)
    delete_on_request: bool = True


class Waiver(_Strict):
    """FR106 — an obligation that may be waived, and by which authority."""

    goal: str
    obligation: str
    authority: Literal["operator"] = "operator"


class BusinessSpecification(_Strict):
    """The single artifact (FR13). Top-level areas are optional so that an
    unwritten area is a recorded absence (FR14), never a silent default."""

    business: Business
    identity: Optional[Identity] = None                    # EX1
    facts: tuple[Fact, ...] = ()
    goals: tuple[Goal, ...] = ()                           # EX2, EX4, EX5
    never_goals: tuple[NeverGoal, ...] = ()                # EX3
    rules: tuple[Rule, ...] = ()                           # EX6
    conclusions: tuple[Conclusion, ...] = ()               # EX7
    capabilities: tuple[Capability, ...] = ()              # EX8
    guards: tuple[Guard, ...] = ()                         # EX9
    escalation: Optional[Escalation] = None                # EX10
    refusals: tuple[Refusal, ...] = ()                     # EX11
    questions: Optional[Questions] = None                  # EX12
    prohibitions: tuple[Prohibition, ...] = ()             # EX13
    grounding: Optional[Grounding] = None                  # EX14
    evidence: Optional[EvidencePolicy] = None              # EX15
    evaluation: Optional[Evaluation] = None                # EX16
    data_lifecycle: Optional[DataLifecycle] = None         # EX17
    waivers: tuple[Waiver, ...] = ()


EXPRESSION_AREAS: dict[str, tuple[str, str]] = {
    "EX1": ("identity", "Identity — what the business is, how it speaks, what it will not say"),
    "EX2": ("goals", "Goals and what resolving each means"),
    "EX3": ("never_goals", "What may never become a goal"),
    "EX4": ("goals.obligations", "What must be established before each outcome or action"),
    "EX5": ("goals.diagnostic_inputs", "What helps the Agent reason without being required"),
    "EX6": ("rules", "Rules — eligibility, pricing, timing, policy, constraints"),
    "EX7": ("conclusions", "What the Agent may conclude, and on whose authority"),
    "EX8": ("capabilities", "Which capabilities are granted, under what contract"),
    "EX9": ("guards", "Guard conditions"),
    "EX10": ("escalation", "Escalation — what this business will not let an Agent decide"),
    "EX11": ("refusals", "Refusal conditions"),
    "EX12": ("questions", "What may be asked, and what must never be asked"),
    "EX13": ("prohibitions", "What the Agent must not infer or do"),
    "EX14": ("grounding", "Authoritative sources and their precedence"),
    "EX15": ("evidence", "What evidence is required, and what happens when it is absent"),
    "EX16": ("evaluation", "What good looks like here"),
    "EX17": ("data_lifecycle", "Data-lifecycle requirements"),
}
"""The PRD's expression surface, mapped to schema locations. Every area is
separately addressable, reviewable and checkable (FR14)."""


def area_established(spec: BusinessSpecification, area: str) -> bool:
    """Whether an expression area was written. Absence is never a default."""
    if area == "EX4":
        return any(g.obligations for g in spec.goals)
    if area == "EX5":
        return any(g.diagnostic_inputs for g in spec.goals)
    value = getattr(spec, EXPRESSION_AREAS[area][0])
    if value is None:
        return False
    if isinstance(value, tuple):
        return len(value) > 0
    if isinstance(value, Questions):
        return bool(value.may_ask or value.never_ask)
    if isinstance(value, Grounding):
        return bool(value.sources)
    if isinstance(value, Evaluation):
        return bool(value.criteria)
    return True
