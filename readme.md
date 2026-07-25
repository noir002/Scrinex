# 🗂️ Snapshot — A GitHub-Style Platform + Custom Version Control CLI

<div align="center">

**A MERN social coding platform, paired with a from-scratch CLI exploring how staging → commit → remote sync works**

</div>

---

## ⚠️ Known gap — read this first

The authorization layer is not finished yet. `authMiddleware.js` and
`authorizeMiddleware.js` exist as stub files but are not currently wired
into any route, which means protected actions (deleting a user, editing a
repo you don't own, etc.) are not yet enforced server-side. This is being
actively worked on — see [Known Issues](#-known-issues) for the full list.
Don't deploy this publicly or point it at real user data until this is
resolved.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Tech Stack](#️-tech-stack)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [The CLI (Snapshot VCS)](#-the-cli-snapshot-vcs)
- [API Reference](#-api-reference)
- [Known Issues](#-known-issues)
- [Roadmap](#-roadmap)

---

## 🎯 Overview

This project is two related pieces built side by side:

1. **A GitHub-style web app** — a REST API + React frontend covering users,
   repositories, and issues, styled after GitHub's own design system, with a
   contribution heatmap on user profiles.
2. **A custom CLI version-control tool** — a from-scratch exploration of the
   core version-control workflow (`init` → `add` → `commit` → `push`/`pull`
   → `revert`), backed by local file staging and remote sync to S3.

The two are not the same thing. The web app is a hosted platform for
browsing/managing repos and issues; the CLI is a separate, simplified take
on *how* version control works under the hood — file copying and commit
metadata, not real Git internals like content-addressable storage or diffing.

---

## ✨ Features

### Web platform
- Signup/login (JWT + bcrypt)
- Repository CRUD, per-user listing, public/private visibility toggle
- Issue tracking scoped to a repository (`open`/`closed`)
- Dashboard: your repos, suggested repos, search
- Profile page with a GitHub-style contribution heatmap
- Lightweight client-side session handling via `authContext`

### CLI (Snapshot VCS)
- `init` — creates a local `.apnaGit/` folder with a `commits/` subfolder and config
- `add <file>` — stages a file into a local `staging/` folder
- `commit <msg>` — copies staged files into `commits/<uuid>/` with a `commit.json` (message + timestamp)
- `push` / `pull` — syncs the local `commits/` tree to/from an S3 bucket
- `revert <commitID>` — restores files from a given commit back into the working directory

This is intentionally a simplified model, not a Git reimplementation — it
demonstrates the staging → commit → sync pattern used by real backup and
version-control systems, without content hashing, diffing, or branching.

---

## 🛠️ Tech Stack

**Frontend** — React 18, Vite, React Router v6, Primer (GitHub's design
system), `@uiw/react-heat-map`, Axios/fetch

**Backend** — Node.js, Express, MongoDB (Mongoose), JWT + bcrypt, Socket.io
(initialized, not yet used for a real-time feature), AWS SDK (S3)

**CLI** — `yargs`, exposed from the same `index.js` that also boots the
Express server

---

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- MongoDB (local or Atlas)
- An AWS account + S3 bucket, if you want to use `push`/`pull`

### 1. Clone and install
```bash
git clone <repo-url>
cd <repo>

# backend
cd backend-main
npm install

# frontend
cd ../frontend-main
npm install
```

### 2. Configure environment
Create `backend-main/.env` (never commit a populated one):
```env
MONGODB_URI=mongodb://localhost:27017/snapshot
JWT_SECRET=<generate your own>
AWS_ACCESS_KEY_ID=<your key>
AWS_SECRET_ACCESS_KEY=<your secret>
AWS_S3_BUCKET=<your bucket name>
```

### 3. Run
```bash
# backend (from backend-main/)
npm run dev

# frontend (from frontend-main/)
npm run dev
```

### 4. Try the CLI
```bash
cd backend-main
node index.js init
node index.js add <file>
node index.js commit -m "first commit"
node index.js push
```

---

## 📁 Project Structure

```
├── frontend-main/
│   └── src/
│       ├── pages/            # Login, Signup, Dashboard, Profile
│       ├── context/          # authContext
│       └── ...
│
├── backend-main/
│   ├── controllers/          # user, repo, issue controllers
│   ├── models/                # Mongoose schemas
│   ├── routes/
│   ├── middleware/
│   │   ├── authMiddleware.js       # stub — not yet wired in
│   │   └── authorizeMiddleware.js  # stub — not yet wired in
│   ├── config/
│   │   └── aws-config.js
│   └── index.js               # boots Express AND exposes the CLI via yargs
```

---

## 💻 The CLI (Snapshot VCS)

Worth calling out on its own, since it's a genuinely separate learning
exercise from the web app: it's a simplified model of what real
version-control and backup systems do — stage locally, commit with
metadata, sync to durable remote storage, roll back on demand. It does
**not** implement:
- Content-addressable storage or hashing (no dedup between commits)
- Diffing (no way to see what changed between two commits)
- Branching

Framed honestly, it's a hands-on exploration of the *shape* of these
systems (the same shape you'll find in tools like DVC), not a Git clone.

---

## 📱 API Reference

```http
POST   /api/users/signup
POST   /api/users/login
GET    /api/users/:id
PUT    /api/users/:id
DELETE /api/users/:id

GET    /api/repos
GET    /api/repos/:id
POST   /api/repos
PUT    /api/repos/:id
DELETE /api/repos/:id

GET    /api/issues?repo=:repoId
POST   /api/issues
PUT    /api/issues/:id
DELETE /api/issues/:id
```

> All of the above are reachable without a valid token right now — see
> Known Issues. Once `authMiddleware`/`authorizeMiddleware` are wired in,
> this section will be updated to mark which routes are public vs.
> protected vs. admin/owner-only.

---



## 🗺️ Roadmap

- [ ] Wire up `authMiddleware` and `authorizeMiddleware` on all protected/owner-only routes
- [ ] Add tests for auth flows and repo/issue ownership checks
- [ ] Move API base URL to environment config
- [ ] Unify MongoDB access pattern (Mongoose everywhere)
- [ ] Remove dead scaffolding and stray test artifacts
- [ ] Explore adding content-addressable storage to the CLI (real diffing between commits)