# Deploying to Railway, and installing on the phone

The web app has to be served over **https** before Android will install it —
service workers don't register from `file://`, and Chrome only offers *Install*
on a secure origin. Railway gives you https on a generated domain, which is why
it's the target here.

Everything Railway needs is already in this repo. There are two steps it can't
do for you.

---

## Step 1 — Put this repo on GitHub

The repo has to exist before Railway can deploy from it. Create it empty:

1. <https://github.com/new>
2. Name: **`cysa-plus-study`** · Private · **no** README, `.gitignore`, or licence
3. Create repository

Then from this folder:

```bash
git remote add origin https://github.com/YOUR-USERNAME/cysa-plus-study.git
git push -u origin main
```

> **Why this is manual:** the GitHub App used by Claude Code sessions has
> read/write on repositories that already exist, but not permission to create
> them — `POST /user/repos` returns `403 Resource not accessible by integration`.
> Creating an empty repo has to come from a browser or a personal access token.

---

## Step 2 — Deploy it

1. <https://railway.app> → **New Project**
2. **Deploy from GitHub repo** → pick `cysa-plus-study`
   (first time only: *Configure GitHub App* and grant access to the repo)
3. Railway detects Python from `requirements.txt` and reads the start command.
   No environment variables are needed — the app has no database, no secrets,
   and no accounts.
4. When the build finishes: **Settings → Networking → Generate Domain**

You get something like `cysa-plus-study-production.up.railway.app`.

Check it's healthy: `https://<your-domain>/healthz` should return `ok`.

### What's already configured

| File | Does |
|---|---|
| `Procfile` | gunicorn start command, matching the convention in the Noted project |
| `railway.json` | builder, start command, `/healthz` healthcheck, restart policy |
| `requirements.txt` | Flask and gunicorn — the whole dependency list |
| `runtime.txt` | pins Python 3.11.9 |

---

## Step 3 — Install it on the phone

1. Open the Railway URL in **Chrome on Android**.
2. Wait for it to finish loading once — that's the service worker caching
   everything for offline use. The contents rail shows *"Saved for offline use"*
   at the bottom when it's done.
3. **⋮ → Add to Home screen** (or take the *Install app* prompt).

It launches full-screen with its own icon and works with no connection.

### Set up the voice

Tap **⚙** in the app:

- **Voice** — pick one marked **(on device)**. Those keep working offline;
  *(network)* voices don't.
- **Speed** — 1.0× to start. Faster once the material is familiar.
- **Answer pause** — the gap between question and answer in the spoken drill.

No voices listed? Android installs them under **Settings → Accessibility →
Text-to-speech output**. Google's engine is the usual one and it's free.

---

## Verify it works offline

Worth doing once, deliberately.

1. Open the app from the home-screen icon and let it load fully.
2. **Turn on airplane mode.**
3. Close the app and reopen it — it should load normally.
4. Read a section, then tap **Listen**. Speech should start with no connection.
5. Open **Cards**, answer a few, grade them.
6. Airplane mode off.

If step 3 fails, the service worker didn't register — it needs one complete
online load first, over https.

If step 4 fails but the text works, the selected voice is a network voice.
Switch to one marked *(on device)*.

---

## Updating it later

```bash
python3 build_content.py     # after editing any Markdown
git commit -am "Update notes"
git push
```

Railway redeploys on push. `build_content.py` stamps `sw.js` with a hash of the
content, so the new version replaces the cached one on the phone's next visit
instead of being masked by a stale service worker.

Flashcard progress lives in the phone's `localStorage` and survives updates.

---

## Costs

Railway's free allowance covers this comfortably — it's a static file server
with no database and no background work. It sleeps when idle and wakes on
request; the app runs from cache on the phone regardless.
