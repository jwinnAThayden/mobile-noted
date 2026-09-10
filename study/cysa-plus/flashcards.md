# CySA+ Flashcard Deck

Format: **Q** on one line, **A** on the next. Cover the answers with your hand,
or split on `|` if you want to import into Anki (`Q | A`).

---

## Domain 1 — Security Operations

**Q** Which Windows Event ID records a successful logon?
**A** 4624 (check Logon Type: 2 = interactive, 3 = network, 10 = RDP)

**Q** Which Event ID records process creation?
**A** 4688 — and command-line auditing must be explicitly enabled

**Q** Which Event ID means the audit log was cleared?
**A** 1102 — always investigate; it's a defence-evasion signal

**Q** Which Sysmon event ID logs process creation with hashes and command line?
**A** Event ID 1

**Q** Which Sysmon event ID logs DNS queries?
**A** Event ID 22

**Q** NetFlow vs full packet capture — what's the difference?
**A** NetFlow is metadata (5-tuple, counters, timing); pcap includes payload. Flow scales for months, pcap for days

**Q** What makes a process suspicious even when the name is legitimate?
**A** Its parent. `winword.exe → powershell.exe` is malicious regardless of names; `svchost.exe` not parented by `services.exe` is masquerading

**Q** What is beaconing and how do you spot it?
**A** Regular-interval callbacks to C2. Look for tight interval clustering and consistent byte counts; discriminate from update checkers by destination reputation

**Q** What does SPF verify?
**A** That the sending IP is authorised to send for the envelope-sender domain

**Q** What does DKIM verify?
**A** A cryptographic signature proving the message wasn't altered in transit

**Q** What does DMARC add over SPF and DKIM?
**A** Alignment with the *visible* From header, a policy (none/quarantine/reject), and reporting

**Q** Which direction do you read a Received: header chain?
**A** Bottom to top — the bottom-most Received is the origin

**Q** What's the classic BEC header tell?
**A** Reply-To differs from From — the display name looks internal, replies go external

**Q** Name the Pyramid of Pain levels bottom to top.
**A** Hash values, IP addresses, domain names, network/host artefacts, tools, TTPs

**Q** Why detect at the TTP level?
**A** TTPs are expensive for the adversary to change; hashes and IPs are trivially rotated

**Q** STIX vs TAXII?
**A** STIX is the language for describing threat intel; TAXII is the transport that moves it

**Q** TLP:AMBER means you can share with…?
**A** Your organisation and clients on a need-to-know basis (AMBER+STRICT = your organisation only)

**Q** TLP:GREEN means?
**A** The peer community — but not public

**Q** What makes threat hunting different from alert triage?
**A** Hunting is proactive and hypothesis-driven; it begins without an alert

**Q** A hunt finds nothing. Was it a failure?
**A** No — a hunt that produces a new detection rule or exposes a visibility gap succeeded

**Q** What is the Admiralty Code used for?
**A** Rating threat intel: source reliability (A–F) and information credibility (1–6)

**Q** Which tasks are good automation candidates?
**A** Repeatable, high-volume, low-judgement tasks with well-defined inputs — enrichment, IOC lookups, ticket creation

**Q** What's the danger of over-automation?
**A** An automated containment action that fires on a false positive can cause the outage the attacker wanted

**Q** Recognise: `powershell -nop -w hidden -enc <base64>`
**A** Malicious download-and-execute cradle — no profile, hidden window, encoded command

**Q** SAML vs OAuth vs OIDC?
**A** SAML = XML-based enterprise SSO; OAuth 2.0 = authorisation delegation (not authentication); OIDC = authentication layer on top of OAuth

**Q** What is a CASB?
**A** Cloud Access Security Broker — a policy enforcement point between users and cloud services; discovers shadow IT

**Q** Split tunnel vs full tunnel VPN?
**A** Split sends only corporate traffic through the VPN (faster, less visibility); full tunnel inspects everything

---

## Domain 2 — Vulnerability Management

**Q** Why does a credentialed scan produce fewer false positives?
**A** It authenticates and reads actual patch level and configuration rather than inferring from banners

**Q** RHEL reports a vulnerable OpenSSH version but the patch is applied. Why?
**A** Back-ported patches — the vendor fixes the flaw without changing the version banner. It's a **false positive**

