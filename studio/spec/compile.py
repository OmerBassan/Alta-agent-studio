"""The Core's specification compiler — one artifact, three projections (AD-4).

From a single validated Business Specification the Core compiles:

* the **agent context** — what the Agent reads: identity, goals, obligations,
  rules, conclusions, what may and may not be asked, escalation and refusal
  conditions, and the authoritative context items it may cite;
* the **capability surface** — the tools offered to the model;
* the **policy** — what the Core enforces.

Because all three come from one artifact, the Agent is never told it may do
something the Core will always refuse (AD-4); the validation suite blocks a
specification in which that could happen (FR23). The Builder produces the
artifact and never compiles it. ``COMPILER_VERSION`` is pinned into every
episode alongside the specification version (AD-11).

The compiler is Core code, but it lives beside the schema it reads so the
dependency points inward: ``studio.core`` imports it; it imports nothing from
``studio.core``.
"""

from __future__ import annotations

from typing import Literal, Optional, Union

from pydantic import BaseModel, ConfigDict

from studio.spec.findings import SpecificationError
from studio.spec.loader import LoadedSpecification, heading_key
from studio.spec.model import AuthorityBasis, AuthorityClass, Consequence, GuardFamily, InputType
from studio.spec.validate import ValidationReport, validate

COMPILER_VERSION = "1"


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True)


# --- agent context -------------------------------------------------------------

class ContextItem(_Frozen):
    """One piece of authoritative business context. The Core issues a
    provenance reference per item per episode (AD-7); the Agent cites the
    reference, never the locator itself."""

    item_id: str
    origin: Literal["specification", "source"]
    source_id: str
    source_version: str
    locator: str
    title: str
    text: str
    precedence: int
    superseded_by: Optional[str] = None
    """Story 2.4 (T11): another item under the same heading outranks this one — a source of lower declared
    precedence, or the specification itself, which outranks every source. Citing a superseded item is refused."""


class GoalView(_Frozen):
    id: str
    description: str
    resolution: str
    obligations: tuple[str, ...]
    diagnostic_inputs: tuple[str, ...]


class FactView(_Frozen):
    name: str
    description: str
    type: InputType


class TextItem(_Frozen):
    id: str
    text: str


class ConclusionView(_Frozen):
    id: str
    text: str
    permitted: bool


class ReasonView(_Frozen):
    reason_class: str
    text: str


class NeverAskView(_Frozen):
    text: str
    facts: tuple[str, ...]


class AgentContext(_Frozen):
    tenant: str
    business_name: str
    description: str
    voice: Optional[str]
    will_not_say: tuple[str, ...]
    goals: tuple[GoalView, ...]
    never_goals: tuple[str, ...]
    facts: tuple[FactView, ...]
    rules: tuple[TextItem, ...]
    conclusions: tuple[ConclusionView, ...]
    prohibitions: tuple[str, ...]
    may_ask: tuple[str, ...]
    never_ask: tuple[NeverAskView, ...]
    escalation_conditions: tuple[ReasonView, ...]
    refusals: tuple[ReasonView, ...]
    general_knowledge_allowed: bool
    items: tuple[ContextItem, ...]


# --- capability surface ---------------------------------------------------------

class ToolInput(_Frozen):
    name: str
    type: InputType
    required: bool
    description: str


class ToolDefinition(_Frozen):
    name: str
    kind: Literal["read", "effect"]
    description: str
    inputs: tuple[ToolInput, ...]
    confirmation_required: bool
    consequence: Optional[Consequence]
    depends_on_read: Optional[str] = None
    """T12: the read this effect needs, recent enough, in the same conversation."""


class CapabilitySurface(_Frozen):
    tools: tuple[ToolDefinition, ...]

    def names(self) -> frozenset[str]:
        return frozenset(t.name for t in self.tools)


# --- policy -------------------------------------------------------------------

class PredicatePolicy(_Frozen):
    fact: str
    op: str
    value: Union[str, int, float, bool, tuple[Union[str, int, float], ...], None]


class DenyRule(_Frozen):
    rule_id: str
    text: str
    predicates: tuple[PredicatePolicy, ...]
    always: bool


class InputPolicy(_Frozen):
    name: str
    type: InputType
    required: bool
    fact: str


class CapabilityPolicy(_Frozen):
    name: str
    kind: Literal["read", "effect"]
    adapter: str
    operation: str
    inputs: tuple[InputPolicy, ...]
    authority_class: AuthorityClass
    confirmation: bool
    authority_basis: Optional[AuthorityBasis]
    success_evidence: Optional[str]
    idempotent: bool
    retry_eligible: bool
    on_unverified: str
    freshness: str
    deny_rules: tuple[DenyRule, ...]
    depends_on_read: Optional[str] = None
    max_basis_age_s: Optional[int] = None


