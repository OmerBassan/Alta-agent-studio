"""The scenario harness — the first channel adapter (AD-16).

It does what any channel adapter does: hands the Core channel-neutral inbound
messages with a conversation key and a message id, and receives outbound
messages back. It adds scenario files: sequences of inbound messages per
conversation, with expectations about the **episode record** — lifecycle,
evidence, denials, outbox, resolution — never about reply wording. That keeps
evaluation computable from the record without anyone reading a transcript
(FR76).

Scenario file (TOML)::

    [[scenarios]]
    id = "D1-book-checkup"
    business = "dental"
    turns = ["I'd like a check-up on Monday at 9am", "Ada Lovelace", "yes"]
    [scenarios.expect]
    lifecycle = "closed"
    close_reason = "resolved"
    evidence = ["confirmation_granted", "effect_verified"]
    no_evidence = ["effect_unverified"]
    denials = []                          # exact set of (classification:reason)
    outbox = ["reply"]                    # kinds that must appear
    halted = "guard"                      # optional
    served = true                         # optional, resolution of the episode
    effects = 1                           # executions recorded by the system of record
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from studio.core import Core, InboundMessage, OutboundMessage


@dataclass
class Transcript:
    episode_ids: list[str] = field(default_factory=list)
    exchanges: list[tuple[str, list[OutboundMessage]]] = field(default_factory=list)


class HarnessChannel:
    """Ingress and egress for one tenant. Message ids are generated per
    conversation; a caller may pass one to test re-sends (FR87)."""

    def __init__(self, core: Core, tenant: str):
        self.core = core
        self.tenant = tenant
        self._counter = 0

    async def send(self, conversation: str, text: str, message_id: Optional[str] = None):
        self._counter += 1
        return await self.core.handle(InboundMessage(
            tenant=self.tenant, conversation_key=conversation, text=text,
            message_id=message_id or f"{conversation}-{self._counter}"))


@dataclass
class ScenarioResult:
    id: str
    passed: bool
    failures: list[str]
    transcript: Transcript
    episode_id: Optional[str]


def load_scenarios(path: str | Path) -> list[dict[str, Any]]:
    return tomllib.loads(Path(path).read_text(encoding="utf-8"))["scenarios"]


def check(core: Core, tenant: str, episode_id: str, expect: dict[str, Any], effects: Optional[int] = None,
          halted: Optional[str] = None) -> list[str]:
    """Compare the episode record against expectations. Returns failures."""
    store = core.store
    episode = store.get_episode(tenant, episode_id)
    failures: list[str] = []

    def mismatch(what: str, expected: Any, observed: Any) -> None:
        failures.append(f"{what}: expected {expected!r}, observed {observed!r}")

    evidence = {e["kind"] for e in store.evidence(tenant, episode_id)}
    denials = sorted({f"{d['classification']}:{d['reason']}" for d in store.denials(tenant, episode_id)})
    outbox = {o["kind"] for o in store.outbox(tenant, episode_id)}
    resolutions = store.resolutions(tenant, episode_id)
    if "lifecycle" in expect and episode.lifecycle != expect["lifecycle"]:
        mismatch("lifecycle", expect["lifecycle"], episode.lifecycle)
    if "close_reason" in expect and episode.close_reason != expect["close_reason"]:
        mismatch("close_reason", expect["close_reason"], episode.close_reason)
    for kind in expect.get("evidence", []):
        if kind not in evidence:
            mismatch("evidence", f"includes {kind}", sorted(evidence))
    for kind in expect.get("no_evidence", []):
        if kind in evidence:
            mismatch("evidence", f"excludes {kind}", sorted(evidence))
    if "denials" in expect and sorted(expect["denials"]) != denials:
        mismatch("denials", sorted(expect["denials"]), denials)
    for kind in expect.get("outbox", []):
        if kind not in outbox:
            mismatch("outbox", f"includes {kind}", sorted(outbox))
    if "halted" in expect and halted != expect["halted"]:
        mismatch("halted", expect["halted"], halted)
    if "served" in expect:
        served = [bool(r["served"]) for r in resolutions]
        if served != [expect["served"]]:
            mismatch("served", [expect["served"]], served)
    if "effects" in expect and effects != expect["effects"]:
        mismatch("effects executed", expect["effects"], effects)
    return failures


async def run_scenario(core: Core, tenant: str, scenario: dict[str, Any], effects_counter=None) -> ScenarioResult:
    channel = HarnessChannel(core, tenant)
    transcript = Transcript()
    conversation = scenario["id"]
    halted = None
    for text in scenario["turns"]:
        outcome = await channel.send(conversation, text)
        transcript.exchanges.append((text, outcome.messages))
        if outcome.episode_id not in transcript.episode_ids:
            transcript.episode_ids.append(outcome.episode_id)
        halted = outcome.halted or halted
    episode_id = transcript.episode_ids[-1] if transcript.episode_ids else None
    effects = effects_counter() if effects_counter else None
    failures = check(core, tenant, episode_id, scenario.get("expect", {}), effects, halted) if episode_id else \
        ["no episode was created"]
    return ScenarioResult(id=scenario["id"], passed=not failures, failures=failures, transcript=transcript,
                          episode_id=episode_id)
