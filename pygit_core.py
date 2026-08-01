"""
pygit_core.py

Reusable core of the PyGit object model + repository operations.
No argparse, no CLI-only code — this module is imported by BOTH:
  - nex.py       (the CLI: nex init / add / commit / push / log / status ...)
  - server.py    (the API server that Scrinex, the web frontend, talks to)

Both processes operate on the same on-disk store (the .git-style folder),
so there is no direct IPC between CLI and server — the filesystem IS the
shared state.
"""

from __future__ import annotations
import difflib
import hashlib
import json
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class GitObject:
    def __init__(self, obj_type: str, content: bytes):
        self.type = obj_type
        self.content = content

    def hash(self) -> str:
        header = f"{self.type} {len(self.content)}\0".encode()
        return hashlib.sha1(header + self.content).hexdigest()

    def serialize(self) -> bytes:
        import zlib
        header = f"{self.type} {len(self.content)}\0".encode()
        return zlib.compress(header + self.content)

    @classmethod
    def deserialize(cls, data: bytes) -> "GitObject":
        import zlib
        decompressed = zlib.decompress(data)
        null_idx = decompressed.find(b"\0")
        header = decompressed[:null_idx].decode()
        content = decompressed[null_idx + 1:]
        obj_type, _ = header.split(" ")
        return cls(obj_type, content)


class Blob(GitObject):
    def __init__(self, content: bytes):
        super().__init__("blob", content)


class Tree(GitObject):
    def __init__(self, entries: List[Tuple[str, str, str]] = None):
        self.entries = entries or []
        content = self._serialize_entries()
        super().__init__("tree", content)

    def _serialize_entries(self) -> bytes:
        content = b""
        for mode, name, obj_hash in sorted(self.entries):
            content += f"{mode} {name}\0".encode()
            content += bytes.fromhex(obj_hash)
        return content

    def add_entry(self, mode: str, name: str, obj_hash: str):
        self.entries.append((mode, name, obj_hash))
        self.content = self._serialize_entries()

    @classmethod
    def from_content(cls, content: bytes) -> "Tree":
        tree = cls()
        i = 0
        while i < len(content):
            null_idx = content.find(b"\0", i)
            if null_idx == -1:
                break
            mode_name = content[i:null_idx].decode()
            mode, name = mode_name.split(" ", 1)
            obj_hash = content[null_idx + 1: null_idx + 21].hex()
            tree.entries.append((mode, name, obj_hash))
            i = null_idx + 21
        return tree


class Commit(GitObject):
    def __init__(
        self,
        tree_hash: str,
        parent_hashes: List[str],
        author: str,
        committer: str,
        message: str,
        timestamp: int = None,
    ):
        self.tree_hash = tree_hash
        self.parent_hashes = parent_hashes
        self.author = author
        self.committer = committer
        self.message = message
        self.timestamp = timestamp or int(time.time())
        content = self._serialize_commit()
        super().__init__("commit", content)

    def _serialize_commit(self):
        lines = [f"tree {self.tree_hash}"]
        for parent in self.parent_hashes:
            lines.append(f"parent {parent}")
        lines.append(f"author {self.author} {self.timestamp} +0000")
        lines.append(f"committer {self.committer} {self.timestamp} +0000")
        lines.append("")
        lines.append(self.message)
        return "\n".join(lines).encode()

    @classmethod
    def from_content(cls, content: bytes) -> "Commit":
        lines = content.decode().split("\n")
        tree_hash = None
        parent_hashes = []
        author = None
        committer = None
        timestamp = int(time.time())
        message_start = 0

        for i, line in enumerate(lines):
            if line.startswith("tree "):
                tree_hash = line[5:]
            elif line.startswith("parent "):
                parent_hashes.append(line[7:])
            elif line.startswith("author "):
                author_parts = line[7:].rsplit(" ", 2)
                author = author_parts[0]
                timestamp = int(author_parts[1])
            elif line.startswith("committer "):
                committer_parts = line[10:].rsplit(" ", 2)
                committer = committer_parts[0]
            elif line == "":
                message_start = i + 1
                break

        message = "\n".join(lines[message_start:])
        return cls(tree_hash, parent_hashes, author, committer, message, timestamp)


