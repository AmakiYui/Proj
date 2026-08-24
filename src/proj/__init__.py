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

# 1. 公共 task 符号(Q5/Q6/Q7 全部契约)
from .core.task import (
    Task, Task2,
    BUILTIN_TASKS, BUILTIN_TASKS_JSON,
    get_task, get_json_task,
    load_task_from_file, scan_tasks_dir,
    ERR_BAD_REQUEST, ERR_UNKNOWN_ACTION, ERR_BAD_JSON,
    ERR_TASK_NOT_FOUND, ERR_BAD_SIGNATURE,  # Q8 Day2 新增(7 类错误码之 2)
    ERR_TASK_EXCEPTION, ERR_BIND_FAILED, ERR_INTERNAL,  # Q8 Day2 新增(5xx 系列)
    ERR_MESSAGES,  # Q8 Day2 新增(7 类错误的 message 表)
    ERR_FORMAT_V2,  # Q7 Day2-2(v1 没有这个常量,直接走 make_error)
    make_error,
    make_error_v2,  # Q7 Day2-2
    safe_call_task,  # Q8 Day2 新增(任务异常防护)
    safe_bind,       # Q8 Day2 新增(端口占用防护)
    err_message,     # Q8 Day2 新增(5xx 区分查表)
)

# 2. 插件 API(Q7 Day2-3 完全版)
from .plugin_loader import (
    register_task,
    unregister_task,
    get_plugin_tasks,
    scan_plugins_dir,
    discover_entry_points,
    clear_plugins,
)

# 3. 安全 API(Q10 Day2 直接开发版)
from .security import (
    safe_recv,
    set_recv_timeout,
    compute_plugin_signature,
    verify_plugin_signature,
    load_manifest,
    DEFAULT_MAX_RECV,
    DEFAULT_ALLOWED_ENTRY_POINT_GROUPS,
    get_logger as get_security_logger,
)

# 4. 可观测 API(Q11 Day2 直接开发版)
from .observability import (
    Counter,
    Gauge,
    Histogram,
    Registry,
    get_registry,
    reset_registry,
    dump_metrics,
)

# 5. 日志配置(Q11 Day2)
from .log_setup import setup_logging, get_proj_logger

# 6. 健康检查(Q12 Day2)
from .health_check import (
    init_server_start_time,
    health_check_handler,
    check_server,
    format_check_result,
)

# 7. 缓存(Q13 Day2)
from .memoize import memoize_task, memoize_builtin_tasks

# 8. 协同(Q14 Day2)
from .client_pool import ClientPool, ServerEndpoint, parse_endpoints
from .process_pool import call_in_subprocess, SafeTask
from .alert import AlertEngine, get_default_engine, DEFAULT_THRESHOLDS

# 9. MVF 模板骨架(Q1 Day2 — 14 问升维)
from . import mvf as _mvf_module
from .mvf.template_factory import generate_scaffold, Scaffold
from .mvf.known_projects import KNOWN_PROJECTS, is_known, get_fills
from .mvf.compare import compare_projects, compare_all

# 10. Pipeline A1:想法 -> MVF(Q1 Day2 扩展)
from . import pipeline as _pipeline_module
from .pipeline.idea_parser import parse_idea, IdeaToMVFError, HEURISTIC_Q_KEYWORDS
from .pipeline.idea_cli import format_mvf_md

# 10. 启动入口
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
    # Q8 Day2:7 类错误码(4xx + 5xx)
    "ERR_BAD_REQUEST", "ERR_UNKNOWN_ACTION", "ERR_BAD_JSON",
    "ERR_TASK_NOT_FOUND", "ERR_BAD_SIGNATURE",
    "ERR_TASK_EXCEPTION", "ERR_BIND_FAILED", "ERR_INTERNAL",
    "ERR_MESSAGES",
    "ERR_FORMAT_V2",
    "make_error", "make_error_v2",
    # Q8 Day2:异常防护层
    "safe_call_task", "safe_bind", "err_message",
    # Q7 Day2-3 插件
    "register_task", "unregister_task", "get_plugin_tasks",
    "scan_plugins_dir", "discover_entry_points", "clear_plugins",
    # Q10 Day2 安全
    "safe_recv", "set_recv_timeout",
    "compute_plugin_signature", "verify_plugin_signature", "load_manifest",
    "DEFAULT_MAX_RECV", "DEFAULT_ALLOWED_ENTRY_POINT_GROUPS",
    "get_security_logger",
    # Q11 Day2 可观测
    "Counter", "Gauge", "Histogram", "Registry",
    "get_registry", "reset_registry", "dump_metrics",
    "setup_logging", "get_proj_logger",
    # Q12 Day2 部署
    "init_server_start_time", "health_check_handler",
    "check_server", "format_check_result",
    # Q13 Day2 性能
    "memoize_task", "memoize_builtin_tasks",
    # Q14 Day2 协同
    "ClientPool", "ServerEndpoint", "parse_endpoints",
    "call_in_subprocess", "SafeTask",
    "AlertEngine", "get_default_engine", "DEFAULT_THRESHOLDS",
    # Q1 Day2 MVF 模板
    "generate_scaffold", "Scaffold",
    "KNOWN_PROJECTS", "is_known", "get_fills",
    "compare_projects", "compare_all",
    # Q1 Day2 Pipeline A1
    "parse_idea", "IdeaToMVFError", "HEURISTIC_Q_KEYWORDS",
    "format_mvf_md",
]