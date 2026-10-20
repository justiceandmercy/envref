#!/usr/bin/env python3
"""Find environment variables referenced by code but missing from .env.example."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable

SOURCE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs",
    ".go", ".rb", ".sh", ".bash", ".zsh", ".yaml", ".yml",
}

SHELL_EXTENSIONS = {".sh", ".bash", ".zsh"}

ENV_PATTERNS = [
    re.compile(r'os\.environ\[\s*["\']([A-Za-z_][A-Za-z0-9_]*)["\']\s*\]'),
    re.compile(r'os\.environ\.get\s*\(\s*["\']([A-Za-z_][A-Za-z0-9_]*)["\']'),
    re.compile(r'os\.getenv\s*\(\s*["\']([A-Za-z_][A-Za-z0-9_]*)["\']'),
    re.compile(r'os\.Getenv\s*\(\s*["\']([A-Za-z_][A-Za-z0-9_]*)["\']'),
    re.compile(r'os\.LookupEnv\s*\(\s*["\']([A-Za-z_][A-Za-z0-9_]*)["\']'),
    re.compile(r'process\.env\.([A-Za-z_][A-Za-z0-9_]*)'),
    re.compile(r'process\.env\[\s*["\']([A-Za-z_][A-Za-z0-9_]*)["\']\s*\]'),
    re.compile(r'ENV\[\s*["\']([A-Za-z_][A-Za-z0-9_]*)["\']\s*\]'),
    re.compile(r'ENV\.fetch\s*\(\s*["\']([A-Za-z_][A-Za-z0-9_]*)["\']'),
]

SHELL_PATTERNS = [
    re.compile(r'\$\{([A-Za-z_][A-Za-z0-9_]*)\}'),
    re.compile(r'\$([A-Za-z_][A-Za-z0-9_]*)'),
]

IGNORED_DIRECTORIES = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", ".tox"}


def parse_env_file(path: Path) -> set[str]:
    keys: set[str] = set()
    if not path.is_file():
        return keys
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key = line.split("=", 1)[0].strip()
        if key.startswith("export "):
            key = key[7:].strip()
        if key and not key.startswith("#"):
            keys.add(key)
    return keys


def scan_directory(root: Path) -> tuple[set[str], int]:
    references: set[str] = set()
    scanned = 0
    if not root.exists():
        return references, scanned
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in IGNORED_DIRECTORIES for part in path.parts):
            continue
        if path.suffix.lower() not in SOURCE_EXTENSIONS:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        scanned += 1
        patterns = list(ENV_PATTERNS)
        if path.suffix.lower() in SHELL_EXTENSIONS:
            patterns.extend(SHELL_PATTERNS)
        for pattern in patterns:
            references.update(pattern.findall(text))
    return references, scanned


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envref",
        description="Compare environment variable references with a .env.example file.",
    )
    parser.add_argument("path", nargs="?", default=".", help="project root to scan")
    parser.add_argument("--env-file", default=".env.example", help="environment template to compare against")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument(
        "--fail-on",
        choices=("missing", "unused", "any", "none"),
        default="missing",
        help="condition that makes the command exit with status 1",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.path).resolve()
    env_path = Path(args.env_file)
    if not env_path.is_absolute():
        env_path = root / env_path

    references, scanned = scan_directory(root)
    declared = parse_env_file(env_path)

    missing = sorted(references - declared)
    unused = sorted(declared - references)

    if args.json:
        print(json.dumps({
            "root": str(root),
            "env_file": str(env_path),
            "files_scanned": scanned,
            "references": sorted(references),
            "declared": sorted(declared),
            "missing": missing,
            "unused": unused,
        }, indent=2))
    else:
        print(f"Scanned {scanned} file(s) in {root}")
        print(f"Environment template: {env_path}")
        if missing:
            print("\nMissing from template:")
            for name in missing:
                print(f"  - {name}")
        if unused:
            print("\nDeclared but not referenced:")
            for name in unused:
                print(f"  - {name}")
        if not missing and not unused:
            print("\nNo environment drift found.")

    if args.fail_on == "none":
        return 0
    if args.fail_on == "missing":
        return 1 if missing else 0
    if args.fail_on == "unused":
        return 1 if unused else 0
    return 1 if (missing or unused) else 0


if __name__ == "__main__":
    raise SystemExit(main())
