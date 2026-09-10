#!/usr/bin/env python3
"""Turn the CySA+ study pack into offline audio.

Two stages, and you can stop after the first:

  1. Convert the Markdown into *narration text* - prose that works spoken
     aloud. Tables become sentences, symbols become words, headings become
     spoken cues. Written to audio/narration/*.txt so you can proofread it.
  2. Synthesise that text with whatever TTS engine this machine has, and
     encode to MP3.

Engines, in the order they are auto-detected:

  piper    neural, offline, best quality. Needs a .onnx voice model:
             pip install piper-tts
             python3 -m piper.download_voices en_US-lessac-medium
  say      macOS built-in. Very good. `say -v ?` lists voices.
  sapi     Windows built-in, via PowerShell.
  espeak   espeak-ng. Robotic but universally available and fully offline.

Examples:
    python3 build_audio.py --text-only          # just the narration text
    python3 build_audio.py                      # auto-detect engine, build MP3s
    python3 build_audio.py --engine say --voice Daniel --rate 180
    python3 build_audio.py --engine piper --voice /path/en_US-lessac-medium.onnx
    python3 build_audio.py --only flashcards --gap 4
"""

from __future__ import annotations

import argparse
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Files worth listening to, in playing order. README/SETUP are project
# scaffolding and commands-cheatsheet.md is a lookup reference - neither
# survives being read aloud, so both are left out.
TRACKS = [
    ("01-security-operations.md", "Domain 1, Security Operations"),
    ("02-vulnerability-management.md", "Domain 2, Vulnerability Management"),
    ("03-incident-response.md", "Domain 3, Incident Response and Management"),
    ("04-reporting-communication.md", "Domain 4, Reporting and Communication"),
    ("frameworks.md", "Frameworks Side by Side"),
    ("tools-reference.md", "Tools Reference"),
    ("acronyms.md", "Acronyms"),
    ("flashcards.md", "Flashcard Drill"),
]

# Spoken forms. Longest keys first at apply time so substrings don't win.
SPEECH_FIXES = {
    "e.g.": "for example", "i.e.": "that is", "etc.": "and so on",
    "vs.": "versus", " vs ": " versus ",
    "&": " and ", "%": " percent", "/": " or ",
    "→": " leads to ", "←": " comes from ", "×": " times ",
    "±": " plus or minus ", "≈": " roughly ", "≥": " at least ",
    "≤": " at most ", "—": ", ", "–": ", ", "…": ".",
    "CVSS": "C V S S", "CVE": "C V E", "CWE": "C W E",
    "SIEM": "SEEM", "SOAR": "SOAR", "EDR": "E D R", "XDR": "X D R",
    "IOC": "I O C", "IOA": "I O A", "TTP": "T T P", "TTPs": "T T Ps",
    "APT": "A P T", "PII": "P I I", "PHI": "P H I",
    "SQLi": "S Q L injection", "XSS": "X S S", "CSRF": "C S R F",
    "SSRF": "S S R F", "XXE": "X X E", "IDOR": "eye-door",
    "MTTD": "M T T D", "MTTR": "M T T R", "MTTA": "M T T A",
    "RTO": "R T O", "RPO": "R P O", "SLA": "S L A", "SLO": "S L O",
    "TLP": "T L P", "STIX": "STIX", "TAXII": "TAXY",
    "SPF": "S P F", "DKIM": "D KIM", "DMARC": "D MARK",
    "SAST": "SAST", "DAST": "DAST", "SBOM": "S BOM",
    "EPSS": "E P S S", "KEV": "KEV", "PBQ": "P B Q", "PBQs": "P B Qs",
    "NIST": "NIST", "ICS": "I C S", "SCADA": "SKAY-dah",
    "C2": "command and control", "MFA": "M F A", "SSO": "single sign-on",
    "lsass.exe": "L SASS dot E X E", ".exe": " dot E X E",
    "GDPR": "G D P R", "PCI DSS": "P C I D S S", "HIPAA": "HIP-uh",
    # Terms espeak mangles, and camel-case that needs pulling apart.
    "NXDOMAIN": "N X domain", "CreateRemoteThread": "Create Remote Thread",
    "pcap": "P cap", "PCAP": "P cap", "tcpdump": "T C P dump",
    "TCP/IP": "T C P I P", "24/7": "24 by 7", "and/or": "and or",
    "NetFlow": "Net Flow", "IPFIX": "I P fix", "Sysmon": "Sys-mon",
    "DGA": "D G A", "IMDSv2": "I M D S version 2", "KRBTGT": "K R B T G T",
    "vssadmin": "V S S admin", "schtasks": "S C H tasks",
    "Kerberoasting": "Kerber-oasting", "BloodHound": "Blood Hound",
    "PowerShell": "Power Shell", "WebAuthn": "Web Auth-n",
    "setuid": "set U I D", "setgid": "set G I D",
    "RDP": "R D P", "NTP": "N T P", "DNS": "D N S", "URL": "U R L",
    "WAF": "WAF", "IPS": "I P S", "IDS": "I D S", "VPN": "V P N",
    "IAM": "I A M", "PAM": "PAM", "CASB": "CAS-B", "SASE": "SASS-ee",
    "SBOM": "S BOM", "OWASP": "OH-wasp", "CISA": "SIS-ah",
    "OSINT": "OH-sint", "ISAC": "EYE-sack", "SOC": "sock",
    "RCE": "R C E", "LFI": "L F I", "RFI": "R F I", "IDS/IPS": "I D S, I P S",
}