class GuardPolicy(_Frozen):
    id: str
    family: GuardFamily
    keywords: tuple[str, ...]
    verdict: Literal["halt", "constrain"]
    constraint: Optional[str]


class GoalPolicy(_Frozen):
    id: str
    obligations: tuple[str, ...]
    diagnostic_inputs: tuple[str, ...]
    waivable: tuple[str, ...]


class Policy(_Frozen):
    tenant: str
    capabilities: dict[str, CapabilityPolicy]
    goals: dict[str, GoalPolicy]
    facts: dict[str, InputType]
    never_ask_facts: frozenset[str]
    conclusions: dict[str, bool]
    general_knowledge_allowed: bool
    guards: tuple[GuardPolicy, ...]
    escalation_destination: str
    escalation_reasons: dict[str, bool]
    """reason_class -> whether escalating for it is a declared success (FR69)."""
    refusal_reasons: frozenset[str]
    disclosure: str
    terminal_notice: str
    refusal_sample_rate: float


class CompiledSpecification(_Frozen):
    tenant: str
    spec_version: str
    compiler_version: str
    context: AgentContext
    surface: CapabilitySurface
    policy: Policy


def _items(loaded: LoadedSpecification) -> tuple[ContextItem, ...]:
    spec, version = loaded.spec, loaded.version
    items: list[ContextItem] = []

    def add_spec(locator: str, title: str, text: str) -> None:
        items.append(ContextItem(item_id=f"spec:{locator}", origin="specification", source_id="specification",
                                 source_version=version, locator=locator, title=title, text=text, precedence=0))

    if spec.identity:
        add_spec("identity", "About the business", spec.identity.description)
    for g in spec.goals:
        add_spec(f"goals/{g.id}", g.description, g.resolution)
    for r in spec.rules:
        add_spec(f"rules/{r.id}", f"Rule: {r.id}", r.text)
    for doc in sorted(loaded.sources.values(), key=lambda d: (d.precedence, d.id)):
        for section in doc.sections:
            items.append(ContextItem(item_id=f"src:{section.locator}", origin="source", source_id=doc.id,
                                     source_version=doc.content_hash, locator=section.locator,
                                     title=section.heading or doc.id, text=section.text, precedence=doc.precedence))
    return _resolve_precedence(items)


def _resolve_precedence(items: list[ContextItem]) -> tuple[ContextItem, ...]:
    """A conflict is the same heading in two places (T11). The specification outranks every source; between
    sources, the lower declared precedence wins. Equal precedence is a validation finding, not resolved here."""
    by_heading: dict[str, list[ContextItem]] = {}
    for item in items:
        by_heading.setdefault(heading_key(item.title), []).append(item)
    out = []
    for item in items:
        if item.origin == "source":
            stronger = [o for o in by_heading[heading_key(item.title)] if o.item_id != item.item_id
                        and o.text.strip() != item.text.strip() and (  # saying the same thing is no conflict
                o.origin == "specification" or (o.source_id != item.source_id and o.precedence < item.precedence))]
            if stronger:
                winner = min(stronger, key=lambda o: (o.origin != "specification", o.precedence, o.item_id))
                item = item.model_copy(update={"superseded_by": winner.item_id})
        out.append(item)
    return tuple(out)


