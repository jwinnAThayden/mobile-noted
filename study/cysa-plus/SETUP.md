# Setup — stand this up as your own private repo

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

## Keeping it accessible

The repo is your durable, versioned copy. For actually *reading* it offline,
pick whichever of these fits how you study:

| Where | How | Offline? |
|---|---|---|
| **Phone / tablet** | Put `cysa-offline.html` in OneDrive or Google Drive and mark it **Available offline**. Open it with any browser. | Yes |
| **Laptop** | Clone the repo, or just keep `cysa-offline.html` on the desktop. | Yes |
| **Any device, quick look** | Browse the Markdown on github.com — renders tables and all. | No |
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
