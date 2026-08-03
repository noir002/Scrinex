#!/usr/bin/env python3
"""
server.py - serves both:
  - the Scrinex frontend (static index.html) at  /
  - a JSON API at                                /api/...

It reads the SAME .nexgit/ store that nex.py writes to. There is no push
from the CLI to this server — every API request just re-reads current
disk state, so running `nex add .` / `nex commit` in a terminal and then
hitting refresh in the browser is enough to see it reflected.

Run:  python3 server.py [repo_path] [port]
"""
from __future__ import annotations
import json
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from pygit_core import Repository, Commit

REPO_PATH = sys.argv[1] if len(sys.argv) > 1 else "."
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
FRONTEND_FILE = Path(__file__).parent / "scrinex" / "index.html"


def head_tree_hash(repo: Repository):
    branch = repo.get_current_branch()
    commit_hash = repo.get_branch_commit(branch)
    if not commit_hash:
        return None, None
    commit = Commit.from_content(repo.load_object(commit_hash).content)
    return commit.tree_hash, commit_hash


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[server] {self.address_string()} - {fmt % args}")

    def _send_json(self, payload, status=200):
        body = json.dumps(payload, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, path: Path):
        if not path.exists():
            self._send_json({"error": "frontend not found"}, 404)
            return
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        route = parsed.path
        params = urllib.parse.parse_qs(parsed.query)
        repo = Repository(REPO_PATH)

        try:
            if route == "/" or route == "/index.html":
                self._send_html(FRONTEND_FILE)
                return

            if not route.startswith("/api/"):
                self._send_json({"error": "not found"}, 404)
                return

            if not repo.exists():
                self._send_json({"error": "no repository initialized here", "initialized": False}, 200)
                return

            if route == "/api/status":
                s = repo.status()
                s["initialized"] = True
                s["repo_path"] = str(repo.path)
                self._send_json(s)

            elif route == "/api/branches":
                branches = repo.list_branches()
                self._send_json({"branches": branches, "current": repo.get_current_branch()})

            elif route == "/api/log":
                max_count = int(params.get("n", ["30"])[0])
                self._send_json({"commits": repo.log(max_count)})

            elif route == "/api/tree":
                # Always reflect the real working directory, not just what's staged
                # or committed -- otherwise files "disappear" from the browser the
                # moment you `nex add` a single other file (they were never gone,
                # the old view just never showed unstaged/uncommitted files at all).
                _, commit_hash = head_tree_hash(repo)
                nodes = repo.build_working_tree()
                self._send_json({"nodes": nodes, "commit": commit_hash, "source": "working"})

            elif route == "/api/file":
                rel_path = params.get("path", [None])[0]
                if rel_path:
                    full_path = (repo.path / rel_path).resolve()
                    if repo.path not in full_path.parents and full_path != repo.path:
                        self._send_json({"error": "invalid path"}, 400)
                        return
                    if not full_path.is_file():
                        self._send_json({"error": "file not found"}, 404)
                        return
                    content_bytes = full_path.read_bytes()
                else:
                    blob_hash = params.get("hash", [None])[0]
                    if not blob_hash:
                        self._send_json({"error": "path or hash query param required"}, 400)
                        return
                    content_bytes = repo.load_object(blob_hash).content
                try:
                    content = content_bytes.decode("utf-8")
                    binary = False
                except UnicodeDecodeError:
                    content = ""
                    binary = True
                self._send_json({"content": content, "binary": binary, "size": len(content_bytes)})

            elif route.startswith("/api/commit/"):
                rest = route[len("/api/commit/"):]
                if rest.endswith("/diff"):
                    commit_hash = rest[: -len("/diff")]
                    diff = repo.diff_commit(commit_hash)
                    self._send_json({"commit": commit_hash, "files": diff})
                else:
                    commit_hash = rest
                    commit = Commit.from_content(repo.load_object(commit_hash).content)
                    self._send_json({
                        "hash": commit_hash, "author": commit.author,
                        "timestamp": commit.timestamp, "message": commit.message,
                        "parents": commit.parent_hashes, "tree": commit.tree_hash,
                    })

            elif route == "/api/diff/working":
                self._send_json({"files": repo.diff_working_tree()})

            elif route == "/api/remotes":
                config = repo.load_config()
                self._send_json({"remotes": config.get("remotes", {})})

            else:
                self._send_json({"error": f"unknown route {route}"}, 404)

        except FileNotFoundError as e:
            self._send_json({"error": str(e)}, 404)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)


def main():
    print(f"Serving nex repo at {Path(REPO_PATH).resolve()}")
    print(f"Scrinex portal:  http://localhost:{PORT}")
    print(f"API base:        http://localhost:{PORT}/api/")
    httpd = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")


if __name__ == "__main__":
    main()