**Q** Which finding type is most dangerous?
**A** False negative — a real vulnerability the scanner missed

**Q** SAST vs DAST?
**A** SAST reads source without running it (early, more false positives); DAST attacks the running app (finds runtime/config issues, no source needed)

**Q** What does SCA produce?
**A** An inventory of third-party dependencies against known CVEs — an SBOM

**Q** Expand the CVSS base metrics.
**A** AV (Attack Vector), AC (Attack Complexity), PR (Privileges Required), UI (User Interaction), S (Scope), C/I/A impacts

**Q** What does `S:C` mean in a CVSS vector?
**A** Scope Changed — the vulnerability affects resources beyond its own security authority. Always worse

**Q** What's the score band for Critical?
**A** 9.0–10.0

**Q** What does `AV:N/AC:L/PR:N/UI:N` describe?
**A** Network-reachable, low complexity, no privileges, no user interaction — the worst possible reachability

**Q** What does EPSS measure?
**A** Probability the vulnerability will be exploited in the wild in the next 30 days

**Q** What is CISA KEV?
**A** The Known Exploited Vulnerabilities catalogue — confirmed in-the-wild exploitation. A KEV-listed medium can outrank a non-KEV critical

**Q** Does CVSS measure risk?
**A** No — severity only. Risk requires asset value, exposure, exploitability, and compensating controls

