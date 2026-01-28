# -*- coding: utf-8 -*-

"""运行配置。

你只需要修改这里的变量，就能切换要操作的应用/模板。
"""

from __future__ import annotations

# 要在“请选择应用”下拉框中选择的应用名称。
# 示例："本源诗"、"测试应用"
APP_NAME = "测试应用"

# 表与字段数据文件路径（相对项目根目录）。
DATA_YAML_PATH = "data/data.yaml"

# 本地可视化运行（scripts/run_local.py）结束后是否暂停页面，便于你手动检查。
# True：不自动退出（会停在 page.pause()）
# False：执行完自动关闭浏览器并结束运行
PAUSE_AFTER_RUN = False
