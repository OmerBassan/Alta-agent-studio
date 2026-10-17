"""A scripted agent — the way to prove a Core guarantee fires.

A live model may or may not happen to test a guarantee. A scripted agent can be
made to misbehave on purpose — claim a booking that never happened, cite a
reference it was never given, skip a confirmation, loop — so each Core check is
shown to fire, and shown to be the thing that stopped it (FR96). Each script
step is either a request, or a function of the view that returns one, so a
script can use references and evidence the Core issued during the run.
"""

from __future__ import annotations

from typing import Callable, Iterable, Union

from studio.core.ports import AgentDecision, AgentView
from studio.core.types import AgentRequest

Step = Union[AgentRequest, Callable[[AgentView], AgentRequest]]


class ScriptedAgent:
    name = "scripted"

    def __init__(self, steps: Iterable[Step] = ()):
        self.steps: list[Step] = list(steps)
        self.views: list[AgentView] = []

    def extend(self, steps: Iterable[Step]) -> None:
        self.steps.extend(steps)

    async def decide(self, view: AgentView) -> AgentDecision:
        self.views.append(view)
        if not self.steps:
            return AgentDecision(error="the script has no further steps")
        step = self.steps.pop(0)
        request = step(view) if callable(step) else step
        return AgentDecision(request=request)
