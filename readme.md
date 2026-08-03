# nex + Scrinex — a working Git-like VCS with a web portal

Three pieces, one shared source of truth (the `.nexgit/` folder in your project):

- **`nex.py`** — the CLI (`nex init`, `add`, `commit`, `push`, `log`, `status`, `diff`, `branch`, `checkout`, `remote`)
- **`pygit_core.py`** — the actual object model / repo logic, imported by both the CLI and the server
- **`server.py`** + **`scrinex/index.html`** — a local API + web portal (Scrinex) that reads the same repo and renders a GitHub-style file browser, commit log, and diffs

The CLI and the portal never talk to each other directly — the CLI writes to `.nexgit/`, and the portal just re-reads it on every request (it auto-refreshes every 4s). Run a command, refresh the page (or wait), see it reflected.

## Quick start (works the same on macOS / Windows / Linux)

The whole project is pure-Python stdlib — no `pip install` needed, no compiled dependencies. The **only** requirement on the presentation machine is Python 3 itself. This is the one command that's guaranteed to work no matter whose laptop you're on, so it's the fallback to fall back on if anything below misbehaves:

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>

python3 nex.py init
python3 nex.py add .
python3 nex.py commit -m "initial commit"

# edit some files, then:
python3 nex.py status
python3 nex.py diff
python3 nex.py add .
python3 nex.py commit -m "second commit"
```

On Windows, if `python3` isn't recognized, use `python` instead (Windows' python.org installer registers the command as `python`, not `python3`) — everything else is identical:
```powershell
python nex.py init
python nex.py add .
python nex.py commit -m "initial commit"
```

### Making `nex` a bare command (optional, per-OS)

This is nice for a live demo (`nex add .` instead of `python3 nex.py add .`) but is **OS-specific setup you'd have to redo on someone else's machine** — so for presenting on an unfamiliar device, skip this section entirely and just use `python3 nex.py ...` above, which needs zero setup.

If you do want it on a machine you control:

**macOS / Linux:**
```bash
chmod +x nex.py
sudo ln -s "$(pwd)/nex.py" /usr/local/bin/nex   # or: alias nex="python3 $(pwd)/nex.py"
```

**Windows (PowerShell):**
```powershell
Set-Alias nex "python $PWD\nex.py"    # current session only
# For a persistent alias, add that line to your PowerShell $PROFILE instead
```

## Push (to a local "remote")

There's no real network transport here — `push` targets a path on disk, standing in for a remote server the way a bare repo would. This is enough to demonstrate the push model (only-copy-missing-objects, update remote ref) without needing auth/networking:

```bash
python3 nex.py remote add origin /some/other/folder
python3 nex.py push origin main
```

## Run the Scrinex portal

From inside the cloned repo (no extra copying needed if `server.py` and `scrinex/` are already in the repo):
```bash
python3 server.py . 8000
```
On Windows, `python server.py . 8000` if `python3` isn't recognized.

Then open **http://localhost:8000** in a browser — you'll see the file tree, commit history (click a commit for its diff), and a "Changes" tab mirroring `nex status`.

`server.py` takes the repo path and port as args, so you can also point it at a separate demo folder: `python3 server.py /path/to/demo-repo 8000`.

### Presenting on an unfamiliar / borrowed machine

Since this needs nothing beyond Python 3 (check with `python3 --version` or `python --version`), the safest presentation flow on any OS is:

```bash
git clone <your-repo-url>
cd <your-repo>
python3 nex.py init && python3 nex.py add . && python3 nex.py commit -m "demo commit"
python3 server.py . 8000
```
then open `http://localhost:8000` in whatever browser is on that machine. No admin rights, no PATH edits, no symlinks required — just `git clone` + `python3`.

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
