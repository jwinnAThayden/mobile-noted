# Domain 1 — Security Operations (33%)

The largest domain. It covers what you look at, what "bad" looks like, and how
you make the looking repeatable.

---

## 1.1 System and network architecture concepts

### Logging — the analyst's raw material

| Source | What it proves | Watch for |
|---|---|---|
| **Windows Event Log** | Auth, process creation, service installs | 4624 logon, 4625 failed logon, 4688 process create, 4672 special privileges, 7045 service install |
| **Sysmon** | Deep process/network/file telemetry | Event ID 1 (process create with hashes + command line), 3 (network connect), 7 (image load), 8 (CreateRemoteThread), 11 (file create), 22 (DNS query) |
| **Syslog** (RFC 5424) | Unix/network device events | Facility + severity 0–7; severity 0 = emergency, 7 = debug |
| **Firewall / NGFW** | Allow/deny by 5-tuple | Egress denies are more interesting than ingress denies |
| **Proxy / web filter** | Full URL, user agent, bytes | Long POST bodies to rare domains = exfil |
| **DNS** | Every name resolution | NXDOMAIN storms, long labels, high-entropy subdomains |
| **NetFlow / IPFIX** | Who talked to whom, how much, how long | No payload — volume and timing only |
| **EDR** | Process trees, parent-child lineage | The single richest host source |

**Key distinctions the exam tests:**
- **NetFlow** = metadata (5-tuple + counters). **Full packet capture** = payload.
  Flow scales; pcap does not. You keep flow for months, pcap for days.
- **Logging levels** trade fidelity for volume. Debug logging in production is a
  storage and privacy problem, not a security win.
- **Time synchronisation (NTP)** is non-negotiable. Correlating three sources with
  skewed clocks produces a false timeline — and a timeline is evidence.
- **Log retention** is driven by regulation (PCI DSS: 1 year, 3 months
  immediately available) and by dwell time — if attackers sit undetected for
  200 days, 30-day retention means you can never reconstruct the intrusion.

### Operating system concepts

- **Windows Registry** — configuration *and* persistence. Autorun keys:
  `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run`, `RunOnce`,
  `HKLM\SYSTEM\CurrentControlSet\Services`, and Winlogon `Shell`/`Userinit`.
- **System hardening** — remove what you don't need before you defend what's
  left. Disable unused services, close ports, remove default accounts, apply a
  benchmark (CIS, DISA STIG).
- **File structure / permissions** — Linux `rwx` octal, `setuid`/`setgid`
  (a `setuid root` binary in a user-writable directory is a privesc waiting to
  happen), Windows ACLs and inheritance.
- **Configuration file locations** — `/etc/passwd`, `/etc/shadow`,
  `/etc/crontab`, `~/.ssh/authorized_keys`, `/var/log/auth.log`.
- **Processes and services** — a service running as SYSTEM with a binary path
  in a writable folder is *unquoted service path* privesc.
- **Hardware architecture** — TPM (sealed key storage, measured boot), HSM
  (tamper-resistant key operations), Secure Boot, UEFI vs legacy BIOS.

### Infrastructure concepts

- **Serverless** — no OS to patch, but you inherit function-level IAM risk and
  dependency risk. The blast radius is the function's role.
- **Virtualisation** — hypervisor Type 1 (bare metal) vs Type 2 (hosted). The
  nightmare case is **VM escape**: guest → hypervisor → every other guest.
- **Containerisation** — shared kernel means a kernel exploit crosses container
  boundaries. Image provenance and registry signing matter more than in VMs.
- **On-prem vs cloud vs hybrid** — the **shared responsibility model** decides
  who patches what. IaaS: you patch the OS. PaaS: provider does. SaaS: you own
  only configuration and data.

### Network architecture

- **Segmentation** — the single highest-value control against lateral movement.
  Flat networks turn one compromised laptop into domain-wide compromise.
- **Zero trust** — never trust, always verify. **Policy Decision Point (PDP)**
  decides; **Policy Enforcement Point (PEP)** enforces. Identity replaces
  network location as the perimeter.
- **SDN** — control plane separated from data plane; policy pushed centrally.
- **SASE** — network + security delivered as a cloud edge service.
- **Secured zones** — screened subnet (DMZ), jump box/bastion for admin access,
  air gap for the truly sensitive.
