# -*- coding: utf-8 -*-
"""The alta:ask parser must extract well-formed cards and degrade to plain chat
on anything else — a malformed block never blocks the user."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ask_protocol import format_card, parse_ask_block, visible_text  # noqa: E402

QUESTION_BLOCK = {
    "phase": "qualification", "step": 2, "of": 5,
    "intro": "Now, how you'll size up whether a lead is worth a meeting.",
    "questions": [
        {"id": "must_know", "label": "What must a lead tell you first?",
         "hint": "e.g. team size, budget", "placeholder": "Type your answer…"},
        {"id": "nice", "label": "Anything nice to know?", "hint": "optional"},
    ],
}

APPROVE_BLOCK = {
    "phase": "review", "kind": "approve",
    "intro": "Here's the call script. Does this sound like your team?",
    "approve_label": "Looks great", "revise_label": "I'd change something",
}


def turn(prose: str, block: dict) -> str:
    return f"{prose}\n\n```alta:ask\n{json.dumps(block)}\n```"


def test_valid_block_is_parsed():
    assert parse_ask_block(turn("Great — next up.", QUESTION_BLOCK)) == QUESTION_BLOCK


def test_valid_block_is_stripped_from_the_visible_bubble():
    text = turn("Great — next up.", QUESTION_BLOCK)
    said = visible_text(text)
    assert said == "Great — next up."
    assert "alta:ask" not in said and "must_know" not in said


def test_approve_block_round_trips():
    block = parse_ask_block(turn("Here's the playbook.", APPROVE_BLOCK))
    assert block["kind"] == "approve"
    assert block["approve_label"] == "Looks great"


@pytest.mark.parametrize("text", [
    "Just a normal chat turn, no card here.",
    "```alta:ask\n{not valid json,,}\n```",          # malformed JSON
    "```alta:ask\n[1, 2, 3]\n```",                    # JSON, but not an object
    "```alta:ask\n\"a string\"\n```",                # JSON, but not an object
    "```python\nprint('hi')\n```",                    # a different fence
    "```alta:ask\n{\"phase\":\"mission\"}",          # unterminated fence
])
def test_malformed_or_absent_degrades_to_chat(text):
    assert parse_ask_block(text) is None


def test_plain_turn_keeps_its_full_text():
    text = "Just a normal chat turn, no card here."
    assert visible_text(text) == text


def test_unparseable_fence_is_still_hidden_from_the_bubble():
    # A broken card must not spill raw JSON at the client, card or no card.
    text = "Some prose.\n\n```alta:ask\n{broken\n```"
    assert parse_ask_block(text) is None
    assert visible_text(text) == "Some prose."


def test_format_card_renders_questions_without_json():
    out = format_card(QUESTION_BLOCK)
    assert "Qualify" in out and "Step 2 of 5" in out
    assert "What must a lead tell you first?" in out
    assert "Continue" in out
    assert "must_know" not in out  # ids are internal, never shown


def test_format_card_renders_approve_actions():
    out = format_card(APPROVE_BLOCK)
    assert "Review" in out and "Looks great" in out and "I'd change something" in out


def test_format_card_survives_a_minimal_block():
    assert format_card({"phase": "mission"})  # no step/of/intro/questions


ASCII_BLOCKS = [
    {"phase": "qualification", "step": 2, "of": 5, "intro": "Sizing up a lead.",
     "questions": [{"label": "What must they tell you?", "hint": "team size"}]},
    {"phase": "review", "kind": "approve", "intro": "Does this look right?",
     "approve_label": "Looks great", "revise_label": "Change something"},
    {"phase": "mission"},
]


@pytest.mark.parametrize("block", ASCII_BLOCKS)
def test_format_card_chrome_renders_on_a_non_utf8_console(block):
    # Regression: the card's box-drawing chrome (U+250C etc.) raised
    # UnicodeEncodeError on a cp1255 console and killed a proof run mid-drive.
    # Given ASCII-only content, the rendered card must encode cleanly there.
    format_card(block).encode("cp1255")

