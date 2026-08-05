# nex + Scrinex

A from-scratch reimplementation of Git's core object model (blobs/trees/commits,
SHA-1 content-addressed, Merkle-tree structured) — NOT a wrapper around the real
`git` binary. No `subprocess` calls to git anywhere. Paired with Scrinex, a local
web portal that visualizes the repo live.

## Files
- `pygit_core.py` — core: `GitObject`, `Blob`, `Tree`, `Commit`, `Repository`. Imported by both nex.py and server.py.
- `nex.py` — CLI: init, add, commit, status, diff, log, branch, checkout, remote add, push
- `server.py` — stdlib-only HTTP server (no Flask/FastAPI). Serves scrinex/landing.html at `/`, scrinex/index.html at `/app`, JSON API at `/api/*`. Reads the same `.nexgit/` folder the CLI writes to — no IPC between them.
- `scrinex/landing.html` — entry page: profile card, live repo stats via API, rain/glass visual theme
- `scrinex/index.html` — repo browser: file tree (with staged/modified/untracked status dots), commit history, diffs, changes tab
- `install.sh` / `install.ps1` — optional: install `nex` as a bare CLI command
- `Dockerfile` / `docker-compose.yml` — containerized run; image bakes in `demoRepo/` so a registry pull has something to show with no volume mount
- `tests/test_pygit_core.py` — stdlib `unittest` suite covering `pygit_core.py` (no pytest/pip dep, run via `python3 -m unittest discover -s tests`)
- `ruff.toml` — CI-only lint config, scoped to real bugs (`E9`, `F`) not style opinions; ruff itself is never a runtime dependency of the app
- `.github/workflows/ci.yml` — lint + test + docker build on every push/PR
- `.github/workflows/cd.yml` — on push to `main`: builds + pushes the image to GHCR (`ghcr.io/noir002/scrinex`), then pings Render's deploy hook (`RENDER_DEPLOY_HOOK_URL` secret)
- `render.yaml` — Render Blueprint; deploys the GHCR image as a web service
- `nex-portable.zip` — checked-in build artifact (not generated at runtime): nex.py/pygit_core.py/server.py/scrinex/README/install scripts, zipped. Served by `server.py` at `/nex-portable.zip` so visitors to the hosted demo (which can't touch their filesystem) can download and run nex locally. Regenerate with `./build_portable_zip.sh` after changing any of the files it bundles — it will silently go stale otherwise.
- `build_portable_zip.sh` — regenerates `nex-portable.zip` from current source; run before committing changes to the files it bundles

## Design constraints (don't violate these silently)
- Repo state lives entirely in `.nexgit/` (objects/, refs/heads/, HEAD, index, config.json) — mirrors real Git's layout but is our own format, not git-compatible.
- Index is JSON (not Git's real binary format) — intentional simplification.
- File browser (`build_working_tree` in pygit_core.py) must always reflect the REAL working directory, not just staged/committed files — this was a fixed bug; don't regress it.
- `push` targets a local filesystem path standing in for a remote (copies missing objects, updates ref) — there is no real network transport yet.
- No `pull`/`fetch`, no merge, no `.gitignore`, no conflict resolution — these are known, deliberate gaps, not bugs to silently "fix" by inventing shortcuts.
- Diff colors (green/add, red/delete) are a fixed convention — don't retheme those even if reskinning the UI. Everything else (accent, glass, brand) is currently a monochrome silver/black "vault" theme.

## Conventions
- Pure Python stdlib only — no pip installs, no external runtime deps. (CI-only tooling like `ruff` and GitHub Actions itself is fine; it never ships in the Docker image.)
- Single-file HTML (inline CSS/JS) for both Scrinex pages — no build step, no bundler.
- Test changes by actually running: `nex init`, `add`, `commit`, then `server.py . <port>` and hitting the real API endpoints, not just reading the code. Also run `python3 -m unittest discover -s tests` before pushing — it's what CI gates on.
- `server.py`'s `REPO_PATH`/`PORT` prefer CLI args, falling back to `NEX_REPO_PATH`/`PORT` env vars — this is how the Docker image and Render deployment configure it without changing local invocation (`python3 server.py . 8000` still works unchanged).