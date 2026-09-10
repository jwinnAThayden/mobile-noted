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
    ("MOBILE.md", "On Your Phone"),
    ("TESTING.md", "Testing It Works"),
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

# Exam weighting, shown as a bar in the contents rail. Real information:
# it says where the study time should go.
WEIGHTS = {
    "01-security-operations": 33,
    "02-vulnerability-management": 30,
    "03-incident-response": 20,
    "04-reporting-communication": 17,
}

CARD_RE = re.compile(
    r"<p><strong>Q</strong>\s*(.*?)</p>\s*<p><strong>A</strong>\s*(.*?)</p>", re.S
)


def as_cards(markup: str) -> str:
    """Turn rendered Q/A paragraph pairs into tap-to-reveal drill cards."""
    def card(match: re.Match) -> str:
        return (
            '<div class="card">'
            f'<p class="q">{match.group(1)}</p>'
            '<button class="reveal" type="button" aria-expanded="false">Show answer</button>'
            f'<p class="a" hidden>{match.group(2)}</p>'
            "</div>"
        )
    return CARD_RE.sub(card, markup)


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "section"


LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
CODE_RE = re.compile(r"`([^`]+)`")


def inline(text: str) -> str:
    """Render inline Markdown.

    Code spans are stashed as placeholders first so that emphasis and links
    spanning them still match - `**[`code`](url)**` is one bold run, and
    splitting on code spans before matching it loses the pairing.
    """
    stash: list[str] = []

    def keep(match: re.Match) -> str:
        stash.append(match.group(1))
        return f"\x00{len(stash) - 1}\x00"

    text = CODE_RE.sub(keep, text)
    text = html.escape(text)

    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", text)

    def link(match: re.Match) -> str:
        label, href = match.group(1), match.group(2)
        if href.endswith(".md"):
            href = "#" + slugify(href[:-3])
        return f'<a href="{href}">{label}</a>'

    text = LINK_RE.sub(link, text)
    return re.sub(r"\x00(\d+)\x00",
                  lambda m: f"<code>{html.escape(stash[int(m.group(1))])}</code>",
                  text)


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
:root{
  --bg:#F5F6F8; --surface:#FFFFFF; --ink:#14171C; --muted:#59616E;
  --line:#DCE0E7; --accent:#1F5C7A; --accent-soft:#E3EEF3; --code-bg:#EDF0F4;
  --shadow:0 1px 2px rgba(20,23,28,.06);
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --bg:#0F1216; --surface:#161A20; --ink:#E4E7EC; --muted:#949CA8;
    --line:#262C35; --accent:#6FB3D2; --accent-soft:#17303C; --code-bg:#191E25;
    --shadow:0 1px 2px rgba(0,0,0,.4);
  }
}
:root[data-theme="dark"]{
  --bg:#0F1216; --surface:#161A20; --ink:#E4E7EC; --muted:#949CA8;
  --line:#262C35; --accent:#6FB3D2; --accent-soft:#17303C; --code-bg:#191E25;
  --shadow:0 1px 2px rgba(0,0,0,.4);
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:var(--serif);font-size:17px;line-height:1.68;
  -webkit-text-size-adjust:100%}
#wrap{display:flex;align-items:flex-start;min-height:100vh}

nav{width:270px;flex:0 0 270px;position:sticky;top:0;height:100vh;overflow-y:auto;
  background:var(--surface);border-right:1px solid var(--line);
  padding:26px 18px;display:flex;flex-direction:column;gap:2px}
nav h2{font-family:var(--sans);font-size:11px;font-weight:600;letter-spacing:.1em;
  text-transform:uppercase;color:var(--muted);margin:0 0 14px}
nav a{font-family:var(--sans);font-size:14px;line-height:1.35;color:var(--ink);
  text-decoration:none;padding:8px 10px;border-radius:6px;display:block}
nav a:hover{background:var(--accent-soft)}
nav a .w{display:block;height:3px;margin-top:6px;border-radius:2px;
  background:var(--accent);opacity:.75}
nav a .pct{font-size:11px;color:var(--muted);float:right;
  font-variant-numeric:tabular-nums}

