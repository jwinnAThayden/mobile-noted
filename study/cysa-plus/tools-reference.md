# Tools Reference

What each named tool does, and the sentence an exam answer wants.

## Network scanning and discovery
| Tool | Use it for |
|---|---|
| **Nmap** | Host discovery, port/service/version detection, OS fingerprinting, NSE scripting |
| **Angry IP Scanner** | Fast, simple host/port sweep |
| **Masscan** | Internet-scale port scanning |
| **hping3** | Custom packet crafting, firewall rule testing, traceroute over arbitrary protocols |
| **Responder** | LLMNR/NBT-NS poisoning to capture hashes (offensive) |

## Vulnerability scanning
| Tool | Use it for |
|---|---|
| **Nessus / Tenable.io** | Commercial general vulnerability scanning |
| **Qualys** | Cloud-delivered vulnerability management |
| **OpenVAS / Greenbone** | Open-source vulnerability scanner |
| **Rapid7 Nexpose / InsightVM** | Vulnerability management with risk scoring |
| **Nikto** | Web server misconfiguration and dangerous-file checks |
| **OpenSCAP** | SCAP-based compliance/configuration scanning |

## Web application
| Tool | Use it for |
|---|---|
| **Burp Suite** | Intercepting proxy, repeater, intruder, scanner — the standard web testing toolkit |
| **OWASP ZAP** | Open-source intercepting proxy and DAST scanner |
| **Arachni / w3af** | Automated web application scanning |
| **sqlmap** | Automated SQL injection detection and exploitation |
| **Gobuster / dirb / ffuf** | Content and directory brute-forcing |
| **wpscan** | WordPress-specific enumeration |

## Packet capture and network analysis
| Tool | Use it for |
|---|---|
| **Wireshark** | GUI packet analysis, stream reassembly, object export |
| **tcpdump** | CLI capture on servers and headless hosts |
| **tshark** | Wireshark's CLI — scriptable capture analysis |
| **NetworkMiner** | Network forensic artefact extraction from pcap |
| **Zeek (Bro)** | Network security monitoring — turns traffic into rich structured logs |
| **Suricata / Snort** | Signature-based IDS/IPS |
| **SiLK / nfdump** | NetFlow collection and analysis |
| **p0f** | Passive OS fingerprinting |

## Endpoint and forensics
| Tool | Use it for |
|---|---|
| **Volatility** | Memory forensics — process lists, injected code, network connections from a RAM image |
| **Autopsy / The Sleuth Kit** | Disk forensics, timeline, deleted file recovery |
| **FTK Imager / dd / dc3dd** | Forensic imaging |
| **Sysinternals (Procmon, Procexp, Autoruns, TCPView)** | Live Windows triage; Autoruns is the persistence-hunting tool |
| **Velociraptor / GRR** | Endpoint hunting at scale |
| **YARA** | Pattern-matching rules to classify malware families |
| **Sysmon** | Enhanced Windows telemetry (deploy it; the default log is too thin) |

## Malware and binary analysis
| Tool | Use it for |
|---|---|
| **Cuckoo Sandbox / Any.Run / Joe Sandbox** | Dynamic analysis by detonation |
| **Ghidra / IDA Pro / radare2** | Disassembly and decompilation |
| **GDB / WinDbg / OllyDbg / Immunity** | Debugging |
| **PEStudio / pefile** | Static PE inspection: imports, sections, entropy |
| **strings / floss** | Extract readable strings, including obfuscated ones |
| **CyberChef** | Decode, deobfuscate, and transform data — "the cyber Swiss Army knife" |

## SIEM, SOAR, and monitoring
| Tool | Use it for |
|---|---|
| **Splunk** | SIEM with SPL query language |
| **Elastic Stack / ELK** | Open search-based log analytics |
| **Microsoft Sentinel** | Cloud-native SIEM, KQL |
| **QRadar / ArcSight / LogRhythm** | Enterprise SIEM platforms |
| **Wazuh / OSSEC** | Open-source HIDS with FIM and log analysis |
| **Security Onion** | Free NSM/IDS distribution bundling Zeek, Suricata, Elastic |
| **TheHive / Cortex** | Case management and observable analysis |
| **Shuffle / Tines / Phantom** | SOAR playbook automation |
| **Grafana / Kibana** | Dashboards and visualisation |

## Threat intelligence
| Tool | Use it for |
|---|---|
| **MISP** | Threat intelligence sharing platform |
| **OpenCTI** | Threat intelligence knowledge management |
| **VirusTotal** | Multi-engine file/URL/hash reputation |
| **Shodan / Censys** | Internet-wide device and service search — attack surface discovery |
| **Maltego** | Link analysis and OSINT graphing |
| **Recon-ng / theHarvester / SpiderFoot** | OSINT collection frameworks |
| **urlscan.io** | Safe URL detonation and page analysis |

## Cloud and container
| Tool | Use it for |
|---|---|
| **Prowler** | AWS/Azure/GCP security posture assessment |
| **ScoutSuite** | Multi-cloud auditing |
| **Pacu** | Offensive AWS exploitation framework |
| **Trivy / Grype / Clair / Anchore** | Container image and dependency vulnerability scanning |
| **Falco** | Runtime container threat detection |
| **kube-bench / kube-hunter** | Kubernetes CIS benchmark and vulnerability testing |

## Exploitation and offensive
| Tool | Use it for |
|---|---|
| **Metasploit Framework** | Exploit development and delivery; module availability changes prioritisation |
| **Cobalt Strike** | Commercial C2 — heavily abused by real adversaries; know its Beacon traffic |
| **Empire / Sliver / Mythic** | Post-exploitation C2 frameworks |
| **BloodHound** | Maps Active Directory attack paths — "shortest path to Domain Admin" |
| **Mimikatz** | Credential dumping from LSASS |
| **Hashcat / John the Ripper** | Password cracking |
| **Aircrack-ng / Reaver** | Wireless assessment |
| **Social-Engineer Toolkit (SET)** | Phishing and social engineering simulation |

## Email security
| Tool | Use it for |
|---|---|
| **MXToolbox** | SPF/DKIM/DMARC and blocklist checks |
| **Message header analysers** | Parse and visualise the Received chain |
| **Proofpoint / Mimecast / Defender for Office 365** | Secure email gateways |
