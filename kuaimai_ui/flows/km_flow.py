# -*- coding: utf-8 -*-

"""快麦后台 UI 自动化流程（Playwright sync）。

约定：
- 页面文字、日志与异常信息使用中文
- 默认从 data/data.yaml 读取要新增的表与字段
"""

from __future__ import annotations

import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from .. import settings

if TYPE_CHECKING:
    from playwright.sync_api import Locator, Page

LOGIN_URL = "http://admin.iot.kuaimai.com/login"
DEFAULT_PHONE = "13826056942"
DEFAULT_PASSWORD = "666666"

TIMEOUT_MS = int(os.getenv("KM_TIMEOUT_MS", "30000"))


def _is_navigation_destroy_error(exc: Exception) -> bool:
    msg = str(exc)
    return (
        'Execution context was destroyed' in msg
        or 'most likely because of a navigation' in msg
    )


def _safe_count(page: 'Page', locator: 'Locator', *, retries: int = 3) -> int:
    """安全获取 locator.count()。

    当页面正在跳转或刷新时，Playwright 可能抛出
    `Execution context was destroyed, most likely because of a navigation`。
    这里做一次短暂重试，避免偶发报错。
    """

    last_exc: Exception | None = None
    for _ in range(max(1, int(retries))):
        try:
            return locator.count()
        except Exception as exc:
            if _is_navigation_destroy_error(exc):
                last_exc = exc
                # 等待页面跳转稳定后再试
                try:
                    page.wait_for_load_state('domcontentloaded', timeout=TIMEOUT_MS)
                except Exception:
                    pass
                try:
                    page.wait_for_timeout(200)
                except Exception:
                    pass
                continue
            raise

    raise RuntimeError("页面正在跳转，读取元素数量失败，请稍后重试。") from last_exc

def get_app_name(app_name: str | None = None) -> str:
    """获取要选择的应用名称。

    优先级：
    1) 传参 app_name
    2) 代码配置 kuaimai_ui/settings.py 里的 APP_NAME
    3) 环境变量 KM_APP_NAME（可选）
    """

    if app_name is not None and str(app_name).strip():
        return str(app_name).strip()

    cfg = getattr(settings, "APP_NAME", "")
    if isinstance(cfg, str) and cfg.strip():
        return cfg.strip()

    env = os.getenv("KM_APP_NAME")
    if env and env.strip():
        return env.strip()

    raise RuntimeError("未配置应用名：请修改 kuaimai_ui/settings.py 中的 APP_NAME")


@dataclass(frozen=True)
class FieldSpec:
    """字段定义。"""

    field_name: str
    cn_name: str
    example: str


@dataclass(frozen=True)
class TableSpec:
    """YAML 表定义。"""

    name: str
    table_name: str
    fields: list[str]


def print_playwright_setup_help(details: str) -> None:
    print("Playwright 环境未就绪，无法启动浏览器。", file=sys.stderr)
    print(details, file=sys.stderr)
    print("", file=sys.stderr)
    print("修复方式(Windows)：", file=sys.stderr)
    print("1) 安装依赖：python -m pip install -r requirements.txt", file=sys.stderr)
    print("2) 安装浏览器：python -m playwright install chromium", file=sys.stderr)
    print(
        "3) 如果出现 `DLL load failed ... _greenlet`：安装 Microsoft Visual C++ Redistributable 2015-2022 (x64) 后重新打开终端",
        file=sys.stderr,
    )


def login(page: "Page") -> None:
    phone = os.getenv("KM_PHONE", DEFAULT_PHONE)
    password = os.getenv("KM_PASSWORD", DEFAULT_PASSWORD)

    page.goto(LOGIN_URL, wait_until="domcontentloaded")

    password_tab = page.get_by_text("密码登录")
    if _safe_count(page, password_tab) > 0:
        password_tab.first.click()

    page.wait_for_selector("input[placeholder='请输入手机号']", timeout=TIMEOUT_MS)
    phone_input = page.locator("input[placeholder='请输入手机号']:visible").first
    password_input = page.locator("input[placeholder='请输入密码']:visible").first

    phone_input.click()
    phone_input.evaluate("el => el.removeAttribute('readonly')")
    phone_input.fill(phone)

    password_input.click()
    password_input.evaluate("el => el.removeAttribute('readonly')")
    password_input.fill(password)

    page.get_by_role("button", name="登录").click()
    page.wait_for_load_state("networkidle")


def _click_menu(page: "Page", menu_text: str) -> None:
    locator = page.get_by_role("menuitem", name=re.compile(rf".*{re.escape(menu_text)}.*"))
    if _safe_count(page, locator) == 0:
        locator = page.get_by_text(menu_text, exact=False)

    target = locator.first
    target.scroll_into_view_if_needed()

    # 侧边栏菜单有时需要点击内部的 <div> 才会展开/跳转。
    div = target.locator("div")
    if _safe_count(page, div) > 0:
        div.first.click()
    else:
        target.click()


