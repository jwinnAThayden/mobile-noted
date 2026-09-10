"""The compiled payload the web app fetches."""

import json
from pathlib import Path

import build_content

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "webapp" / "static" / "content.json"


def load():
    return json.loads(CONTENT.read_text(encoding="utf-8"))


def test_content_is_committed():
    # app.py refuses to start without it and the service worker precaches it.
    assert CONTENT.exists(), "run: python3 webapp/build_content.py"


def test_sections_carry_what_the_app_renders():
    for section in load()["sections"]:
        assert section["id"] and section["title"] and section["html"]
        assert isinstance(section["speech"], list) and section["speech"]
        assert section["group"] in {"study", "project"}


def test_utterances_stay_under_the_engine_limit():
    # Long utterances are unreliable across speech engines.
    for section in load()["sections"]:
        for line in section["speech"]:
            assert len(line) <= build_content.MAX_CHUNK


def test_cards_have_both_display_and_spoken_forms():
    cards = load()["cards"]
    assert len(cards) >= 90
    ids = [c["id"] for c in cards]
    assert len(ids) == len(set(ids)), "card ids must be unique for scheduling"
    for card in cards:
        assert card["q"] and card["a"] and card["qs"] and card["as"]
        assert "**" not in card["q"] and "**" not in card["a"]


def test_domain_weights_reach_the_app():
    weighted = [s for s in load()["sections"] if s.get("weight")]
    assert len(weighted) == 4
    assert sum(s["weight"] for s in weighted) == 100


def test_long_lines_are_split_on_punctuation():
    chunks = build_content.sentences("One. Two. " + "word " * 200)
    assert all(len(c) <= build_content.MAX_CHUNK for c in chunks)
    assert chunks[0] == "One."
