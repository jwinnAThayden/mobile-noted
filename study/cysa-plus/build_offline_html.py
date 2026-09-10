#!/usr/bin/env python3
"""Bundle the CySA+ study pack into one self-contained offline HTML file.

Standard library only - no network, no CDN, no pip install. Run it once while
you have the repo, then carry `cysa-offline.html` anywhere.

    python study/cysa-plus/build_offline_html.py [-o OUTPUT]
"""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Order matters: this is the reading order in the bundled document.
PAGES = [
    ("README.md", "Overview"),
    ("SETUP.md", "Setup & Offline Access"),
    ("AUDIO.md", "Audio Version"),
    ("study-plan.md", "Study Plan"),
    ("01-security-operations.md", "1. Security Operations"),
    ("02-vulnerability-management.md", "2. Vulnerability Management"),
    ("03-incident-response.md", "3. Incident Response"),
    ("04-reporting-communication.md", "4. Reporting & Communication"),
    ("frameworks.md", "Frameworks"),
    ("commands-cheatsheet.md", "Command Cheatsheet"),
    ("tools-reference.md", "Tools Reference"),
    ("acronyms.md", "Acronyms"),
    ("flashcards.md", "Flashcards"),
]


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "section"


LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
CODE_RE = re.compile(r"`([^`]+)`")


def inline(text: str) -> str:
    """Render inline Markdown: links first, so code spans may appear in labels."""
    out = []
    pos = 0
    for match in LINK_RE.finditer(text):
        out.append(_spans(text[pos:match.start()]))
        label, href = match.group(1), match.group(2)
        if href.endswith(".md"):
            href = "#" + slugify(href[:-3])
        out.append(f'<a href="{html.escape(href, quote=True)}">{_spans(label)}</a>')
        pos = match.end()
    out.append(_spans(text[pos:]))
    return "".join(out)


def _spans(text: str) -> str:
    """Code spans are literal, so protect them before emphasis runs."""
    out = []
    pos = 0
    for match in CODE_RE.finditer(text):
        out.append(_emphasis(text[pos:match.start()]))
        out.append(f"<code>{html.escape(match.group(1))}</code>")
        pos = match.end()
    out.append(_emphasis(text[pos:]))
    return "".join(out)


def _emphasis(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", text)
    return text


def render_table(rows: list[str]) -> str:
    def cells(row: str) -> list[str]:
        return [c.strip() for c in row.strip().strip("|").split("|")]

    header = cells(rows[0])
    body = [cells(r) for r in rows[2:]]  # rows[1] is the --- separator
    parts = ['<div class="tw"><table>', "<thead><tr>"]
    parts += [f"<th>{inline(c)}</th>" for c in header]
    parts.append("</tr></thead><tbody>")
    for row in body:
        parts.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row) + "</tr>")
    parts.append("</tbody></table></div>")
    return "".join(parts)


def render(markdown: str) -> str:
    lines = markdown.split("\n")
    out: list[str] = []
    i = 0
    list_stack: list[str] = []

    def close_lists() -> None:
        while list_stack:
            out.append(f"</{list_stack.pop()}>")

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            close_lists()
            lang = stripped[3:].strip()
            i += 1
            block = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                block.append(lines[i])
                i += 1
            i += 1
            cls = f' class="lang-{html.escape(lang)}"' if lang else ""
            out.append(f"<pre><code{cls}>{html.escape(chr(10).join(block))}</code></pre>")
            continue

        if not stripped:
            close_lists()
            i += 1
            continue

        if re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", stripped):
            close_lists()
            out.append("<hr>")
            i += 1
            continue

        heading = re.match(r"(#{1,6})\s+(.*)", stripped)
        if heading:
            close_lists()
            level = len(heading.group(1))
            text = heading.group(2)
            out.append(f'<h{level} id="{slugify(text)}">{inline(text)}</h{level}>')
            i += 1
            continue

        # Table: a pipe row followed by a separator row.
        if stripped.startswith("|") and i + 1 < len(lines) and re.fullmatch(
            r"\|[\s:\-|]+\|", lines[i + 1].strip()
        ):
            close_lists()
            block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                block.append(lines[i])
                i += 1
            out.append(render_table(block))
            continue

        if stripped.startswith(">"):
            close_lists()
            quote = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                # Strip one level of "> " only, so nesting and indentation survive.
                content = lines[i].strip()[1:]
                quote.append(content[1:] if content.startswith(" ") else content)
                i += 1
            # Render recursively: blockquotes may contain headings, lists, tables.
            out.append(f"<blockquote>{render(chr(10).join(quote))}</blockquote>")
            continue

        bullet = re.match(r"[-*+]\s+(.*)", stripped)
        number = re.match(r"\d+\.\s+(.*)", stripped)
        if bullet or number:
            want = "ul" if bullet else "ol"
            if not list_stack or list_stack[-1] != want:
                close_lists()
                out.append(f"<{want}>")
                list_stack.append(want)
            content = (bullet or number).group(1)
            # Absorb continuation lines belonging to this bullet.
            i += 1
            while (
                i < len(lines)
                and lines[i].strip()
                and not re.match(r"([-*+]|\d+\.)\s+", lines[i].strip())
                and not lines[i].strip().startswith(("#", "|", "```", ">"))
                and lines[i].startswith((" ", "\t"))
            ):
                content += " " + lines[i].strip()
                i += 1
            out.append(f"<li>{inline(content)}</li>")
            continue

        close_lists()
        para = [stripped]
        i += 1
        while (
            i < len(lines)
            and lines[i].strip()
            and not lines[i].strip().startswith(("#", "|", "```", ">", "-", "*"))
            and not re.match(r"\d+\.\s", lines[i].strip())
        ):
            para.append(lines[i].strip())
            i += 1
        out.append(f"<p>{inline(' '.join(para))}</p>")

    close_lists()
    return "\n".join(out)