def open_field_management(page: "Page") -> None:
    _click_menu(page, "模板管理")
    _click_menu(page, "字段管理")

    page.get_by_role("button", name="新建字段").wait_for(state="visible", timeout=TIMEOUT_MS)


def select_app(page: "Page", app_name: str) -> None:
    page.get_by_placeholder("请选择应用").click()

    option = page.get_by_role("option", name=app_name)
    if _safe_count(page, option) == 0:
        option = page.locator("li").filter(has_text=app_name)
    option.first.click()


def get_data_table_modal(page: "Page") -> "Locator":
    modal = page.get_by_label("数据表管理")
    if _safe_count(page, modal) == 0:
        modal = page.get_by_role("dialog").filter(has_text=re.compile(r"数据表管理"))
    modal.first.wait_for(state="visible", timeout=TIMEOUT_MS)
    return modal.first


def _default_data_yaml_path() -> Path:
    # kuaimai_ui/flows/km_flow.py -> 项目根目录
    return Path(__file__).resolve().parents[2] / "data" / "data.yaml"


def load_table_specs_from_yaml(yaml_path: Path) -> list[TableSpec]:
    try:
        import yaml  # type: ignore
    except ModuleNotFoundError as exc:
        raise RuntimeError("缺少依赖：pyyaml。请执行：python -m pip install pyyaml") from exc

    try:
        raw = yaml_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise RuntimeError(f"找不到数据文件：{yaml_path}") from exc

    data = yaml.safe_load(raw) or {}

    if not isinstance(data, dict):
        raise RuntimeError("YAML 顶层必须是映射(key -> {table_name, fields})")

    result: list[TableSpec] = []
    for name, item in data.items():
        if not isinstance(item, dict):
            raise RuntimeError(f"YAML 节点 {name} 必须是映射")

        table_name = item.get("table_name")
        fields = item.get("fields")

        if not isinstance(table_name, str) or not table_name.strip():
            raise RuntimeError(f"YAML 节点 {name} 缺少 table_name")

        if fields is None:
            fields = []

        if not isinstance(fields, list) or any((not isinstance(x, str)) for x in fields):
            raise RuntimeError(f"YAML 节点 {name} 的 fields 必须是字符串列表")

        result.append(TableSpec(name=str(name), table_name=table_name, fields=list(fields)))

    return result


def _get_table_name_input(modal: "Locator") -> "Locator":
    return (
        modal.locator("div")
        .filter(has_text=re.compile(r"^表名$"))
        .get_by_role("textbox")
        .first
    )



def _fill_field_row_triplet(modal: "Locator", row_index: int, *, field_name: str, cn_name: str, example: str) -> None:
    """填写一行字段的三个输入框。

    说明：该弹窗里输入框的顺序通常是：表名 + (字段名, 中文名称, 字段值示例) * N。
    因此第 1 行字段从 textbox[1] 开始，每行占 3 个。

    如果页面结构有调整，请优先用 Playwright Inspector 重新录制并同步这里的定位策略。
    """

    textboxes = modal.get_by_role("textbox")
    base = 1 + row_index * 3

    try:
        textboxes.nth(base).wait_for(state="visible", timeout=TIMEOUT_MS)
        textboxes.nth(base + 1).wait_for(state="visible", timeout=TIMEOUT_MS)
        textboxes.nth(base + 2).wait_for(state="visible", timeout=TIMEOUT_MS)

        textboxes.nth(base).fill(field_name)
        textboxes.nth(base + 1).fill(cn_name)
        textboxes.nth(base + 2).fill(example)
    except Exception as exc:
        try:
            count = textboxes.count()
        except Exception:
            count = -1

        count_text = "未知" if count < 0 else str(count)
        raise RuntimeError(

            f"填写第 {row_index + 1} 行字段失败。当前弹窗内找到 {count_text} 个输入框(角色为 textbox)，本次需要访问到索引 {base + 2}。请检查：是否已打开“数据表管理”弹窗；点击“增加字段”后是否出现了新行；页面输入框顺序是否发生变化。"
        ) from exc


def _fill_field_row_value(modal: "Locator", row_index: int, value: str) -> None:
    _fill_field_row_triplet(modal, row_index, field_name=value, cn_name=value, example=value)


def _fill_field_row_spec(modal: "Locator", row_index: int, field: FieldSpec) -> None:
    _fill_field_row_triplet(
        modal,
        row_index,
        field_name=field.field_name,
        cn_name=field.cn_name,
        example=field.example,
    )





_DUPLICATE_TIPS: tuple[str, ...] = ("表名重复了", "字段名不能重复")


def _locator_visible(locator: "Locator") -> bool:
    try:
        return locator.count() > 0 and locator.first.is_visible()
    except Exception:
        return False


