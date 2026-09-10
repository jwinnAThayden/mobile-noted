# Handoff — staging copy

This directory is a **backup mirror** of a standalone study pack. It is staged
here only because it was built in this repository; it has no dependency on
`mobile-noted` and no connection to the Noted application.

## Where the real thing goes

The pack is intended to live in its own private repository,
`cysa-plus-study`. Setup instructions are in
**[`SETUP.md`](SETUP.md)** — roughly three minutes of work, one step of which
(creating the empty repo) must be done from a browser because the GitHub App
used by Claude Code sessions cannot create repositories.

A ready-to-push zip of this folder, with git history already committed, was
delivered directly to the repository owner. If that zip is still to hand, use
it rather than copying files out of here.

## Rebuilding from this copy instead

```bash
git clone --branch claude/course-offline-access-uk538j \
  https://github.com/jwinnAThayden/mobile-noted.git /tmp/src

mkdir cysa-plus-study && cd cysa-plus-study
cp /tmp/src/study/cysa-plus/*.md /tmp/src/study/cysa-plus/*.py /tmp/src/study/cysa-plus/*.html .
rm HANDOFF.md                     # this file does not belong in the new repo
printf '__pycache__/\n*.pyc\n.DS_Store\n' > .gitignore

python3 build_offline_html.py
git init -b main && git add -A && git commit -m "Offline CySA+ (CS0-003) study pack"
git remote add origin https://github.com/jwinnAThayden/cysa-plus-study.git
git push -u origin main
```

Then follow `SETUP.md` from Step 3 onward.

## Deleting this branch

Once the standalone repo exists, this branch is redundant:

```bash
git push origin --delete claude/course-offline-access-uk538j
```

Nothing on `master` is affected — this branch was never merged and the Noted
application was never modified.
