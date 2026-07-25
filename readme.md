# 🗂️ Scrinex

<div align="center">

![Scrinex](https://img.shields.io/badge/Scrinex-Code%20Hosting%20%2B%20Version%20Control-blue?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-In%20Development-yellow?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-lightgrey?style=for-the-badge)

**A GitHub-style code hosting platform, paired with a from-scratch CLI exploring how staging → commit → remote sync works**

[🐛 Report Bug](../../issues) • [✨ Request a Feature](../../issues)

</div>

---

## ⚠️ Known gap — read this first

The authorization layer is not finished yet. `authMiddleware.js` and
`authorizeMiddleware.js` exist as stub files but are not currently wired
into any route, so protected actions (deleting a user, editing a repo you
don't own, etc.) are not yet enforced server-side. This is being actively
worked on — see [Known Issues](#-known-issues) for the full list. Please
don't deploy this publicly or point it at real user data until it's
resolved.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Tech Stack](#️-tech-stack)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [The Scrinex CLI](#-the-scrinex-cli)
- [API Reference](#-api-reference)
- [Known Issues](#-known-issues)
- [Roadmap](#️-roadmap)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Overview

Scrinex is two related pieces built side by side:

1. **A code hosting web platform** — a REST API + React frontend covering
   users, repositories, and issues, styled after GitHub's own design system,
   with a contribution heatmap on user profiles.
2. **A custom CLI version-control tool** — a from-scratch exploration of
   the core version-control workflow (`init` → `add` → `commit` →
   `push`/`pull` → `revert`), backed by local file staging and remote sync
   to S3.

These are two different things solving two different problems. The web
platform is a hosted app for browsing and managing repos and issues; the
CLI is a separate, simplified take on *how* version control works under
the hood — file staging and commit metadata, not real Git internals like
content-addressable storage or diffing.

---

## ✨ Features

### Web platform
- Signup/login (JWT + bcrypt)
- Repository CRUD, per-user listing, public/private visibility toggle
- Issue tracking scoped to a repository (`open`/`closed`)
- Dashboard: your repos, suggested repos, search
- Profile page with a GitHub-style contribution heatmap
- Client-side session handling via `authContext`

### Scrinex CLI
- `init` — creates a local version-control folder with a `commits/` subfolder and config
- `add <file>` — stages a file for the next commit
- `commit <msg>` — copies staged files into a new commit directory with a message + timestamp
- `push` / `pull` — syncs local commits to/from an S3 bucket
- `revert <commitID>` — restores files from a given commit back into the working directory

This is intentionally a simplified model, not a Git reimplementation — it
demonstrates the staging → commit → sync pattern used by real backup and
version-control systems, without content hashing, diffing, or branching.

---

## 🛠️ Tech Stack

| Layer | Stack |
|---|---|
| **Frontend** | React 18, Vite, React Router v6, Primer (GitHub's design system), `@uiw/react-heat-map`, Axios |
| **Backend** | Node.js, Express, MongoDB (Mongoose), JWT + bcrypt, Socket.io (initialized, not yet used for a live feature), AWS SDK (S3) |
| **CLI** | `yargs`, exposed from the same entry point that boots the Express server |

---

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- MongoDB (local or Atlas)
- An AWS account + S3 bucket (only needed for `push`/`pull`)

### 1. Clone and install
```bash
git clone https://github.com/<your-username>/scrinex.git
cd scrinex

# backend
cd backend-main
npm install

# frontend
cd ../frontend-main
npm install
```

### 2. Configure environment
Create `backend-main/.env` — never commit a populated one:
```env
MONGODB_URI=mongodb://localhost:27017/scrinex
JWT_SECRET=<generate your own — do not reuse examples>
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
scrinex/
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
│
└── README.md
```

---

## 💻 The Scrinex CLI

Worth calling out on its own, since it's a genuinely separate learning
exercise from the web platform: it's a simplified model of what real
version-control and backup systems do — stage locally, commit with
metadata, sync to durable remote storage, roll back on demand. It does
**not** implement:
- Content-addressable storage or hashing (no dedup between commits)
- Diffing (no way to see what changed between two commits)
- Branching

Framed accurately, it's a hands-on exploration of the *shape* of these
systems — the same shape you'll find in tools like DVC — not a Git clone,
and it isn't described as one anywhere in this project.

---

## 📱 API Reference

**Base URL:** `http://localhost:<port>` (set via your backend `.env`)

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
> [Known Issues](#-known-issues). Once auth middleware is wired in, this
> section will be updated to mark each route public vs. protected vs.
> owner/admin-only.

---

## 🔒 Known Issues

| Issue | Where | Impact |
|---|---|---|
| Auth middleware not wired into any route | `authMiddleware.js`, `authorizeMiddleware.js` | Any client can hit any endpoint — including deleting another user's account or editing a repo they don't own |
| Unused Vite scaffolding still present | `frontend-main/src/App.jsx` | Dead code left from project setup; the app actually renders a separate routes component |
| Hardcoded API base URLs | frontend components | Points at a local dev URL; won't work post-deploy without a config change |
| Two different MongoDB access patterns | raw `MongoClient` in one controller vs. Mongoose in others | Inconsistent data layer, worth unifying |
| S3 bucket name is a placeholder | `config/aws-config.js` | `push`/`pull` won't work until real bucket + credentials are set |
| Stray commit artifact in repo root | backend root | Leftover from local CLI testing |
| No automated tests | — | Testing libraries are installed but unused |

---

## 🗺️ Roadmap

- [ ] Wire up `authMiddleware` and `authorizeMiddleware` on all protected/owner-only routes
- [ ] Add tests for auth flows and repo/issue ownership checks
- [ ] Move API base URL to environment config
- [ ] Unify MongoDB access pattern (Mongoose everywhere)
- [ ] Remove dead scaffolding and stray test artifacts
- [ ] Explore content-addressable storage in the CLI (real diffing between commits)

---

## 👥 Contributing

Contributions are welcome once the auth layer lands. In the meantime:

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes with a clear message
4. Open a pull request describing what changed and why

---

## 📄 License

MIT — see [LICENSE](LICENSE) for details.

<div align="center">

**⭐ Star this repo if you find it useful!**

</div>