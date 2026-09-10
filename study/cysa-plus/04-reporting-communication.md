# Domain 4 — Reporting and Communication (17%)

The smallest domain and the one technical people most often underestimate. Its
premise: analysis nobody acts on is worthless. Expect scenario questions about
*who* to tell, *when*, and *in what language*.

---

## 4.1 Vulnerability management reporting and communication

### What goes in a vulnerability report

- **Vulnerability details** — CVE, description, affected assets, evidence.
- **Affected hosts** — with owner and business function, not just IP.
- **Risk score** — CVSS, plus contextual adjustment for your environment.
- **Mitigation** — the concrete fix or compensating control.
- **Recurrence** — has this been reported before? Recurrence points at a broken
  process (golden image, config drift), not a lazy admin.
- **Prioritisation** — ranked, with the ranking rationale stated.

### Compliance reports
Evidence for auditors and regulators: scan coverage, findings, remediation
status, exceptions, and the timeline. Mapped to the framework in question
(PCI DSS, HIPAA, SOX, ISO 27001, FedRAMP).

### Action plans

- **Configuration management** — the change record for every fix.
- **Patching** — schedule, rollback plan, verification.
- **Compensating controls** — where patching is impossible.
- **Awareness, training, and education** — when the root cause is human.

### Inhibitors to remediation

Know these by name; the exam asks which one a scenario describes.

| Inhibitor | Meaning |
|---|---|
| **MOU (Memorandum of Understanding)** | Informal agreement constraining action |
| **SLA (Service Level Agreement)** | Uptime commitments limit when you can patch |
| **Organisational governance** | Approval chains and change advisory boards |
| **Business process interruption** | The fix breaks a revenue-generating process |
| **Degrading functionality** | The patch removes a feature the business relies on |
| **Legacy systems** | Unsupported, unpatchable, still load-bearing |
| **Proprietary systems** | Vendor prohibits modification or voids support |

The correct analyst response to an inhibitor is never "patch anyway" — it is
**document the risk, propose compensating controls, and escalate the acceptance
decision to the business owner.**

### Metrics and key performance indicators

- **Trends** — is risk going up or down over time? Direction beats snapshots.
- **Top 10** — most prevalent or highest-risk findings.
- **Critical vulnerabilities and zero-days** — reported separately, immediately.
- **SLO (service level objective)** — remediation targets and adherence rate.
- **Coverage**, **MTTR**, **recurrence rate**, **risk burn-down**.

### Stakeholder identification and communication

| Audience | What they need | Language |
|---|---|---|
| **Executive / board** | Business risk, trend, spend justification | One page, no CVEs, money and risk |
| **Risk / compliance** | Framework mapping, exceptions, evidence | Control language |
| **System owners / IT ops** | Exactly what to fix on which host, and by when | Technical, actionable |
| **Developers** | Code location, class of flaw, secure pattern | Code-level |
| **Legal / privacy** | Regulatory exposure, notification duties | Obligation-focused |

**Rule of thumb the exam rewards:** match the abstraction level to the audience.
A CVSS vector string in a board deck is a communication failure.

---

## 4.2 Incident response reporting and communication

### Stakeholder identification and communication

Who gets told, and when, is a **plan decision made in advance** — not an
improvisation during the incident.

Typical stakeholders: incident response team, IT operations, executive
leadership, **legal counsel**, HR (insider cases), public relations /
communications, affected business units, customers, law enforcement,
regulators, cyber-insurance carrier, and third-party IR retainer.

**Critical points:**
- **Legal is involved early**, both for regulatory duties and to establish
  attorney–client privilege over the investigation where applicable.
- **Communicate out-of-band** if the corporate network or mail may be
  compromised.
- **Limit distribution** on a need-to-know basis during an active incident.
- **Single source of truth** — one designated spokesperson externally; avoid
  contradictory statements.
- Never speculate publicly about attribution or scope before it is established.

### Incident declaration and escalation

- **Declaration** — the formal moment an event becomes an incident, triggering
  the plan. Defined criteria prevent both under- and over-reaction.
- **Escalation** — predefined thresholds and timeframes decide who is woken.
  Escalate on severity, on scope expansion, on regulatory trigger, or when the
  response needs authority you don't have.

### Incident response reporting — required content

- **Executive summary** — plain language, front-loaded, readable by a
  non-technical executive. What happened, what was affected, what you did, what
  it means, what's next.
- **Who, what, when, where, and why** — the factual narrative.
- **Timeline** — the spine of the report. Timestamps with time zone, correlated
  across sources.
- **Scope** — systems, accounts, and data affected; and explicitly what was
  *not* affected.
- **Impact** — operational, financial, reputational, regulatory.
- **Evidence** — with chain of custody references.
- **Recommendations** — prioritised, owned, dated.
- **Lessons learned** — what changes structurally.

Write to be read by someone six months later who wasn't there — that's the test
of a good incident report.

### Legal and regulatory considerations

- **Breach notification timelines** vary by regime. **GDPR: 72 hours** to the
  supervisory authority from becoming aware — the most-quoted number on the
  exam. Others (HIPAA, state breach laws, SEC disclosure rules, PCI DSS) differ;
  know that the obligation exists and that **legal determines it**, not you.
- **Evidence preservation and legal hold** obligations begin early.
- **Law enforcement engagement** — a decision made by leadership and legal;
  it can constrain your remediation timeline.
- **Cyber-insurance** — carriers often require prompt notification and may
  mandate their own IR firm. Failing to notify can void coverage.
- **Regulatory reporting** — sector-specific (financial, healthcare, critical
  infrastructure).

### Root cause analysis in the report
State the *structural* cause and the control that failed, not the individual who
made a mistake. Blame produces silence; blameless analysis produces information.

### Lessons learned
Document what worked, what didn't, what was missing (visibility gaps, tooling
gaps, authority gaps), and the tracked actions arising, each with an owner and
a due date.

### Metrics and KPIs for incident response

- **MTTD**, **MTTA**, **MTTR**, **dwell time**
- Number of incidents by category and severity
- **Alert volume** and **false positive rate**
- Percentage of incidents detected internally vs reported externally — a low
  internal-detection rate is a damning visibility metric
- Recurrence of incident types

---

## Domain 4 self-check

1. Your executive summary opens with "The threat actor leveraged CVE-2023-1234
   to achieve RCE via a deserialisation flaw." What's wrong with it?
2. Name four inhibitors to remediation and the correct analyst response to each.
3. Under GDPR, how long do you have to notify the supervisory authority?
4. Why might the incident bridge be run on a channel outside corporate IT?
5. What does a high ratio of externally-reported incidents tell you?
6. A patch would break a revenue-critical legacy app. What do you do?
