# Testing the pack on an Android device

Run this once, after copying the files across, before you depend on it. Roughly
ten minutes. Each test has a **concrete checkpoint** — a number to match, not a
vague "does it seem OK".

Tests are ordered so that a failure tells you where the problem is. **If a test
fails, stop and fix it before moving on** — later tests assume the earlier ones
passed.

---

## Test 1 — The transfer completed

**Why first:** a truncated download or a partial extract explains almost every
later symptom, and looks like something else.

In your file manager, open `Download/cysa-plus-study/` and check:

| Check | Expected |
|---|---|
| Visible files in the root folder | **19** — 15 `.md`, 2 `.py`, 1 `.html`, 1 `.sha256` — plus the `audio` folder |
| `cysa-offline.html` | ~160 KB |
| `audio/` contains | 8 `.mp3`, `playlist.m3u`, and a `narration/` folder |
| `audio/` total size | ~24 MB |

**Fails if:** the folder is missing files, or `cysa-offline.html` is under
150 KB. Re-download the zip and extract again — most likely the extract was
interrupted.

### Optional: verify byte-for-byte

If you have **Termux** installed:

```bash
cd /sdcard/Download/cysa-plus-study
sha256sum -c checksums.sha256
```

Every line should read `OK`. This is the only test that proves the files are
*identical*, not merely present. Skip it if you don't already use Termux — the
size checks above catch real-world corruption.

---

## Test 2 — Audio plays, and is complete

Open `audio/` in VLC or AntennaPod. Check each track's total length against this
table — a track that plays but is short was truncated in transfer.

| Track | Expected length |
|---|---|
| `01-security-operations.mp3` | 22:04 |
| `02-vulnerability-management.mp3` | 20:42 |
| `03-incident-response.mp3` | 11:14 |
| `04-reporting-communication.mp3` | 8:58 |
| `frameworks.mp3` | 4:01 |
| `tools-reference.mp3` | 6:34 |
| `acronyms.mp3` | 7:32 |
| `flashcards.mp3` | 24:02 |
| **Total** | **1:45:11** |

**Fails if:** tracks don't appear at all → Android's media scanner hasn't indexed
them. Open the folder once in VLC, or reboot. This is not a file problem.

---

## Test 3 — The flashcard drill has its gaps

This is the one feature that can break silently, so it gets its own test.

Play `audio/flashcards.mp3` from the start. You should hear:

1. An intro: *"Flashcard Drill. 92 cards…"*
2. At about **0:12**, the first question ends and a **3-second silence** begins
3. At about **0:16**, the answer starts: *"Answer. Four six two four…"*
4. The next question at roughly **0:29**, the one after at **0:43**

**Fails if:** the answer follows the question immediately with no pause. The file
was re-encoded by something in transit, or you're playing a different build.
Re-copy from the zip.

**Also check:** playback speed is at **1.0×**. At 1.5× the gap is 2 seconds,
which isn't long enough to retrieve an answer — the drill stops working as a
drill.

---

## Test 4 — The written pack renders

Tap `cysa-offline.html` → **Open with → Chrome**.

| Check | Expected |
|---|---|
| Contents button | A **☰ Contents** button, top-left |
| Tapping it | A sidebar slides in listing 13 sections |
| Tap "3. Incident Response" | Jumps to that section |
| The order-of-volatility list | Numbered 1–7, readable |
| Domain 1's logging table | Scrolls sideways on its own without the page scrolling |
| Command Cheatsheet section | Code blocks in a monospace font, scrolling sideways |
| Page body | Does **not** scroll sideways at any point |

**Fails if:** the page is unstyled black-on-white text → the file is truncated;
recheck its size in Test 1.

### Dark mode

Switch the phone to dark theme (**Settings → Display → Dark theme**) and reload.
The page should follow — dark background, light text, tables still legible.
Switch back and it should follow again.

---

## Test 5 — It genuinely works offline

The test that matters. Everything above can pass while the files are still cloud
placeholders that fetch on open.

1. **Turn on airplane mode.** Confirm Wi-Fi and mobile data are both off.
2. Play one minute of `flashcards.mp3`. It should start instantly.
3. Open `cysa-offline.html` in Chrome. Scroll to Domain 3 and confirm the tables
   still render.
4. Tap two sidebar links.
5. **Turn airplane mode off.**

**Fails if:** anything spins, stalls, or shows an error. The files aren't local.
If you used OneDrive, mark them **Make available offline**; better, copy them
into device storage directly.

> Chrome may show a "no internet" banner on a `file://` page. That's Chrome
> being noisy about the network, not about the page. If the content renders,
> the test passed.

---

## Test 6 — It survives a reboot

Cheap and worth doing. Some file managers extract to a cache directory that
Android clears on its own.

1. Reboot the phone.
2. Open `Download/cysa-plus-study/` — everything should still be there.
3. Play ten seconds of any track.

**Fails if:** the folder is gone or thinned out → it was extracted somewhere
temporary. Re-extract to `Internal Storage/Download/`, not to an app's cache.

---

## Quick pass/fail record

| # | Test | Pass |
|---|---|---|
| 1 | Transfer complete — 19 root files, HTML ~160 KB, audio ~24 MB | ☐ |
| 2 | All 8 tracks present, total 1:45:11 | ☐ |
| 3 | Flashcard gaps: first pause at ~0:12, ~3 seconds long | ☐ |
| 4 | HTML renders — sidebar, tables scroll, dark mode follows | ☐ |
| 5 | Airplane mode: audio and HTML both work | ☐ |
| 6 | Survives reboot | ☐ |

All six pass and the pack is genuinely yours, offline, permanently.

---

## If you rebuild the audio

Regenerating with a better voice (see [`AUDIO.md`](AUDIO.md)) changes every
track's length and every checksum, so Tests 1–3 no longer match this document.
Regenerate the checksums at the same time:

```bash
find . -type f ! -path './.git/*' ! -name 'checksums.sha256' | sort | xargs sha256sum > checksums.sha256
```

Tests 4–6 are unaffected.