# Windows and Sysmon event identifiers must be read digit by digit.
EVENT_IDS = {
    "1102", "4624", "4625", "4634", "4647", "4648", "4672", "4688",
    "4697", "4698", "4719", "4720", "4726", "5140", "7045",
}

# Digit strings that must be read as separate digits, not as a quantity.
DIGIT_CONTEXT = re.compile(
    r"\b(?:Event\s+ID|ID|IDs|event)\s*:?\s*(\d{3,5})\b", re.I
)


def say_digits(number: str) -> str:
    return " ".join(number)


def strip_markdown(text: str) -> str:
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)          # images
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)      # links -> label
    text = re.sub(r"`([^`]+)`", r"\1", text)                  # code spans
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"\1", text)
    return text


def speechify(text: str) -> str:
    text = strip_markdown(text)

    # Numeric ranges first: "0-7" and "0.1-3.9" must survive dash rewriting.
    text = re.sub(r"(\d(?:\.\d+)?)\s*[\u2013\u2014-]\s*(\d(?:\.\d+)?)", r"\1 to \2", text)

    # Known event identifiers, wherever they appear.
    text = re.sub(r"\b\d{4}\b",
                  lambda m: say_digits(m.group(0)) if m.group(0) in EVENT_IDS else m.group(0),
                  text)
    # Anything explicitly introduced as an ID, even if not in the known set.
    text = DIGIT_CONTEXT.sub(
        lambda m: m.group(0).replace(m.group(1), say_digits(m.group(1))), text)

    # Operators that are silent when spoken.
    text = re.sub(r"\s*=\s*", " equals ", text)
    text = re.sub(r"(?<=\w)\s*\+\s*(?=\w)", " plus ", text)
    text = re.sub(r"(?<=[A-Za-z])/(?=[A-Za-z])", " or ", text)

    for key in sorted(SPEECH_FIXES, key=len, reverse=True):
        text = text.replace(key, SPEECH_FIXES[key])

    # Tidy the punctuation the substitutions leave behind.
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"([,;:])\1+", r"\1", text)
    text = re.sub(r"\.{2,}", ".", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"^[,;:.\s]+", "", text)

    # A sentence needs terminal punctuation or the engine runs lines together.
    if text and text[-1] not in ".!?:;,":
        text += "."
    return text


def table_to_prose(rows: list[str]) -> list[str]:
    def cells(row: str) -> list[str]:
        return [c.strip() for c in row.strip().strip("|").split("|")]

    header = cells(rows[0])
    out = []
    for raw in rows[2:]:
        values = cells(raw)
        if not any(values):
            continue
        if len(values) == 2:
            # Key/value table: "X: Y." reads naturally.
            left, right = speechify(values[0]), speechify(values[1]).rstrip(".")
            out.append(f"{left.rstrip('.')}: {right}.")
        else:
            parts = []
            for name, value in zip(header, values):
                if not value or value == "-":
                    continue
                parts.append(f"{speechify(name).rstrip('.')}: {speechify(value).rstrip('.')}")
            if parts:
                out.append(". ".join(parts) + ".")
    return out


def narrate(markdown: str, title: str) -> str:
    """Markdown -> spoken prose."""
    lines = markdown.split("\n")
    out: list[str] = [f"{title}.", ""]
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):                     # skip code blocks
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                i += 1
            i += 1
            continue

        if not stripped or re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", stripped):
            i += 1
            continue

        heading = re.match(r"(#{1,6})\s+(.*)", stripped)
        if heading:
            level, text = len(heading.group(1)), heading.group(2)
            if level == 1:                                  # page title: already said
                i += 1
                continue
            out += ["", f"{speechify(text).rstrip('.')}.", ""]
            i += 1
            continue

        if stripped.startswith("|") and i + 1 < len(lines) and re.fullmatch(
            r"\|[\s:\-|]+\|", lines[i + 1].strip()
        ):
            block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                block.append(lines[i])
                i += 1
            out += table_to_prose(block)
            continue

        if stripped.startswith(">"):
            quote = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip()[1:].strip())
                i += 1
            body = speechify(" ".join(q for q in quote if not q.startswith("#")))
            if body.strip(" ."):
                out.append(f"Note. {body}")
            continue

        bullet = re.match(r"(?:[-*+]|\d+\.)\s+(.*)", stripped)
        if bullet:
            content = bullet.group(1)
            i += 1
            while (i < len(lines) and lines[i].strip()
                   and lines[i].startswith((" ", "\t"))
                   and not re.match(r"([-*+]|\d+\.)\s+", lines[i].strip())):
                content += " " + lines[i].strip()
                i += 1
            out.append(speechify(content))
            continue

        para = [stripped]
        i += 1
        while (i < len(lines) and lines[i].strip()
               and not lines[i].strip().startswith(("#", "|", "```", ">", "-", "*"))
               and not re.match(r"\d+\.\s", lines[i].strip())):
            para.append(lines[i].strip())
            i += 1
        out.append(speechify(" ".join(para)))

    return "\n".join(out)