- **VPN** — site-to-site vs remote access; **split tunnel** sends only corporate
  traffic through the VPN (faster, less visibility) vs **full tunnel** (all
  traffic inspected, more load).

### Identity and access management

- **MFA** — something you know / have / are. Push fatigue is a real attack;
  number matching and FIDO2 hardware tokens resist it. SMS OTP is the weakest
  common factor (SIM swap, SS7).
- **SSO** — one authentication, many services. **SAML** (XML assertions,
  enterprise web SSO), **OAuth 2.0** (authorisation delegation, *not*
  authentication), **OpenID Connect** (authentication layer on top of OAuth).
- **Federation** — trust relationship across organisational boundaries.
- **Privileged access management (PAM)** — vaulted credentials, session
  recording, just-in-time elevation, automatic rotation.
- **Passwordless** — FIDO2/WebAuthn; phishing-resistant because the credential
  is origin-bound.
- **Cloud access security broker (CASB)** — policy enforcement point between
  users and cloud services; discovers shadow IT.

### Encryption and sensitive data protection

- **Public key infrastructure (PKI)** — CA, RA, CRL, OCSP. Certificate pinning
  breaks MITM inspection (and breaks your proxy).
- **SSL/TLS inspection** — you must decrypt to inspect, which creates a
  privacy and compliance obligation and a single point of interception.
- **Data loss prevention (DLP)** — at rest, in transit, in use. Detection by
  pattern (regex), fingerprint (exact document match), or classification label.
- **Personally identifiable information (PII) / protected health information
  (PHI) / cardholder data (CHD)** — know which regime governs which:
  GDPR → personal data, HIPAA → PHI, PCI DSS → CHD.
- **Data masking / tokenisation / de-identification** — tokenisation replaces
  the value with a reference; masking obscures part of it; encryption is
  reversible with a key.

---

## 1.2 Analysing indicators of potentially malicious activity

### Network-related indicators

| Indicator | What it usually means |
|---|---|
| Bandwidth consumption spike (outbound) | Data exfiltration or DDoS participation |
| Beaconing — regular interval callbacks | C2 channel. Look for low **jitter** and consistent byte counts |
| Irregular peer-to-peer communication | Lateral movement; workstations should rarely talk to each other |
| Rogue device on the network | Unmanaged asset, possible pivot point |
| Scan / sweep | Reconnaissance — internal scans are far more alarming than external |
| Unusual traffic spike | Could be legitimate; correlate with change tickets first |
| Activity on unexpected ports | Tunnelling — SSH on 443, DNS on 53 carrying non-DNS payloads |
| Non-standard port usage | Protocol/port mismatch is a strong signal |

**Beaconing detection:** compute the interval between successive connections
from one host to one destination. Malware C2 shows tight clustering
(e.g. every 60s ±5s). Legitimate software (update checkers) beacons too — the
discriminator is destination reputation, not periodicity alone.

### Host-related indicators

- **Processor consumption** — sustained 100% CPU on an idle workstation:
  cryptomining is the usual suspect.
- **Memory consumption** — memory-resident (fileless) malware lives here and
  leaves nothing on disk.
- **Drive capacity consumption** — staging area for exfil, often a `.rar`/`.7z`
  archive in `C:\Windows\Temp` or `%APPDATA%`.
- **Unauthorised software** — RATs, remote-access tools (AnyDesk, TeamViewer)
  installed outside a change window.
- **Malicious processes** — the tell is **lineage**, not name.
  `winword.exe → cmd.exe → powershell.exe` is malicious regardless of what
  the binary is called. A `svchost.exe` whose parent is not `services.exe` is
  masquerading.
- **Unauthorised changes / privileges** — new local admin, new service, new
  scheduled task, modified registry autorun.
- **Data exfiltration** — large outbound transfers, especially to cloud storage
  or newly registered domains.
- **Abnormal OS process behaviour** — `lsass.exe` being *read* by another
  process is credential dumping (Mimikatz).
- **File system changes / anomalies** — mass rename with a new extension =
  ransomware in progress; shadow copy deletion (`vssadmin delete shadows`) is
  the precursor.
- **Registry changes / anomalies** — persistence, defence evasion (disabling
  Defender via registry policy).
- **Unauthorised scheduled tasks** — `schtasks /create` running from a temp path.

### Application-related indicators

