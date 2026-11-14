"""Smart build-cache invalidation.

Computes one cache key per module from the module's own content hash plus the
content hashes of everything it transitively imports. A module's key changes
only when it or one of its dependencies changes, so unrelated modules keep
their cached results. A whole-build key is also emitted for GitHub Actions.

Usage:
    python scripts/smart_cache.py            # print keys, compare to manifest
    python scripts/smart_cache.py --write    # update the manifest
    python scripts/smart_cache.py --github-output   # emit keys for Actions
"""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from depgraph import build_graph, transitive  # noqa: E402

MANIFEST = Path(".smartci-cache/manifest.json")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_hash(path: Path) -> str:
    return sha(path.read_bytes())


def module_keys(src_dir="src"):
    graph = build_graph(src_dir)
    own = {m: file_hash(Path(src_dir) / f"{m}.py") for m in graph}
    keys = {}
    for m in graph:
        parts = [own[m]] + [own[d] for d in sorted(transitive(m, graph))]
        keys[m] = sha("".join(parts).encode())[:16]
    return keys


def requirements_key():
    p = Path("requirements.txt")
    return sha(p.read_bytes())[:16] if p.exists() else "none"


def build_key(keys):
    joined = requirements_key() + "".join(f"{m}:{k}" for m, k in sorted(keys.items()))
    return sha(joined.encode())[:16]


def diff(old, new):
    changed = sorted(m for m in new if old.get(m) != new[m])
    removed = sorted(m for m in old if m not in new)
    return changed, removed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--github-output", action="store_true")
    args = ap.parse_args()

    keys = module_keys()
    old = json.loads(MANIFEST.read_text())["modules"] if MANIFEST.exists() else {}
    changed, removed = diff(old, keys)

    print("module keys:")
    for m, k in sorted(keys.items()):
        flag = "CHANGED" if m in changed else "cached"
        print(f"  {m:<12} {k}  {flag}")
    if removed:
        print("removed:", ", ".join(removed))
    bk = build_key(keys)
    print("build key:", bk)

    if args.write:
        MANIFEST.parent.mkdir(exist_ok=True)
        MANIFEST.write_text(json.dumps({"modules": keys, "build": bk}, indent=2))
    if args.github_output and os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"build_key={bk}\n")
            f.write(f"changed={','.join(changed)}\n")


if __name__ == "__main__":
    main()
