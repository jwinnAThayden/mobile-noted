# Six-Week CySA+ Study Plan

Assumes ~8–10 hours per week. Adjust the calendar, keep the sequence.

## Week 1 — Foundations and Security Operations, part 1
- Read `01-security-operations.md` sections 1.1 and 1.2 twice.
- Build the logging table from memory on blank paper.
- Drill: Windows Event IDs, Sysmon event IDs, order of volatility.
- **Checkpoint:** can you list five host indicators and five network indicators
  and explain what each usually means?

## Week 2 — Security Operations, part 2
- Read sections 1.3–1.5.
- Work through `commands-cheatsheet.md`: run every nmap and tcpdump command in a
  lab (or read output samples until parsing them is automatic).
- Practise reading an email header top to bottom.
- **Checkpoint:** explain SPF vs DKIM vs DMARC without notes. Explain the
  Pyramid of Pain and why TTP-level detection matters.

## Week 3 — Vulnerability Management, part 1
- Read `02-vulnerability-management.md` sections 2.1–2.3.
- Memorise the CVSS v3.1 base metrics and practise reading vectors until you can
  estimate severity from the string alone.
- Drill: scan types and their trade-offs; true/false positive/negative.
- **Checkpoint:** given a scanner finding, can you argue whether it's a false
  positive and what you'd do to validate?

## Week 4 — Vulnerability Management, part 2
- Read sections 2.4–2.5.
- Memorise the vulnerability classes and their *specific* mitigations —
  the exam wants "parameterised queries", not "validate input".
- Drill: inhibitors to remediation, compensating controls, risk responses.
- **Checkpoint:** explain the full vulnerability management lifecycle and name
  the step people skip (verification).

## Week 5 — Incident Response
- Read `03-incident-response.md` fully.
- Memorise: order of volatility, NIST 800-61 phases, chain of custody elements.
- Compare the frameworks using `frameworks.md` until you can say when each fits.
- **Checkpoint:** walk through a ransomware incident end to end, naming your
  first three actions and justifying the containment choice.

## Week 6 — Reporting, review, and exam prep
- Read `04-reporting-communication.md`.
- Full pass through `flashcards.md`; mark and re-drill every miss.
- Take timed practice exams. Review **every** question you got right for the
  wrong reason as well as every miss.
- Re-read the self-check questions at the end of each domain file.
- **Checkpoint:** consistently scoring above 80% on practice exams.

---

## Ongoing daily habits

- 15 minutes of flashcards, every day, no exceptions. Spacing beats cramming.
- Read one real incident write-up or threat report a week and map it to ATT&CK.
- Say answers out loud. If you can't explain it in a sentence, you don't have it.

## The week before

- Stop learning new material three days out; consolidate only.
- Re-drill acronyms, CVSS metrics, event IDs, order of volatility, and GDPR's
  72 hours — the pure-recall items that are free marks.
- Sleep. Tired pattern-matching is the main cause of avoidable misses on PBQs.

## Exam-day approach

1. Flag and skip the PBQs on the first pass — they're front-loaded and they eat
   time. Bank the multiple-choice points first.
2. On multiple choice, eliminate two answers before choosing between the rest.
3. When two answers are technically correct, pick the one showing better
   **process**: validate, document, preserve, escalate.
4. Watch for "first", "next", "best", "most likely", and "least" — they reverse
   or reorder the answer.
5. Budget roughly 90 seconds per multiple-choice question, leaving ~45 minutes
   for the PBQs and review.
