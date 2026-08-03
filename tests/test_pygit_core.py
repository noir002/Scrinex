"""
Stdlib-only tests for pygit_core.py, run via `python3 -m unittest` in CI.
No external test framework -- keeps the "no pip installs" rule intact even
for the CI job, not just the shipped app.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pygit_core import Blob, Repository, Tree  # noqa: E402


class TempRepoTestCase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="nex-test-")
        self.repo = Repository(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def write(self, rel_path: str, content: str):
        path = Path(self.tmpdir) / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)


class TestObjectModel(unittest.TestCase):
    def test_blob_hash_is_content_addressed(self):
        a = Blob(b"hello world")
        b = Blob(b"hello world")
        c = Blob(b"different content")
        self.assertEqual(a.hash(), b.hash())
        self.assertNotEqual(a.hash(), c.hash())

    def test_tree_roundtrip(self):
        tree = Tree()
        tree.add_entry("100644", "a.txt", "a" * 40)
        tree.add_entry("40000", "subdir", "b" * 40)
        restored = Tree.from_content(tree.content)
        self.assertEqual(tree.entries, restored.entries)


class TestInit(TempRepoTestCase):
    def test_init_creates_nexgit_layout(self):
        self.assertTrue(self.repo.init())
        self.assertTrue(self.repo.exists())
        self.assertTrue((Path(self.tmpdir) / ".nexgit" / "objects").is_dir())
        self.assertTrue((Path(self.tmpdir) / ".nexgit" / "refs" / "heads").is_dir())
        self.assertEqual(self.repo.get_current_branch(), "main")

    def test_double_init_is_noop(self):
        self.repo.init()
        self.assertFalse(self.repo.init())


class TestAddCommit(TempRepoTestCase):
    def setUp(self):
        super().setUp()
        self.repo.init()
        self.write("hello.txt", "hello nex\n")

    def test_add_file_stages_blob_in_index(self):
        blob_hash = self.repo.add_file("hello.txt")
        index = self.repo.load_index()
        self.assertEqual(index["hello.txt"], blob_hash)
        self.assertTrue(self.repo.has_object(blob_hash))

    def test_commit_with_empty_index_returns_none(self):
        self.assertIsNone(self.repo.commit("nothing staged"))

    def test_commit_records_history(self):
        self.repo.add_file("hello.txt")
        commit_hash = self.repo.commit("first commit")
        self.assertIsNotNone(commit_hash)
        log = self.repo.log()
        self.assertEqual(len(log), 1)
        self.assertEqual(log[0]["message"], "first commit")
        self.assertEqual(log[0]["hash"], commit_hash)

    def test_second_identical_commit_is_skipped(self):
        self.repo.add_file("hello.txt")
        first = self.repo.commit("first commit")
        self.assertIsNotNone(first)
        self.repo.add_file("hello.txt")  # same content, same tree
        second = self.repo.commit("no-op commit")
        self.assertIsNone(second)
        self.assertEqual(len(self.repo.log()), 1)


class TestStatusAndDiff(TempRepoTestCase):
    def setUp(self):
        super().setUp()
        self.repo.init()
        self.write("a.txt", "line one\n")
        self.repo.add_file("a.txt")
        self.repo.commit("add a.txt")

    def test_status_clean_after_commit(self):
        status = self.repo.status()
        self.assertTrue(status["clean"])
        self.assertEqual(status["untracked"], [])

    def test_status_detects_staged_modification(self):
        self.write("a.txt", "line one, changed\n")
        self.repo.add_file("a.txt")
        status = self.repo.status()
        staged_paths = [entry["path"] for entry in status["staged"]]
        self.assertIn("a.txt", staged_paths)
        self.assertFalse(status["clean"])

    def test_status_detects_untracked(self):
        self.write("b.txt", "brand new file\n")
        status = self.repo.status()
        self.assertIn("b.txt", status.get("untracked", []))

    def test_diff_working_tree_reports_change(self):
        self.write("a.txt", "line one, changed\n")
        diff = self.repo.diff_working_tree()
        paths = [entry["path"] for entry in diff]
        self.assertIn("a.txt", paths)


class TestBranchAndCheckout(TempRepoTestCase):
    def setUp(self):
        super().setUp()
        self.repo.init()
        self.write("a.txt", "on main\n")
        self.repo.add_file("a.txt")
        self.repo.commit("main commit")

    def test_branch_create_lists_new_branch(self):
        self.repo.branch("feature")
        self.assertIn("feature", self.repo.list_branches())

    def test_checkout_switches_current_branch(self):
        self.repo.branch("feature")
        ok, _ = self.repo.checkout("feature", create_branch=False)
        self.assertTrue(ok)
        self.assertEqual(self.repo.get_current_branch(), "feature")

    def test_checkout_missing_branch_without_create_fails(self):
        ok, _ = self.repo.checkout("does-not-exist", create_branch=False)
        self.assertFalse(ok)


class TestWorkingTree(TempRepoTestCase):
    def test_build_working_tree_reflects_uncommitted_untracked_files(self):
        # Guards the previously-fixed bug in build_working_tree: the file
        # browser must always show real working-directory state, not just
        # committed/staged files.
        self.repo.init()
        self.write("only_on_disk.txt", "never added or committed\n")
        nodes = self.repo.build_working_tree()
        names = [node["name"] for node in nodes]
        self.assertIn("only_on_disk.txt", names)


if __name__ == "__main__":
    unittest.main()
