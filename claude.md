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
- `Dockerfile` / `docker-compose.yml` — optional: containerized run, only useful if the host already has Docker

## Design constraints (don't violate these silently)
- Repo state lives entirely in `.nexgit/` (objects/, refs/heads/, HEAD, index, config.json) — mirrors real Git's layout but is our own format, not git-compatible.
- Index is JSON (not Git's real binary format) — intentional simplification.
- File browser (`build_working_tree` in pygit_core.py) must always reflect the REAL working directory, not just staged/committed files — this was a fixed bug; don't regress it.
- `push` targets a local filesystem path standing in for a remote (copies missing objects, updates ref) — there is no real network transport yet.
- No `pull`/`fetch`, no merge, no `.gitignore`, no conflict resolution — these are known, deliberate gaps, not bugs to silently "fix" by inventing shortcuts.
- Diff colors (green/add, red/delete) are a fixed convention — don't retheme those even if reskinning the UI. Everything else (accent, glass, brand) is currently a monochrome silver/black "vault" theme.

## Conventions
- Pure Python stdlib only — no pip installs, no external runtime deps.
- Single-file HTML (inline CSS/JS) for both Scrinex pages — no build step, no bundler.
- Test changes by actually running: `nex init`, `add`, `commit`, then `server.py . <port>` and hitting the real API endpoints, not just reading the code.