- **Anomalous activity** — an app making outbound connections it has never made.
- **Introduction of new accounts** — especially service accounts with
  interactive logon rights.
- **Unexpected output** — SQL errors leaking schema, stack traces to users.
- **Unexpected outbound communication** — a database server initiating internet
  connections should never happen.
- **Service interruption** — could be DoS, could be the attacker disabling
  logging or AV.
- **Application logs** — HTTP 500 bursts, authentication failures, unusual
  user agents, very long query strings (injection attempts).

### Other indicators

- **Social engineering attacks** — pretexting, phishing, vishing, smishing, BEC.
- **Obfuscated links** — URL shorteners, homoglyph/punycode domains
  (`раypal.com` with a Cyrillic а), open redirects on trusted domains.

---

## 1.3 Tools and techniques for determining malicious activity

### Packet capture

- **Wireshark** — GUI analysis. `Follow TCP Stream` reconstructs a conversation;
  `Statistics → Conversations` finds the top talkers; `Export Objects` pulls
  transferred files out of a capture.
- **tcpdump** — capture on headless boxes. Always write to a file (`-w`) and
  analyse later; analysing live drops packets.
- **WireEdit / Network Miner** — extract artefacts and reassemble sessions.

### Log analysis and correlation

- **SIEM** — aggregation, normalisation, correlation, alerting. The value is
  *correlation across sources*, not storage.
- **Rule writing** — a rule that fires 400 times a day is a rule nobody reads.
  Tune to the environment, then tune again.
- **Search languages** — Splunk SPL, Elastic KQL/Lucene, Sentinel KQL.
- **Sigma** — vendor-neutral detection rule format; converts to whatever your
  SIEM speaks.

### Endpoint

- **EDR** — process trees, isolate-host action, retrospective search.
- **Reputation analysis** — hash lookups (VirusTotal), file/IP/domain scoring.
- **File analysis** — static (strings, PE headers, imports, entropy) vs dynamic
  (execute and observe).
- **Sandboxing** — detonate in isolation. Modern malware is **sandbox-aware**:
  it checks for VM artefacts, low core counts, no mouse movement, and sleeps
  past the analysis window.

### Network

- **DNS and IP reputation** — WHOIS age (a domain registered yesterday is
  suspicious), AbuseIPDB-style scoring.
- **DGA (domain generation algorithm)** detection — high-entropy names,
  NXDOMAIN floods as malware cycles through candidates.
- **Flow analysis** — long-duration, low-bandwidth sessions are the classic
  C2 shape.

### Email analysis

| Header / control | What it tells you |
|---|---|
| **SPF** | Is the sending IP authorised for that domain? Checks the envelope sender |
| **DKIM** | Cryptographic signature — was the message altered in transit? |
| **DMARC** | Policy (`none`/`quarantine`/`reject`) + alignment + reporting. Ties SPF/DKIM to the *visible* From header |
| **Received:** chain | Read **bottom to top** — the bottom-most is the origin |
| **Reply-To mismatch** | Classic BEC tell: From looks internal, Reply-To is external |
| **Message ID / X-headers** | Sending infrastructure fingerprint |
| **Embedded links** | Check the *href*, not the display text |
| **Attachments** | Macro-enabled Office, ISO/IMG (bypasses mark-of-the-web), double extensions |

**Impersonation techniques:** display-name spoofing, lookalike domains
(`rnicrosoft.com`), compromised legitimate accounts (hardest to detect — SPF and
DKIM both pass).

### Programming and scripting for analysts

You are not expected to write production code, but you must **read** it:

- **Python** — the automation default; `requests`, `pandas`, `re` for log parsing.
- **PowerShell** — both the admin tool and the attacker's tool. Recognise
  `-EncodedCommand` (base64), `-nop -w hidden -ExecutionPolicy Bypass`,
  `IEX (New-Object Net.WebClient).DownloadString(...)` — that last one is a
  download-and-execute cradle, memorise it.
- **Shell / Bash** — pipeline literacy: `grep | awk | sort | uniq -c | sort -rn`
  is the analyst's most-used idiom.
- **Regular expressions** — extracting IPs, hashes, and domains from log text.
- **JSON / XML** — every modern API and log format.

---

## 1.4 Threat intelligence and threat hunting

### Intelligence fundamentals

