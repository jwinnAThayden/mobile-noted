# Frameworks Side by Side

A single page for the comparison questions.

## Attack frameworks

| | Cyber Kill Chain | Diamond Model | MITRE ATT&CK | Unified Kill Chain |
|---|---|---|---|---|
| **Shape** | 7 linear stages | 4 connected vertices | Matrix of tactics × techniques | 18 phases |
| **Best for** | Explaining an intrusion to leadership | Pivoting during analysis; actor clustering | Detection coverage; shared vocabulary | End-to-end incl. internal movement |
| **Weakness** | Linear, malware/perimeter-centric | Not a process; no defensive guidance | Large; not a narrative | Complex |
| **Use it when** | Reporting | Investigating | Mapping detections | Modelling full campaigns |

### Kill Chain ↔ ATT&CK rough mapping
| Kill Chain | ATT&CK tactics |
|---|---|
| Reconnaissance | Reconnaissance, Resource Development |
| Weaponisation | Resource Development |
| Delivery | Initial Access |
| Exploitation | Execution |
| Installation | Persistence, Privilege Escalation, Defense Evasion |
| C2 | Command and Control |
| Actions on Objectives | Credential Access, Discovery, Lateral Movement, Collection, Exfiltration, Impact |

## Incident response process

| NIST SP 800-61 (4 phases) | SANS (6 steps) |
|---|---|
| Preparation | Preparation |
| Detection and Analysis | Identification |
| Containment, Eradication, and Recovery | Containment |
| " | Eradication |
| " | Recovery |
| Post-Incident Activity | Lessons Learned |

## NIST Cybersecurity Framework functions
**Govern** (CSF 2.0) · **Identify** · **Protect** · **Detect** · **Respond** · **Recover**

## Threat modelling

| Model | Structure |
|---|---|
| **STRIDE** | Spoofing, Tampering, Repudiation, Information disclosure, Denial of service, Elevation of privilege |
| **DREAD** | Damage, Reproducibility, Exploitability, Affected users, Discoverability (risk rating) |
| **PASTA** | Process for Attack Simulation and Threat Analysis — 7 risk-centric stages |
| **Attack trees** | Goal at the root, attack paths as branches |

## Pyramid of Pain (bottom = easy for adversary to change)

```
            TTPs                  ← Tough!
         Tools                    ← Challenging
   Network/Host Artifacts         ← Annoying
       Domain Names               ← Simple
       IP Addresses               ← Easy
       Hash Values                ← Trivial
```

Detect higher up and you force the adversary to retool, not just re-register.

## Traffic Light Protocol

| Marking | Share with |
|---|---|
| `TLP:RED` | Named recipients only — no onward sharing |
| `TLP:AMBER` | Recipient's organisation and clients, need-to-know |
| `TLP:AMBER+STRICT` | Recipient's organisation only |
| `TLP:GREEN` | The community / peer organisations — not public |
| `TLP:CLEAR` | Unrestricted; public release permitted |

## OWASP Top 10 (2021)

1. Broken Access Control
2. Cryptographic Failures
3. Injection (incl. XSS)
4. Insecure Design
5. Security Misconfiguration
6. Vulnerable and Outdated Components
7. Identification and Authentication Failures
8. Software and Data Integrity Failures
9. Security Logging and Monitoring Failures
10. Server-Side Request Forgery (SSRF)

## Risk formulas

```
SLE = Asset Value × Exposure Factor
ALE = SLE × ARO
Risk = Threat × Vulnerability × Impact
Residual Risk = Inherent Risk − Control Effectiveness
```

## Risk response options
**Mitigate** (apply controls) · **Transfer** (insure/contract) · **Avoid** (stop the activity) · **Accept** (document and own it)
