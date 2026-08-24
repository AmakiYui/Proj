# src/proj/plugins/ 子包
# ============================================================
# Proj 内置 task 实现(Q7 Day2-3)
# ============================================================
# 这些函数通过 pyproject.toml 的 entry_points 注册到 proj.plugins 组
# 用户也可以自己写 .py 文件放别的目录,用 scan_plugins_dir() 加载
#
# 内置 task 列表(都在 builtins.py 里):
#   shout / whisper / hello / bye / double / len_count
# ============================================================

from . import builtins  # noqa: F401  # 让 builtins 模块可被发现