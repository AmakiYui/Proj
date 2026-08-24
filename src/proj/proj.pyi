# Proj typing stub(Q7 Day2-1)
# ============================================================
# 静态类型契约,给 mypy / pyright / IDE 智能提示用
# 这份文件运行时不会被加载(import proj 不会 .pyi),但 IDE 会读它
# ============================================================
# 维护规则:
#   1. 跟 __init__.py 的 __all__ 保持一一对应
#   2. 内部模块(_config / cli / core.*)也写,IDE 跳转用得到
#   3. 不写实现细节,只写"契约"(类型 + 默认行为 + 抛什么异常)
# ============================================================

from typing import Callable, Final
import logging

# ============================================================
# 版本
# ============================================================

__version__: str

# ============================================================
# 入口
# ============================================================

def main() -> int: ...

# ============================================================
# Q5:Task 契约
# ============================================================
# Task = bytes -> bytes 纯函数契约(Q5 Day1)
# 约束:不依赖 socket、不读 stdin、只用 data 参数

Task: Callable[[bytes], bytes]
Task2: Callable[[dict], dict]

# 内置 task 注册表(Q5 Day2)
BUILTIN_TASKS: dict[str, Task]
BUILTIN_TASKS_JSON: dict[str, Task2]

# 按名查 task(Q5 Day2)
# 默认行为:未知名字回退 echo / json_echo,不抛异常
def get_task(name: str) -> Task: ...
def get_json_task(name: str) -> Task2: ...

# ============================================================
# Q5 Day3-4:外部 task 加载
# ============================================================

def load_task_from_file(file_path: str, func_name: str) -> Task:
    """
    从 .py 文件动态加载 task 函数。

    参数:
        file_path: .py 文件路径
        func_name: 文件里的函数名

    返回:
        Task 函数(签名必须是 (bytes) -> bytes)

    抛出:
        FileNotFoundError: 文件不存在
        AttributeError:     文件里没这个函数
        TypeError:          函数签名不是 (bytes) -> bytes
    """
    ...

def scan_tasks_dir(dir_path: str) -> dict[str, Task]:
    """
    扫描目录下所有 .py 文件,把签名合规的函数收成 task。

    参数:
        dir_path: 目录路径(不递归,只扫第一层 *.py)

    返回:
        dict[task_name, Task],task_name 格式 "文件名::函数名"

    抛出:
        FileNotFoundError: 目录不存在
    """
    ...

# ============================================================
# Q7 Day2-3:插件 API
# ============================================================
# 插件 task 通过 register_task() 注册到全局表,
# 然后用 get_plugin_tasks() 取所有注册项。
# 或者用 scan_plugins_dir() / discover_entry_points() 自动发现。

def register_task(name: str, fn: Task) -> None: ...
def unregister_task(name: str) -> None: ...
def get_plugin_tasks() -> dict[str, Task]: ...
def scan_plugins_dir(dir_path: str) -> list[str]: ...
def discover_entry_points(group: str = ...) -> list[str]: ...
def clear_plugins() -> None: ...

# ============================================================
# Q6 Day4:错误码 + 错误格式构造器
# ============================================================

# 错误码常量(Q6 Day4,集中地,避免散落数字)
ERR_BAD_REQUEST: Final[int]       # 400 - 协议 / schema 错误
ERR_UNKNOWN_ACTION: Final[int]    # 404 - action 不在白名单
ERR_BAD_JSON: Final[int]          # 400 - json 解析失败(复用 BAD_REQUEST 数字)

# 错误格式版本常量(Q7 Day2-2,v1 是默认,不需要常量;只标记 v2)
ERR_FORMAT_V2: Final[int]         # 2 - 加 request_id / timestamp / details

# 统一错误格式构造器(Q7 Day2-2:拆成两个独立函数)
# make_error(code, message) -> v1 固定(向后兼容,Q6 老调用不破)
# make_error_v2(code, message, *, request_id=None, timestamp=None, details=None) -> v2 固定
def make_error(code: int, message: str) -> dict: ...
def make_error_v2(
    code: int,
    message: str,
    *,
    request_id: str | None = ...,
    auto_request_id: bool = ...,
    timestamp: int | None = ...,
    auto_timestamp: bool = ...,
    details: dict | None = ...,
) -> dict: ...

# ============================================================
# 内部模块契约(IDE 跳转用,不在 __all__ 里,用户别直接用)
# ============================================================

# cli 模块暴露 main(),其他都是 argparse 实现细节
# (从 src.proj import cli 已被 Q7 Day1 拦截,但 IDE 跳转会进 cli.py)
from . import cli as _cli  # noqa: F401

# core.echo_server 暴露 4 种并发风格入口
class _StyleRegistry:
    def __getitem__(self, key: str) -> Callable[[str], None]: ...
    def keys(self) -> list[str]: ...

STYLES: _StyleRegistry

def set_current_task(task: Task | Task2) -> None: ...