def parse_flashcards(markdown: str) -> list[tuple[str, str]]:
    cards = []
    question = None
    for raw in markdown.split("\n"):
        line = raw.strip()
        if line.startswith("**Q**"):
            question = speechify(line[5:])
        elif line.startswith("**A**") and question:
            cards.append((question, speechify(line[5:])))
            question = None
    return cards


# ---------------------------------------------------------------- engines

def detect_engine() -> str:
    if shutil.which("piper"):
        return "piper"
    if platform.system() == "Darwin" and shutil.which("say"):
        return "say"
    if platform.system() == "Windows":
        return "sapi"
    if shutil.which("espeak-ng") or shutil.which("espeak"):
        return "espeak"
    return ""


def synth(text: str, wav: Path, engine: str, voice: str | None, rate: int) -> None:
    """Render `text` to a WAV file at `wav`."""
    if engine == "espeak":
        binary = shutil.which("espeak-ng") or shutil.which("espeak")
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False,
                                         encoding="utf-8") as handle:
            handle.write(text)
            src = handle.name
        subprocess.run([binary, "-v", voice or "en-us+f3", "-s", str(rate),
                        "-p", "45", "-f", src, "-w", str(wav)], check=True)
        Path(src).unlink(missing_ok=True)

    elif engine == "say":
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False,
                                         encoding="utf-8") as handle:
            handle.write(text)
            src = handle.name
        cmd = ["say", "-r", str(rate), "-o", str(wav),
               "--data-format=LEI16@22050", "-f", src]
        if voice:
            cmd[1:1] = ["-v", voice]
        subprocess.run(cmd, check=True)
        Path(src).unlink(missing_ok=True)

    elif engine == "sapi":
        # System.Speech rate is -10..10; map from words per minute.
        sapi_rate = max(-10, min(10, round((rate - 175) / 15)))
        select = f'$s.SelectVoice("{voice}");' if voice else ""
        script = (
            "Add-Type -AssemblyName System.Speech;"
            "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer;"
            f"{select}"
            f"$s.Rate = {sapi_rate};"
            f'$s.SetOutputToWaveFile("{wav}");'
            "$s.Speak([Console]::In.ReadToEnd());"
            "$s.Dispose();"
        )
        subprocess.run(["powershell", "-NoProfile", "-Command", script],
                       input=text, text=True, check=True)

    elif engine == "piper":
        if not voice:
            sys.exit("piper needs --voice pointing at a .onnx model file")
        subprocess.run(["piper", "-m", voice, "-f", str(wav)],
                       input=text, text=True, check=True)
    else:
        sys.exit(f"unknown engine: {engine}")


def silence(seconds: float, wav: Path, reference: Path) -> None:
    """Generate a silent WAV matching `reference`'s format."""
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0",
         "-show_entries", "stream=sample_rate,channels",
         "-of", "csv=p=0", str(reference)],
        capture_output=True, text=True, check=True).stdout.strip()
    rate, channels = (probe.split(",") + ["22050", "1"])[:2]
    layout = "mono" if channels.strip() == "1" else "stereo"
    subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi",
         "-i", f"anullsrc=r={rate}:cl={layout}", "-t", str(seconds), str(wav)],
        check=True)


def concat(parts: list[Path], out: Path) -> None:
    listing = out.with_suffix(".list")
    listing.write_text("\n".join(f"file '{p.as_posix()}'" for p in parts),
                       encoding="utf-8")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat",
                    "-safe", "0", "-i", str(listing), "-c", "copy", str(out)],
                   check=True)
    listing.unlink(missing_ok=True)


def to_mp3(wav: Path, mp3: Path, bitrate: str) -> None:
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(wav),
                    "-b:a", bitrate, "-ac", "1", "-ar", "22050", str(mp3)],
                   check=True)


def duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True)
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0


# ------------------------------------------------------------------ main

