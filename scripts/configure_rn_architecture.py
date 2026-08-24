#!/usr/bin/env python3
"""Configure the React Native Legacy or New Architecture benchmark build consistently."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRADLE = ROOT / "apps" / "react-native-benchmark-app" / "android" / "gradle.properties"
MODULE = ROOT / "apps" / "react-native-benchmark-app" / "modules" / "CommunicationModule.ts"

GRADLE_PATTERN = re.compile(
    r"(?m)^newArchEnabled=(true|false)[ \t]*(?=\r?$)"
)
MODULE_PATTERN = re.compile(
    r"(?m)^export const IS_LEGACY = (true|false);[ \t]*(?=\r?$)"
)


def read_preserving_newlines(path: Path) -> str:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


def write_preserving_newlines(path: Path, content: str) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(content)


def read_state() -> tuple[bool, bool]:
    gradle = read_preserving_newlines(GRADLE)
    module = read_preserving_newlines(MODULE)

    g = GRADLE_PATTERN.search(gradle)
    m = MODULE_PATTERN.search(module)
    if not g or not m:
        raise RuntimeError("Could not locate architecture configuration markers.")

    new_arch = g.group(1) == "true"
    is_legacy = m.group(1) == "true"
    return new_arch, is_legacy


def describe() -> str:
    new_arch, is_legacy = read_state()
    if new_arch and not is_legacy:
        return "new"
    if not new_arch and is_legacy:
        return "legacy"
    return "INCONSISTENT"


def configure(target: str) -> None:
    target_new = target == "new"
    target_legacy = not target_new

    gradle = read_preserving_newlines(GRADLE)
    module = read_preserving_newlines(MODULE)

    gradle_new, count_g = GRADLE_PATTERN.subn(
        f"newArchEnabled={'true' if target_new else 'false'}",
        gradle,
    )
    module_new, count_m = MODULE_PATTERN.subn(
        f"export const IS_LEGACY = {'true' if target_legacy else 'false'};",
        module,
    )

    if count_g != 1 or count_m != 1:
        raise RuntimeError(
            f"Expected exactly one marker in each file; got gradle={count_g}, module={count_m}."
        )

    try:
        write_preserving_newlines(GRADLE, gradle_new)
        write_preserving_newlines(MODULE, module_new)

        if describe() != target:
            raise RuntimeError("Post-write consistency check failed.")
    except Exception as exc:
        try:
            write_preserving_newlines(GRADLE, gradle)
            write_preserving_newlines(MODULE, module)
        except Exception as rollback_exc:
            raise RuntimeError(
                f"Configuration failed and rollback also failed: {rollback_exc}"
            ) from exc
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["legacy", "new", "check"])
    args = parser.parse_args()

    if args.mode == "check":
        state = describe()
        print(f"RN architecture configuration: {state}")
        return 0 if state != "INCONSISTENT" else 2

    configure(args.mode)
    print(f"Configured RN benchmark for: {describe()}")
    print("Rebuild the application before benchmarking.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