def _find_duplicate_tip(page: "Page", modal: "Locator") -> str | None:
    for tip in _DUPLICATE_TIPS:
        if _locator_visible(modal.get_by_text(tip, exact=False)):
            return tip

        if _locator_visible(page.get_by_text(tip, exact=False)):
            return tip

        if _locator_visible(page.get_by_role("alert").filter(has_text=re.compile(re.escape(tip)))):
            return tip

    return None


def _dismiss_alert_like(page: "Page", tip: str) -> None:
    # 容错：尝试关闭提示层，避免遮挡“取消”按钮。
    try:
        page.get_by_text(tip, exact=False).first.click(timeout=500)
    except Exception:
        pass

    try:
        page.get_by_role("alert").first.click(timeout=500)
    except Exception:
        pass


def _click_cancel(modal: "Locator", page: "Page") -> None:
    try:
        modal.get_by_role("button", name="取消").click(timeout=TIMEOUT_MS)
        return
    except Exception:
        pass

    page.get_by_role("button", name="取消").first.click(timeout=TIMEOUT_MS)


def _save_modal_or_cancel_on_duplicate(page: "Page", modal: "Locator") -> bool:
    # 点击保存：
    # - 成功：弹窗关闭，返回 True
    # - 表名/字段名重复：点击取消关闭弹窗，返回 False

    modal.get_by_role("button", name="保存").click()

    deadline = time.monotonic() + TIMEOUT_MS / 1000
    while time.monotonic() < deadline:
        try:
            if not modal.is_visible():
                return True
        except Exception:
            return True

        tip = _find_duplicate_tip(page, modal)
        if tip:
            print(f"检测到提示“{tip}”，将取消本次新增并跳过。")
            _dismiss_alert_like(page, tip)
            _click_cancel(modal, page)
            modal.wait_for(state="hidden", timeout=TIMEOUT_MS)
            return False

        page.wait_for_timeout(200)

    raise RuntimeError("点击“保存”后等待超时：弹窗未关闭且未检测到重复提示。")


def _create_one_table(page: "Page", *, table_name: str, field_values: list[str]) -> bool:
    page.get_by_role("button", name="新建字段").click()

    modal = get_data_table_modal(page)

    table_input = _get_table_name_input(modal)
    table_input.click()
    table_input.fill(table_name)

    for idx, value in enumerate(field_values):
        if idx > 0:
            modal.get_by_role("button").filter(has_text=re.compile(r"增加字段")).first.click()

        _fill_field_row_value(modal, idx, value)

    saved = _save_modal_or_cancel_on_duplicate(page, modal)

    page.get_by_role("button", name="新建字段").wait_for(state="visible", timeout=TIMEOUT_MS)
    return saved

def create_fields(page: "Page", *, app_name: str, table_name: str, fields: list[FieldSpec]) -> None:
    if not fields:
        raise ValueError("fields 不能为空")

    open_field_management(page)
    select_app(page, app_name)

    page.get_by_role("button", name="新建字段").click()
    modal = get_data_table_modal(page)

    table_input = _get_table_name_input(modal)
    table_input.click()
    table_input.fill(table_name)

    for idx, field in enumerate(fields):
        if idx > 0:
            modal.get_by_role("button").filter(has_text=re.compile(r"增加字段")).first.click()

        _fill_field_row_spec(modal, idx, field)

    saved = _save_modal_or_cancel_on_duplicate(page, modal)
    if not saved:
        raise RuntimeError("保存失败：表名或字段名重复，请修改后重试。")



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


def create_tables_from_yaml(page: "Page", *, app_name: str | None = None, yaml_path: str | os.PathLike[str] | None = None) -> None:
    app_name = get_app_name(app_name)
    if yaml_path is None:
        cfg_path = getattr(settings, 'DATA_YAML_PATH', '')
        env_path = os.getenv('KM_DATA_YAML')
        raw = env_path or cfg_path
        yaml_file = Path(raw) if raw else _default_data_yaml_path()
    else:
        yaml_file = Path(yaml_path)

    tables = load_table_specs_from_yaml(yaml_file)
    start = time.monotonic()

    print(f"开始根据 YAML 新建字段，共 {len(tables)} 张表")

    open_field_management(page)
    select_app(page, app_name)

    success = 0
    skipped = 0

    for table in tables:
        if not table.fields:
            print(f"跳过空字段表：{table.table_name}")
            skipped += 1
            continue

        print(f"正在处理：{table.table_name}，字段数 {len(table.fields)}")
        ok = _create_one_table(page, table_name=table.table_name, field_values=table.fields)
        if ok:
            success += 1
        else:
            skipped += 1

    print(f"所有表处理完成：成功 {success}，跳过 {skipped}，耗时 {_format_duration(time.monotonic() - start)}")
