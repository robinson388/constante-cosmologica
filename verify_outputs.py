#!/usr/bin/env python3
"""Verifica outputs JSON del paper_lambda contra manifest.json (CI / GitHub)."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "expected_outputs" / "manifest.json"


def get_nested(d: dict, dotted: str):
    cur = d
    for part in dotted.split("."):
        cur = cur[part]
    return cur


def ok(expected, actual, tol_rel: float, tol_abs: float) -> bool:
    if isinstance(expected, bool):
        return actual == expected
    if not isinstance(actual, (int, float)) or not isinstance(expected, (int, float)):
        return actual == expected
    if math.isclose(actual, expected, rel_tol=tol_rel, abs_tol=tol_abs):
        return True
    return abs(actual - expected) <= max(tol_abs, tol_rel * abs(expected))


def main() -> int:
    spec = json.loads(MANIFEST.read_text(encoding="utf-8"))
    tol_r = spec.get("tolerance_rel", 0.02)
    tol_a = spec.get("tolerance_abs", 0.005)
    failed = []

    for chk in spec["checks"]:
        name = chk["file"]
        path = ROOT / name
        if name.endswith(".py"):
            print(f"SKIP runtime-only: {name} (run via run_all.sh)")
            continue
        if not path.exists():
            failed.append(f"MISSING {name}")
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for key, exp in chk["keys"].items():
            try:
                act = get_nested(data, key)
            except KeyError:
                failed.append(f"{name}: missing key {key}")
                continue
            if not ok(exp, act, tol_r, tol_a):
                failed.append(f"{name}: {key} expected {exp!r} got {act!r}")

    if failed:
        print("VERIFY FAILED:")
        for line in failed:
            print(f"  - {line}")
        return 1

    print(f"VERIFY OK ({len(spec['checks'])} checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
