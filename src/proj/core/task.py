# src/server/core/task.py
# Q5 Day1:把"任务"从 echo 里抽出来,变成可替换的动作单元
#
# 关键设计:
#   Task = bytes -> bytes  (纯函数,不依赖 socket)
#   handle 负责"怎么调度任务"——socket 收字节,丢给 task,发回去
#   task   负责"做什么"——原样返回?转大写?反转?解析协议?都是 task 的事
#
# 解耦之后:
#   handle 不知道在做 echo 还是在做 upper,只知道"接到字节 → 调 task → 发回去"
#   task   不知道数据从 socket 来还是从 stdin 来,只知道"给我 bytes,我给你 bytes"

from typing import Callable


# Task 的最小类型:接收输入字节,产出输出字节
Task = Callable[[bytes], bytes]


def echo_task(data: bytes) -> bytes:
    """Echo 任务:回 'echo: <原文>'。
    这是 echo 协议的语义,放在 task 里,而不是 serve_loop 里——
    让 serve_loop 真的不知道 task 在做什么。
    """
    return b"echo: " + data


def upper_task(data: bytes) -> bytes:
    """Upper 任务:转大写,前缀 'upper: '。"""
    return b"upper: " + data.upper()


def lower_task(data: bytes) -> bytes:
    """Lower 任务:转小写,前缀 'lower: '。"""
    return b"lower: " + data.lower()


def reverse_task(data: bytes) -> bytes:
    """Reverse 任务:反转字节,前缀 'rev: '。"""
    return b"rev: " + data[::-1]


def count_task(data: bytes) -> bytes:
    """Count 任务:统计字节数,前缀 'count: '。"""
    return f"count: {len(data)}".encode("utf-8")


# 内置任务集(Q5 Day2:扩到 5 个)
BUILTIN_TASKS = {
    "echo":    echo_task,
    "upper":   upper_task,
    "lower":   lower_task,
    "reverse": reverse_task,
    "count":   count_task,
}


def get_task(name: str) -> Task:
    """按名字取任务。未知名字 = 默认 echo_task。"""
    return BUILTIN_TASKS.get(name, echo_task)


# ============================================================
# Q5 Day3:从外部 .py 文件动态加载 task
# ============================================================
# 设计要点:
#   1. 不污染 sys.modules(用 importlib.util.spec_from_file_location)
#   2. 校验函数签名确实是 (bytes) -> bytes(duck typing + 显式 hint 检查)
#   3. 失败给明确异常(文件名错 / 函数名错 / 签名错)
#
# 用法:
#   load_task_from_file("./md/my_tasks.py", "my_func")
#
# 用户文件示例(md/my_tasks.py):
#   def my_func(data: bytes) -> bytes:
#       return b"yours: " + data
# ============================================================

import importlib.util
import inspect


def load_task_from_file(file_path: str, func_name: str) -> Task:
    """从任意 .py 文件动态加载 task 函数。

    抛异常:
        FileNotFoundError: 文件不存在
        AttributeError:     文件里没这个函数
        TypeError:          函数签名不是 (bytes) -> bytes
    """
    # 1. 动态加载模块(用唯一 module_name 避免冲突)
    spec = importlib.util.spec_from_file_location(
        f"_user_task_{func_name}",  # 唯一模块名,不让它污染 sys.modules
        file_path,
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"无法加载文件: {file_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # 2. 取函数
    if not hasattr(module, func_name):
        raise AttributeError(
            f"文件 {file_path} 里没有函数 {func_name!r}"
        )
    func = getattr(module, func_name)

    # 3. 签名校验(参数数量必须是 1)
    sig = inspect.signature(func)
    params = list(sig.parameters.values())
    if len(params) != 1:
        raise TypeError(
            f"task 函数必须是 (bytes) -> bytes,实际有 {len(params)} 个参数"
        )
    # 参数类型 hint 是 best effort——不强制要求,duck typing 也行
    return func


# ============================================================
# Q5 Day4:扫描目录自动发现 task
# ============================================================
# 设计要点:
#   1. 不递归(只扫当前目录第一层 *.py)
#   2. 每个 .py 文件里所有签名合规的函数都会被收
#   3. 同名函数后注册覆盖前注册(简单粗暴)
#   4. 文件名 / 函数名 都成为 task 名(用 "文件名::函数名" 避免冲突)
#
# 用户文件示例(md/tasks/greet.py):
#   def hello(data: bytes) -> bytes:
#       return b"hello: " + data
#   def bye(data: bytes) -> bytes:
#       return b"bye: " + data
#
# CLI 调用:
#   --tasks-dir=./md/tasks/  --task=greet::hello
# ============================================================

import os as _os  # 已经在文件里用过 os,这里显式 alias 避免歧义


def scan_tasks_dir(dir_path: str) -> dict[str, Task]:
    """扫描目录下所有 .py,把所有 (bytes) -> bytes 函数收成 task。

    返回: dict[task_name, Task]
    task_name 格式:"文件名::函数名"
    抛异常: FileNotFoundError(目录不存在)
    """
    if not _os.path.isdir(dir_path):
        raise FileNotFoundError(f"目录不存在: {dir_path}")

    found: dict[str, Task] = {}

    for fname in _os.listdir(dir_path):
        if not fname.endswith(".py"):
            continue
        if fname.startswith("_"):
            continue  # 跳过 __init__.py 等
        fpath = _os.path.join(dir_path, fname)
        module_stem = fname[:-3]  # 去 .py

        # 用 importlib 加载模块
        spec = importlib.util.spec_from_file_location(
            f"_scan_{module_stem}", fpath,
        )
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception:
            continue  # 单个文件坏掉不影响其他文件

        # 遍历模块里所有函数,挑出签名合规的
        for name in dir(module):
            if name.startswith("_"):
                continue
            obj = getattr(module, name)
            if not callable(obj):
                continue
            try:
                sig = inspect.signature(obj)
                params = list(sig.parameters.values())
                if len(params) == 1:
                    found[f"{module_stem}::{name}"] = obj
            except (ValueError, TypeError):
                # 有些 callable(builtin)拿不到签名,跳过
                continue

    return found