def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--engine", choices=["auto", "espeak", "say", "sapi", "piper"],
                        default="auto")
    parser.add_argument("--voice", help="engine-specific voice name or model path")
    parser.add_argument("--rate", type=int, default=155, help="words per minute")
    parser.add_argument("--gap", type=float, default=3.0,
                        help="thinking pause between flashcard Q and A, seconds")
    parser.add_argument("--bitrate", default="32k",
                        help="MP3 bitrate; 32k mono is transparent for speech")
    parser.add_argument("--out", type=Path, default=HERE / "audio")
    parser.add_argument("--only", help="build one track by filename stem")
    parser.add_argument("--text-only", action="store_true",
                        help="write narration text and stop, no audio")
    args = parser.parse_args()

    out = args.out
    narration_dir = out / "narration"
    narration_dir.mkdir(parents=True, exist_ok=True)

    selected = [t for t in TRACKS
                if not args.only or Path(t[0]).stem.startswith(args.only)]
    if not selected:
        sys.exit(f"no track matches --only {args.only!r}")

    # ---- stage 1: narration text
    print("Writing narration text...")
    prepared: list[tuple[str, str, str]] = []   # stem, title, text
    for filename, title in selected:
        source = HERE / filename
        if not source.exists():
            print(f"  missing, skipped: {filename}")
            continue
        markdown = source.read_text(encoding="utf-8")
        stem = Path(filename).stem
        if stem == "flashcards":
            cards = parse_flashcards(markdown)
            text = f"{title}. {len(cards)} cards. After each question, pause and answer before the answer is read."
            prepared.append((stem, title, text))
            print(f"  {stem}: {len(cards)} cards")
            (narration_dir / f"{stem}.txt").write_text(
                text + "\n\n" + "\n\n".join(
                    f"Question. {q}\n[pause {args.gap}s]\nAnswer. {a}" for q, a in cards),
                encoding="utf-8")
            continue
        text = narrate(markdown, title)
        prepared.append((stem, title, text))
        (narration_dir / f"{stem}.txt").write_text(text, encoding="utf-8")
        print(f"  {stem}: {len(text.split()):,} words (~{len(text.split())/args.rate:.0f} min)")

    if args.text_only:
        print(f"\nNarration text in {narration_dir}")
        return

    # ---- stage 2: audio
    engine = detect_engine() if args.engine == "auto" else args.engine
    if not engine:
        sys.exit("No TTS engine found. Install espeak-ng, or use --engine say "
                 "on macOS / --engine sapi on Windows.")
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg is required for MP3 encoding and joining. Install it and retry.")
    print(f"\nSynthesising with '{engine}' at {args.rate} wpm...")

    built: list[tuple[Path, str, float]] = []
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        for stem, title, _ in prepared:
            mp3 = out / f"{stem}.mp3"
            print(f"  {stem}...", end="", flush=True)

            if stem == "flashcards":
                cards = parse_flashcards((HERE / "flashcards.md").read_text(encoding="utf-8"))
                intro = tmp / "fc-intro.wav"
                synth(f"{title}. {len(cards)} cards. After each question, pause "
                      f"and answer before the answer is read.",
                      intro, engine, args.voice, args.rate)
                gap = tmp / "gap.wav"
                silence(args.gap, gap, intro)
                beat = tmp / "beat.wav"
                silence(1.0, beat, intro)
                parts = [intro, beat]
                for index, (question, answer) in enumerate(cards):
                    qw, aw = tmp / f"q{index}.wav", tmp / f"a{index}.wav"
                    synth(f"Question. {question}", qw, engine, args.voice, args.rate)
                    synth(f"Answer. {answer}", aw, engine, args.voice, args.rate)
                    parts += [qw, gap, aw, beat]
                joined = tmp / "flashcards.wav"
                concat(parts, joined)
            else:
                joined = tmp / f"{stem}.wav"
                synth((narration_dir / f"{stem}.txt").read_text(encoding="utf-8"),
                      joined, engine, args.voice, args.rate)

            to_mp3(joined, mp3, args.bitrate)
            length = duration(mp3)
            built.append((mp3, title, length))
            print(f" {length/60:.1f} min, {mp3.stat().st_size/1024/1024:.1f} MB")

    playlist = out / "playlist.m3u"
    lines = ["#EXTM3U"]
    for mp3, title, length in built:
        lines.append(f"#EXTINF:{int(length)},{title}")
        lines.append(mp3.name)
    playlist.write_text("\n".join(lines) + "\n", encoding="utf-8")

    total = sum(length for _, _, length in built)
    size = sum(mp3.stat().st_size for mp3, _, _ in built) / 1024 / 1024
    print(f"\n{len(built)} tracks, {total/60:.0f} minutes, {size:.0f} MB total")
    print(f"Output: {out}")
    print(f"Playlist: {playlist.name}")


if __name__ == "__main__":
    main()
