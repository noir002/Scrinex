#!/usr/bin/env python3
"""
nex - the CLI. `python3 nex.py <command>` (or `./nex <command>` once chmod +x'd).

This is a thin wrapper: all the real logic lives in pygit_core.Repository,
which the API server (server.py) also imports — so the CLI and the Scrinex
web UI always agree on repo state, because they read/write the same
on-disk store (.nexgit/) rather than talking to each other.
"""
from __future__ import annotations
import argparse
import sys
import time

from pygit_core import Repository


def need_repo(repo: Repository) -> bool:
    if not repo.exists():
        print("Not a nex repository (run `nex init` first)")
        return False
    return True


def print_diff(diff_entries):
    if not diff_entries:
        print("No changes.")
        return
    for entry in diff_entries:
        print(f"\n--- {entry['status']}: {entry['path']} ---")
        for line in entry["diff"][2:]:  # skip the a/ b/ header lines
            print(line)


def main():
    parser = argparse.ArgumentParser(prog="nex", description="nex - a small git-like VCS with a web portal (Scrinex)")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("init", help="Initialize a new repository")

    p_add = sub.add_parser("add", help="Stage files/directories")
    p_add.add_argument("paths", nargs="+")

    p_commit = sub.add_parser("commit", help="Create a commit")
    p_commit.add_argument("-m", "--message", required=True)
    p_commit.add_argument("--author")

    p_checkout = sub.add_parser("checkout", help="Switch/create a branch")
    p_checkout.add_argument("branch")
    p_checkout.add_argument("-b", "--create-branch", action="store_true")

    p_branch = sub.add_parser("branch", help="List/create/delete branches")
    p_branch.add_argument("name", nargs="?")
    p_branch.add_argument("-d", "--delete", action="store_true")

    p_log = sub.add_parser("log", help="Show commit history")
    p_log.add_argument("-n", "--max-count", type=int, default=10)

    sub.add_parser("status", help="Show working tree status")

    p_diff = sub.add_parser("diff", help="Show staged changes vs HEAD")

    p_remote = sub.add_parser("remote", help="Manage remotes")
    remote_sub = p_remote.add_subparsers(dest="remote_command")
    p_remote_add = remote_sub.add_parser("add", help="Add a remote (path to a local bare-style folder)")
    p_remote_add.add_argument("name")
    p_remote_add.add_argument("path")
    remote_sub.add_parser("list", help="List remotes")

    p_push = sub.add_parser("push", help="Push current branch to a remote")
    p_push.add_argument("remote", nargs="?", default="origin")
    p_push.add_argument("branch", nargs="?")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    repo = Repository()

    try:
        if args.command == "init":
            if repo.init():
                print(f"Initialized empty nex repository in {repo.git_dir}")
            else:
                print("Repository already exists")

        elif args.command == "add":
            if not need_repo(repo):
                return
            for path in args.paths:
                repo.add_path(path)
                print(f"added {path}")

        elif args.command == "commit":
            if not need_repo(repo):
                return
            author = args.author or "nex user <user@nex.local>"
            commit_hash = repo.commit(args.message, author)
            if commit_hash:
                print(f"[{repo.get_current_branch()} {commit_hash[:7]}] {args.message}")
            else:
                print("nothing to commit, working tree clean")

        elif args.command == "checkout":
            if not need_repo(repo):
                return
            ok, msg = repo.checkout(args.branch, args.create_branch)
            print(msg)

        elif args.command == "branch":
            if not need_repo(repo):
                return
            ok, result = repo.branch(args.name, args.delete)
            if isinstance(result, list):
                current = repo.get_current_branch()
                for b in result:
                    marker = "* " if b == current else "  "
                    print(f"{marker}{b}")
            else:
                print(result)

        elif args.command == "log":
            if not need_repo(repo):
                return
            entries = repo.log(args.max_count)
            if not entries:
                print("No commits yet!")
            for e in entries:
                print(f"commit {e['hash']}")
                print(f"Author: {e['author']}")
                print(f"Date:   {time.ctime(e['timestamp'])}")
                print(f"\n    {e['message']}\n")

        elif args.command == "status":
            if not need_repo(repo):
                return
            s = repo.status()
            print(f"On branch {s['branch']}")
            if s["staged"]:
                print("\nChanges to be committed:")
                for item in s["staged"]:
                    print(f"   {item['status']}: {item['path']}")
            if s["unstaged"]:
                print("\nChanges not staged for commit:")
                for p in s["unstaged"]:
                    print(f"   modified: {p}")
            if s["untracked"]:
                print("\nUntracked files:")
                for p in s["untracked"]:
                    print(f"   {p}")
            if s["deleted"]:
                print("\nDeleted files:")
                for p in s["deleted"]:
                    print(f"   deleted: {p}")
            if s["clean"]:
                print("\nnothing to commit, working tree clean")

        elif args.command == "diff":
            if not need_repo(repo):
                return
            print_diff(repo.diff_working_tree())

        elif args.command == "remote":
            if not need_repo(repo):
                return
            if args.remote_command == "add":
                repo.add_remote(args.name, args.path)
                print(f"Added remote {args.name} -> {args.path}")
            elif args.remote_command == "list":
                remotes = repo.load_config().get("remotes", {})
                for name, path in remotes.items():
                    print(f"{name}\t{path}")
            else:
                p_remote.print_help()

        elif args.command == "push":
            if not need_repo(repo):
                return
            ok, msg, _ = repo.push(args.remote, args.branch)
            print(msg)
            if not ok:
                sys.exit(1)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