- **Levels:** *strategic* (board-level, risk trends), *operational* (campaigns,
  actor intent), *tactical* (TTPs, immediately actionable).
- **Confidence levels** — never treat a feed as fact. Use the **Admiralty Code**
  (source reliability A–F, information credibility 1–6).
- **Indicator lifecycle** — IOCs decay. An IP burns in days; a TTP lasts years.
  This is the **Pyramid of Pain**: hash values → IP addresses → domain names →
  network/host artefacts → tools → **TTPs**. The higher you detect, the more it
  costs the adversary to adapt.

### Collection sources

- **Open source (OSINT)** — free, broad, noisy.
- **Closed / proprietary** — paid feeds, vetted, timelier.
- **ISAC** (Information Sharing and Analysis Center) — sector-specific
  (FS-ISAC for finance, H-ISAC for health).
- **Internal telemetry** — your own past incidents are your highest-fidelity feed.

### Sharing standards

- **STIX** — the *language* for describing threat information (objects,
  relationships).
- **TAXII** — the *transport* that moves STIX around.
- **MISP** — an open sharing platform.
- **Traffic Light Protocol (TLP):**
  - `TLP:RED` — named recipients only
  - `TLP:AMBER` — recipient's organisation, need-to-know (`AMBER+STRICT` = org only)
  - `TLP:GREEN` — the community, not public
  - `TLP:CLEAR` — unrestricted
  Handling TLP correctly is exam-favourite material.

### Threat actors

| Actor | Motivation | Sophistication |
|---|---|---|
| Nation-state / APT | Espionage, disruption | Very high; long dwell time, custom tooling |
| Organised crime | Financial | High; ransomware, RaaS affiliates |
| Hacktivist | Ideological | Variable; defacement, DDoS, leaks |
| Insider | Grievance, money, or accident | Low technical, high access |
| Script kiddie | Notoriety | Low; known exploits, off-the-shelf tools |
| Supply chain | Varies | Access through a trusted third party |

### Threat hunting

Hunting is **hypothesis-driven** and **proactive** — it starts *without* an
alert. That distinction is the exam's favourite hunting question.

1. Form a hypothesis ("if an adversary used Kerberoasting, I'd see TGS requests
   with RC4 encryption for service accounts").
2. Decide the data required and confirm you actually collect it.
3. Hunt — query, pivot, correlate.
4. Outcome is a win either way: you find evidence, **or** you find a visibility
   gap, **or** you produce a new detection rule.

**Concepts:** *focus on critical assets* first; *bundling critical assets into
protection groups*; *attack vectors*; *integrated intelligence*; *improving
detection capabilities* is the real deliverable — a hunt that finds nothing but
produces a durable detection was still successful.

---

## 1.5 Efficiency and process improvement

### Standardising processes

- **Identification of tasks suitable for automation** — repeatable, high-volume,
  low-judgement, well-defined inputs. Enrichment, ticket creation, and IOC
  lookups qualify. Containment decisions on production systems do not, at least
  not without approval gating.
- **Team coordination** — a documented, repeatable process means results don't
  depend on which analyst caught the ticket.

### Streamlining operations

- **Automation and orchestration (SOAR)** — orchestration connects tools;
  automation executes without a human; a **playbook** encodes the decision tree.
- **Orchestration playbooks** — codify triage so tier-1 handles more, faster.
- **Minimising human engagement** — reserve analyst attention for judgement.
- **Single pane of glass** — one console instead of twelve; reduces context
  switching and missed alerts.
- **Technology and tool integration** — **APIs**, webhooks, and **workflow
  orchestration** are the plumbing.

**Benefits to cite in an exam answer:** reduced **MTTD** and **MTTR**, lower
analyst fatigue and turnover, consistent handling, better metrics, and scale
without linear headcount growth.

**Risks of over-automation:** an automated containment action that isolates a
production database at month-end close causes the outage the attacker wanted.
Always ask what the automation does when it's *wrong*.

---

## Domain 1 self-check

1. Why is a process's parent more diagnostic than its name?
2. What does DMARC add that SPF and DKIM alone cannot provide?
3. Where does "tools" sit on the Pyramid of Pain, and why does that matter?
4. You see 60-second-interval outbound connections of identical size. What do
   you check next before calling it C2?
5. Which TLP marking permits sharing with your whole organisation?
6. Name three tasks that are good automation candidates and one that is not.
