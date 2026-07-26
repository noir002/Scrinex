const express = require("express");
const cors = require("cors");
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

const DB_FILE = path.join(__dirname, "db.json");
const PORT = process.env.PORT || 4000;

const app = express();
app.use(cors());
app.use(express.json());
// Serve the dashboard (scrinex-web) at the site root.
app.use(express.static(path.join(__dirname, "..", "scrinex-web")));

// --- tiny JSON-file "database" ---------------------------------------------
function loadDB() {
  if (!fs.existsSync(DB_FILE)) {
    return { repos: {} };
  }
  return JSON.parse(fs.readFileSync(DB_FILE, "utf-8"));
}

function saveDB(db) {
  fs.writeFileSync(DB_FILE, JSON.stringify(db, null, 2));
}

function getRepoOr404(db, id, res) {
  const repo = db.repos[id];
  if (!repo) {
    res.status(404).json({ error: "repo not found" });
    return null;
  }
  return repo;
}

// --- routes ------------------------------------------------------------
app.post("/api/repos", (req, res) => {
  const db = loadDB();
  const id = crypto.randomUUID();
  const repo = {
    id,
    name: req.body.name || "untitled",
    createdAt: new Date().toISOString(),
    staged: [],
    commits: [],
  };
  db.repos[id] = repo;
  saveDB(db);
  res.status(201).json(repo);
});

app.get("/api/repos", (req, res) => {
  const db = loadDB();
  res.json(Object.values(db.repos));
});

app.get("/api/repos/:id", (req, res) => {
  const db = loadDB();
  const repo = getRepoOr404(db, req.params.id, res);
  if (repo) res.json(repo);
});

app.post("/api/repos/:id/staged", (req, res) => {
  const db = loadDB();
  const repo = getRepoOr404(db, req.params.id, res);
  if (!repo) return;
  repo.staged = req.body.files || [];
  repo.updatedAt = new Date().toISOString();
  saveDB(db);
  res.json({ ok: true, staged: repo.staged });
});

app.post("/api/repos/:id/commits", (req, res) => {
  const db = loadDB();
  const repo = getRepoOr404(db, req.params.id, res);
  if (!repo) return;
  const commit = {
    hash: req.body.hash,
    message: req.body.message,
    author: req.body.author,
    timestamp: req.body.timestamp,
    files: req.body.files || [],
  };
  repo.commits.unshift(commit); // newest first
  repo.staged = []; // clear staging area after commit, like real git
  repo.updatedAt = new Date().toISOString();
  saveDB(db);
  res.status(201).json(commit);
});

if (!fs.existsSync(DB_FILE)) saveDB({ repos: {} });

app.listen(PORT, () => {
  console.log(`Scrinex server running at http://localhost:${PORT}`);
});
