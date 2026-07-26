#!/usr/bin/env node

const { Command } = require("commander");
const simpleGit = require("simple-git");
const fetch = require("node-fetch");
const { readConfig, writeConfig, requireConfig } = require("../lib/config");

const git = simpleGit();
const program = new Command();

program
  .name("nex")
  .description("nex - a git wrapper CLI that mirrors your work to Scrinex");

// ---------------------------------------------------------------------------
// nex init <repo-name> [--server <url>]
// ---------------------------------------------------------------------------
program
  .command("init <repoName>")
  .description("git init this folder, then register it with Scrinex")
  .option("-s, --server <url>", "Scrinex server URL", "http://localhost:4000")
  .action(async (repoName, opts) => {
    await git.init();
    console.log("✓ git repository initialized");

    const res = await fetch(`${opts.server}/api/repos`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: repoName }),
    });

    if (!res.ok) {
      console.error("✗ Failed to register repo with Scrinex:", await res.text());
      process.exit(1);
    }

    const repo = await res.json();
    writeConfig({ repoId: repo.id, repoName: repo.name, server: opts.server });
    console.log(`✓ Registered "${repo.name}" on Scrinex (id: ${repo.id})`);
    console.log(`  View it at ${opts.server.replace(/\/api.*/, "")}/?repo=${repo.id}`);
  });

// ---------------------------------------------------------------------------
// nex add <files...>
// ---------------------------------------------------------------------------
program
  .command("add <files...>")
  .description("git add, then report staged changes to Scrinex")
  .action(async (files) => {
    const config = requireConfig();

    await git.add(files);
    console.log(`✓ staged: ${files.join(", ")}`);

    const status = await git.status();
    const stagedFiles = [
      ...status.staged.map((f) => ({ path: f, status: "modified" })),
      ...status.created.map((f) => ({ path: f, status: "added" })),
      ...status.deleted.map((f) => ({ path: f, status: "deleted" })),
    ];

    // Capture the actual content diff for everything currently staged,
    // so the dashboard can show *what* changed, not just *which files*.
    const diff = await git.diff(["--cached"]);

    await postJSON(`${config.server}/api/repos/${config.repoId}/staged`, {
      files: stagedFiles,
      diff,
    });
    console.log(`✓ synced staged changes to Scrinex`);
  });

// ---------------------------------------------------------------------------
// nex commit -m "message"
// ---------------------------------------------------------------------------
program
  .command("commit")
  .description("git commit, then push the commit record to Scrinex")
  .requiredOption("-m, --message <message>", "commit message")
  .action(async (opts) => {
    const config = requireConfig();

    await git.commit(opts.message);
    console.log(`✓ committed: "${opts.message}"`);

    const log = await git.log({ maxCount: 1 });
    const latest = log.latest;

    const diffRaw = await git.raw([
      "diff-tree",
      "--no-commit-id",
      "--name-status",
      "-r",
      latest.hash,
    ]);
    const files = diffRaw
      .split("\n")
      .filter(Boolean)
      .map((line) => {
        const [statusCode, filePath] = line.split("\t");
        return { path: filePath, status: statusCode };
      });

    // Full unified diff for this commit - this is what lets Scrinex show
    // the actual code that changed, not just filenames.
    const patch = await git.raw(["show", latest.hash, "--format=", "-p"]);

    await postJSON(`${config.server}/api/repos/${config.repoId}/commits`, {
      hash: latest.hash,
      message: latest.message,
      author: latest.author_name,
      timestamp: latest.date,
      files,
      patch,
    });
    console.log(`✓ pushed commit ${latest.hash.slice(0, 7)} to Scrinex`);
  });

// ---------------------------------------------------------------------------
async function postJSON(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    console.error(`✗ Scrinex sync failed (${res.status}):`, await res.text());
  }
  return res;
}

program.parse();
