# -*- coding: utf-8 -*-

"""兼容入口：保留历史 import 路径。

推荐新代码直接使用：from kuaimai_ui import ...
"""

from __future__ import annotations

from kuaimai_ui.flows.km_flow import (
    FieldSpec,
    create_fields,
    create_tables_from_yaml,
    login,
    print_playwright_setup_help,
)

__all__ = [
    "FieldSpec",
    "create_fields",
    "create_tables_from_yaml",
    "login",
    "print_playwright_setup_help",
]
