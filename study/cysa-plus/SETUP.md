# Setup — get this onto the device, and into a private repo

## The goal

**Download this entire project to the local device for offline access.**

The study pack must be fully usable with the network off: on a plane, in an exam
prep session with no signal, on a machine that has never been online. That means
the whole project — notes, build script, and generated HTML — lives *on the
device itself*. A hosted copy is a backup, not the deliverable.

Two separate things follow from that, and they are independent:

| | What it gives you | Required? |
|---|---|---|
| **Part 1 — Get it on the device** | Offline access. This is the actual goal. | Yes |
| **Part 2 — Put it in a private repo** | Version history, sync across machines, a durable backup. | Optional |

Do Part 1. Part 2 is filing.

---

# Part 1 — Get the project onto this device

Pick whichever applies. All of them end with the complete project in a local
folder, and none of them need a connection afterwards.

### From the chat attachment (simplest)

The file `cysa-plus-study.zip` was delivered directly in conversation. Download
it, then unzip it wherever you keep working files. Done — that folder *is* the
project, git history included.

### From GitHub, with git

```bash
git clone https://github.com/YOUR-USERNAME/cysa-plus-study.git
```

### From GitHub, without git

On the repo page: **Code → Download ZIP**. Unzip it. You lose the git history;
the content is identical.

### From the staging branch, if the standalone repo doesn't exist yet

```bash
git clone --branch claude/course-offline-access-uk538j \
  https://github.com/jwinnAThayden/mobile-noted.git
```

The pack is under `study/cysa-plus/`.

### Verify you actually have offline access

Turn the network off, open `cysa-offline.html`, and click through the sidebar.
Then play `audio/flashcards.mp3` to confirm the narrated version came across too.
If everything renders — tables, code blocks, all eleven sections — you're done.
The page makes **zero** network requests by design, so nothing should degrade.

> **A note on what a Claude Code session can and cannot do here.** These sessions
> run in an ephemeral cloud container, not on your device. Nothing can be written
> to your local disk directly. The download has to be initiated from your end —
> via the chat attachment, a clone, or a browser download. That is why this
> project is packaged as a single zip and a single self-contained HTML file
> rather than as something that installs itself.

---

# Part 2 — Stand it up as your own private repo

Optional for reading the notes; **required** if you want the web app on your
phone, since Android only installs a PWA from an https origin. For that path
do Step 1 below, then follow [`DEPLOY.md`](DEPLOY.md).

Everything you need is in this folder. It does **not** depend on any other
repository, and the study material works right now without doing any of this.

**Time required: about 3 minutes.**

---

## Before you start

You need a GitHub account. That's it. The git history is already committed in
this folder, so there's nothing to prepare.

> **Why this step is manual:** the GitHub App used by Claude Code sessions has
> read/write access to repositories that already exist, but not permission to
> *create* new ones (`POST /user/repos` → `403 Resource not accessible by
> integration`). Creating the empty repo has to come from a browser or a
> personal access token. Everything after that can be automated.

---

## Step 1 — Create the empty repository

1. Go to <https://github.com/new>
2. **Repository name:** `cysa-plus-study`
3. **Visibility:** Private
4. **Leave every initialise option unticked** — no README, no `.gitignore`,
   no licence. The repo must be completely empty or the first push is rejected.
5. Click **Create repository**

---

## Step 2 — Push this folder into it

Pick whichever path suits the machine you're on.

### Path A — Git command line (recommended)

From inside this folder:

```bash
git remote add origin https://github.com/YOUR-USERNAME/cysa-plus-study.git
git push -u origin main
```

Replace `YOUR-USERNAME` with your GitHub username.

If this folder somehow lost its git history (you copied the files rather than
the whole folder), run this first:

```bash
git init -b main
git add -A
git commit -m "Offline CySA+ (CS0-003) study pack"
```

### Path B — GitHub Desktop

1. **File → Add local repository**, choose this folder
2. **Publish repository**, tick **Keep this code private**

### Path C — Browser upload, no tools needed

Works from a tablet or a locked-down machine.

1. On your new empty repo page, click **uploading an existing file**
2. Drag in every file from this folder **except** the hidden `.git` folder
3. Commit directly to `main`

You lose the commit history this way; the content is identical.

---

## Step 3 — Confirm it worked

Open `https://github.com/YOUR-USERNAME/cysa-plus-study`. You should see the
README rendered, and `cysa-offline.html` in the file list.

---

## Step 4 — Clean up the staging copy (optional)

A copy was staged on a branch of the `mobile-noted` repository while this was
being built. Once the new repo is live, that branch is redundant:

```bash
git push origin --delete claude/course-offline-access-uk538j
```

Or delete it from the GitHub web UI: **mobile-noted → Branches → 🗑**.

---

## Keeping it accessible on the device

The repo is your durable, versioned copy. For actually *reading* it offline,
pick whichever of these fits how you study:

| Where | How | Offline? |
|---|---|---|
| **Phone / tablet** | Put `cysa-offline.html` in OneDrive or Google Drive and mark it **Available offline**. Open it with any browser. | Yes |
| **Laptop** | Clone the repo, or just keep `cysa-offline.html` on the desktop. | Yes |
| **Any device, quick look** | Browse the Markdown on github.com — renders tables and all. | No |
| **Audio, offline** | Copy `audio/` to the phone (OneDrive marked *Available offline*, or straight onto the device). 105 minutes of MP3s, including a 92-card spoken drill. See [`AUDIO.md`](AUDIO.md). | Yes |
| **Printed** | Open `cysa-offline.html`, Ctrl/Cmd-P. The sidebar is hidden automatically in print styles. | Yes |

`cysa-offline.html` makes **zero network requests** — no CDN, no fonts, no
analytics, no external scripts. Copy it to a USB stick and it works on a machine
that has never been online.

---

## Editing it later

The Markdown files are the source of truth. After changing any of them:

```bash
python3 build_offline_html.py
```

Python 3, standard library only — nothing to install, works offline. The script
regenerates `cysa-offline.html` from every `.md` file. Then commit and push as
normal.

To add a section, create a new `.md` file and add it to the `PAGES` list near
the top of `build_offline_html.py`.
