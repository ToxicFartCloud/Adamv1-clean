import json
import sys
from pathlib import Path


def _read_lines(p):
    return [ln for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]


def _ok(msg):
    print(f"[OK] {msg}")


def _fail(msg):
    print(f"[FAIL] {msg}")


def main():
    root = Path(".").resolve()
    problems = 0

    # 1) tasks.jsonl: 10–20 lines, each JSON with id/prompt/expected or question/answer
    tasks = root / "evaluations" / "tasks.jsonl"
    if not tasks.exists():
        _fail("evaluations/tasks.jsonl missing")
        problems += 1
    else:
        lines = _read_lines(tasks)
        if not (10 <= len(lines) <= 20):
            _fail(f"tasks.jsonl has {len(lines)} lines (expected 10–20)")
            problems += 1
        else:
            ok_rows = 0
            for i, ln in enumerate(lines, 1):
                try:
                    obj = json.loads(ln)
                    has_a = "question" in obj and "answer" in obj
                    has_b = "prompt" in obj and "expected" in obj
                    if has_a or has_b:
                        ok_rows += 1
                    else:
                        _fail(f"tasks.jsonl line {i}: missing required fields")
                        problems += 1
                except Exception as e:
                    _fail(f"tasks.jsonl line {i}: invalid JSON ({e})")
                    problems += 1
            if ok_rows == len(lines):
                _ok(f"tasks.jsonl format looks good ({ok_rows} items)")

    # 2) feedback_tags.json contains required tags
    tagsf = root / "evaluations" / "feedback_tags.json"
    required = {"too_long", "off_topic", "wrong_tone", "hallucinated", "great"}
    if not tagsf.exists():
        _fail("evaluations/feedback_tags.json missing")
        problems += 1
    else:
        try:
            tags = set(json.loads(tagsf.read_text(encoding="utf-8")))
            missing = required - tags
            if missing:
                _fail(f"feedback_tags.json missing: {sorted(missing)}")
                problems += 1
            else:
                _ok("feedback_tags.json contains all required tags")
        except Exception as e:
            _fail(f"feedback_tags.json invalid JSON ({e})")
            problems += 1

    # 3) decisions log exists
    changelog = root / "DECISIONS" / "CHANGELOG.md"
    if not changelog.exists():
        _fail("DECISIONS/CHANGELOG.md missing")
        problems += 1
    else:
        rows = [ln for ln in _read_lines(changelog) if "|" in ln]
        if len(rows) < 2:  # header + at least one row
            _fail("CHANGELOG.md has no entries")
            problems += 1
        else:
            _ok("CHANGELOG.md present with at least one entry")

    # 4) project_tree.txt exists
    project_tree = root / "project_tree.txt"
    if not project_tree.exists():
        _fail("project_tree.txt missing")
        problems += 1
    else:
        _ok("project_tree.txt present")

    # 5) eval_cycle.md runbook exists
    eval_cycle_runbook = root / "gemini" / "runbooks" / "eval_cycle.md"
    if not eval_cycle_runbook.exists():
        _fail("gemini/runbooks/eval_cycle.md missing")
        problems += 1
    else:
        _ok("gemini/runbooks/eval_cycle.md present")

    print("\nPASS" if problems == 0 else f"\nFAILED with {problems} problem(s)")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
