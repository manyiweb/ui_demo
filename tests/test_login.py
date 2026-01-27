# -*- coding: utf-8 -*-


from kuaimai_ui import create_tables_from_yaml, login


def test_login(page):
    """pytest 用例入口：登录 + 根据 data/data.yaml 新建字段。"""

    login(page)

    create_tables_from_yaml(page)
