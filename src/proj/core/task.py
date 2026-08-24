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


# ============================================================
# Q6 Day2:JSON 协议 task(structured dict 契约)
# ============================================================
# 设计要点:
#   1. 不破坏 Task = bytes -> bytes 老契约(向后兼容)
#   2. 新契约 Task2 = dict -> dict,纯函数
#   3. 输入输出都通过 json.dumps / json.loads 转换
#   4. "q" 协议不在这里(Q5 Day4 已决定留在 serve_loop)
#
# 协议格式(Q6 Day2 默认):
#   请求: {"action": "<task_name>", "text": "<原文>"}
#   响应: {<task_name>: "<结果>"}  例 echo→{"echo": "hi"}
#
# 用法(json mode):
#   1. 客户端发: {"action":"echo","text":"hi"}\n
#   2. server 解析 dict → 调 json_echo_task(dict) → 收 dict
#   3. server 序列化 dict → 发回: {"echo":"hi"}\n
# ============================================================

import json


# Task2:结构化 dict 契约
Task2 = Callable[[dict], dict]


def json_echo_task(data: dict) -> dict:
    """JSON echo:{"action":"echo","text":"hi"} → {"echo":"hi"}"""
    return {"echo": data.get("text", "")}


def json_upper_task(data: dict) -> dict:
    """JSON upper:{"action":"upper","text":"hi"} → {"upper":"HI"}"""
    return {"upper": data.get("text", "").upper()}


def json_reverse_task(data: dict) -> dict:
    """JSON reverse:{"action":"reverse","text":"hi"} → {"reverse":"ih"}"""
    return {"reverse": data.get("text", "")[::-1]}


# JSON 内置任务集
BUILTIN_TASKS_JSON = {
    "echo":    json_echo_task,
    "upper":   json_upper_task,
    "reverse": json_reverse_task,
}


def get_json_task(name: str) -> Task2:
    """按名字取 JSON task。未知名字 = 默认 json_echo_task。"""
    return BUILTIN_TASKS_JSON.get(name, json_echo_task)


def bytes_to_dict(b: bytes) -> dict:
    """bytes → dict(json.loads + utf-8)。"""
    return json.loads(b.decode("utf-8"))


def dict_to_bytes(d: dict) -> bytes:
    """dict → bytes(json.dumps + utf-8)。"""
    return json.dumps(d, ensure_ascii=False).encode("utf-8")


# ============================================================
# Q6 Day3:JSON 请求校验器(最小 schema)
# ============================================================
# 设计要点:
#   1. 返回 (bool, str) 元组,不抛异常(Q6 Day3 决策:优雅路径)
#   2. 校验规则最小化:dict + action(str) + text(str)
#   3. 不在这里校验 action 是否合法(Day4 的话题)
#
# 客户端行为:
#   ok=True  → 继续调 task
#   ok=False → 直接返回 {"error": err_msg}
# ============================================================

def validate_request(
    d: dict,
    allowed_actions: set[str] | None = None,
) -> tuple[bool, str]:
    """校验 JSON 请求格式。

    返回:
        (True, "")        校验通过
        (False, "<reason>") 校验失败 + 错误信息

    规则:
        - d 必须是 dict
        - d["action"] 必须存在且是字符串
        - d["text"]   必须存在且是字符串(可空字符串)
        - d["action"] 必须在 allowed_actions 白名单里(Q6 Day4,可选)

    allowed_actions=None 时不校验 action 是否合法(向后兼容 Day3 行为)。
    """
    if not isinstance(d, dict):
        return False, "request must be a dict"
    if "action" not in d or not isinstance(d["action"], str):
        return False, "request.action must be a string"
    if "text" not in d or not isinstance(d["text"], str):
        return False, "request.text must be a string"
    if allowed_actions is not None and d["action"] not in allowed_actions:
        return False, f"action {d['action']!r} not allowed"
    return True, ""


# Q6 Day4:错误码常量(集中地,避免散落数字)
ERR_BAD_REQUEST = 400    # 协议/schema 错误
ERR_UNKNOWN_ACTION = 404 # action 不在白名单
ERR_BAD_JSON = 400       # json 解析失败(复用 BAD_REQUEST 数字)


# Q7 Day2-2:错误格式版本常量(避免魔法数字,只用于 make_error_v2)
ERR_FORMAT_V2 = 2   # {"error":{"code","message","request_id","timestamp","details"}}


def make_error(code: int, message: str) -> dict:
    """统一错误格式 v1(Q6 Day4 原行为)。

    格式:{"error":{"code":<int>,"message":"<str>"}}

    v2 协议请用 make_error_v2()。
    """
    return {"error": {"code": code, "message": message}}


def make_error_v2(
    code: int,
    message: str,
    *,
    request_id: str | None = None,
    auto_request_id: bool = True,
    timestamp: int | None = None,
    auto_timestamp: bool = True,
    details: dict | None = None,
) -> dict:
    """统一错误格式 v2(Q7 Day2-2 新增)。

    格式:{"error":{"code","message","request_id","timestamp","details"}}

    request_id / timestamp 自动生成规则(Q7 Day2-3 完整 UUID):
        - request_id=None, auto_request_id=True  → 自动生成完整 UUID4(默认)
        - request_id="<str>", auto_request_id=... → 用调用者传的字符串
        - request_id=None, auto_request_id=False  → 不输出该字段

    timestamp 同理:
        - timestamp=None, auto_timestamp=True    → 自动生成当前时间 ms
        - timestamp=<int>, auto_timestamp=...    → 用调用者传的
        - timestamp=None, auto_timestamp=False   → 不输出该字段

    details:可选,None 时不输出。

    参数:
        code:             错误码(用 ERR_* 常量)
        message:          错误描述(给人看的)
        request_id:       请求追踪 ID(None + auto_request_id=True 时自动生成 UUID4)
        auto_request_id:  是否自动生成 request_id(默认 True)
        timestamp:        错误发生时间戳 ms(None + auto_timestamp=True 时自动取当前 ms)
        auto_timestamp:   是否自动生成 timestamp(默认 True)
        details:          附加结构化信息(可选,如 {"field": "action", "expected": "str"})

    返回:
        dict — 直接 dict_to_bytes() 发回客户端即可
    """
    import uuid as _uuid
    import time as _time

    err: dict = {"code": code, "message": message}

    # request_id
    if request_id is not None:
        err["request_id"] = request_id
    elif auto_request_id:
        err["request_id"] = str(_uuid.uuid4())

    # timestamp
    if timestamp is not None:
        err["timestamp"] = timestamp
    elif auto_timestamp:
        err["timestamp"] = int(_time.time() * 1000)

    # details
    if details is not None:
        err["details"] = details

    return {"error": err}