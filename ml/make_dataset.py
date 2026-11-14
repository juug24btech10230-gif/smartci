"""Create ml/build_history.csv.

Real CI history for a tiny repo is too small to train on, so this generates a
labelled, reproducible (seeded) history using a plausible failure model:
bigger diffs, more files touched, touching core modules, dependency changes and
late-night commits raise failure probability. State this in the report.
"""
import csv
import random

random.seed(42)
rows = []
for _ in range(600):
    files = random.randint(1, 12)
    lines = int(random.expovariate(1 / 60)) + 1
    touched_core = random.random() < 0.35
    dep_change = random.random() < 0.10
    test_changed = random.random() < 0.50
    hour = random.randint(0, 23)
    prev_failed = random.random() < 0.25
    logit = (-3.0 + 0.12 * files + 0.012 * lines + 0.9 * touched_core
             + 1.4 * dep_change - 0.6 * test_changed + 0.5 * (hour >= 22 or hour <= 4)
             + 1.1 * prev_failed)
    p = 1 / (1 + 2.718281828 ** (-logit))
    failed = int(random.random() < p)
    rows.append([files, lines, int(touched_core), int(dep_change),
                 int(test_changed), hour, int(prev_failed), failed])

with open("ml/build_history.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["files_changed", "lines_changed", "touched_core", "dep_change",
                "test_changed", "hour", "prev_failed", "failed"])
    w.writerows(rows)
print(f"wrote {len(rows)} rows, failure rate {sum(r[-1] for r in rows)/len(rows):.2%}")
