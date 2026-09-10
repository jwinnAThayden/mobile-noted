# Developing

Open the folder in VS Code. It's configured — interpreter, tests, formatting,
run and debug targets are all in `.vscode/`.

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

VS Code will offer the recommended extensions on first open. The ones that
matter are **Python**, **Ruff**, and **EditorConfig**.

---

## Running it

**F5** gives you four launch targets:

| Target | Does |
|---|---|
| **Web app (Flask)** | Debug server on :5000, auto-reload, rebuilds content first |
| **Web app (gunicorn, as Railway runs it)** | The production start command, for reproducing deploy issues |
| **Build offline HTML** | Regenerates `cysa-offline.html` |
| **Build content.json** | Regenerates the web app payload |

**Ctrl/Cmd-Shift-B** runs *Build everything* — offline HTML plus web app content.
Other tasks live under **Terminal → Run Task**: `Test`, `Lint`,
`Install dependencies`, `Verify checksums`.

---

## How the pieces fit

The Markdown files at the root are the **single source**. Three outputs are
generated from them, and none should be edited by hand:

```
*.md  ──┬─→ build_offline_html.py ──→ cysa-offline.html      (one-file, offline)
        │                         └─→ cysa-artifact.html     (--artifact, hosted)
        ├─→ build_audio.py        ──→ audio/*.mp3            (pre-rendered speech)
        └─→ webapp/build_content.py ─→ webapp/static/content.json  (the app)
```

`build_content.py` imports the other two rather than reimplementing them, so
display HTML and spoken prose stay identical across all three outputs. Change
the renderer once and every output follows.

**After editing any Markdown, run *Build everything*.** CI fails if the
generated files don't match their sources.

---

## Tests

```bash
pytest            # or the Test task, or the Testing panel
```

25 tests, and most of them exist because something broke once:

- **Emphasis around a link containing a code span** rendered as literal
  asterisks — the renderer split on code spans before matching `**`, so the
  pair never matched. Two tests pin this.
- **Blockquotes were flattened** into a single inline run, losing headings.
- **Event IDs read as quantities** — "four thousand six hundred twenty-four"
  instead of "four six two four".
- **Utterance length** — long strings are unreliable across speech engines, so
  a test asserts every chunk stays under the cap.
- **Card ids are unique** — scheduling is keyed on them; duplicates would make
  two cards share one review history.

Add a test whenever you fix a rendering bug. They're fast (~0.05s) and the
transform is exactly the kind of code that regresses quietly.

---

## Linting

```bash
ruff check .          # and ruff check . --fix
```

Configured in `pyproject.toml`. Ruff formats on save in VS Code.

Worth knowing: ruff caught a duplicate `"SBOM"` key in `build_audio.py`'s
pronunciation table, where the second silently shadowed the first. That table
is a dict literal of ~90 entries and grows — the linter is the only thing
watching it.

---

## The web app

See [`webapp/README.md`](webapp/README.md) for architecture. In short: entirely
static, Flask only exists so a service worker can register (they can't from
`file://`) and to set two headers.

The front end is plain ES5-flavoured JavaScript in three files with no build
step and no dependencies — `tts.js` (speech), `cards.js` (SM-2), `app.js`
(wiring). That's deliberate: the whole point is a page that works offline on a
phone forever, and a toolchain is a thing that rots.

The **Live Server** extension is configured to serve `webapp/static` if you
want the front end without Flask — but the service worker won't register from
it on a non-localhost origin, so use the Flask target when testing offline
behaviour.

---

## CI

`.github/workflows/ci.yml` runs ruff, pytest, and a check that the generated
files match their sources. That last one matters most: a stale `content.json`
ships wrong notes to every installed app, and a stale service-worker stamp
stops the update reaching phones at all.

---

## Deploying

See [`DEPLOY.md`](DEPLOY.md). Railway redeploys on push to `main`.
