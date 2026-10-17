"""Strict consent: only the requester's own bare yes or no answers a confirmation.

A confirmation record is granted by the requester's event, never by the model
(AD-3, DL-008): the Agent proposes a payload, the Core records an offer bound to
it, and only an inbound message that is *nothing but* a yes grants it. A
yes-word inside a longer sentence ("okay, but my cheek is really puffy") is not
consent; a no-word inside one ("no, get me a person") is not a decline — both
reach the Agent as ordinary messages. This is the strict-consent rule the user
approved in DL-015, carried over unchanged. Known cost, accepted there: a
longer yes ("yes, Tuesday works") is asked again.
"""

from __future__ import annotations

import re
from typing import Literal

_YES_PHRASES = ("yes", "yeah", "yep", "yup", "sure", "ok", "okay", "alright", "all right",
                "correct", "right", "confirm", "confirmed", "absolutely", "go ahead",
                "do it", "please do", "sounds good", "that works", "works for me")
_NO_PHRASES = ("no", "nope", "nah", "cancel", "not now", "not today", "not yet", "wait",
               "hold on", "stop", "don't", "do not", "don't do it", "never mind", "nevermind",
               "changed my mind", "i changed my mind")
_COURTESY = ("please", "thanks", "thank you")


def _phrase_run(phrases: tuple[str, ...]) -> re.Pattern:
    alt = "|".join(re.escape(p) for p in sorted(phrases + _COURTESY, key=len, reverse=True))
    return re.compile(rf"(?:(?:{alt}) )+")


_YES = _phrase_run(_YES_PHRASES)
_NO = _phrase_run(_NO_PHRASES)


def bare_answer(message: str) -> Literal["yes", "no", ""]:
    """'yes' or 'no' when the whole message is that answer, else ''."""
    words = re.findall(r"[a-z']+", message.lower().replace("’", "'"))
    if not words or all(w in ("please", "thanks", "thank", "you") for w in words):
        return ""
    text = " ".join(words) + " "
    if _NO.fullmatch(text):
        return "no"
    if _YES.fullmatch(text):
        return "yes"
    return ""