**Q** Correct fix for SQL injection?
**A** Parameterised queries / prepared statements (input validation alone is not the exam's answer)

**Q** Reflected vs stored vs DOM-based XSS?
**A** Reflected = in the response to a crafted request; stored = persisted and served to every viewer (most severe); DOM-based = client-side only, never reaches the server

**Q** Primary XSS mitigation?
**A** Context-appropriate output encoding, plus CSP and HttpOnly cookies

**Q** What is SSRF and what's the cloud-specific target?
**A** Server fetches an attacker-controlled URL; in cloud it targets the metadata endpoint 169.254.169.254 to steal instance credentials. IMDSv2 mitigates

**Q** What is IDOR?
**A** Insecure Direct Object Reference — changing an identifier in a request to access another user's data. A broken access control failure

**Q** What's #1 on the OWASP Top 10 (2021)?
**A** Broken Access Control

**Q** Buffer overflow mitigations?
**A** ASLR, DEP/NX, stack canaries, bounds checking, memory-safe languages

**Q** What is TOCTOU?
**A** Time of Check to Time of Use — a race condition where state changes between validation and use

**Q** Vertical vs horizontal privilege escalation?
**A** Vertical = user to admin; horizontal = user to another user's data at the same level

**Q** You cannot patch a medical device. What now?
**A** Compensating controls: network segmentation, virtual patching at IPS/WAF, disabling the vulnerable feature, restricting access, enhanced monitoring

**Q** Name the four risk responses.
**A** Mitigate, transfer, avoid, accept — and residual risk always remains

**Q** When can a remediation ticket close?
**A** Only after a verification rescan confirms the fix. Remediation isn't complete until verified

**Q** A vulnerability keeps reappearing after remediation. What's the real problem?
**A** Process — a stale golden image or config drift, not patching diligence

**Q** Why is scan coverage the metric that gates all the others?
**A** Metrics computed over a fraction of your estate misrepresent risk entirely

**Q** Why not actively scan ICS/SCADA?
**A** Active probing can cause physical process disruption. Use passive discovery, or a test environment

**Q** SLE and ALE formulas?
**A** SLE = Asset Value × Exposure Factor; ALE = SLE × ARO

---

## Domain 3 — Incident Response

**Q** Name the seven Cyber Kill Chain stages.
**A** Reconnaissance, Weaponisation, Delivery, Exploitation, Installation, Command and Control, Actions on Objectives

**Q** Main weakness of the Cyber Kill Chain?
**A** Linear and malware/perimeter-centric — poor fit for insider threat or credential-only attacks

**Q** Name the four Diamond Model vertices.
**A** Adversary, Capability, Infrastructure, Victim

**Q** What is the Diamond Model actually for?
**A** Pivoting — from one known vertex you discover the others

**Q** ATT&CK structure?
**A** Tactics (the goal) × Techniques (how) × Sub-techniques × Procedures (observed implementations)

**Q** What is MITRE D3FEND?
**A** A knowledge base of defensive countermeasures, the counterpart to ATT&CK

**Q** NIST SP 800-61 phases?
**A** Preparation; Detection and Analysis; Containment, Eradication and Recovery; Post-Incident Activity

**Q** Order of volatility, most to least?
**A** Registers/cache → routing table, ARP cache, process table, RAM → temp filesystems → disk → remote logs → physical config → archival media

**Q** Why capture memory before powering off?
**A** Encryption keys, injected code, and live network connections exist only in RAM

**Q** What is chain of custody and why does it matter?
**A** An unbroken documented record of who handled evidence, when, and why. Gaps can render evidence inadmissible

**Q** What does a write blocker do?
**A** Prevents any write to original media during acquisition — you analyse the image, never the original

**Q** IOC vs IOA?
**A** IOC = evidence something already happened; IOA = behaviour indicating an attack in progress. IOAs catch novel attacks

**Q** Why isolate with EDR rather than power off?
**A** It stops network-borne spread while preserving volatile memory evidence and keeping the host analysable

**Q** Trade-off of immediate containment?
**A** Stops damage but may alert the adversary and destroy volatile evidence; delayed containment preserves intelligence but risks further loss

**Q** Eradication removed the malware but the host was reinfected. What was skipped?
**A** Closing the vulnerability that allowed entry — eradication must remove the vector, not just the payload

**Q** When is reimaging the only trustworthy option?
**A** Root-level or kernel-level compromise (rootkits) — you cannot verifiably clean it

**Q** What must be true of a backup before restoring?
**A** It must predate the compromise. Attacker dwell time is often weeks, so recent backups may already contain the backdoor

**Q** What must be rotated after a domain compromise?
**A** Every credential the adversary could reach — including service accounts and KRBTGT (twice, for Golden Ticket)

**Q** Why run incident communications out-of-band?
**A** If the adversary is in your email or chat, coordinating there hands them your response plan

**Q** RTO vs RPO?
**A** RTO = how long until service is restored; RPO = how much data loss is tolerable

**Q** What is a tabletop exercise?
**A** A discussion-based walkthrough of a scenario — cheapest way to find process and authority gaps

**Q** What are the three incident impact dimensions?
**A** Functional impact, information impact, and recoverability

**Q** What is dwell time?
**A** How long the adversary was present before detection — the headline IR metric

**Q** What makes lessons-learned productive?
**A** Held promptly, blameless, and producing tracked actions with owners and due dates

**Q** Root cause analysis: "the user clicked the link" — is that a root cause?
**A** No. Ask why the link arrived, why it executed, why it reached the internet, and why nothing alerted

---

## Domain 4 — Reporting and Communication

**Q** Name four inhibitors to remediation.
**A** MOU, SLA, organisational governance, business process interruption, degrading functionality, legacy systems, proprietary systems

**Q** Correct analyst response to an inhibitor?
**A** Document the risk, propose compensating controls, and escalate the risk-acceptance decision to the business owner

**Q** How long does GDPR give you to notify the supervisory authority?
**A** 72 hours from becoming aware of the breach

**Q** What belongs in an incident report executive summary?
**A** Plain language: what happened, what was affected, what you did, what it means, what's next. No CVEs, no jargon

**Q** What's the spine of an incident report?
**A** The timeline — timestamps with time zones, correlated across sources

**Q** Who decides breach notification obligations?
**A** Legal counsel — not the analyst

**Q** Why involve legal early?
**A** Regulatory duties, and to establish attorney–client privilege over the investigation where applicable

**Q** What does a high ratio of externally-reported incidents indicate?
**A** A serious internal detection and visibility failure

**Q** What does an exception without an expiry date represent?
**A** Unmanaged risk — exceptions must be time-bounded with a review date and named owner

**Q** How do you pitch remediation to an executive audience?
**A** Business risk, trend direction, and cost — one page, no CVSS vectors

**Q** What does recurrence in vulnerability reporting tell you?
**A** A process failure (golden image, config drift), not an individual's negligence

**Q** Why does cyber insurance matter during an incident?
**A** Carriers often require prompt notification and may mandate their own IR firm; failing to notify can void coverage
