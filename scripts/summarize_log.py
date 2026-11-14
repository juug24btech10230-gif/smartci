"""LLM-based build/error-log summarization.

Reads build.log, trims it to the lines that matter (errors, failed tests,
tracebacks) so the prompt stays small, then asks an LLM for a short summary and
a suggested fix. If no API key is configured, or the call fails, it falls back
to a deterministic rule-based summary so the CI step never breaks.

Usage:
    python scripts/summarize_log.py build.log
Env:
    ANTHROPIC_API_KEY   optional; enables the LLM call
"""
import os
import re
import sys

import requests

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = os.environ.get("SUMMARY_MODEL", "claude-sonnet-4-6")
MAX_CHARS = 6000
SIGNALS = re.compile(r"(FAILED|ERROR|Error|assert|Traceback|Exception|E  )")


def trim_log(text, max_chars=MAX_CHARS):
    lines = text.splitlines()
    keep = set()
    for i, line in enumerate(lines):
        if SIGNALS.search(line):
            keep.update(range(max(0, i - 2), min(len(lines), i + 3)))
    picked = [lines[i] for i in sorted(keep)] or lines[-40:]
    out = "\n".join(picked)
    return out[-max_chars:]


def rule_based_summary(text):
    failed = re.findall(r"FAILED (\S+)", text)
    passed = re.search(r"(\d+) passed", text)
    failed_n = re.search(r"(\d+) failed", text)
    asserts = re.findall(r"^E\s+(assert .+)$", text, re.M)
    parts = []
    if failed:
        parts.append(f"{len(failed)} test(s) failed: {', '.join(sorted(set(failed)))}.")
        if asserts:
            parts.append(f"First failing assertion: {asserts[0]}")
        parts.append("Suggested fix: compare the expected value in that assertion "
                     "with the function's real output and correct whichever is wrong.")
    elif failed_n:
        parts.append(f"{failed_n.group(1)} test(s) failed; see log for details.")
    elif passed:
        parts.append(f"Build healthy: {passed.group(1)} tests passed.")
    else:
        parts.append("No test summary found in the log.")
    return " ".join(parts)


def llm_summary(trimmed, key):
    prompt = (
        "You are a CI assistant. Summarize this build log in at most 4 sentences: "
        "what failed, the most likely root cause, and one concrete fix.\n\n"
        f"```\n{trimmed}\n```"
    )
    r = requests.post(
        API_URL,
        headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"},
        json={"model": MODEL, "max_tokens": 300,
              "messages": [{"role": "user", "content": prompt}]},
        timeout=30,
    )
    r.raise_for_status()
    return "".join(b.get("text", "") for b in r.json()["content"]).strip()


def summarize(text):
    key = os.environ.get("ANTHROPIC_API_KEY")
    trimmed = trim_log(text)
    if key:
        try:
            return "LLM summary", llm_summary(trimmed, key)
        except Exception as exc:  # network, quota, bad key
            print(f"LLM call failed ({exc}); using rule-based summary", file=sys.stderr)
    return "Rule-based summary", rule_based_summary(text)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "build.log"
    text = open(path, encoding="utf-8", errors="replace").read()
    kind, summary = summarize(text)
    block = f"## Build summary ({kind})\n\n{summary}\n"
    print(block)
    out = os.environ.get("GITHUB_STEP_SUMMARY")
    if out:
        with open(out, "a") as f:
            f.write(block)


if __name__ == "__main__":
    main()
