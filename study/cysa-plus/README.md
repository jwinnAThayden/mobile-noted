# CompTIA CySA+ (CS0-003) — Offline Study Pack

Self-contained study material for the CompTIA Cybersecurity Analyst (CySA+)
exam. **No connection required** — clone once, read anywhere.

> ## Goal
>
> **Download this entire project onto the local device so the full study pack is
> available offline, with no network connection and no dependency on any hosted
> service.**
>
> Every design decision here serves that goal: no CDN links, no external fonts
> or scripts, no build toolchain, no package installs. The whole project is
> plain text plus one generated HTML file, and it is intended to be *held
> locally* — a copy on the device is the primary artefact, not a convenience.
> See [`SETUP.md`](SETUP.md) for how to get it there.
>
> The pack is also fully **narrated** — 105 minutes of offline audio, including
> a 92-card spoken drill. See [`AUDIO.md`](AUDIO.md).

## Start here

Open **[`cysa-offline.html`](cysa-offline.html)** in any browser. It's a single
file with no CDN links, no external scripts, and no network calls: sidebar
contents, dark mode, phone-friendly layout, and it prints cleanly. Copy it to a
phone, tablet, or USB stick and it just works.

The Markdown files are the editable source; the HTML is generated from them.

Prefer to listen? `audio/` holds the whole pack as MP3s — start with
`audio/flashcards.mp3`, a 92-card spoken drill that pauses after each question.
See **[`AUDIO.md`](AUDIO.md)**.

Not set up as a repository yet? See **[`SETUP.md`](SETUP.md)** — about three minutes.

> **Note on sources.** Written from the publicly published CS0-003 exam
> objectives and general security-domain knowledge. It is *not* a copy of
> CompTIA's CertMaster course and is not a substitute for licensed course
> material. Cross-check the domain/objective numbering against the free
> official objectives PDF from CompTIA.

## Exam at a glance

| Item | Value |
|---|---|
| Exam code | CS0-003 |
| Questions | Max 85 (multiple choice + performance-based) |
| Time | 165 minutes |
| Passing score | 750 (scale 100–900) |
| Recommended experience | 4+ years hands-on IR / security analyst work |
| Prerequisite | None formally; Security+ and Network+ knowledge assumed |

## Domains and weighting

| # | Domain | Weight | Source file |
|---|---|---|---|
| 1 | Security Operations | 33% | [`01-security-operations.md`](01-security-operations.md) |
| 2 | Vulnerability Management | 30% | [`02-vulnerability-management.md`](02-vulnerability-management.md) |
| 3 | Incident Response and Management | 20% | [`03-incident-response.md`](03-incident-response.md) |
| 4 | Reporting and Communication | 17% | [`04-reporting-communication.md`](04-reporting-communication.md) |

## Supporting references

- [`acronyms.md`](acronyms.md) — every acronym the exam expects you to expand
- [`tools-reference.md`](tools-reference.md) — what each named tool does and when an analyst reaches for it
- [`commands-cheatsheet.md`](commands-cheatsheet.md) — the CLI you must be able to read under time pressure
- [`flashcards.md`](flashcards.md) — 92-card Q/A drill deck
- [`frameworks.md`](frameworks.md) — kill chain, Diamond Model, ATT&CK, OWASP, and friends side by side
- [`study-plan.md`](study-plan.md) — a six-week schedule with checkpoints
- [`AUDIO.md`](AUDIO.md) — the narrated version: 105 minutes of offline MP3s
- [`MOBILE.md`](MOBILE.md) — getting the pack onto an Android phone for offline use
- [`TESTING.md`](TESTING.md) — a six-test checklist to prove the offline copy actually works

## Rebuilding the HTML

After editing any Markdown file:

```bash
python3 build_offline_html.py
```

Standard library only — nothing to install, works offline. Use `-o PATH` to
write somewhere else.

## How to use this pack

1. Read the domain file end to end once, slowly. Don't take notes yet.
2. Re-read with `flashcards.md` open; mark anything you can't answer cold.
3. Drill the marked cards daily until they're automatic.
4. Performance-based questions are where people lose time — practise reading
   log excerpts and `nmap`/`tcpdump` output from `commands-cheatsheet.md` until
   parsing them is reflexive.

## Exam-day mechanics worth knowing

- PBQs cluster at the **start**. Flag and skip them; bank the multiple-choice
  points first, then return with whatever time is left.
- CySA+ is an *analyst* exam, not a *tool operator* exam. When two answers both
  look technically right, pick the one that reflects better **process**
  (escalate, document, preserve evidence, validate before acting).
- "First/next/best" in the stem is doing work. Read it twice.
