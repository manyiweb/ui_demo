# ui_demo

## 使用说明（Windows）

### 1）安装依赖与浏览器

```bash
python -m pip install -r requirements.txt
python -m playwright install chromium
```

如果导入 Playwright 或启动浏览器报错：ImportError: DLL load failed ... _greenlet，通常是缺少 Microsoft Visual C++ Redistributable 2015-2022 (x64)，安装后重开终端再试。

### 2）手动执行（可视化）

```bash （执行速度慢，终端可查看当前进度）
python scripts/run_local.py
```

执行完成后会自动关闭浏览器并输出总耗时。
如需执行完暂停页面便于检查，把 `kuaimai_ui/settings.py` 里的 `PAUSE_AFTER_RUN` 设为 True。

### 3）运行 pytest（自动化）

```bash （执行速度快）
python -m pytest -q
```

> pytest 只执行 test_*.py，不会执行 main.py 里的 run()。

配置：
- 进入快麦后台应用管理，新增应用，脚本可自动获取最新应用名（如：本源诗）
- 修改 `kuaimai_ui/settings.py`：
  - APP_NAME：应用名（例如：测试应用）
  - DATA_YAML_PATH：数据文件路径（默认：data/data.yaml）**存放打印数据表名和字段，如快麦后台近期有新增字段，需在该文件手动添加**
  - PAUSE_AFTER_RUN：本地可视化执行后是否暂停页面（默认：False）

可选环境变量（需要时再用）：
- KM_PHONE：手机号
- KM_PASSWORD：密码
- KM_APP_NAME：应用名
- KM_DATA_YAML：数据文件路径
- KM_TIMEOUT_MS：等待超时（毫秒，默认：30000）

## Playwright 录制代码清理（必须）

从 Playwright Inspector 复制的代码可能包含菜单图标等“私用区字符”（U+E000-U+F8FF）或中文乱码，粘贴到代码前必须先清理。

```bash
python tools/normalize_playwright_code.py main.py
```

仅检查（不改文件）：

```bash
python tools/normalize_playwright_code.py --check .
```
