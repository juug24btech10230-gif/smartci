"""Predict failure risk for the current change using git diff stats.

Usage: python ml/predict.py [--base origin/main] [--threshold 0.6]
Exit code 0 always; prints risk so the workflow can warn, not block.
"""
import argparse
import pickle
import subprocess
from datetime import datetime

import pandas as pd

CORE = ("src/pricing.py",)


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True).stdout


def diff_features(base):
    names = git("diff", "--name-only", f"{base}...HEAD").split()
    stat = git("diff", "--numstat", f"{base}...HEAD").splitlines()
    lines = 0
    for s in stat:
        a, d, *_ = s.split("\t")
        lines += (int(a) if a.isdigit() else 0) + (int(d) if d.isdigit() else 0)
    return {
        "files_changed": max(len(names), 1),
        "lines_changed": max(lines, 1),
        "touched_core": int(any(n in CORE for n in names)),
        "dep_change": int("requirements.txt" in names),
        "test_changed": int(any(n.startswith("tests/") for n in names)),
        "hour": datetime.utcnow().hour,
        "prev_failed": 0,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="HEAD~1")
    ap.add_argument("--threshold", type=float, default=0.6)
    args = ap.parse_args()

    with open("ml/model.pkl", "rb") as f:
        bundle = pickle.load(f)
    feats = diff_features(args.base)
    X = pd.DataFrame([feats])[bundle["features"]]
    risk = bundle["model"].predict_proba(X)[0, 1]
    level = "HIGH" if risk >= args.threshold else "LOW"
    print(f"features: {feats}")
    print(f"predicted failure risk: {risk:.0%} ({level})")


if __name__ == "__main__":
    main()
