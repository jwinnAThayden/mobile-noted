# CySA+ Field Notes — web app

The study pack as an installable app: the notes as text, read-aloud for any
part of it, and spaced-repetition flashcards. Works offline once loaded.

```bash
pip install -r requirements.txt
python3 build_content.py     # Markdown -> static/content.json
python3 app.py               # http://localhost:5000
```

---

## Why there are no audio files

Earlier versions shipped 24 MB of MP3s. This doesn't, and the result is better.

The app uses the **Web Speech API**, so read-aloud runs through the *device's own*
text-to-speech engine. On Android that's usually Google's, which sounds far
better than anything that could be pre-rendered and shipped — and once the voice
data is installed it works with the network off.

That means:

- No audio files to download, transfer, or keep in sync
- The voice is whatever the user already likes on their device
- Speed is adjustable live, not baked in
- Any part can be read — every section, and both sides of every card

If a device has no speech engine, the Listen buttons simply don't appear and the
app is still a complete set of notes.

> **Android voices:** Settings → Accessibility → Text-to-speech output. Voices
> marked *(on device)* in the app's voice picker keep working offline; ones
> marked *(network)* don't.

---

## Installing it on Android

This is a PWA, so it installs from the browser — no Play Store, no APK, no
file transfer.

1. Serve it over **http://** or **https://** (a service worker will not register
   from a `file://` URL — this is why there's a server at all).
2. Open it in Chrome on the phone.
3. **⋮ → Add to Home screen** (or the *Install app* prompt).

It then launches full-screen with its own icon and works with no connection.

To reach a phone on the same Wi-Fi as your PC, find the PC's LAN address and
open `http://<pc-ip>:5000` on the phone. `app.py` already binds `0.0.0.0`.

Chrome requires https for install prompts on non-localhost origins, so for a
permanent install, deploy it (below) rather than serving from your PC.

---

## Flashcards

92 cards, scheduled with **SM-2** — the algorithm behind Anki and SuperMemo.

- **Again / Hard / Good / Easy** — keyboard `1` `2` `3` `4`, space reveals
- *Again* returns the card later in the same session rather than tomorrow
- Progress lives in `localStorage`, on the device, per browser
- Filter by domain, or study everything
- **Read aloud** speaks the question, holds for a configurable pause, then reads
  the answer — the hands-free drill, now with a real voice

Scheduling is per-device and per-browser. Installing the PWA and using the
browser are the same origin, so progress carries over.

---

## Layout

```
webapp/
├── app.py                 Flask: serves static/, sets service-worker headers
├── build_content.py       Markdown -> static/content.json (+ stamps sw version)
├── requirements.txt
├── Procfile               for Railway or any Procfile host
└── static/
    ├── index.html
    ├── css/app.css
    ├── js/tts.js          speech engine wrapper
    ├── js/cards.js        SM-2 scheduling
    ├── js/app.js          wiring
    ├── sw.js              offline cache (version stamped at build time)
    ├── manifest.webmanifest
    ├── icons/
    └── content.json       generated — do not edit
```

The app is entirely static: Flask serves files and sets two headers. Any static
host works.

### Rebuilding after editing the notes

```bash
python3 build_content.py
```

It re-renders every Markdown file, regenerates the spoken form, and stamps
`sw.js` with a hash of the content — so the new version replaces the cached one
on the next visit instead of being masked by a stale service worker.

`build_content.py` reuses `../build_offline_html.py` for display HTML and
`../build_audio.py` for the spoken text, so all three outputs — offline HTML,
audio, and this app — stay consistent from one source.

---

## Deploying

`Procfile` is included, so a Procfile host works as-is:

```
web: gunicorn --chdir webapp app:app --bind 0.0.0.0:$PORT
```

Any static host (Netlify, Pages, S3) also works — serve `static/` and make sure
`.webmanifest` is sent as `application/manifest+json` and `sw.js` isn't cached.

---

## If you want a real Android app later

The PWA is genuinely installable and offline, which covers most of what an APK
would give you. If you need a Play Store listing or native APIs:

| Route | What it involves |
|---|---|
| **TWA via Bubblewrap** | Wraps this exact PWA in an APK/AAB. `npx @bubblewrap/cli init --manifest <url>/manifest.webmanifest`. Needs the site on https with a Digital Asset Links file. Least work by a wide margin. |
| **Capacitor** | `npx cap init`, drop `static/` in as the web root. Gives native plugin access if you later want notifications or background audio. |
| **Kivy + buildozer** | Matches `mobile-noted/` in the parent project, but means rewriting the UI. Only worth it if you want one codebase with that app. |

Start with the PWA. Reach for TWA only when the Play Store listing is the actual
requirement.
