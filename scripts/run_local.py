# -*- coding: utf-8 -*-

"""手动入口（可视化浏览器）。

- 运行：python scripts/run_local.py
- 测试：python -m pytest
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

# 直接运行 scripts/run_local.py 时，Python 的 sys.path[0] 是 scripts 目录。
# 这里显式把项目根目录加入 sys.path，确保可以导入 kuaimai_ui。
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kuaimai_ui import create_tables_from_yaml, login, print_playwright_setup_help
from kuaimai_ui import settings as km_settings


def _format_duration(seconds: float) -> str:
    seconds = float(seconds)
    if seconds < 60:
        return f"{seconds:.2f} 秒"

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    remain = seconds % 60

    if hours > 0:
        return f"{hours} 小时 {minutes} 分 {remain:.2f} 秒"
    return f"{minutes} 分 {remain:.2f} 秒"


def run() -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError as exc:
        print_playwright_setup_help(f"缺少 Python 包：{exc}")
        raise SystemExit(2) from exc
    except ImportError as exc:
        print_playwright_setup_help(f"导入 Playwright 失败：{exc}")
        raise SystemExit(2) from exc

    start = time.monotonic()
    ok = False
    auto_duration: float | None = None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)
        page = browser.new_page()

        try:
            login(page)
            create_tables_from_yaml(page)
            auto_duration = time.monotonic() - start
            ok = True

            if getattr(km_settings, "PAUSE_AFTER_RUN", False):
                print("已开启 PAUSE_AFTER_RUN，将暂停页面，手动关闭后再结束。")
                page.pause()
        finally:
            duration = auto_duration if auto_duration is not None else time.monotonic() - start
            status = "成功" if ok else "失败"
            print(f"本次运行{status}，总耗时：{_format_duration(duration)}")
            browser.close()

if __name__ == "__main__":
    run()
