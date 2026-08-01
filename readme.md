# nex + Scrinex — a working Git-like VCS with a web portal

Three pieces, one shared source of truth (the `.nexgit/` folder in your project):

- **`nex.py`** — the CLI (`nex init`, `add`, `commit`, `push`, `log`, `status`, `diff`, `branch`, `checkout`, `remote`)
- **`pygit_core.py`** — the actual object model / repo logic, imported by both the CLI and the server
- **`server.py`** + **`scrinex/index.html`** — a local API + web portal (Scrinex) that reads the same repo and renders a GitHub-style file browser, commit log, and diffs

The CLI and the portal never talk to each other directly — the CLI writes to `.nexgit/`, and the portal just re-reads it on every request (it auto-refreshes every 4s). Run a command, refresh the page (or wait), see it reflected.

## Quick start

```bash
# 1. Put nex.py, pygit_core.py, server.py, and scrinex/ in (or alongside) your project folder
cd my-project
cp /path/to/nex.py /path/to/pygit_core.py .

python3 nex.py init
python3 nex.py add .
python3 nex.py commit -m "initial commit"

# edit some files, then:
python3 nex.py status
python3 nex.py diff
python3 nex.py add .
python3 nex.py commit -m "second commit"
```

Optionally make it feel like a real command:
```bash
chmod +x nex.py
alias nex="python3 $(pwd)/nex.py"   # now: nex init, nex add ., nex commit -m "..."
```

## Push (to a local "remote")

There's no real network transport here — `push` targets a path on disk, standing in for a remote server the way a bare repo would. This is enough to demonstrate the push model (only-copy-missing-objects, update remote ref) without needing auth/networking:

```bash
python3 nex.py remote add origin /some/other/folder
python3 nex.py push origin main
```

## Run the Scrinex portal

```bash
cp -r /path/to/server.py /path/to/scrinex .
python3 server.py . 8000
```
Then open **http://localhost:8000** — you'll see the file tree, commit history (click a commit for its diff), and a "Changes" tab mirroring `nex status`.

`server.py` takes the repo path and port as args: `python3 server.py /path/to/repo 8000`.

## What's implemented (the "basic/core" scope)

- `init`, `add` (files or whole directories), `commit`, `status`, `diff` (staged vs HEAD), `log`
- `branch`, `checkout` (create/switch)
- `remote add`, `push` (local-path remote, object-copy based)
- API: `/api/status`, `/api/tree`, `/api/file`, `/api/log`, `/api/branches`, `/api/commit/<hash>`, `/api/commit/<hash>/diff`, `/api/diff/working`, `/api/remotes`
- Scrinex UI: file browser (click to view content), commit history (click for diff), live status/changes tab, auto-refresh

## Known gaps (deliberately out of scope for this prototype)

- No merge/conflict resolution — checkout just swaps the tree, no three-way merge
- No `pull`/`fetch` yet (push is one-directional; add the mirror operation when you scale this up)
- No auth on the API or the "remote" — anyone with API access can read everything; fine for local use, not for a real multi-user deployment
- No `.gitignore` support — the whole directory gets staged on `add .`
- Push is local-filesystem only, not a real network protocol — swapping in real transport (HTTP+auth) is the natural next step when you scale past prototype