def compile_specification(loaded: LoadedSpecification,
                          report: Optional[ValidationReport] = None) -> CompiledSpecification:
    """Compile a specification that has passed the validation suite.

    Raises ``SpecificationError`` carrying the blocking findings otherwise:
    there is exactly one gate, and nothing that fails it can be run (FR22)."""
    report = report or validate(loaded)
    if not report.passed:
        raise SpecificationError(list(report.blocking))
    spec = loaded.spec
    assert spec.identity and spec.escalation  # guaranteed by the required-area checks
    facts = {f.name: f for f in spec.facts}
    questions = spec.questions
    grounding = spec.grounding

    context = AgentContext(
        tenant=spec.business.tenant,
        business_name=spec.business.name,
        description=spec.identity.description,
        voice=spec.identity.voice,
        will_not_say=spec.identity.will_not_say,
        goals=tuple(GoalView(id=g.id, description=g.description, resolution=g.resolution,
                             obligations=g.obligations, diagnostic_inputs=g.diagnostic_inputs)
                    for g in sorted(spec.goals, key=lambda g: g.id)),
        never_goals=tuple(n.text for n in spec.never_goals),
        facts=tuple(FactView(name=f.name, description=f.description, type=f.type)
                    for f in sorted(spec.facts, key=lambda f: f.name)),
        rules=tuple(TextItem(id=r.id, text=r.text) for r in sorted(spec.rules, key=lambda r: r.id)),
        conclusions=tuple(ConclusionView(id=c.id, text=c.text, permitted=c.permitted)
                          for c in sorted(spec.conclusions, key=lambda c: c.id)),
        prohibitions=tuple(p.text for p in spec.prohibitions),
        may_ask=questions.may_ask if questions else (),
        never_ask=tuple(NeverAskView(text=n.text, facts=n.facts) for n in (questions.never_ask if questions else ())),
        escalation_conditions=tuple(ReasonView(reason_class=e.reason_class, text=e.text)
                                    for e in spec.escalation.conditions),
        refusals=tuple(ReasonView(reason_class=r.reason_class, text=r.text) for r in spec.refusals),
        general_knowledge_allowed=bool(grounding and grounding.general_knowledge_allowed),
        items=_items(loaded),
    )

    surface = CapabilitySurface(tools=tuple(
        ToolDefinition(
            name=c.name, kind=c.kind, description=c.description,
            inputs=tuple(ToolInput(name=i.name, type=i.type, required=i.required,
                                   description=i.description or facts[i.fact or i.name].description)
                         for i in c.inputs),
            confirmation_required=c.confirmation, consequence=c.consequence,
            depends_on_read=c.depends_on.read if c.depends_on else None)
        for c in sorted(spec.capabilities, key=lambda c: c.name)))

    capabilities = {}
    for c in spec.capabilities:
        rules = tuple(
            DenyRule(rule_id=r.id, text=r.text, always=r.always_deny,
                     predicates=tuple(PredicatePolicy(fact=p.fact, op=p.op, value=p.value) for p in r.deny_when))
            for r in sorted(spec.rules, key=lambda r: r.id)
            if c.name in r.applies_to and (r.deny_when or r.always_deny))
        capabilities[c.name] = CapabilityPolicy(
            name=c.name, kind=c.kind, adapter=c.adapter, operation=c.operation,
            inputs=tuple(InputPolicy(name=i.name, type=i.type, required=i.required, fact=i.fact or i.name)
                         for i in c.inputs),
            authority_class=c.authority_class, confirmation=c.confirmation, authority_basis=c.authority_basis,
            success_evidence=c.success_evidence, idempotent=c.idempotency == "episode",
            retry_eligible=c.idempotency == "episode", on_unverified=c.on_unverified,
            freshness=c.freshness, deny_rules=rules,
            depends_on_read=c.depends_on.read if c.depends_on else None,
            max_basis_age_s=c.depends_on.max_age_seconds if c.depends_on else None)

    waivable: dict[str, list[str]] = {}
    for w in spec.waivers:
        waivable.setdefault(w.goal, []).append(w.obligation)

    policy = Policy(
        tenant=spec.business.tenant,
        capabilities=capabilities,
        goals={g.id: GoalPolicy(id=g.id, obligations=g.obligations, diagnostic_inputs=g.diagnostic_inputs,
                                waivable=tuple(waivable.get(g.id, ()))) for g in spec.goals},
        facts={f.name: f.type for f in spec.facts},
        never_ask_facts=frozenset(f for n in (questions.never_ask if questions else ()) for f in n.facts),
        conclusions={c.id: c.permitted for c in spec.conclusions},
        general_knowledge_allowed=context.general_knowledge_allowed,
        guards=tuple(GuardPolicy(id=g.id, family=g.family, keywords=tuple(k.lower() for k in g.detect_keywords),
                                 verdict=g.verdict, constraint=g.constraint) for g in spec.guards),
        escalation_destination=spec.escalation.destination,
        escalation_reasons={e.reason_class: e.is_success for e in spec.escalation.conditions},
        refusal_reasons=frozenset(r.reason_class for r in spec.refusals),
        disclosure=spec.identity.disclosure,
        terminal_notice=spec.identity.terminal_notice,
        refusal_sample_rate=spec.evaluation.refusal_sample_rate if spec.evaluation else 0.0,
    )
    return CompiledSpecification(tenant=spec.business.tenant, spec_version=loaded.version,
                                 compiler_version=COMPILER_VERSION, context=context, surface=surface, policy=policy)
