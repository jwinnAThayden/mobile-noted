# CompTIA CySA+ (CS0-003) — Offline Study Pack

Self-contained study material for the CompTIA Cybersecurity Analyst (CySA+)
exam. Everything here is plain Markdown with **no external links required** —
clone once, read anywhere, no connection needed.

> **Note on sources.** This pack is written from the publicly published CS0-003
> exam objectives and general security-domain knowledge. It is *not* a copy of
> CompTIA's CertMaster course, and it is not a substitute for your licensed
> course material. Cross-check the domain/objective numbering against the free
> official objectives PDF from CompTIA when you next have a connection.

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

| # | Domain | Weight | File |
|---|---|---|---|
| 1 | Security Operations | 33% | [`01-security-operations.md`](01-security-operations.md) |
| 2 | Vulnerability Management | 30% | [`02-vulnerability-management.md`](02-vulnerability-management.md) |
| 3 | Incident Response and Management | 20% | [`03-incident-response.md`](03-incident-response.md) |
| 4 | Reporting and Communication | 17% | [`04-reporting-communication.md`](04-reporting-communication.md) |

## Supporting references

- [`acronyms.md`](acronyms.md) — every acronym the exam expects you to expand
- [`tools-reference.md`](tools-reference.md) — what each named tool does and when an analyst reaches for it
- [`commands-cheatsheet.md`](commands-cheatsheet.md) — the CLI you must be able to read under time pressure
- [`flashcards.md`](flashcards.md) — Q/A drill deck, one fact per line
- [`frameworks.md`](frameworks.md) — kill chain, Diamond Model, ATT&CK, OWASP, and friends side by side
- [`study-plan.md`](study-plan.md) — a 6-week schedule with checkpoints

## Reading it offline

**In Noted (this repo's app):** these are ordinary `.md` files. Open the desktop
app and use *File → Import* on any of them, or point the mobile app's storage
directory at `study/cysa-plus/`.

**Single-file HTML:** run `python study/cysa-plus/build_offline_html.py` to bundle
everything into `cysa-offline.html` — one file, no CDN, no JavaScript
dependencies, opens in any browser on a plane.

**On a phone:** `git clone` the repo once over Wi-Fi; every file is text and the
whole pack is well under a megabyte.

## How to use this pack

1. Read the domain file end to end once, slowly. Don't take notes yet.
2. Re-read with `flashcards.md` open; anything you can't answer cold, mark it.
3. Drill the marked cards daily until they're automatic.
4. Performance-based questions (PBQs) are where people lose time — practise
   reading log excerpts and `nmap`/`tcpdump` output from
   `commands-cheatsheet.md` until parsing them is reflexive.

## Exam-day mechanics worth knowing

- PBQs cluster at the **start**. Flag and skip them; bank the multiple-choice
  points first, then return with whatever time is left.
- CySA+ is an *analyst* exam, not a *tool operator* exam. When two answers both
  look technically right, pick the one that reflects better **process**
  (escalate, document, preserve evidence, validate before acting).
- "First/next/best" in the stem is doing work. Read it twice.
