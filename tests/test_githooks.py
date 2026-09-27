"""The tracked git hooks, and the clone settings that switch them on.

Every repository here is a throwaway under ``tmp_path``; none of this touches
the clone the tests run from, except to read the hook and how it is tracked.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

from setup_repo import GIT_CONFIG, configure_git  # noqa: E402

HOOK = REPO / ".githooks" / "post-merge"

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")

# The machine's own git config must not decide the outcome.
ENV = {
    **os.environ,
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "test",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "test",
    "GIT_COMMITTER_EMAIL": "test@example.com",
}


def git(cwd: Path, *args: str) -> str:
    done = subprocess.run(["git", *args], cwd=cwd, env=ENV, capture_output=True, text=True)
    assert done.returncode == 0, f"git {' '.join(args)}\n{done.stdout}{done.stderr}"
    return done.stdout


def commit(cwd: Path, name: str, text: str, message: str) -> None:
    (cwd / name).write_text(text, newline="\n")
    git(cwd, "add", name)
    git(cwd, "commit", "-m", message)


def branches(cwd: Path) -> set[str]:
    return set(git(cwd, "branch", "--format=%(refname:short)").split())


def test_configure_git_sets_the_clone_settings(tmp_path):
    clone = tmp_path / "clone"
    clone.mkdir()
    git(clone, "init", "-b", "master")
    assert configure_git(clone)
    for key, value in GIT_CONFIG.items():
        assert git(clone, "config", "--local", "--get", key).strip() == value
    # The hook the setting points at is the one this repo tracks.
    assert (REPO / GIT_CONFIG["core.hooksPath"] / "post-merge") == HOOK and HOOK.is_file()


def test_configure_git_skips_a_directory_that_is_not_a_clone(tmp_path):
    assert not configure_git(tmp_path)
    assert not (tmp_path / ".git").exists()


def test_post_merge_deletes_a_merged_branch_and_keeps_unmerged_work(tmp_path, monkeypatch):
    for key, value in ENV.items():
        monkeypatch.setenv(key, value)  # configure_git runs git itself
    origin, work, hub = tmp_path / "origin.git", tmp_path / "work", tmp_path / "hub"
    git(tmp_path, "init", "--bare", "-b", "master", str(origin))

    git(tmp_path, "clone", str(origin), str(work))
    (work / ".githooks").mkdir()
    shutil.copy(HOOK, work / ".githooks" / "post-merge")
    (work / ".githooks" / "post-merge").chmod(0o755)
    git(work, "add", ".githooks")
    commit(work, "base.txt", "base\n", "base")
    git(work, "push", "-u", "origin", "master")
    assert configure_git(work)

    git(work, "checkout", "-b", "pr-merged")
    commit(work, "a.txt", "one\n", "add a")
    commit(work, "a.txt", "one\ntwo\n", "more a")
    git(work, "push", "-u", "origin", "pr-merged")
    git(work, "checkout", "-b", "pr-unmerged", "master")
    commit(work, "b.txt", "b\n", "add b")
    git(work, "push", "-u", "origin", "pr-unmerged")
    git(work, "checkout", "master")

    # A second clone plays GitHub: master moves on, one branch is rebase-merged
    # (so its commits land under new hashes), and both remote branches go.
    git(tmp_path, "clone", str(origin), str(hub))
    commit(hub, "other.txt", "other\n", "other work")
    git(hub, "checkout", "-b", "landing", "origin/pr-merged")
    git(hub, "rebase", "master")
    git(hub, "checkout", "master")
    git(hub, "merge", "--ff-only", "landing")
    git(hub, "push", "origin", "master")
    git(hub, "push", "origin", "--delete", "pr-merged", "pr-unmerged")

    assert branches(work) == {"master", "pr-merged", "pr-unmerged"}
    git(work, "pull")
    assert branches(work) == {"master", "pr-unmerged"}


def test_the_hook_is_lf_and_tracked_as_executable():
    # sh cannot run a CRLF script, and Linux and macOS skip a hook without the
    # executable bit -- which Windows neither shows nor sets, so read the index.
    assert b"\r" not in HOOK.read_bytes()
    if not (REPO / ".git").exists():
        pytest.skip("not a git clone")
    entry = git(REPO, "ls-files", "-s", "--", ".githooks/post-merge")
    assert entry.startswith("100755 "), entry or "the hook is not tracked"
