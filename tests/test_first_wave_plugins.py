import json
from pathlib import Path

import pytest

from adam_tools.plugins.backup_snapshot import plugin as backup_snapshot
from adam_tools.plugins.git_ops import plugin as git_ops
from adam_tools.plugins.guard_approval import plugin as guard_approval
from adam_tools.plugins.proc_app import plugin as proc_app
from adam_tools.plugins.proc_ps import plugin as proc_ps
from adam_tools.plugins.web_search import plugin as web_search
from adam_tools.plugins.wmgr import plugin as wmgr

AUDIT_LOG = Path("logs/audit.jsonl")
STANDARD_KEYS = {
    "ok",
    "action",
    "dry_run",
    "approval_required",
    "plan",
    "report",
    "artifacts",
    "logs_path",
}


@pytest.fixture(autouse=True)
def clean_audit_log():
    if AUDIT_LOG.exists():
        AUDIT_LOG.unlink()
    yield
    if AUDIT_LOG.exists():
        AUDIT_LOG.unlink()


def _assert_schema(result):
    assert STANDARD_KEYS.issubset(result.keys())
    assert isinstance(result["plan"], list)
    assert isinstance(result["report"], dict)
    assert "summary" in result["report"]
    assert result["logs_path"].endswith("logs/audit.jsonl")


def _read_audit_lines():
    if not AUDIT_LOG.exists():
        return []
    return [
        json.loads(line) for line in AUDIT_LOG.read_text().strip().splitlines() if line
    ]


def test_proc_app_launch_dry_run():
    payload = {
        "action": "launch",
        "args": {"program": "gedit"},
        "dry_run": True,
        "reason": "demo",
    }
    result = proc_app.run(payload)
    _assert_schema(result)
    assert result["ok"] is True
    assert result["dry_run"] is True
    assert result["plan"]
    lines = _read_audit_lines()
    assert lines and lines[-1]["plugin"] == "proc.app"


def test_proc_app_kill_requires_approval():
    payload = {
        "action": "kill",
        "args": {"program": "gedit"},
        "dry_run": False,
        "reason": "cleanup",
    }
    result = proc_app.run(payload)
    _assert_schema(result)
    assert result["approval_required"] is True
    assert result["ok"] is False


def test_proc_ps_list_structure():
    payload = {"action": "list", "args": {}, "dry_run": True, "reason": "overview"}
    result = proc_ps.run(payload)
    _assert_schema(result)
    assert result["ok"] is True
    assert result["report"]["details"]["processes"]


def test_web_search_demo_result():
    payload = {
        "action": "query",
        "args": {"q": "hello"},
        "dry_run": True,
        "reason": "demo",
    }
    result = web_search.run(payload)
    _assert_schema(result)
    assert result["ok"] is True
    assert result["report"]["details"]["results"]


def test_git_ops_commit_requires_approval():
    payload = {
        "action": "commit",
        "args": {"message": "test"},
        "dry_run": False,
        "reason": "ensure safety",
    }
    result = git_ops.run(payload)
    _assert_schema(result)
    assert result["approval_required"] is True
    assert result["ok"] is False


def test_wmgr_list_demo_windows():
    payload = {"action": "list", "args": {}, "dry_run": True, "reason": "inventory"}
    result = wmgr.run(payload)
    _assert_schema(result)
    assert result["ok"] is True
    assert result["report"]["details"]["windows"]


def test_guard_approval_dry_run_requires_followup():
    payload = {
        "action": "request",
        "args": {"plan": {"steps": ["demo"]}},
        "dry_run": True,
        "reason": "trial",
    }
    result = guard_approval.run(payload)
    _assert_schema(result)
    assert result["approval_required"] is True
    assert result["ok"] is True


def test_backup_snapshot_dry_run_plan_and_log():
    payload = {
        "action": "pre",
        "args": {"tag": "demo"},
        "dry_run": True,
        "reason": "pre-check",
    }
    result = backup_snapshot.run(payload)
    _assert_schema(result)
    assert result["ok"] is True
    lines = _read_audit_lines()
    assert lines and lines[-1]["plugin"] == "backup.snapshot"
