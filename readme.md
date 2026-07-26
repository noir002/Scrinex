# Scrinex prototype

A minimal "your own GitHub" demo:
- `nex` — a CLI that wraps real `git` (init/add/commit) and reports each action to a backend
- `scrinex-server` — Express API that stores repo/staged/commit state in `db.json`
- `scrinex-web` — a single static dashboard page, served by the same backend, that polls and shows staged changes + commit history live

## 1. Start the backend (also serves the dashboard)

```
cd scrinex-server
npm install
npm start
```

Open http://localhost:4000 in a browser — this is your Scrinex dashboard. It'll be empty until you register a repo.

## 2. Install the CLI globally (from a second terminal)

```
cd nex-cli
npm install
npm link
```

`npm link` makes the `nex` command available anywhere on your machine.

## 3. Try it on a demo project

```
mkdir ~/demo-project && cd ~/demo-project
nex init my-first-repo
echo "hello world" > file.txt
nex add file.txt
nex commit -m "Initial commit"
```

Refresh (or just wait ~3s — it polls) http://localhost:4000 and you'll see:
- the repo appear in the sidebar
- "file.txt" show up under Staged changes right after `nex add`
- it move into the commit timeline right after `nex commit`, with the staged panel clearing (just like real git)

### Viewing actual code changes

Every "Staged changes" panel and every commit now has a **"View code"** button. Clicking it expands a real unified diff (green = added lines, red = removed lines, amber = hunk headers) — this is the actual `git diff --cached` output for staged changes, and the actual `git show <hash> -p` patch for a commit. So you're not just seeing *which* files changed, you're seeing *what* changed line by line, pulled straight from git.

Try editing `file.txt` again and running `nex add file.txt` — you'll see the diff appear in Staged changes before you've even committed.

## Notes on scope (intentional, for a clean demo)
- Storage is a flat `db.json` file, not a real database — swap for Postgres later if you want persistence beyond the demo.
- `nex` doesn't reimplement git's network protocol — your actual code and history stay in real git, Scrinex only mirrors *metadata* (hash, message, changed files) for display.
- Dashboard updates via polling every 3s, not websockets — good enough to look "live" in a demo without extra infrastructure.

## Natural next steps
- `nex push` — sync full commit history if commits were made with plain `git commit` instead of `nex commit`
- A commit detail view showing actual diffs (the `diff` npm package, comparing file content between commits)
- Swap `db.json` for Postgres if you want this to double as a backend/schema-design portfolio piece
