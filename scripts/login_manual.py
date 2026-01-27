# -*- coding: utf-8 -*-

"""手动脚本（非 pytest），仅用于参考。

该文件刻意不命名为 test_*.py，避免 pytest 导入冲突。
需要可视化执行请用 python scripts/run_local.py；跑自动化用例请用 pytest 运行 tests/test_login.py。
"""

from __future__ import annotations

from run_local import run


if __name__ == "__main__":
    run()
