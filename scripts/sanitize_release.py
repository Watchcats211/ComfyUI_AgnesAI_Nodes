#!/usr/bin/env python3
"""
Sanitize the repository before publishing it to GitHub.

Usage:
  python3 scripts/sanitize_release.py --write .
  python3 scripts/sanitize_release.py --check .
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys


API_KEY_RE = re.compile(r"sk-[A-Za-z0-9]{20,}")
LOCAL_PATH_RE = re.compile(r"/Users/[^\"'\\s]+")


def sanitize_workflow(path: pathlib.Path) -> bool:
    changed = False
    original = path.read_text(encoding="utf-8")
    data = json.loads(original)

    for node in data.get("nodes", []):
        node_type = node.get("type")

        if node_type == "Agnes_Config":
            values = node.get("widgets_values")
            if isinstance(values, list):
                if len(values) >= 1 and values[0] != "":
                    values[0] = ""
                    changed = True
                if len(values) >= 2 and not values[1]:
                    values[1] = "https://apihub.agnes-ai.com/v1"
                    changed = True

        if node_type == "LoadImage":
            values = node.get("widgets_values")
            if isinstance(values, list) and values:
                if values[0] != "agnes_i2v_source.png":
                    values[0] = "agnes_i2v_source.png"
                    changed = True

        if node_type == "VHS_VideoCombine":
            values = node.get("widgets_values")
            if isinstance(values, dict):
                preview = values.get("videopreview")
                if isinstance(preview, dict) and preview.get("params"):
                    preview["params"] = {}
                    changed = True

    new_text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    if new_text != original:
        path.write_text(new_text, encoding="utf-8")
        changed = True

    return changed


def scan_text_file(path: pathlib.Path) -> list[str]:
    hits: list[str] = []
    text = path.read_text(encoding="utf-8", errors="replace")

    for lineno, line in enumerate(text.splitlines(), start=1):
        if API_KEY_RE.search(line):
            hits.append(f"{path}:{lineno}: possible Agnes API key")
        if "LOCAL_PATH_RE =" in line:
            continue
        if LOCAL_PATH_RE.search(line):
            hits.append(f"{path}:{lineno}: local absolute path")

    return hits


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", help="Repository root")
    parser.add_argument("--write", action="store_true", help="Rewrite workflow JSON in place")
    parser.add_argument("--check", action="store_true", help="Check for likely secrets or local paths")
    args = parser.parse_args()

    root = pathlib.Path(args.root).resolve()
    if not root.exists():
        print(f"Path not found: {root}", file=sys.stderr)
        return 2

    if not args.write and not args.check:
        parser.error("choose at least one of --write or --check")

    if args.write:
        changed_any = False
        for workflow in sorted((root / "workflows").glob("*.json")):
            if sanitize_workflow(workflow):
                print(f"sanitized: {workflow.relative_to(root)}")
                changed_any = True
        if not changed_any:
            print("no workflow changes needed")

    if args.check:
        hits: list[str] = []
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if any(part in {"__pycache__", ".git"} for part in path.parts):
                continue
            if path.suffix.lower() not in {".py", ".json", ".md", ".js", ".txt"}:
                continue
            hits.extend(scan_text_file(path))

        if hits:
            print("release check failed:")
            for hit in hits:
                print(hit)
            return 1

        print("release check passed")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
