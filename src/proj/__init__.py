# src/proj 包入口
# ============================================================
# 公共 API(Q7 Day1:正式契约化)
# ============================================================
# 用户用 src.proj 时的稳定接口(全在 __all__ 里):
#   from src.proj import main
#   main()                  # 启动 CLI,等价于 python -m src.proj.cli
#
#   # Q5 Day2:task 抽象层
#   from src.proj import Task, Task2
#   from src.proj import BUILTIN_TASKS, BUILTIN_TASKS_JSON
#   from src.proj import get_task, get_json_task
#
#   # Q5 Day3-4:外部 task 加载
#   from src.proj import load_task_from_file, scan_tasks_dir
#
#   # Q6 Day4:错误码 + 构造器
#   from src.proj import ERR_BAD_REQUEST, ERR_UNKNOWN_ACTION, ERR_BAD_JSON
#   from src.proj import make_error
#
# 用户不要用(下划线开头 + 没在 __all__):
#   src.proj._config        ← 内部常量(Q4 Day2 集中地)
#   src.proj.cli            ← 走 main(),别走 cli.main()
#   src.proj.core.*         ← 业务本体,改时小心
# ============================================================

__version__ = "0.1.0"  # Q7 Day1:惯例

# 1. 公共 task 符号(Q5/Q6 全部契约)
from .core.task import (
    Task, Task2,
    BUILTIN_TASKS, BUILTIN_TASKS_JSON,
    get_task, get_json_task,
    load_task_from_file, scan_tasks_dir,
    ERR_BAD_REQUEST, ERR_UNKNOWN_ACTION, ERR_BAD_JSON,
    make_error,
)

# 2. 启动入口
from .cli import main

# 3. 兜底清理(防 from .X import Y 把 X 注进当前包 namespace)
# 注意:由于 sys.path 同时含 'src' 和 '.',同一个 __init__.py 会被加载两次
# 产生两个模块实例(sys.modules['proj'] 和 sys.modules['src.proj'])
# delattr 必须对两个实例都执行
for _mod_name in ("src.proj", __name__):
    import sys as _sys
    _pkg = _sys.modules.get(_mod_name)
    if _pkg is None:
        continue
    for _name in ("_config", "cli", "core"):
        if hasattr(_pkg, _name):
            delattr(_pkg, _name)
del _mod_name, _sys, _pkg, _name

# 4. 显式公共 API 清单
__all__ = [
    "__version__",
    "main",
    "Task", "Task2",
    "BUILTIN_TASKS", "BUILTIN_TASKS_JSON",
    "get_task", "get_json_task",
    "load_task_from_file", "scan_tasks_dir",
    "ERR_BAD_REQUEST", "ERR_UNKNOWN_ACTION", "ERR_BAD_JSON",
    "make_error",
]