CSS = """
:root{--bg:#fbfaf8;--fg:#22201d;--muted:#6b655d;--line:#e2ded6;--accent:#8a4b2a;
--code-bg:#f2efe9;--card:#fff;}
@media (prefers-color-scheme:dark){:root{--bg:#16151a;--fg:#e6e2db;--muted:#9a938a;
--line:#2e2b33;--accent:#d59a6a;--code-bg:#1f1d24;--card:#1b1a20;}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}
#wrap{display:flex;min-height:100vh}
nav{width:260px;flex:0 0 260px;border-right:1px solid var(--line);padding:24px 16px;
position:sticky;top:0;height:100vh;overflow-y:auto;background:var(--card)}
nav h2{font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin:0 0 12px}
nav a{display:block;padding:7px 10px;border-radius:6px;color:var(--fg);text-decoration:none;font-size:14px}
nav a:hover{background:var(--code-bg)}
main{flex:1;min-width:0;padding:40px 32px 120px;max-width:900px;margin:0 auto}
h1{font-size:1.9rem;line-height:1.25;margin:0 0 .6em;padding-bottom:.3em;border-bottom:2px solid var(--accent)}
h2{font-size:1.4rem;margin:2em 0 .6em;padding-bottom:.25em;border-bottom:1px solid var(--line)}
h3{font-size:1.15rem;margin:1.6em 0 .5em;color:var(--accent)}
h4{font-size:1rem;margin:1.3em 0 .4em}
a{color:var(--accent)}
code{background:var(--code-bg);padding:.12em .35em;border-radius:4px;
font:.87em/1.5 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
pre{background:var(--code-bg);padding:14px 16px;border-radius:8px;overflow-x:auto;
border:1px solid var(--line)}
pre code{background:none;padding:0;font-size:.85rem;line-height:1.55}
.tw{overflow-x:auto;margin:1.1em 0}
table{border-collapse:collapse;width:100%;font-size:.92rem}
th,td{border:1px solid var(--line);padding:8px 11px;text-align:left;vertical-align:top}
th{background:var(--code-bg);font-weight:600}
blockquote{margin:1.1em 0;padding:.8em 1.1em;border-left:3px solid var(--accent);
background:var(--code-bg);border-radius:0 6px 6px 0;color:var(--muted)}
blockquote>*:first-child{margin-top:0}
blockquote>*:last-child{margin-bottom:0}
blockquote h1,blockquote h2,blockquote h3,blockquote h4{border:0;padding:0;color:var(--fg);
font-size:1.08rem;margin:.1em 0 .5em}
blockquote strong{color:var(--fg)}
blockquote table{background:var(--card)}
hr{border:0;border-top:1px solid var(--line);margin:2.4em 0}
ul,ol{padding-left:1.5em}
li{margin:.3em 0}
.section{scroll-margin-top:20px}
.toggle{display:none;position:fixed;top:12px;left:12px;z-index:10;background:var(--card);
color:var(--fg);border:1px solid var(--line);border-radius:6px;padding:8px 12px;font-size:14px}
@media(max-width:820px){
  nav{display:none;position:fixed;z-index:9;width:80%;max-width:300px}
  nav.open{display:block}
  .toggle{display:block}
  main{padding:64px 16px 100px}
}
@media print{nav,.toggle{display:none}main{max-width:none;padding:0}}
"""

JS = """
document.querySelector('.toggle').addEventListener('click',function(){
  document.querySelector('nav').classList.toggle('open');
});
document.querySelectorAll('nav a').forEach(function(a){
  a.addEventListener('click',function(){
    document.querySelector('nav').classList.remove('open');
  });
});
"""


def build(output: Path) -> Path:
    sections, toc = [], []
    for filename, title in PAGES:
        path = HERE / filename
        if not path.exists():
            print(f"  skipped (missing): {filename}")
            continue
        anchor = slugify(path.stem)
        toc.append(f'<a href="#{anchor}">{html.escape(title)}</a>')
        sections.append(
            f'<section class="section" id="{anchor}">{render(path.read_text(encoding="utf-8"))}</section>'
        )
        print(f"  added: {filename}")

    doc = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CySA+ (CS0-003) Offline Study Pack</title>
<style>{CSS}</style>
</head><body>
<button class="toggle" aria-label="Toggle contents">&#9776; Contents</button>
<div id="wrap">
<nav><h2>Contents</h2>{''.join(toc)}</nav>
<main>{''.join(sections)}</main>
</div>
<script>{JS}</script>
</body></html>"""

    output.write_text(doc, encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-o", "--output", type=Path, default=HERE / "cysa-offline.html",
        help="output HTML path (default: alongside this script)",
    )
    args = parser.parse_args()
    print("Building offline study pack...")
    result = build(args.output)
    size_kb = result.stat().st_size / 1024
    print(f"\nWrote {result} ({size_kb:.0f} KB)")
    print("Open it in any browser. No connection required.")


if __name__ == "__main__":
    main()
