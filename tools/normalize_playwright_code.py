from __future__ import annotations

import argparse
import io
import ast
import sys
import tokenize
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Candidate:
    text: str
    label: str


def _has_private_use_chars(s: str) -> bool:
    return any(unicodedata.category(ch) == "Co" for ch in s)


def _strip_private_use_chars(s: str) -> str:
    return "".join(ch for ch in s if unicodedata.category(ch) != "Co")


def _score_chinese_readability(s: str) -> int:
    score = 0
    for ch in s:
        cp = ord(ch)
        # CJK Unified Ideographs
        if 0x4E00 <= cp <= 0x9FFF:
            score += 3
        # CJK Extension A
        elif 0x3400 <= cp <= 0x4DBF:
            score += 2
        # Common CJK punctuation
        elif ch in "，。；：！？（）【】《》“”‘’、·—":
            score += 1
        elif ch == "?" or ch == "�":
            score -= 2
    return score


def _try_mojibake_fix(s: str) -> list[Candidate]:
    candidates: list[Candidate] = []

    # Common case on Windows CN: UTF-8 bytes were interpreted as CP936 text.
    for enc in ("cp936", "gbk", "gb18030"):
        try:
            fixed = s.encode(enc).decode("utf-8")
        except Exception:
            continue
        candidates.append(Candidate(fixed, f"{enc}->utf-8"))

    # Another common case: UTF-8 bytes interpreted as latin-1.
    try:
        fixed = s.encode("latin-1").decode("utf-8")
        candidates.append(Candidate(fixed, "latin1->utf-8"))
    except Exception:
        pass

    return candidates


def normalize_ui_text(s: str) -> str:
    original = s

    # 1) Strip icon glyphs from Playwright Inspector recordings.
    stripped = _strip_private_use_chars(s)

    best = stripped
    best_score = _score_chinese_readability(best)

    # 2) Try to recover Chinese if the string is mojibake.
    for cand in _try_mojibake_fix(stripped):
        score = _score_chinese_readability(cand.text)
        if score > best_score:
            best = cand.text
            best_score = score

    # Only return changed text if it actually improved or removed PUA chars.
    if best != original:
        return best
    return original


def _is_probably_fstring(token_text: str) -> bool:
    lower = token_text.lstrip()[:2].lower()
    return lower.startswith("f") or lower.startswith("fr") or lower.startswith("rf")


def _rewrite_python_bytes(data: bytes) -> bytes:
    newline = b"\r\n" if b"\r\n" in data else b"\n"

    out_tokens: list[tokenize.TokenInfo] = []

    reader = tokenize.tokenize(io.BytesIO(data).readline)
    for tok in reader:
        if tok.type != tokenize.STRING:
            out_tokens.append(tok)
            continue

        # Skip f-strings (need a full parser to safely rewrite them)
        if _is_probably_fstring(tok.string):
            out_tokens.append(tok)
            continue

        # Skip bytes literals
        if tok.string.lstrip().lower().startswith("b"):
            out_tokens.append(tok)
            continue

        try:
            value = ast.literal_eval(tok.string)
        except Exception:
            out_tokens.append(tok)
            continue

        if not isinstance(value, str):
            out_tokens.append(tok)
            continue

        new_value = normalize_ui_text(value)
        if new_value == value:
            out_tokens.append(tok)
            continue

        new_literal = repr(new_value)
        out_tokens.append(tok._replace(string=new_literal))

    rewritten = tokenize.untokenize(out_tokens)

    # Normalize line endings deterministically
    rewritten = rewritten.replace(b"\r\n", b"\n")
    if newline == b"\r\n":
        rewritten = rewritten.replace(b"\n", b"\r\n")

    return rewritten


def _iter_py_files(paths: Iterable[str]) -> list[Path]:
    result: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            result.extend(sorted(p.rglob("*.py")))
        else:
            result.append(p)
    return result


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="?? Playwright ??? Python ?????????????PUA??????????????",
    )
    parser.add_argument("paths", nargs="+", help=".py ?????")
    parser.add_argument("--check", action="store_true", help="??????????????????? 0")
    args = parser.parse_args(argv)

    changed = False
    for path in _iter_py_files(args.paths):
        data = path.read_bytes()
        new_data = _rewrite_python_bytes(data)
        if new_data != data:
            changed = True
            if not args.check:
                path.write_bytes(new_data)
                print(f"????{path}")

    return 1 if (args.check and changed) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))