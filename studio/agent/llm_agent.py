"""The model-in-charge Agent (AD-1): a language model reads the Core's view and
emits one typed request.

The model decides what the person wants, what is still missing, when to look
something up, which capability to use, whether to act, ask, answer, wait or hand
over (FR38). It decides nothing about what is *permitted*: everything it emits
is validated and authorized by the Core, and anything it gets wrong comes back
as a typed result it can reason about (AD-3, AD-18). Its output is untrusted
input — parsed and validated here, and a malformed output is reported to the
Core as an error, never repaired by guessing (FR46).
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import TypeAdapter, ValidationError

from studio.agent.model_port import ModelError, ModelPort
from studio.core.ports import AgentDecision, AgentView
from studio.core.types import AgentRequest

_REQUEST = TypeAdapter(AgentRequest)

REQUEST_GUIDE = """\
Reply with exactly ONE JSON object: the next request. Kinds:
- {"kind":"retrieve","query":"..."} look something up in the business's material.
- {"kind":"read","capability":"<read capability>","arguments":[{"name":..,"value":..}]}
- {"kind":"effect","capability":"<effect capability>","arguments":[...]} change something. Arguments must equal facts
  already established. If the capability needs confirmation, first ask with clarify+confirm and wait for a plain yes.
- {"kind":"clarify","message":"...","asks_for":["<fact>",...],"confirm":{"capability":..,"arguments":[...]}|null}
  ask the person something (confirm = ask them to say yes to exactly these details).
- {"kind":"respond","message":"...","claims":[...],"resolution":{...}|null} answer the person.
  Every business fact you state must be a claim {"kind":"business_fact","text":..,"reference":"<ref id>"} citing a
  reference listed below. General knowledge: {"kind":"general_knowledge","text":..} (only if allowed). A conclusion:
  {"kind":"conclusion","text":..,"conclusion":"<id>"}. Something you did: {"kind":"action_taken","text":..,
  "evidence":"<evidence id from a verified effect>"}. When a goal is finished add
  "resolution":{"goal":..,"served":true|false,"authority":"agent" or "capability:<name>","evidence":[..],"payload":[]}.
- {"kind":"escalate","reason_class":"<declared reason or rules_silent>","summary":"...","message":"..."} hand to a person.
  Use rules_silent when the business's rules do not cover the situation — never invent a rule.
- {"kind":"suspend","awaiting":"<named input>","message":"...","deadline":null} wait for something specific.
Any request may also carry "goal":"<declared goal id>" and "facts":[{"name":..,"value":..}] for facts the person
has told you. Dates are YYYY-MM-DD, times HH:MM. Write messages as a short email from the business, in its voice."""


def _section(title: str, lines: list[str]) -> str:
    body = "\n".join(lines) if lines else "(none)"
    return f"## {title}\n{body}"


def render(view: AgentView) -> list[dict[str, str]]:
    ctx, s = view.context, view.surface
    system = [
        f"You work for {ctx.business_name}. {ctx.description}",
        f"Voice: {ctx.voice}" if ctx.voice else "Write plainly.",
        _section("Never say", list(ctx.will_not_say)),
        _section("Goals you may pursue (no others)", [
            f"- {g.id}: {g.description} Resolved when: {g.resolution} Must establish: {', '.join(g.obligations) or '-'}."
            f" Helpful: {', '.join(g.diagnostic_inputs) or '-'}." for g in ctx.goals]),
        _section("Never a goal", [f"- {t}" for t in ctx.never_goals]),
        _section("Facts", [f"- {f.name} ({f.type}): {f.description}" for f in ctx.facts]),
        _section("Rules", [f"- {r.id}: {r.text}" for r in ctx.rules]),
        _section("Conclusions", [f"- {c.id} ({'permitted' if c.permitted else 'FORBIDDEN'}): {c.text}"
                                 for c in ctx.conclusions]),
        _section("Must not", [f"- {p}" for p in ctx.prohibitions]),
        _section("Never ask", [f"- {n.text}" for n in ctx.never_ask]),
        _section("Hand to a person when", [f"- {e.reason_class}: {e.text}" for e in ctx.escalation_conditions]),
        _section("Refuse when", [f"- {r.reason_class}: {r.text}" for r in ctx.refusals]),
        "General knowledge (not from the business's material) is "
        + ("allowed, but must be marked." if ctx.general_knowledge_allowed else "NOT allowed."),
        _section("Capabilities", [
            f"- {t.name} [{t.kind}{', needs confirmation' if t.confirmation_required else ''}]: {t.description} "
            f"Inputs: {', '.join(f'{i.name}:{i.type}' for i in t.inputs) or '-'}" for t in s.tools]),
        _section("Business material you may cite (reference id: text)", [
            f"- {r.ref} [{r.title}]: {r.text}" for r in view.references]),
        REQUEST_GUIDE,
    ]
    state = [
        _section("Conversation so far", [f"{e.role.upper()}: {e.text}" for e in view.conversation]),
        _section("Facts established", [f"- {k} = {v}" for k, v in view.facts]),
        f"Active goal: {view.active_goal or 'none'}; parked: {', '.join(view.parked_goals) or 'none'}",
        _section("Outstanding obligations", [f"- {o.goal}: {', '.join(o.outstanding) or 'none'}"
                                             for o in view.obligations]),
        _section("Confirmations", [f"- {o.offer_id} {o.capability}: {o.state}" for o in view.offers]),
        _section("Constraints from the platform (binding)", list(view.constraints)),
        _section("Results of your requests this turn", [
            f"- {kind}: {json.dumps(r.model_dump(mode='json', exclude_none=True), ensure_ascii=False)}"
            for kind, r in view.turn_results]),
        f"Requests left this turn: {view.requests_left}. "
        + ("Nothing has been sent to this person yet." if view.first_message else ""),
    ]
    return [{"role": "system", "content": "\n\n".join(system)},
            {"role": "user", "content": "\n\n".join(state) + "\n\nYour next request (one JSON object):"}]


class LLMAgent:
    name = "llm"

    def __init__(self, port: ModelPort):
        self.port = port

    async def decide(self, view: AgentView) -> AgentDecision:
        try:
            raw, call = await self.port.complete_json(render(view))
        except ModelError as exc:
            return AgentDecision(error=str(exc), model_calls=(exc.call,))
        try:
            request = _REQUEST.validate_python(_normalise(raw))
        except ValidationError as exc:
            return AgentDecision(error=f"the model's request was invalid: {exc.errors()[:3]}", model_calls=(call,))
        return AgentDecision(request=request, model_calls=(call,))


def _normalise(raw: Any) -> Any:
    """Accept the two shapes models commonly produce for argument lists — a
    list of pairs (the schema) or an object — without guessing at anything
    else. A JSON ``null`` for an optional field is left for validation."""
    if not isinstance(raw, dict):
        return raw
    out = dict(raw)
    for key in ("arguments", "facts"):
        if isinstance(out.get(key), dict):
            out[key] = [{"name": k, "value": v} for k, v in out[key].items()]
    confirm = out.get("confirm")
    if isinstance(confirm, dict) and isinstance(confirm.get("arguments"), dict):
        out["confirm"] = {**confirm, "arguments": [{"name": k, "value": v} for k, v in confirm["arguments"].items()]}
    resolution = out.get("resolution")
    if isinstance(resolution, dict) and isinstance(resolution.get("payload"), dict):
        out["resolution"] = {**resolution,
                             "payload": [{"name": k, "value": v} for k, v in resolution["payload"].items()]}
    return out
