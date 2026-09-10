# Getting this onto Android for offline use

25 MB of ordinary files. No account, no sync service, no special app required.
Once it's on the device it works in airplane mode, permanently.

---

## The whole process, on the phone, no computer

1. **Open the Claude conversation** in the Claude app and tap the
   `cysa-plus-study.zip` attachment. It downloads to `Download/`.
2. **Open Files** (Google Files, Samsung *My Files*, or whatever ships on the
   device), find the zip, long-press → **Extract**.
   *If your file manager has no Extract option, install **ZArchiver** — free,
   does one job.*
3. Done. You have `Download/cysa-plus-study/` on the device.

That's the entire setup. Under a minute on a decent connection.

---

## Audio

Eight MP3s in `audio/`, 105 minutes total, including a 92-card spoken drill.

### Recommended: AntennaPod

Sounds like an odd choice — it's a podcast app — but it supports **local
folders**, which gives you the three things that actually matter for long-form
study material:

- resumes exactly where you stopped, per track
- variable playback speed
- a queue, so the domains play in order

Add it as: **☰ → Add Podcast → Add Local Folder → pick `cysa-plus-study/audio`.**

### Simpler: VLC

Also free, also fine. Opens the folder directly, reads `playlist.m3u`, remembers
position. Less setup than AntennaPod, slightly worse for a 24-minute drill track.

### Folder players

Musicolet and Poweramp both browse by folder rather than forcing a library
import, and both read `.m3u`. Good if you already use one.

> **If the tracks don't show up:** Android's media scanner hasn't indexed them
> yet. Opening the folder once in VLC forces a scan, or reboot. This is the most
> common "it didn't work" and it isn't a problem with the files.

### On the flashcard drill

Keep it at **1.0× the first time through.** The gaps after each question are
3 seconds. At 1.5× that's 2 seconds — not long enough to actually retrieve the
answer, and retrieval is the whole point of the format. Speed it up on later
passes once the answers are quick.

---

## The written pack

`cysa-offline.html` is one self-contained file, already laid out for phone width
with a collapsing contents menu.

**Easiest:** in your file manager, tap `cysa-offline.html` → **Open with →
Chrome**. Then ⋮ → **Bookmark** it so you don't go hunting next time.

**By address:** Chrome can open it directly —

```
file:///sdcard/Download/cysa-plus-study/cysa-offline.html
```

If `/sdcard` doesn't resolve on your device, use the full path:

```
file:///storage/emulated/0/Download/cysa-plus-study/cysa-offline.html
```

Chrome won't let you add a `file://` page to the home screen — bookmark it
instead, or make a shortcut from your file manager if it supports one.

The `.md` files are plain text and readable in any editor, if you'd rather skip
HTML entirely.

---

## Alternative: OneDrive

Works, and keeps the phone copy in step with a desktop copy.

1. On a computer, copy `cysa-plus-study` into OneDrive.
2. In the OneDrive Android app, long-press the folder → **Make available
   offline**.
3. If that's greyed out for the folder, mark the individual files instead.

> **The trap:** "in OneDrive" is not "on the device". A file that isn't
> explicitly marked available offline is a placeholder — the app fetches it when
> you open it, so it fails exactly when you have no signal. Run the check below
> before you rely on it.

## Alternative: USB cable

Plug in, pull down the notification, set USB mode to **File Transfer**, then drag
the folder to `Internal Storage/Download/`. Nothing to configure and nothing to
go wrong.

---

## Verify it works offline

Do this once, deliberately, before you need it.

1. **Airplane mode on.**
2. Play two minutes of `audio/flashcards.mp3` — you should hear a question, a
   pause, then the answer.
3. Open `cysa-offline.html`, jump to Domain 3, confirm the tables render.
4. Airplane mode off.

If either step fails, the files aren't local yet — almost always cloud
placeholders. Copy them into device storage directly.

---

## If you're short on space

The whole thing is 25 MB, so this rarely comes up. But in priority order:

| | File | Size | Why |
|---|---|---|---|
| 1 | `cysa-offline.html` | 154 KB | Every word of the written pack, in one file |
| 2 | `audio/flashcards.mp3` | 5.5 MB | Hands-free retrieval practice |
| 3 | `audio/01-` … `04-*.mp3` | 14 MB | The four domains narrated |
| 4 | the rest | 5 MB | Frameworks, tools, acronyms |

---

## Note for iOS

Not the target here, but if the repo gets shared: the Files app can uncompress
the zip and preview the HTML, though local HTML is fiddlier than on Android —
**Documents by Readdle** handles it properly. VLC works the same on both.
