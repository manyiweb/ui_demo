# -*- coding: utf-8 -*-

from __future__ import annotations

import sys
from pathlib import Path


def pytest_configure() -> None:
    # 确保项目根目录在 sys.path 中，便于 pytest 直接导入 kuaimai_ui。
    root = Path(__file__).resolve().parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
