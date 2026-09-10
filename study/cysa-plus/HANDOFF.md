# Handoff — completing the move to a standalone repo

**Status:** the study pack is finished. The only thing left is relocating it out
of `mobile-noted` into its own repository.

## Why it stalled

The GitHub App backing the Claude Code session had read/write on existing
repositories but **not** permission to create new ones — `POST /user/repos`
returned `403 Resource not accessible by integration`. Repository creation has
to happen from a browser or a personal access token.

## What lives where

| Item | Location |
|---|---|
| Study pack (final) | `study/cysa-plus/` on branch `claude/course-offline-access-uk538j` |
| README for the standalone repo root | `study/cysa-plus/README-standalone.md` |
| `.gitignore` for the standalone repo | `study/cysa-plus/gitignore-standalone.txt` |
| Generated single-file HTML | `study/cysa-plus/cysa-offline.html` |

`README.md` in this directory is the *in-repo* version and references
`mobile-noted`. `README-standalone.md` is the rewritten version with those
references removed — use that one at the root of the new repo.

## Finishing it yourself

1. Create an empty repo at <https://github.com/new> named `cysa-plus-study`.
   Private, and **do not** initialise it with a README.

2. Then:

```bash
git clone --branch claude/course-offline-access-uk538j \
  https://github.com/jwinnAThayden/mobile-noted.git /tmp/src

mkdir cysa-plus-study && cd cysa-plus-study
cp /tmp/src/study/cysa-plus/*.md  .
cp /tmp/src/study/cysa-plus/*.py  .
cp /tmp/src/study/cysa-plus/*.html .

mv README-standalone.md README.md
mv gitignore-standalone.txt .gitignore
rm HANDOFF.md                     # this file doesn't belong in the new repo

python3 build_offline_html.py     # rebuild so the HTML matches the new README

git init -b main
git add -A
git commit -m "Offline CySA+ (CS0-003) study pack"
git remote add origin https://github.com/jwinnAThayden/cysa-plus-study.git
git push -u origin main
```

3. Once the push succeeds, delete the staging branch:

```bash
git push origin --delete claude/course-offline-access-uk538j
```

## Finishing it in a new Claude Code session

Create the empty repo first, then paste:

> Finish the CySA+ study pack move. Everything is on the
> `claude/course-offline-access-uk538j` branch of `jwinnAThayden/mobile-noted`
> under `study/cysa-plus/`, and `HANDOFF.md` in that directory has the full
> procedure. Move it to `jwinnAThayden/cysa-plus-study`, then delete the branch.

## If you'd rather not bother

The pack is already usable as-is. `cysa-offline.html` is self-contained — open
it from anywhere, no network needed. Leaving it on the branch costs nothing.
