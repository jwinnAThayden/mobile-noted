# Getting this onto a phone or tablet for offline use

The whole pack is 25 MB of ordinary files — no app, no account, no sync service
required. Once it's on the device it works in airplane mode, permanently.

---

## Fastest route: straight from the chat, no computer

The project zip was delivered as an attachment in the Claude conversation. On
the phone:

### iPhone / iPad

1. Open the conversation in the **Claude** app and tap the `.zip` attachment.
2. Tap **Share → Save to Files**. Put it in *On My iPhone* (not iCloud Drive) if
   you want it genuinely local.
3. Open the **Files** app, find the zip, **long-press → Uncompress**.

You now have a `cysa-plus-study` folder on the device.

### Android

1. Open the conversation in the **Claude** app and tap the `.zip` attachment to
   download it. It lands in `Downloads`.
2. Open **Files** (or Google Files / Samsung My Files), long-press the zip and
   choose **Extract**. If your file manager can't, install **ZArchiver** — free
   and does nothing else.

You now have a `cysa-plus-study` folder on the device.

---

## Then: what opens what

### Audio — the part that works best on a phone

The eight MP3s in `audio/` are plain files. Anything that plays music plays them.

| Platform | Recommended | Why |
|---|---|---|
| **Both** | **VLC** (free) | Opens the folder directly, reads `playlist.m3u`, remembers your position, and has playback speed. This is the one to use. |
| Android | Musicolet, Poweramp | Folder-based players; no library import needed |
| iOS | Files app's built-in player | Fine for a single track, but loses your place |

**Use VLC and add `audio/` as a folder.** Position memory matters — `flashcards.mp3`
is 24 minutes and you will not want to restart it every time.

For the flashcard drill specifically, turn playback speed to **1.0×** the first
time through. The 3-second answer gaps are timed for normal speed; at 1.5× you
get 2 seconds, which isn't long enough to actually retrieve the answer.

> **Android tip:** if the tracks don't appear in your music app, the media
> scanner hasn't picked them up. Opening the folder in VLC once forces a scan,
> or reboot the phone.

### The written pack

`cysa-offline.html` is one self-contained file — the layout is already
phone-width responsive with a collapsing contents menu.

- **Android:** open Chrome, type `file:///sdcard/Download/cysa-plus-study/cysa-offline.html`
  in the address bar, and bookmark it. Or tap the file in your file manager and
  choose Chrome.
- **iOS:** tap `cysa-offline.html` in the Files app — it previews and renders.
  If the sidebar or dark mode misbehaves in the preview, install
  **Documents by Readdle** (free), which has a real browser for local files and
  handles this properly.

The `.md` files are readable as plain text in any editor if you'd rather not
deal with HTML at all.

---

## Alternative: via OneDrive

You already use OneDrive, so this works and keeps the phone copy in sync with a
desktop copy.

1. On a computer, copy the `cysa-plus-study` folder into OneDrive.
2. In the OneDrive **mobile app**, find the folder.
3. Long-press it → **Make available offline**.

If **Make available offline** is greyed out for the folder, mark the individual
files instead — same effect, a few more taps. Files marked offline stay on the
device and survive airplane mode.

> A caution: "in OneDrive" is not the same as "on the device". Unless a file is
> explicitly marked available offline, the app will try to fetch it when you
> open it, and you'll get nothing on a plane. **Verify before you rely on it** —
> see the check below.

---

## Alternative: USB cable

The least clever and most reliable option.

- **Android:** plug in, set the USB mode to **File Transfer**, drag the folder to
  `Internal Storage/Download/`.
- **iPhone:** plug into a Mac, open Finder, select the iPhone, use the **Files**
  tab to drop the folder into an app that accepts it (VLC and Documents both do).

---

## Verify it actually works offline

Do this once, before you're relying on it somewhere with no signal.

1. **Turn on airplane mode.**
2. Play two minutes of `audio/flashcards.mp3`. Confirm you hear a question, a
   pause, then the answer.
3. Open `cysa-offline.html`. Click through to Domain 3 and confirm tables render.
4. Turn airplane mode off.

If either step fails, the files aren't actually local — most likely they're
still cloud placeholders. Go back and mark them available offline, or copy them
into device storage directly.

---

## What to put where, if you're short on space

The whole thing is 25 MB, so this rarely matters. But if you're picking:

| Priority | File | Size | Why |
|---|---|---|---|
| 1 | `audio/flashcards.mp3` | 5.5 MB | Retrieval practice, hands-free |
| 2 | `cysa-offline.html` | 154 KB | The entire written pack |
| 3 | `audio/01-` … `04-*.mp3` | 14 MB | The four domains narrated |
| 4 | everything else | 5 MB | Frameworks, tools, acronyms |

`cysa-offline.html` alone is 154 KB and contains every word of the written
material. If you take nothing else, take that.
