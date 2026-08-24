# Changelog

All notable changes to **Proj** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] - 2026-08-24

### 🎉 First public release

Proj 是 14 问 14 维软件分析法(Q3-Q7)的教学产出物:
一个最小可运行的 socket server + task 系统 + 插件体系。

### ✨ Added(Q3-Q7 累积)

#### Q3 活着 — 进程生命周期
- `simple / thread / pool / pro` 四种并发模型(STYLES)
- `boot.py / boot.bat` 菜单化启动
- `dist/proj.exe` 7.2 MB pyinstaller 单文件可执行

#### Q4 组织 — 代码结构
- `src/proj/` src-layout 包结构
- `core / plugins` 子包分离
- `.gitignore` 7 大类隔离

#### Q5 任务 — 业务契约
- `Task = bytes → bytes` 老契约
- `Task2 = dict → dict` 新契约(Q6 升级)
- `BUILTIN_TASKS`(5 个)+ `BUILTIN_TASKS_JSON`(3 个)
- `load_task_from_file` / `scan_tasks_dir` 外部加载

#### Q6 数据 — 结构化协议
- JSON 协议 + schema 校验
- Logger(`proj.cli.json`)记录协议错误
- 错误码字段:`{code, message}` 双可读

#### Q7 接口 — 公共契约
- 22 项稳定 API(`__all__` 锁定)
- `proj.pyi` typing stub(IDE 智能提示)
- `pyproject.toml` 完整 packaging
- 6 个 `proj.plugins` entry_points
- `make_error_v2` + `ERR_FORMAT_V2` v2 错误协议

### 🔧 Added(Q9 演)

- `python -m build` wheel + sdist 端到端构建 ✅
- `README.md` 标准文件(PEP 639 / sdist 需要)
- `license = "MIT"` SPDX 表达式(替代 table 形式)
- `--version` 命令行参数(action="version")
- `CHANGELOG.md` Keep a Changelog 格式
- `twine check` 全 PASSED(wheel + sdist)

### ✅ Verified

| 项目 | 结果 |
|---|---|
| `python -m build` | exit 0, wheel 23 KB + sdist 21 KB |
| `pip install proj-0.1.0-py3-none-any.whl`(干净 venv) | ✅ |
| `import proj` | version 0.1.0 ✅ |
| `proj --version` | "proj 0.1.0" ✅ |
| `proj --help` | usage 完整,epilog 带版本 ✅ |
| `discover_entry_points()` | 6 个 ✅ |
| `get_task` / `get_json_task` | 5 + 3 = 8 task 全活 ✅ |
| `twine check` | wheel + sdist 双 PASSED ✅ |

### 📦 Distribution Artifacts

- `dist/proj-0.1.0-py3-none-any.whl` (23909 bytes)
- `dist/proj-0.1.0.tar.gz` (20831 bytes)
- `dist/proj.exe` (7266046 bytes, pyinstaller)