class Repository:
    def __init__(self, path="."):
        self.path = Path(path).resolve()
        self.git_dir = self.path / ".nexgit"
        self.objects_dir = self.git_dir / "objects"
        self.ref_dir = self.git_dir / "refs"
        self.heads_dir = self.ref_dir / "heads"
        self.head_file = self.git_dir / "HEAD"
        self.index_file = self.git_dir / "index"
        self.config_file = self.git_dir / "config.json"

    # ---------- basic plumbing ----------

    def init(self) -> bool:
        if self.git_dir.exists():
            return False
        self.path.mkdir(parents=True, exist_ok=True)
        self.git_dir.mkdir()
        self.objects_dir.mkdir()
        self.ref_dir.mkdir()
        self.heads_dir.mkdir()
        self.head_file.write_text("ref: refs/heads/main\n")
        self.save_index({})
        self.config_file.write_text(json.dumps({"remotes": {}}, indent=2))
        return True

    def exists(self) -> bool:
        return self.git_dir.exists()

    def store_object(self, obj: GitObject) -> str:
        obj_hash = obj.hash()
        obj_dir = self.objects_dir / obj_hash[:2]
        obj_file = obj_dir / obj_hash[2:]
        if not obj_file.exists():
            obj_dir.mkdir(exist_ok=True)
            obj_file.write_bytes(obj.serialize())
        return obj_hash

    def has_object(self, obj_hash: str) -> bool:
        return (self.objects_dir / obj_hash[:2] / obj_hash[2:]).exists()

    def load_object(self, obj_hash: str) -> GitObject:
        obj_file = self.objects_dir / obj_hash[:2] / obj_hash[2:]
        if not obj_file.exists():
            raise FileNotFoundError(f"Object {obj_hash} not found")
        return GitObject.deserialize(obj_file.read_bytes())

    def load_index(self) -> Dict[str, str]:
        if not self.index_file.exists():
            return {}
        try:
            return json.loads(self.index_file.read_text())
        except Exception:
            return {}

    def save_index(self, index: Dict[str, str]):
        self.index_file.write_text(json.dumps(index, indent=2))

    def load_config(self) -> dict:
        if not self.config_file.exists():
            return {"remotes": {}}
        try:
            return json.loads(self.config_file.read_text())
        except Exception:
            return {"remotes": {}}

    def save_config(self, config: dict):
        self.config_file.write_text(json.dumps(config, indent=2))

    # ---------- staging ----------

    def add_file(self, path: str) -> str:
        full_path = self.path / path
        if not full_path.exists():
            raise FileNotFoundError(f"Path {path} not found")
        content = full_path.read_bytes()
        blob = Blob(content)
        blob_hash = self.store_object(blob)
        index = self.load_index()
        index[path] = blob_hash
        self.save_index(index)
        return blob_hash

    def add_directory(self, path: str) -> int:
        full_path = self.path / path
        if not full_path.exists():
            raise FileNotFoundError(f"Directory {path} not found")
        if not full_path.is_dir():
            raise ValueError(f"{path} is not a directory")
        index = self.load_index()
        added = 0
        for file_path in full_path.rglob("*"):
            if file_path.is_file():
                if ".nexgit" in file_path.parts or ".git" in file_path.parts:
                    continue
                content = file_path.read_bytes()
                blob = Blob(content)
                blob_hash = self.store_object(blob)
                rel_path = str(file_path.relative_to(self.path))
                index[rel_path] = blob_hash
                added += 1
        self.save_index(index)
        return added

    def add_path(self, path: str) -> None:
        full_path = self.path / path
        if not full_path.exists():
            raise FileNotFoundError(f"Path {path} not found")
        if full_path.is_file():
            self.add_file(path)
        elif full_path.is_dir():
            self.add_directory(path)
        else:
            raise ValueError(f"{path} is neither a file nor a directory")

    # ---------- trees / commits ----------

    def create_tree_from_index(self) -> str:
        index = self.load_index()
        if not index:
            tree = Tree()
            return self.store_object(tree)

        dirs, files = {}, {}
        for file_path, blob_hash in index.items():
            parts = file_path.split("/")
            if len(parts) == 1:
                files[parts[0]] = blob_hash
            else:
                dir_name = parts[0]
                current = dirs.setdefault(dir_name, {})
                for part in parts[1:-1]:
                    current = current.setdefault(part, {})
                current[parts[-1]] = blob_hash

        def create_tree_recursive(entries_dict: Dict) -> str:
            tree = Tree()
            for name, val in entries_dict.items():
                if isinstance(val, str):
                    tree.add_entry("100644", name, val)
                else:
                    subtree_hash = create_tree_recursive(val)
                    tree.add_entry("40000", name, subtree_hash)
            return self.store_object(tree)

        root_entries = {**files, **dirs}
        return create_tree_recursive(root_entries)

    def get_current_branch(self) -> str:
        if not self.head_file.exists():
            return "main"
        head_content = self.head_file.read_text().strip()
        if head_content.startswith("ref: refs/heads/"):
            return head_content[16:]
        return head_content  # detached HEAD (a raw commit hash)

    def get_branch_commit(self, branch: str) -> Optional[str]:
        branch_file = self.heads_dir / branch
        if branch_file.exists():
            return branch_file.read_text().strip()
        return None

    def set_branch_commit(self, branch: str, commit_hash: str):
        self.heads_dir.mkdir(exist_ok=True, parents=True)
        (self.heads_dir / branch).write_text(commit_hash + "\n")

    def commit(self, message: str, author: str = "nex user <user@nex.local>") -> Optional[str]:
        tree_hash = self.create_tree_from_index()
        current_branch = self.get_current_branch()
        parent_commit = self.get_branch_commit(current_branch)
        parent_hashes = [parent_commit] if parent_commit else []

        index = self.load_index()
        if not index:
            return None

        if parent_commit:
            parent_obj = self.load_object(parent_commit)
            parent_data = Commit.from_content(parent_obj.content)
            if tree_hash == parent_data.tree_hash:
                return None

        commit = Commit(
            tree_hash=tree_hash,
            parent_hashes=parent_hashes,
            author=author,
            committer=author,
            message=message,
        )
        commit_hash = self.store_object(commit)
        self.set_branch_commit(current_branch, commit_hash)
        self.save_index({})
        return commit_hash

    def build_index_from_tree(self, tree_hash: str, prefix: str = "") -> Dict[str, str]:
        index = {}
        try:
            tree_obj = self.load_object(tree_hash)
            tree = Tree.from_content(tree_obj.content)
            for mode, name, obj_hash in tree.entries:
                full_name = f"{prefix}{name}"
                if mode.startswith("100"):
                    index[full_name] = obj_hash
                elif mode.startswith("400"):
                    index.update(self.build_index_from_tree(obj_hash, f"{full_name}/"))
        except Exception:
            pass
        return index

    def build_nested_tree(self, tree_hash: Optional[str]) -> List[dict]:
        """Nested [{name, type, hash, children?}] structure for a file-browser UI."""
        if not tree_hash:
            return []
        tree_obj = self.load_object(tree_hash)
        tree = Tree.from_content(tree_obj.content)
        nodes = []
        for mode, name, obj_hash in sorted(tree.entries, key=lambda e: (e[0].startswith("100"), e[1])):
            if mode.startswith("400"):
                nodes.append({
                    "name": name, "type": "dir", "hash": obj_hash,
                    "children": self.build_nested_tree(obj_hash),
                })
            else:
                nodes.append({"name": name, "type": "file", "hash": obj_hash, "mode": mode})
        return nodes

    def get_files_from_tree_recursive(self, tree_hash: str, prefix: str = "") -> set:
        files = set()
        try:
            tree_obj = self.load_object(tree_hash)
            tree = Tree.from_content(tree_obj.content)
            for mode, name, obj_hash in tree.entries:
                full_name = f"{prefix}{name}"
                if mode.startswith("100"):
                    files.add(full_name)
                elif mode.startswith("400"):
                    files.update(self.get_files_from_tree_recursive(obj_hash, f"{full_name}/"))
        except Exception:
            pass
        return files

    # ---------- branch / checkout ----------

    def checkout(self, branch: str, create_branch: bool) -> Tuple[bool, str]:
        previous_branch = self.get_current_branch()
        files_to_clear = set()
        previous_commit_hash = self.get_branch_commit(previous_branch)
        try:
            if previous_commit_hash:
                prev_commit = Commit.from_content(self.load_object(previous_commit_hash).content)
                if prev_commit.tree_hash:
                    files_to_clear = self.get_files_from_tree_recursive(prev_commit.tree_hash)
        except Exception:
            pass

        branch_file = self.heads_dir / branch
        if not branch_file.exists():
            if create_branch:
                if previous_commit_hash:
                    self.set_branch_commit(branch, previous_commit_hash)
                else:
                    return False, "No commits yet, cannot create a branch"
            else:
                return False, f"Branch '{branch}' not found"

        self.head_file.write_text(f"ref: refs/heads/{branch}\n")
        self.restore_working_directory(branch, files_to_clear)
        return True, f"Switched to branch {branch}"

    def restore_tree(self, tree_hash: str, path: Path):
        tree = Tree.from_content(self.load_object(tree_hash).content)
        for mode, name, obj_hash in tree.entries:
            file_path = path / name
            if mode.startswith("100"):
                blob = Blob(self.load_object(obj_hash).content)
                file_path.write_bytes(blob.content)
            elif mode.startswith("400"):
                file_path.mkdir(exist_ok=True)
                self.restore_tree(obj_hash, file_path)

    def restore_working_directory(self, branch: str, files_to_clear: set):
        target_commit_hash = self.get_branch_commit(branch)
        if not target_commit_hash:
            return
        for rel_path in sorted(files_to_clear):
            file_path = self.path / rel_path
            try:
                if file_path.is_file():
                    file_path.unlink()
            except Exception:
                pass
        target_commit = Commit.from_content(self.load_object(target_commit_hash).content)
        if target_commit.tree_hash:
            self.restore_tree(target_commit.tree_hash, self.path)
        self.save_index({})

    def branch(self, branch_name: Optional[str], delete: bool = False):
        if delete and branch_name:
            branch_file = self.heads_dir / branch_name
            if branch_file.exists():
                branch_file.unlink()
                return True, f"Deleted branch {branch_name}"
            return False, f"Branch {branch_name} not found"

        current_branch = self.get_current_branch()
        if branch_name:
            current_commit = self.get_branch_commit(current_branch)
            if current_commit:
                self.set_branch_commit(branch_name, current_commit)
                return True, f"Created branch {branch_name}"
            return False, "No commits yet, cannot create a new branch"

        branches = []
        if self.heads_dir.exists():
            for f in self.heads_dir.iterdir():
                if f.is_file() and not f.name.startswith("."):
                    branches.append(f.name)
        return True, sorted(branches)

    def list_branches(self) -> List[str]:
        if not self.heads_dir.exists():
            return []
        return sorted(f.name for f in self.heads_dir.iterdir() if f.is_file())

    # ---------- log / status ----------

    def log(self, max_count: int = 10) -> List[dict]:
        current_branch = self.get_current_branch()
        commit_hash = self.get_branch_commit(current_branch)
        entries = []
        count = 0
        while commit_hash and count < max_count:
            commit = Commit.from_content(self.load_object(commit_hash).content)
            entries.append({
                "hash": commit_hash,
                "author": commit.author,
                "timestamp": commit.timestamp,
                "message": commit.message,
                "parents": commit.parent_hashes,
            })
            commit_hash = commit.parent_hashes[0] if commit.parent_hashes else None
            count += 1
        return entries

    def get_all_files(self) -> List[Path]:
        files = []
        for item in self.path.rglob("*"):
            if ".nexgit" in item.parts or ".git" in item.parts:
                continue
            if item.is_file():
                files.append(item)
        return files

    def status(self) -> dict:
        current_branch = self.get_current_branch()
        index = self.load_index()
        current_commit_hash = self.get_branch_commit(current_branch)

        last_index_files = {}
        if current_commit_hash:
            try:
                commit = Commit.from_content(self.load_object(current_commit_hash).content)
                if commit.tree_hash:
                    last_index_files = self.build_index_from_tree(commit.tree_hash)
            except Exception:
                pass

        working_files = {}
        for item in self.get_all_files():
            rel_path = str(item.relative_to(self.path))
            try:
                working_files[rel_path] = Blob(item.read_bytes()).hash()
            except Exception:
                continue

        staged, unstaged, untracked, deleted = [], [], [], []

        for file_path in set(index.keys()) | set(last_index_files.keys()):
            idx_hash = index.get(file_path)
            last_hash = last_index_files.get(file_path)
            if idx_hash and not last_hash:
                staged.append({"status": "new file", "path": file_path})
            elif idx_hash and last_hash and idx_hash != last_hash:
                staged.append({"status": "modified", "path": file_path})

        for file_path in working_files:
            if file_path in index and working_files[file_path] != index[file_path]:
                unstaged.append(file_path)

        for file_path in working_files:
            if file_path not in index and file_path not in last_index_files:
                untracked.append(file_path)

        for file_path in index:
            if file_path not in working_files:
                deleted.append(file_path)

        return {
            "branch": current_branch,
            "staged": sorted(staged, key=lambda x: x["path"]),
            "unstaged": sorted(unstaged),
            "untracked": sorted(untracked),
            "deleted": sorted(deleted),
            "clean": not (staged or unstaged or untracked or deleted),
        }

    # ---------- diff ----------

    def _decode(self, content: bytes) -> List[str]:
        try:
            return content.decode("utf-8").splitlines(keepends=True)
        except UnicodeDecodeError:
            return ["<binary file>"]

    def diff_trees(self, tree_a: Optional[str], tree_b: Optional[str]) -> List[dict]:
        """Compare two trees (either may be None) path by path, with unified line diffs."""
        files_a = self.build_index_from_tree(tree_a) if tree_a else {}
        files_b = self.build_index_from_tree(tree_b) if tree_b else {}

        results = []
        for path in sorted(set(files_a) | set(files_b)):
            ha, hb = files_a.get(path), files_b.get(path)
            if ha == hb:
                continue
            if ha is None:
                status = "added"
                old_lines = []
                new_lines = self._decode(self.load_object(hb).content)
            elif hb is None:
                status = "deleted"
                old_lines = self._decode(self.load_object(ha).content)
                new_lines = []
            else:
                status = "modified"
                old_lines = self._decode(self.load_object(ha).content)
                new_lines = self._decode(self.load_object(hb).content)

            diff_lines = list(difflib.unified_diff(
                old_lines, new_lines, fromfile=f"a/{path}", tofile=f"b/{path}", lineterm=""
            ))
            results.append({"path": path, "status": status, "diff": diff_lines})
        return results

    def diff_commit(self, commit_hash: str) -> List[dict]:
        commit = Commit.from_content(self.load_object(commit_hash).content)
        parent_tree = None
        if commit.parent_hashes:
            parent = Commit.from_content(self.load_object(commit.parent_hashes[0]).content)
            parent_tree = parent.tree_hash
        return self.diff_trees(parent_tree, commit.tree_hash)

    def diff_working_tree(self) -> List[dict]:
        """Diff HEAD's committed tree against the current index (staged changes)."""
        current_branch = self.get_current_branch()
        commit_hash = self.get_branch_commit(current_branch)
        head_tree = None
        if commit_hash:
            head_tree = Commit.from_content(self.load_object(commit_hash).content).tree_hash

        index = self.load_index()
        staged_tree = None
        if index:
            # Build a throwaway tree from the index without mutating branch state
            staged_tree = self.create_tree_from_index()
        return self.diff_trees(head_tree, staged_tree)

    # ---------- remote / push ----------

    def add_remote(self, name: str, remote_path: str):
        config = self.load_config()
        config.setdefault("remotes", {})[name] = str(Path(remote_path).resolve())
        self.save_config(config)

    def get_remote(self, name: str) -> Optional[str]:
        return self.load_config().get("remotes", {}).get(name)

    def _collect_reachable_objects(self, commit_hash: str, seen: set) -> None:
        if not commit_hash or commit_hash in seen:
            return
        seen.add(commit_hash)
        commit = Commit.from_content(self.load_object(commit_hash).content)

        def walk_tree(tree_hash):
            if tree_hash in seen:
                return
            seen.add(tree_hash)
            tree = Tree.from_content(self.load_object(tree_hash).content)
            for mode, name, obj_hash in tree.entries:
                if mode.startswith("400"):
                    walk_tree(obj_hash)
                else:
                    seen.add(obj_hash)

        if commit.tree_hash:
            walk_tree(commit.tree_hash)
        for parent in commit.parent_hashes:
            self._collect_reachable_objects(parent, seen)

    def push(self, remote_name: str, branch: Optional[str] = None) -> Tuple[bool, str, int]:
        remote_path = self.get_remote(remote_name)
        if not remote_path:
            return False, f"No remote named '{remote_name}' — add one first", 0

        branch = branch or self.get_current_branch()
        commit_hash = self.get_branch_commit(branch)
        if not commit_hash:
            return False, f"Branch '{branch}' has no commits to push", 0

        remote = Repository(remote_path)
        if not remote.exists():
            remote.init()

        seen = set()
        self._collect_reachable_objects(commit_hash, seen)

        copied = 0
        for obj_hash in seen:
            if not remote.has_object(obj_hash):
                src = self.objects_dir / obj_hash[:2] / obj_hash[2:]
                dst_dir = remote.objects_dir / obj_hash[:2]
                dst_dir.mkdir(exist_ok=True, parents=True)
                shutil.copy2(src, dst_dir / obj_hash[2:])
                copied += 1

        remote.set_branch_commit(branch, commit_hash)
        return True, f"Pushed {branch} -> {remote_name} ({copied} new objects)", copied
