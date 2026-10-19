"""The validation suite — the one gate in front of promotion and deployment.

Platform-owned, domain-agnostic and derived from the specification (FR95): no
check here names a business, and none is authored by the Builder it gates.
Platform invariants are *blocking*; everything else is a *warning*. A check
whose shape a business lacks adapts or skips rather than failing. The suite is
never stubbed to pass: a passing result means every blocking check actually
ran (FR22, FR25).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from studio.spec.findings import Finding
from studio.spec.loader import LoadedSpecification, heading_key
from studio.spec.model import EXPRESSION_AREAS, BusinessSpecification, Capability, area_established

REQUIRED_AREAS = {
    "EX1": "Without an identity there is no disclosure wording and no terminal notice, and the Agent "
           "cannot be put in front of a requester (FR111, FR112).",
    "EX2": "Without at least one goal the Agent has nothing it is permitted to pursue (FR49).",
    "EX10": "Without an escalation destination a handed-off request arrives nowhere (FR103).",
    "EX14": "Without an authoritative source no business fact can be grounded (FR32).",
}
"""Areas whose absence makes the Agent inoperable, so their absence blocks.
Every other unwritten area is reported as not established, without blocking."""

VERBS = frozenset({
    "add", "book", "cancel", "change", "check", "close", "confirm", "create", "extend", "find",
    "freeze", "get", "hold", "issue", "list", "look", "lookup", "open", "place", "quote", "record",
    "refund", "register", "release", "remove", "request", "reschedule", "reserve", "schedule",
    "send", "submit", "unfreeze", "update", "verify", "waive",
})

_SEQUENCING_PROSE = [
    (re.compile(r"\bstep\s*\d", re.I), "numbered steps"),
    (re.compile(r"\bfirst\b[^.]{0,120}\bthen\b", re.I), "'first … then'"),
    (re.compile(r"\b(and\s+)?then\s+(ask|check|book|confirm|send|offer|call|move on)\b", re.I), "'then <do something>'"),
    (re.compile(r"\bafter\s+(that|this)\b", re.I), "'after that'"),
    (re.compile(r"\bonce\s+(that|this)\s+is\s+done\b", re.I), "'once that is done'"),
    (re.compile(r"\bnext,", re.I), "'next,'"),
]
"""Backstop only (FR24). The schema is the mechanism that makes ordering
unexpressible; this catches ordering smuggled into prose, which would reach the
Agent as an instruction and be invisible to audit."""


@dataclass(frozen=True)
class ValidationReport:
    findings: tuple[Finding, ...]

    @property
    def passed(self) -> bool:
        return not any(f.severity == "blocking" for f in self.findings)

    @property
    def blocking(self) -> tuple[Finding, ...]:
        return tuple(f for f in self.findings if f.severity == "blocking")


def _prose_fields(spec: BusinessSpecification):
    """Every free-text field that reaches the Agent, with its location."""
    if spec.identity:
        yield "identity.description", spec.identity.description, "EX1"
        if spec.identity.voice:
            yield "identity.voice", spec.identity.voice, "EX1"
    for g in spec.goals:
        yield f"goals.{g.id}.description", g.description, "EX2"
        yield f"goals.{g.id}.resolution", g.resolution, "EX2"
    for r in spec.rules:
        yield f"rules.{r.id}.text", r.text, "EX6"
    for c in spec.capabilities:
        yield f"capabilities.{c.name}.description", c.description, "EX8"
    if spec.escalation:
        for e in spec.escalation.conditions:
            yield f"escalation.conditions.{e.id}.text", e.text, "EX10"
    for r in spec.refusals:
        yield f"refusals.{r.id}.text", r.text, "EX11"
    for p in spec.prohibitions:
        yield f"prohibitions.{p.id}.text", p.text, "EX13"


def _check_absent_areas(spec: BusinessSpecification) -> list[Finding]:
    out = []
    for area, (_, label) in EXPRESSION_AREAS.items():
        if area_established(spec, area):
            continue
        if area in REQUIRED_AREAS:
            out.append(Finding(code="area_not_established", severity="blocking", area=area,
                               message=f"{label}: not established. {REQUIRED_AREAS[area]}"))
        else:
            out.append(Finding(code="area_not_established", severity="warning", area=area,
                               message=f"{label}: not established. This is recorded as an absence; "
                                       "nothing is assumed in its place."))
    if spec.identity:
        for fld, req in (("disclosure", "FR112"), ("terminal_notice", "FR111")):
            if not getattr(spec.identity, fld).strip():
                out.append(Finding(code="area_not_established", severity="blocking", area="EX1",
                                   location=f"identity.{fld}",
                                   message=f"identity.{fld} is empty; it is required ({req})."))
    if spec.escalation and not spec.escalation.destination.strip():
        out.append(Finding(code="area_not_established", severity="blocking", area="EX10",
                           location="escalation.destination",
                           message="The escalation destination is empty, so escalations would arrive nowhere (FR103)."))
    return out


def _check_unique(spec: BusinessSpecification) -> list[Finding]:
    out = []
    groups = {
        "facts": [f.name for f in spec.facts], "goals": [g.id for g in spec.goals],
        "rules": [r.id for r in spec.rules], "conclusions": [c.id for c in spec.conclusions],
        "capabilities": [c.name for c in spec.capabilities], "guards": [g.id for g in spec.guards],
        "refusals": [r.id for r in spec.refusals], "prohibitions": [p.id for p in spec.prohibitions],
        "sources": [s.id for s in (spec.grounding.sources if spec.grounding else ())],
    }
    for group, ids in groups.items():
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        for d in dupes:
            out.append(Finding(code="duplicate_id", severity="blocking", location=f"{group}.{d}",
                               message=f"'{d}' is declared more than once in {group}."))
    return out


def _check_references(loaded: LoadedSpecification) -> list[Finding]:
    spec = loaded.spec
    facts = {f.name for f in spec.facts}
    caps = {c.name: c for c in spec.capabilities}
    conclusions = {c.id for c in spec.conclusions}
    goals = {g.id: g for g in spec.goals}
    out = []

    def missing(kind: str, name: str, where: str, area: str) -> None:
        out.append(Finding(code="unresolved_reference", severity="blocking", area=area, location=where,
                           message=f"{where} refers to {kind} '{name}', which is not declared."))

    for c in spec.capabilities:
        if c.depends_on is None:
            continue
        where = f"capabilities.{c.name}.depends_on"
        if c.kind != "effect":
            out.append(Finding(code="basis_on_a_read", severity="blocking", area="EX8", location=where,
                               message=f"'{c.name}' is a read; only an effect contract can depend on a read."))
        elif c.depends_on.read not in caps:
            missing("capability", c.depends_on.read, where, "EX8")
        elif caps[c.depends_on.read].kind != "read":
            out.append(Finding(code="basis_not_a_read", severity="blocking", area="EX8", location=where,
                               message=f"'{c.name}' depends on '{c.depends_on.read}', which is not a read."))
        elif not {i.name for i in c.inputs} & {i.name for i in caps[c.depends_on.read].inputs}:
            out.append(Finding(code="basis_shares_no_details", severity="blocking", area="EX8", location=where,
                               message=f"'{c.name}' and '{c.depends_on.read}' share no input, so no read could be "
                                       "shown to be about the same details."))
    for g in spec.goals:
        for f in g.obligations:
            if f not in facts:
                missing("fact", f, f"goals.{g.id}.obligations", "EX4")
        for f in g.diagnostic_inputs:
            if f not in facts:
                missing("fact", f, f"goals.{g.id}.diagnostic_inputs", "EX5")
        overlap = set(g.obligations) & set(g.diagnostic_inputs)
        for f in sorted(overlap):
            out.append(Finding(code="obligation_and_diagnostic", severity="blocking", area="EX4",
                               location=f"goals.{g.id}",
                               message=f"'{f}' is both an obligation and a diagnostic input of goal '{g.id}'. "
                                       "An obligation must be established; a diagnostic input need not be (FR15)."))
    for c in spec.capabilities:
        for i in c.inputs:
            fact = i.fact or i.name
            if fact not in facts:
                missing("fact", fact, f"capabilities.{c.name}.inputs.{i.name}", "EX8")
    for r in spec.rules:
        for cap in r.applies_to:
            if cap not in caps:
                missing("capability", cap, f"rules.{r.id}.applies_to", "EX6")
        for p in r.deny_when:
            known_inputs = {i.name for cap in r.applies_to if cap in caps for i in caps[cap].inputs}
            if p.fact not in facts and p.fact not in known_inputs:
                missing("fact or input", p.fact, f"rules.{r.id}.deny_when", "EX6")
    if spec.questions:
        for n in spec.questions.never_ask:
            for f in n.facts:
                if f not in facts:
                    missing("fact", f, f"questions.never_ask.{n.id}", "EX12")
        for f in spec.questions.may_ask:
            if f not in facts:
                missing("fact", f, "questions.may_ask", "EX12")
        never = {f for n in spec.questions.never_ask for f in n.facts}
        for g in spec.goals:
            for f in g.obligations:
                if f in never:
                    out.append(Finding(
                        code="obligation_never_askable", severity="warning", area="EX12",
                        location=f"goals.{g.id}.obligations",
                        message=f"'{f}' is an obligation of goal '{g.id}' but may never be asked. It can only "
                                "be established another way (a read, or a waiver), so check that is intended."))
    for p in spec.prohibitions:
        for c in p.conclusions:
            if c not in conclusions:
                missing("conclusion", c, f"prohibitions.{p.id}.conclusions", "EX13")
    for w in spec.waivers:
        if w.goal not in goals:
            missing("goal", w.goal, "waivers", "EX4")
        elif w.obligation not in goals[w.goal].obligations:
            missing("obligation", w.obligation, f"waivers.{w.goal}", "EX4")
    return out


def _consequential(c: Capability) -> bool:
    if c.kind != "effect":
        return False
    if c.authority_class in ("state_changing", "liability"):
        return True
    return bool(c.consequence and (c.consequence.costs_money or c.consequence.reaches_customer))


def _check_capabilities(spec: BusinessSpecification) -> list[Finding]:
    out = []
    for c in spec.capabilities:
        where = f"capabilities.{c.name}"
        if c.kind == "effect" and c.success_evidence is None:
            out.append(Finding(code="no_success_evidence", severity="blocking", area="EX15", location=where,
                               message=f"'{c.name}' changes something but declares no success evidence. Without "
                                       "a read-back, nobody could tell whether it happened (FR51)."))
        if c.kind == "effect" and c.consequence is None:
            out.append(Finding(code="no_consequence_class", severity="blocking", area="EX8", location=where,
                               message=f"'{c.name}' does not say whether it is reversible, costs money or reaches "
                                       "a customer (FR52)."))
        if _consequential(c) and c.authority_basis is None:
            out.append(Finding(code="no_authority_basis", severity="blocking", area="EX7", location=where,
                               message=f"'{c.name}' is consequential but declares no basis for the authority to "
                                       "run it. Authority is never assumed from the channel (FR109)."))
        if c.authority_class == "liability" and c.authority_basis != "operator_approval":
            out.append(Finding(code="liability_without_operator", severity="blocking", area="EX7",
                               location=where,
                               message=f"'{c.name}' is liability-bearing, so it must require operator approval "
                                       "(FR16 gates liability separately)."))
        if c.kind == "read" and (c.confirmation or c.success_evidence):
            out.append(Finding(code="read_with_effect_contract", severity="warning", area="EX8", location=where,
                               message=f"'{c.name}' is a read but declares confirmation or success evidence, "
                                       "which only apply to effects."))
        if c.name.split("_", 1)[0] not in VERBS:
            out.append(Finding(code="not_verb_first", severity="warning", area="EX8", location=where,
                               message=f"'{c.name}' should start with a verb (for example check_, book_, cancel_)."))
    return out


def _always_denies(rule, cap: Capability) -> bool:
    """A deny rule that fires on every possible invocation (FR23).

    Decidable because the predicate language is closed: a rule always fires if
    it is marked ``always_deny``, or if every one of its predicates is
    ``present`` on an input the capability requires."""
    if rule.always_deny:
        return True
    if not rule.deny_when:
        return False
    required = {i.name for i in cap.inputs if i.required}
    return all(p.op == "present" and p.fact in required for p in rule.deny_when)


def _check_always_denied(spec: BusinessSpecification) -> list[Finding]:
    caps = {c.name: c for c in spec.capabilities}
    out = []
    for r in spec.rules:
        for name in r.applies_to:
            cap = caps.get(name)
            if cap and _always_denies(r, cap):
                out.append(Finding(
                    code="granted_but_always_denied", severity="blocking", area="EX8",
                    location=f"rules.{r.id}",
                    message=f"Capability '{name}' is granted, but rule '{r.id}' denies it every time. The Agent "
                            "would promise what the platform then refuses, which is worse than a refusal. Remove "
                            "the grant or narrow the rule (FR23)."))
    return out


def _check_rules_enforced(spec: BusinessSpecification) -> list[Finding]:
    out = []
    for r in spec.rules:
        if r.applies_to and not r.deny_when and not r.always_deny:
            out.append(Finding(
                code="rule_not_enforceable", severity="warning", area="EX6", location=f"rules.{r.id}",
                message=f"Rule '{r.id}' names capabilities but no condition, so only the Agent's reading of its "
                        "text upholds it. Text alone is advisory (AD-3); add a condition if it must hold."))
    return out


def _check_guards(spec: BusinessSpecification) -> list[Finding]:
    out = []
    for g in spec.guards:
        where = f"guards.{g.id}"
        if g.verdict == "constrain" and not (g.constraint or "").strip():
            out.append(Finding(code="guard_without_constraint", severity="blocking", area="EX9", location=where,
                               message=f"Guard '{g.id}' constrains the Agent but does not say how."))
        if not g.detect_keywords:
            out.append(Finding(code="guard_without_detector", severity="blocking", area="EX9", location=where,
                               message=f"Guard '{g.id}' declares no way to detect its condition, so it could never "
                                       "fire."))
    return out


def _check_sequencing_prose(spec: BusinessSpecification) -> list[Finding]:
    out = []
    for where, text, area in _prose_fields(spec):
        for pattern, label in _SEQUENCING_PROSE:
            if pattern.search(text):
                out.append(Finding(
                    code="sequencing_construct", severity="blocking", area=area, location=where,
                    message=f"{where} describes an order of steps ({label}). A specification states what must be "
                            "true, not what happens next: express the prerequisite as an obligation of the goal or "
                            "an input of the capability (FR18, FR24)."))
                break
    return out


def _check_source_conflicts(loaded: LoadedSpecification) -> list[Finding]:
    """Story 2.4: two sources of equal declared precedence that say different things under the same heading
    leave no rule for which one is authoritative (FR31)."""
    out: list[Finding] = []
    seen: dict[tuple[int, str], tuple[str, str]] = {}
    for doc in sorted(loaded.sources.values(), key=lambda d: d.id):
        for section in doc.sections:
            key = (doc.precedence, heading_key(section.heading or doc.id))
            if key in seen and seen[key][0] != doc.id and seen[key][1] != section.text:
                out.append(Finding(code="conflicting_sources_without_precedence", severity="blocking", area="EX14",
                                   location=f"grounding.sources.{seen[key][0]} / grounding.sources.{doc.id}",
                                   message=f"'{seen[key][0]}' and '{doc.id}' both say something different under "
                                           f"'{section.heading or doc.id}' at the same precedence ({doc.precedence}); declare "
                                           "which one is authoritative."))
            seen.setdefault(key, (doc.id, section.text))
    return out


def validate(loaded: LoadedSpecification) -> ValidationReport:
    spec = loaded.spec
    findings: list[Finding] = list(loaded.load_findings)
    for check in (_check_absent_areas, _check_unique, _check_capabilities, _check_always_denied,
                  _check_rules_enforced, _check_guards, _check_sequencing_prose):
        findings.extend(check(spec))
    findings.extend(_check_references(loaded))
    findings.extend(_check_source_conflicts(loaded))
    return ValidationReport(findings=tuple(findings))