main{flex:1;min-width:0;max-width:70ch;margin:0 auto;padding:46px 28px 140px;\n  overflow-wrap:break-word}

h1{font-family:var(--sans);font-weight:700;font-size:2rem;line-height:1.15;
  text-wrap:balance;margin:0 0 .5em;letter-spacing:-.02em}
h2{font-family:var(--sans);font-weight:600;font-size:1.35rem;line-height:1.25;
  text-wrap:balance;margin:2.2em 0 .5em;padding-bottom:.3em;
  border-bottom:1px solid var(--line);letter-spacing:-.01em}
h3{font-family:var(--sans);font-weight:600;font-size:1.08rem;margin:1.7em 0 .4em;
  color:var(--accent);text-wrap:balance}
h4{font-family:var(--sans);font-weight:600;font-size:.97rem;margin:1.4em 0 .3em}
p{margin:0 0 1.05em}
a{color:var(--accent)}
strong{font-weight:600}

code{font-family:var(--mono);font-size:.85em;background:var(--code-bg);
  padding:.14em .38em;border-radius:4px}
pre{background:var(--code-bg);border:1px solid var(--line);border-radius:8px;
  padding:14px 16px;overflow-x:auto;margin:1.2em 0}
pre code{background:none;padding:0;font-size:.83rem;line-height:1.6}

.tw{overflow-x:auto;margin:1.3em 0;border:1px solid var(--line);border-radius:8px}
table{border-collapse:collapse;width:100%;font-family:var(--sans);font-size:.87rem;
  font-variant-numeric:tabular-nums}
th,td{padding:9px 12px;text-align:left;vertical-align:top;
  border-bottom:1px solid var(--line)}
th{background:var(--code-bg);font-weight:600;white-space:nowrap}
tr:last-child td{border-bottom:0}

blockquote{margin:1.3em 0;padding:.9em 1.1em;background:var(--accent-soft);
  border-left:3px solid var(--accent);border-radius:0 8px 8px 0}
blockquote>*:first-child{margin-top:0}
blockquote>*:last-child{margin-bottom:0}
blockquote h1,blockquote h2,blockquote h3,blockquote h4{border:0;padding:0;
  color:var(--ink);font-size:1.02rem;margin:.1em 0 .45em}

hr{border:0;border-top:1px solid var(--line);margin:2.6em 0}
ul,ol{padding-left:1.35em;margin:0 0 1.05em}
li{margin:.32em 0}
.section{scroll-margin-top:16px}

/* Flashcard drill */
.card{background:var(--surface);border:1px solid var(--line);border-radius:10px;
  padding:16px 18px;margin:0 0 12px;box-shadow:var(--shadow)}
.card .q{font-family:var(--sans);font-weight:600;font-size:.98rem;margin:0 0 12px}
.card .a{margin:12px 0 0;padding-top:12px;border-top:1px solid var(--line);
  color:var(--ink)}
.reveal{font-family:var(--sans);font-size:.8rem;font-weight:500;cursor:pointer;
  background:var(--accent-soft);color:var(--accent);border:1px solid transparent;
  padding:6px 12px;border-radius:999px}
.reveal:hover{border-color:var(--accent)}
.reveal[aria-expanded="true"]{background:transparent;color:var(--muted)}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}

.toggle{display:none;position:fixed;top:10px;left:10px;z-index:20;
  font-family:var(--sans);font-size:13px;font-weight:500;
  background:var(--surface);color:var(--ink);border:1px solid var(--line);
  border-radius:8px;padding:9px 13px;box-shadow:var(--shadow);cursor:pointer}
.scrim{display:none;position:fixed;inset:0;z-index:9;background:rgba(0,0,0,.45)}
.scrim.on{display:block}

@media(max-width:860px){
  nav{display:none;position:fixed;z-index:10;width:84%;max-width:310px;
    box-shadow:0 0 40px rgba(0,0,0,.3)}
  nav.open{display:flex}
  .toggle{display:block}
  #wrap{display:block}
  main{max-width:none;width:100%;margin:0;padding:62px 16px 120px}
  body{font-size:16px}
  h1{font-size:1.6rem}
}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
@media print{nav,.toggle,.reveal,.scrim{display:none}
  main{max-width:none;padding:0}.card .a[hidden]{display:block!important}}
