"""The credential-free agent: deterministic, domain-agnostic, zero tokens.

It lets the whole product run — and be tested end to end — without a model
provider (PRD §7.4 keeps "a credential-free mock mode"). It reads only the
``AgentView`` the Core builds: no business is named in this file, and every
decision is derived from the compiled specification (declared goals, facts and
their types, capabilities and their inputs, references). It is a stand-in, not
the product's intelligence, and it is never presented as such: it follows the
simplest reasonable course and hands over when unsure.

It obeys the same boundary as any other agent: it can only emit requests, and
the Core decides whether each is permitted.
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Any, Callable, Optional

from studio.core.consent import bare_answer
from studio.core.ports import AgentDecision, AgentView
from studio.core.types import (Argument, Claim, ClarifyRequest, ConfirmProposal, EffectRequest, EscalateRequest,
                               FactUpdate, ResolutionClaim, RespondRequest, RetrieveRequest)
from studio.spec.compile import ToolDefinition

_WORD = re.compile(r"[a-z0-9]+")
_STOP = frozenset(
    "a an and are at be can could do for from has have how i i'd i'm in is it like me my of on or our please the "
    "there this to we what when where which with would you your want wants".split())
_WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_ISO_DATE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
_TIME = re.compile(r"\b(?:at\s+)?([01]?\d|2[0-3])(?::([0-5]\d))?\s*(am|pm)?\b", re.I)
_NAME = re.compile(r"\b(?i:my name is|i am|i'm|this is|name[:\s]+)\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)")
_SIGNATURE = re.compile(r"\b([A-Z][a-z]+\s+[A-Z][a-z]+),?\s+[\w.+-]+@")
_COUNT = re.compile(r"\b(\d{1,4})\s*(?:people|guests|persons|of us|adults|pax)\b", re.I)
_OPTIONS = re.compile(r"\b([a-z]+(?:_[a-z]+)+|[a-z]{4,})\b")


def _terms(text: str) -> set[str]:
    return {w for w in _WORD.findall(text.lower()) if w not in _STOP}


def _squash(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


class DeterministicAgent:
    name = "deterministic"

    def __init__(self, today: Callable[[], date] = date.today):
        self._today = today

    # --- reading the person's message -----------------------------------------------

    def _options(self, description: str) -> list[str]:
        """Enumerated values, when a fact's description lists them
        (``a, b or c``). Only snake_case tokens or words after a colon count."""
        if ":" not in description:
            return []
        listed = description.split(":", 1)[1]
        return [t for t in _OPTIONS.findall(listed) if t not in ("or", "and")]

    def _extract(self, view: AgentView, text: str) -> dict[str, Any]:
        found: dict[str, Any] = {}
        lowered = text.lower()
        email = _EMAIL.search(text)
        name = _NAME.search(text) or _SIGNATURE.search(text)
        count = _COUNT.search(text)
        iso = _ISO_DATE.search(text)
        weekday = next((d for d in _WEEKDAYS if re.search(rf"\b{d}\b", lowered)), None)
        time_match = None
        for m in _TIME.finditer(text):
            if m.group(3) or m.group(2) or lowered[max(0, m.start() - 3):m.start() + 3].strip().startswith("at"):
                time_match = m
                break
        established = dict(view.facts)
        outstanding = [o for ob in view.obligations if ob.goal == view.active_goal for o in ob.outstanding]
        for fact in view.context.facts:
            if fact.type == "date" and (iso or weekday):
                if iso:
                    found[fact.name] = iso.group(1)
                else:
                    today = date.fromisoformat(view.today) if view.today else self._today()
                    ahead = (_WEEKDAYS.index(weekday) - today.weekday()) % 7 or 7
                    found[fact.name] = (today + timedelta(days=ahead)).isoformat()
            elif fact.type == "time" and time_match:
                hour = int(time_match.group(1))
                if (time_match.group(3) or "").lower() == "pm" and hour < 12:
                    hour += 12
                found[fact.name] = f"{hour:02d}:{time_match.group(2) or '00'}"
            elif fact.type == "integer" and count:
                found[fact.name] = int(count.group(1))
            elif fact.type == "string" and "email" in fact.name and email:
                found[fact.name] = email.group(0)
            elif fact.type == "string" and "name" in fact.name and name:
                found[fact.name] = name.group(1)
            elif fact.type == "string":
                options = self._options(fact.description)
                squashed = _squash(text)
                match = next((o for o in options if _squash(o) in squashed), None)
                if match:
                    found[fact.name] = match
        # A short reply to the question just asked answers its first outstanding
        # string fact, when nothing else claimed the message.
        if outstanding and not found and len(text) <= 60 and not bare_answer(text):
            first = next((f for f in view.context.facts if f.name == outstanding[0]), None)
            if first and first.type == "string" and not self._options(first.description) and "?" not in text:
                found[first.name] = text.strip().rstrip(".")
        return {k: v for k, v in found.items() if established.get(k) != v}

    # --- choosing a goal and a capability ------------------------------------------------

    def _capability_for(self, view: AgentView, goal_id: str, text: str) -> Optional[ToolDefinition]:
        goal = next(g for g in view.context.goals if g.id == goal_id)
        candidates = [t for t in view.surface.tools if t.kind == "effect"
                      and {i.name for i in t.inputs if i.required} <= set(goal.obligations)]
        if not candidates:
            return None
        terms = _terms(text)
        return max(candidates, key=lambda t: (len(terms & _terms(t.name.replace("_", " ") + " " + t.description)),
                                              t.confirmation_required, len(t.inputs)))

    def _goal(self, view: AgentView, text: str) -> Optional[str]:
        terms = _terms(text)
        scored = []
        for g in view.context.goals:
            tools = [t for t in view.surface.tools if {i.name for i in t.inputs if i.required} <= set(g.obligations)
                     and t.kind == "effect"]
            words = _terms(g.id.replace("_", " ") + " " + g.description + " " +
                           " ".join(t.name.replace("_", " ") for t in tools))
            scored.append((len(terms & words), bool(tools), g.id))
        best = max(scored, default=(0, False, None))
        if best[0] == 0:
            return view.active_goal
        if view.active_goal and best[2] != view.active_goal:
            active = next(s for s in scored if s[2] == view.active_goal)
            if active[0] >= best[0]:
                return view.active_goal
        return best[2]

    # --- the decision -------------------------------------------------------------------

    async def decide(self, view: AgentView) -> AgentDecision:
        return AgentDecision(request=self._decide(view))

    def _decide(self, view: AgentView):
        text = next((e.text for e in reversed(view.conversation) if e.role == "requester"), "")
        last = view.turn_results[-1] if view.turn_results else None

        if view.constraints:
            return self._escalate(view, " ".join(view.constraints), "A member of the team will pick this up.")

        if last is not None:
            kind, result = last
            if kind == "effect" and result.status == "ok" and result.verified:
                return self._report_done(view, result.evidence_id, result.capability)
            if kind == "effect" and result.status == "failed":
                return self._escalate(view, f"could not complete: {result.denial.detail if result.denial else ''}",
                                      "I wasn't able to confirm that, so I've passed it to the team, who will be in "
                                      "touch.")
            if kind == "retrieve" and result.status == "ok":
                if result.items:
                    item = result.items[0]
                    return RespondRequest(message=item["text"], claims=(Claim(
                        kind="business_fact", text=item["text"][:120], reference=item["reference"]),))
                return self._escalate(view, "the business's material does not answer this", "I don't have that "
                                      "information, so I've asked the team to reply.", silent=True)
            if result.status == "refused" and result.denial and result.denial.rule:
                return self._refuse_with_rule(view, result.denial.rule)
            if result.status == "refused" and result.denial and result.denial.reason not in (
                    "confirmation_missing", "arguments_not_established"):
                return self._escalate(view, result.denial.detail, "That's something the team needs to look at; "
                                      "I've passed it on.", silent=result.denial.classification == "spec_defect")

        new_facts = self._extract(view, text)
        updates = tuple(FactUpdate(name=k, value=v) for k, v in new_facts.items())
        goal_id = self._goal(view, text)
        if goal_id is None:
            return RetrieveRequest(query=text, facts=updates)
        tool = self._capability_for(view, goal_id, text)
        if tool is None:
            return RetrieveRequest(query=text, goal=goal_id, facts=updates)

        known = {**dict(view.facts), **new_facts}
        goal = next(g for g in view.context.goals if g.id == goal_id)
        waived = {w for o in view.obligations if o.goal == goal_id for w in o.waived}
        missing = [o for o in goal.obligations if o not in known and o not in waived]
        if missing:
            fact = next(f for f in view.context.facts if f.name == missing[0])
            return ClarifyRequest(goal=goal_id, facts=updates, asks_for=(fact.name,),
                                  message=f"Could you tell me {fact.description[0].lower()}{fact.description[1:]}?")
        arguments = tuple(Argument(name=i.name, value=known[i.name]) for i in tool.inputs if i.name in known)
        granted = any(o.capability == tool.name and o.state == "granted" for o in view.offers)
        if tool.confirmation_required and not granted:
            details = ", ".join(f"{a.name.replace('_', ' ')}: {a.value}" for a in arguments)
            return ClarifyRequest(goal=goal_id, facts=updates, message=f"Just to confirm — {details}. Shall I go "
                                  "ahead? Please reply yes or no.",
                                  confirm=ConfirmProposal(capability=tool.name, arguments=arguments))
        return EffectRequest(goal=goal_id, facts=updates, capability=tool.name, arguments=arguments)

    def _report_done(self, view: AgentView, evidence_id: str, capability: Optional[str]) -> RespondRequest:
        claim = Claim(kind="action_taken", text="done", evidence=evidence_id)
        message = "That's done, and I've checked it went through."
        if not view.active_goal or not capability:
            return RespondRequest(message=message, claims=(claim,))
        return RespondRequest(goal=view.active_goal, message=message, claims=(claim,),
                              resolution=ResolutionClaim(goal=view.active_goal, served=True,
                                                         authority=f"capability:{capability}", evidence=(evidence_id,)))

    def _refuse_with_rule(self, view: AgentView, rule_id: str):
        """Refuse with a reason drawn from the business's own rules (BRIEF: one
        of the four things a retrieval chatbot cannot do), citing the rule."""
        ref = next((r for r in view.references if r.item_id == f"spec:rules/{rule_id}"), None)
        if ref is None:
            return self._escalate(view, f"refused by rule {rule_id}", "I can't arrange that; I've asked the team.")
        return RespondRequest(goal=view.active_goal, message=f"I'm sorry, I can't arrange that: {ref.text}",
                              claims=(Claim(kind="business_fact", text=ref.text, reference=ref.ref),))

    def _escalate(self, view: AgentView, summary: str, message: str, silent: bool = False) -> EscalateRequest:
        reasons = view.context.escalation_conditions
        if silent or not reasons:
            return EscalateRequest(reason_class="rules_silent", summary=summary, message=message)
        terms = _terms(summary)
        best = max(reasons, key=lambda r: len(terms & _terms(r.reason_class.replace("_", " ") + " " + r.text)))
        if not terms & _terms(best.reason_class.replace("_", " ") + " " + best.text):
            return EscalateRequest(reason_class="rules_silent", summary=summary, message=message)
        return EscalateRequest(reason_class=best.reason_class, summary=summary, message=message)
