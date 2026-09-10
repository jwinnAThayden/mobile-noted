# Audio — digesting this pack by listening, offline

**Goal: consume the whole study pack as synthesized speech on the local device,
with no network connection.**

Everything in `audio/` is pre-built and ready to play. Nothing streams, nothing
phones home, and no app is required beyond whatever plays an MP3.

---

## What's in `audio/`

| Track | Length | Content |
|---|---|---|
| `01-security-operations.mp3` | 22 min | Domain 1 (33% of the exam) |
| `02-vulnerability-management.mp3` | 21 min | Domain 2 (30%) |
| `03-incident-response.mp3` | 11 min | Domain 3 (20%) |
| `04-reporting-communication.mp3` | 9 min | Domain 4 (17%) |
| `frameworks.mp3` | 4 min | Kill chain, Diamond, ATT&CK, TLP, OWASP |
| `tools-reference.mp3` | 7 min | What each tool is for |
| `acronyms.mp3` | 8 min | Every acronym, expanded |
| `flashcards.mp3` | 24 min | **92-card spoken drill** |
| `playlist.m3u` | — | Correct playing order |
| `narration/*.txt` | — | The exact spoken text, for proofreading |

**Total: 105 minutes, 36 MB.**

### The flashcard drill is the good one

`flashcards.mp3` reads a question, leaves a **3-second gap** for you to answer
out loud, then reads the answer. 92 cards. It's built for commutes, walking, and
the gym — the places you can't read but can still study. Retrieval practice
works better than re-reading, and this is the only format that forces it on you
while your hands are busy.

Change the thinking gap:

```bash
python3 build_audio.py --only flashcards --gap 5
```

---

## Getting it onto a device

The MP3s are ordinary files. Whatever you already do with music or podcasts
works here.

| Device | How |
|---|---|
| **Phone** | Copy `audio/` into OneDrive or Google Drive, mark **Available offline**. Any music app will see the files; VLC and Musicolet read `playlist.m3u` directly. |
| **iPhone** | Drop the folder into the Files app, or add the MP3s to Apple Music and sync. |
| **Car** | Copy `audio/` to a USB stick. Most head units read the folder and play in filename order — which is why the domains are numbered. |
| **Laptop** | Open `playlist.m3u` in VLC, Winamp, foobar2000, or anything else. |
| **Podcast-style** | Some apps import a local folder as a "podcast" so you get resume-where-you-left-off and playback speed. |

Play at 1.25× or 1.5× on a second pass — the narration is written to survive it.

---

## Rebuilding with a better voice

The committed audio was generated with **espeak-ng**, which is fully offline and
runs anywhere, but sounds robotic. Your own machine almost certainly has
something better. Same script, one flag:

### macOS — built-in, genuinely good

```bash
python3 build_audio.py --engine say --voice Daniel --rate 180
```

`say -v ?` lists installed voices. The "Enhanced" and "Premium" voices in
**System Settings → Accessibility → Spoken Content → System Voice** are a large
step up and download once for permanent offline use. Ava, Serena, and Daniel are
good for long-form listening.

### Windows — built-in

```bash
python3 build_audio.py --engine sapi --rate 170
```

Add more voices under **Settings → Time & Language → Speech**. The neural
"Natural" voices are much better than the legacy David/Zira pair.

### Piper — best quality, fully offline, any platform

```bash
pip install piper-tts
python3 -m piper.download_voices en_US-lessac-medium
python3 build_audio.py --engine piper --voice en_US-lessac-medium.onnx
```

Piper is neural, runs on CPU, and needs no connection once the voice model is
downloaded. `en_US-lessac-medium` is a good default; `libritts_r-medium` is
better still and larger.

> The voice model download is the *only* step in this whole project that needs a
> connection, and it is one-time. It could not be done in the environment where
> this pack was built, because that network policy blocked `huggingface.co` —
> which is why the committed audio uses espeak-ng.

### Any engine

```bash
python3 build_audio.py --text-only      # narration text only, no synthesis
python3 build_audio.py --rate 170       # faster
python3 build_audio.py --bitrate 64k    # better quality, larger files
python3 build_audio.py --only 01        # rebuild one track
```

Requires `ffmpeg` for MP3 encoding and joining.

---

## How the narration is produced

Reading raw Markdown aloud is unbearable, so `build_audio.py` rewrites it first.
The output lands in `audio/narration/*.txt` — read it if a track sounds wrong,
since the fix is almost always there rather than in the audio settings.

What the transform does:

- **Tables become sentences.** A row of a three-column table is read as
  `"Source: Windows Event Log. What it proves: auth, process creation. Watch
  for: ..."` rather than as disconnected fragments.
- **Symbols become words.** `=` → "equals", `+` → "plus", `/` → "or",
  `→` → "leads to", `%` → "percent", `0–7` → "zero to seven".
- **Event IDs are spelled digit by digit.** `4624` is read "four six two four",
  not "four thousand six hundred and twenty-four".
- **Acronyms get a spoken form.** `SIEM` → "seem", `SCADA` → "SKAY-dah",
  `TAXII` → "TAXY", `IDOR` → "eye-door", `NXDOMAIN` → "N X domain".
- **Camel case is split.** `CreateRemoteThread` → "Create Remote Thread".
- **Code blocks are dropped.** Shell commands don't survive being spoken, so
  `commands-cheatsheet.md` has no audio track at all — it's a lookup reference,
  not something you digest by ear. Same for `README.md` and `SETUP.md`.

To adjust pronunciation, edit the `SPEECH_FIXES` dictionary near the top of
`build_audio.py` and rebuild. To add a section to the audio, add its filename to
the `TRACKS` list.

---

## A caveat worth stating

Synthesized speech is good for **review and reinforcement**, not first contact
with hard material. Concepts like reading a CVSS vector, parsing an email header
chain, or working through `nmap` output need your eyes. Use the audio to keep
the material warm between reading sessions, and to turn dead time into retrieval
practice — not as a replacement for the written pack.
