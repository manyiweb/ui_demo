# -*- coding: utf-8 -*-

"""文本守卫：防止乱码/图标字符进入代码库。

检查项目（递归检查目录下的 .py）：
- 私用区字符（PUA，U+E000-U+F8FF），常见于菜单图标
- 字符替换符：�（通常来自解码错误）
- 连续问号占位（通常来自中文乱码）

用法：python tools/text_guard.py --check .
"""

from __future__ import annotations

import argparse
import ast
import io
import re
import sys
import tokenize
import unicodedata
from pathlib import Path
from typing import Iterable


SKIP_NAMES = {"normalize_playwright_code.py", "text_guard.py"}


def _iter_py_files(paths: Iterable[str]) -> list[Path]:
    result: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            result.extend(sorted(p.rglob("*.py")))
        else:
            if p.suffix.lower() == ".py":
                result.append(p)
    return result


def _has_pua(s: str) -> bool:
    return any(unicodedata.category(ch) == "Co" for ch in s)


def _string_literals(path: Path) -> list[str]:
    data = path.read_bytes()
    values: list[str] = []

    reader = tokenize.tokenize(io.BytesIO(data).readline)
    for tok in reader:
        if tok.type != tokenize.STRING:
            continue

        lower = tok.string.lstrip().lower()
        if lower.startswith("f"):
            continue
        if lower.startswith("b"):
            continue

        try:
            value = ast.literal_eval(tok.string)
        except Exception:
            continue

        if isinstance(value, str):
            values.append(value)

    return values


def _has_question_placeholder(s: str) -> bool:
    return re.search(r"\?{2,}", s) is not None


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="检查代码文本中是否存在乱码/图标字符。")
    parser.add_argument("paths", nargs="*", default=["."], help="要检查的 .py 文件或目录（默认：.）")
    parser.add_argument("--check", action="store_true", help="仅检查；返回码表示是否通过")
    args = parser.parse_args(argv)

    problems: list[str] = []

    for path in _iter_py_files(args.paths):
        if path.name in SKIP_NAMES:
            continue

        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            problems.append(f"{path}: 读取失败：{exc}")
            continue

        if "�" in text:
            problems.append(f"{path}: 包含替换符 �（疑似编码问题）")

        if _has_pua(text):
            problems.append(f"{path}: 包含私用区字符（疑似菜单图标字符）")

        if _has_question_placeholder(text):
            problems.append(f"{path}: 包含连续问号占位（疑似中文乱码）")

        for s in _string_literals(path):
            if "�" in s:
                problems.append(f"{path}: 字符串字面量包含替换符 �（疑似编码问题）")
            if _has_pua(s):
                problems.append(f"{path}: 字符串字面量包含私用区字符（疑似菜单图标字符）")
            if _has_question_placeholder(s):
                problems.append(f"{path}: 字符串字面量包含连续问号占位（疑似中文乱码）")

    if problems:
        for msg in problems:
            print(msg, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