"""

JS = """
var nav=document.querySelector('nav'),scrim=document.querySelector('.scrim');
function setNav(open){nav.classList.toggle('open',open);scrim.classList.toggle('on',open);}
document.querySelector('.toggle').addEventListener('click',function(){
  setNav(!nav.classList.contains('open'));});
scrim.addEventListener('click',function(){setNav(false);});
nav.addEventListener('click',function(e){if(e.target.tagName==='A')setNav(false);});
document.addEventListener('click',function(e){
  var b=e.target.closest('.reveal'); if(!b)return;
  var a=b.parentNode.querySelector('.a'), open=a.hidden;
  a.hidden=!open; b.setAttribute('aria-expanded',open?'true':'false');
  b.textContent=open?'Hide answer':'Show answer';});
"""


# Offline builds must not reach the network, so they use system faces only.
# The hosted build adds the Plex/Source Serif pairing on top of the same stacks.
FONTS_LOCAL = """
:root{
  --sans:ui-sans-serif,system-ui,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  --serif:Charter,"Bitstream Charter","Iowan Old Style",Georgia,"Times New Roman",serif;
  --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace;
}
"""

FONTS_HOSTED = """
:root{
  --sans:"IBM Plex Sans",ui-sans-serif,system-ui,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  --serif:"Source Serif 4",Charter,"Iowan Old Style",Georgia,"Times New Roman",serif;
  --mono:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
}
"""

FONT_LINK = (
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
    "family=IBM+Plex+Mono:wght@400;500&"
    "family=IBM+Plex+Sans:wght@500;600;700&"
    "family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap\">"
)


def assemble(hosted: bool) -> tuple[str, str]:
    """Return (nav markup, main markup) for the whole pack."""
    sections, toc = [], []
    for filename, title in PAGES:
        path = HERE / filename
        if not path.exists():
            print(f"  skipped (missing): {filename}")
            continue
        stem = path.stem
        anchor = slugify(stem)
        body = render(path.read_text(encoding="utf-8"))
        if stem == "flashcards":
            body = as_cards(body)
        weight = WEIGHTS.get(stem)
        label = html.escape(title)
        if weight:
            bar = (f'<span class="pct">{weight}%</span>{label}'
                   f'<span class="w" style="width:{weight * 2.4:.0f}%"></span>')
        else:
            bar = label
        toc.append(f'<a href="#{anchor}">{bar}</a>')
        sections.append(f'<section class="section" id="{anchor}">{body}</section>')
        print(f"  added: {filename}")
    nav = f'<nav><h2>Contents</h2>{"".join(toc)}</nav>'
    return nav, f'<main>{"".join(sections)}</main>'


SHELL = """<button class="toggle" type="button" aria-label="Toggle contents">\u2630 Contents</button>
<div class="scrim"></div>
<div id="wrap">{nav}{main}</div>"""


def build(output: Path, hosted: bool = False) -> Path:
    nav, main_markup = assemble(hosted)
    fonts = FONTS_HOSTED if hosted else FONTS_LOCAL
    shell = SHELL.format(nav=nav, main=main_markup)

    if hosted:
        # The Artifact runtime supplies doctype, html, head and body.
        doc = (f"<title>CySA+ Analyst Field Notes</title>\n"
               f"{FONT_LINK}\n<style>{fonts}{CSS}</style>\n"
               f"{shell}\n<script>{JS}</script>\n")
    else:
        doc = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CySA+ (CS0-003) Offline Study Pack</title>
<style>{fonts}{CSS}</style>
</head><body>
{shell}
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
    parser.add_argument("--artifact", action="store_true",
                        help="emit a body-only fragment for publishing as an Artifact")
    args = parser.parse_args()
    if args.artifact and args.output == HERE / "cysa-offline.html":
        args.output = HERE / "cysa-artifact.html"
    print("Building hosted page..." if args.artifact else "Building offline study pack...")
    result = build(args.output, hosted=args.artifact)
    size_kb = result.stat().st_size / 1024
    print(f"\nWrote {result} ({size_kb:.0f} KB)")
    print("Open it in any browser. No connection required.")


if __name__ == "__main__":
    main()
