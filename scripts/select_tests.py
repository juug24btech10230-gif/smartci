"""Dynamic test-subset routing.

Looks at the files changed between two git refs, walks the reverse dependency
graph (who imports the changed module), and prints only the tests that could be
affected. Falls back to the full suite when a change cannot be mapped safely
(requirements, config, workflows, test helpers).

Usage:
    python scripts/select_tests.py --base origin/main --head HEAD
    python scripts/select_tests.py --files src/pricing.py
"""
import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from depgraph import build_graph, reverse_graph, transitive  # noqa: E402

FULL_SUITE_TRIGGERS = ("requirements.txt", "pytest.ini", "tests/conftest.py", ".github/")


def changed_files(base, head):
    out = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...{head}"],
        capture_output=True, text=True, check=True,
    ).stdout
    return [l.strip() for l in out.splitlines() if l.strip()]


def select(files, tests_dir="tests"):
    all_tests = sorted(str(p) for p in Path(tests_dir).glob("test_*.py"))
    graph = build_graph()
    rev = reverse_graph(graph)

    if any(f.startswith(FULL_SUITE_TRIGGERS) for f in files):
        return all_tests, "config change: running full suite"

    affected_modules, selected = set(), set()
    for f in files:
        p = Path(f)
        if f.startswith("tests/") and p.name.startswith("test_"):
            if p.exists():
                selected.add(f)
        elif f.startswith("src/") and p.suffix == ".py" and p.name != "__init__.py":
            m = p.stem
            affected_modules.add(m)
            affected_modules |= transitive(m, rev)

    for m in affected_modules:
        t = Path(tests_dir) / f"test_{m}.py"
        if t.exists():
            selected.add(str(t))
    return sorted(selected), f"affected modules: {sorted(affected_modules) or 'none'}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--files", nargs="*")
    args = ap.parse_args()

    files = args.files if args.files is not None else changed_files(args.base, args.head)
    tests, reason = select(files)
    print(f"# changed: {files}", file=sys.stderr)
    print(f"# {reason}", file=sys.stderr)
    print(" ".join(tests))


if __name__ == "__main__":
    main()
