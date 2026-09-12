nex + Scrinex -- STATUS
=======================

What's actually done, verified and working -- versus what's still missing
to be a real GitHub-level platform. Written plainly so nothing here
overstates scope.


DONE (PHASE 1)
--------------

Core engine (pygit_core.py)
- Content-addressed object model -- Blob, Tree, Commit, all SHA-1 hashed
- Full Merkle-tree structure: parent hashes derived from child hashes, all
  the way to the commit
- Zlib-compressed object storage, Git-style objects/<2>/<38> layout
- Staging area (JSON index), commit graph with parent-chain history
- Branching and checkout (tree swap, no merge)
- Line-level diff (difflib.unified_diff) between any two trees/commits/
  working state
- Working-directory-aware file browser data (shows staged/modified/
  untracked/tracked status per file -- not just committed state)

CLI (nex.py)
- init, add, commit, status, diff, log, branch, checkout, remote add, push
- Zero runtime dependencies -- pure Python stdlib

Push / remote
- Local-path push (copy missing objects, update ref) -- works like a
  bare-repo remote
- HTTP push -- nex push can target a live server.py instance (e.g. a
  deployed URL), checking for missing objects and updating the remote's
  ref over the network, so a hosted dashboard reflects a push immediately,
  no redeploy needed
- Optional shared-secret push token (NEX_PUSH_TOKEN) -- single global
  token only, not per-user

Web portal (Scrinex)
- Landing page: live repo stats, profile card, download CTA
- Repo browser (/app): file tree, commit history with diffs, changes/
  status tab
- Polling-based live refresh (no websockets)
- Metallic/glass visual theme, consistent across both pages

Distribution
- nex-portable.zip -- tested standalone: extract, init/add/commit all
  verified working fresh
- install.sh / install.ps1 -- one-shot nex command installer (Mac/Linux/
  Windows)
- Dockerfile + docker-compose.yml

DevOps
- GitHub Actions CI (lint with ruff, unittest suite, Docker build check)
- GitHub Actions CD (build -> push to GHCR -> trigger Render deploy) on
  every push to main
- Verified: clean-room Docker rebuild, byte-identical zip-vs-served-file
  check, live redeploy confirmed reaching Render without a manual click

In progress / built but not finished
- Process-transparency logging -- server now logs the real receipt time
  of every push (push_log.jsonl), independent of the commit's self-
  reported timestamp, and /api/process correlates the two to flag
  "steady" vs "bulk" push patterns. Backend built and partially tested
  (steady-pattern case only); no frontend UI yet, and the "bulk dump"
  detection path is untested.


PENDING -- WHAT'S MISSING TO BE "LIKE GITHUB"
----------------------------------------------

Core VCS gaps (stated limitations, not bugs)
- Merge + conflict resolution -- checkout currently swaps the whole tree;
  no three-way merge, no conflict markers
- pull / fetch -- push is one-directional only; no way to bring remote
  changes down
- .gitignore -- nex add . stages everything in the directory, no
  exclusion rules
- File mode tracking -- no executable bit, no symlinks; everything
  hardcoded as a regular file
- Real binary index format -- currently JSON; fine functionally, not
  Git-compatible
- Packfiles / delta compression / garbage collection -- every object
  stored loose, forever

Multi-user / platform gaps (needed before "many colleges" or "many
users" is safe)
- No real authentication -- no accounts, no login, no per-user
  permissions; the API and push endpoint have no per-user isolation
- No multi-tenancy -- one server process currently serves one repo;
  nothing partitions data between different users/organizations
- No authorization model -- can't yet express "this user can read but
  not write," "this repo is private to this team," etc.

GitHub-specific features not attempted (correctly out of scope for now)
- Pull requests / code review workflow
- Issues / project boards
- Organizations, teams, granular permissions
- Notifications
- In-browser file editing
- Search (code search, repo search)
- OAuth / API tokens for third-party integrations
- Rate limiting / abuse protection on public endpoints
- Package registries, Actions-equivalent CI hosted per-repo

Product-direction items discussed but not built
- Academic-integrity dashboard UI (backend groundwork exists -- see
  "in progress" above)
- White-label branding layer (per-organization name/logo/theme as
  config, not hardcoded)
- In-browser (no-download) execution path -- would require a
  fundamentally different runtime (e.g. Pyodide/WASM + File System
  Access API), not attempted
