from __future__ import annotations

import os
import platform
import struct
import sys
from importlib import metadata
from pathlib import Path


def _find_windows_dll(dll_name: str) -> list[Path]:
    if os.name != "nt":
        return []
    windir = Path(os.environ.get("WINDIR", "C:/Windows"))
    candidates = [windir / "System32" / dll_name, windir / "SysWOW64" / dll_name]
    return [p for p in candidates if p.exists()]


def main() -> int:
    print("Python:", sys.executable)
    print("Version:", sys.version.replace("\n", " "))
    print("Bits:", struct.calcsize("P") * 8)
    print("OS:", platform.platform())

    dll = "vcruntime140_1.dll"
    dll_paths = _find_windows_dll(dll)
    if dll_paths:
        print(f"{dll}: OK ({dll_paths[0]})")
    else:
        print(f"{dll}: MISSING (likely need Microsoft Visual C++ Redistributable 2015-2022 x64)")

    try:
        import greenlet  # noqa: F401
        print("greenlet: OK")
    except Exception as exc:
        print("greenlet: FAIL ->", exc)

    try:
        pw_version = metadata.version("playwright")
        print("playwright (package): OK", pw_version)
    except Exception as exc:
        print("playwright (package): FAIL ->", exc)

    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
        print("playwright.sync_api: OK")
    except Exception as exc:
        print("playwright.sync_api: FAIL ->", exc)

    browsers_dir = Path(os.environ.get("LOCALAPPDATA", "")) / "ms-playwright"
    print("browsers dir:", browsers_dir, "(exists)" if browsers_dir.exists() else "(missing)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
