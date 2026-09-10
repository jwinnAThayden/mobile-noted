#!/usr/bin/env python3
"""Compile the Markdown study pack into static/content.json for the web app.

Reuses the renderers already in the project rather than reimplementing them:
build_offline_html.render() for display HTML, and build_audio.narrate() /
speechify() for the spoken form, so read-aloud gets prose that survives being
spoken instead of raw Markdown.

    python3 build_content.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

import build_audio as speech          # noqa: E402
import build_offline_html as page     # noqa: E402

# group: "study" drives the main nav; "project" is the how-this-works material.
PAGES = [
    ("01-security-operations.md", "Security Operations", "study"),
    ("02-vulnerability-management.md", "Vulnerability Management", "study"),
    ("03-incident-response.md", "Incident Response", "study"),
    ("04-reporting-communication.md", "Reporting & Communication", "study"),
    ("frameworks.md", "Frameworks", "study"),
    ("commands-cheatsheet.md", "Command Reference", "study"),
    ("tools-reference.md", "Tools Reference", "study"),
    ("acronyms.md", "Acronyms", "study"),
    ("study-plan.md", "Study Plan", "study"),
    ("README.md", "About This Pack", "project"),
    ("AUDIO.md", "Audio & Voice", "project"),
    ("MOBILE.md", "Install on Android", "project"),
    ("TESTING.md", "Verify It Works", "project"),
]

MAX_CHUNK = 220   # speechSynthesis is unreliable with long utterances


def sentences(text: str) -> list[str]:
    """Split narration into utterance-sized chunks on sentence boundaries."""
    out: list[str] = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        for part in re.split(r"(?<=[.!?])\s+", line):
            part = part.strip()
            if not part:
                continue
            while len(part) > MAX_CHUNK:
                cut = part.rfind(", ", 0, MAX_CHUNK)
                if cut < 60:
                    cut = part.rfind(" ", 0, MAX_CHUNK)
                if cut < 60:
                    cut = MAX_CHUNK
                out.append(part[:cut].strip())
                part = part[cut:].strip()
            if part:
                out.append(part)
    return out


def build_cards() -> list[dict]:
    """Flashcards, tagged by the domain heading they sit under."""
    source = (ROOT / "flashcards.md").read_text(encoding="utf-8")
    cards, domain, question = [], "General", None
    for raw in source.split("\n"):
        line = raw.strip()
        heading = re.match(r"##\s+(.*)", line)
        if heading:
            domain = re.sub(r"\s*—.*$", "", heading.group(1)).strip()
            continue
        if line.startswith("**Q**"):
            question = line[5:].strip()
        elif line.startswith("**A**") and question is not None:
            answer = line[5:].strip()
            cards.append({
                "id": f"c{len(cards):03d}",
                "domain": domain,
                "q": page.inline(question),
                "a": page.inline(answer),
                "qs": speech.speechify(question),
                "as": speech.speechify(answer),
            })
            question = None
    return cards


def main() -> None:
    sections = []
    for filename, title, group in PAGES:
        source = ROOT / filename
        if not source.exists():
            print(f"  missing, skipped: {filename}")
            continue
        markdown = source.read_text(encoding="utf-8")
        stem = source.stem
        body = page.render(markdown)
        if stem == "flashcards":
            continue
        spoken = sentences(speech.narrate(markdown, title))
        sections.append({
            "id": page.slugify(stem),
            "title": title,
            "group": group,
            "weight": page.WEIGHTS.get(stem),
            "html": body,
            "speech": spoken,
            "minutes": round(sum(len(s.split()) for s in spoken) / 155),
        })
        print(f"  {stem}: {len(spoken)} utterances, ~{sections[-1]['minutes']} min")

    cards = build_cards()
    print(f"  flashcards: {len(cards)} cards")

    data = {
        "title": "CySA+ Field Notes",
        "exam": "CompTIA CySA+ (CS0-003)",
        "sections": sections,
        "cards": cards,
    }
    out = HERE / "static" / "content.json"
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    out.write_text(payload, encoding="utf-8")
    print(f"\nWrote {out} ({out.stat().st_size/1024:.0f} KB)")

    # Stamp the service worker so a rebuild invalidates the old offline cache.
    import hashlib
    stamp = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:10]
    sw = HERE / "static" / "sw.js"
    text = sw.read_text(encoding="utf-8")
    sw.write_text(re.sub(r"var VERSION = '[^']*';",
                         f"var VERSION = '{stamp}';", text, count=1),
                  encoding="utf-8")
    print(f"Service worker cache version: {stamp}")


if __name__ == "__main__":
    main()
