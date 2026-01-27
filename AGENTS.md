<INSTRUCTIONS>
## 语言与输出
- 与我对话时始终使用中文回复。

## 代码文本规范（必须）
- 代码中不允许出现中文乱码占位符（例如连续问号占位）。
- 代码里的注释、Docstring、日志/报错描述（print/logger/异常消息）一律用中文。
- 从 Playwright Inspector 复制的录制代码，上代码前先运行清理：
  - `python tools/normalize_playwright_code.py <file_or_dir>`
- 结束修改前必须通过检查（退出码为 0）：
  - `python tools/normalize_playwright_code.py --check .`

## 测试说明
- pytest 只执行 test_*.py，不会执行 main.py 里的 run()。
</INSTRUCTIONS>
