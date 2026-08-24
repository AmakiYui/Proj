# src/proj/memoize.py
# ============================================================
# Proj Task 缓存包装(Q13 Day2 怎么快 之 缓存)
# ============================================================
# 思路:
#   - 纯函数 task(echo/upper/lower/reverse/count)同输入必同输出
#   - 用 functools.lru_cache 风格的 dict 缓存包装
#   - 跟 Q11 metrics 联动:记 cache_hits / cache_misses
#
# 限制(Q13 边界):
#   - 教学项目,只缓存 bytes 不可变输入(任务契约固定)
#   - 不做 TTL / LRU(只做最简单的 dict cache,够看效果)
#   - 不做分布式缓存(那是 Q14 协同)
#   - 不缓存 JSON task(可变 dict 不适合 hash)
#
# 设计原则:
#   - 装饰器模式(对原 task 函数透明)
#   - 缓存大小可配(默认 128,够教学)
#   - 提供 stats 接口(跟 metrics 联动)
# ============================================================

import functools
from typing import Callable

from .observability import get_registry

# Task 类型别名(跟 task.py 一致)
Task = Callable[[bytes], bytes]


def memoize_task(task: Task, maxsize: int = 128) -> Task:
    """给纯函数 task 加 dict 缓存。

    用法:
        fast_echo = memoize_task(echo_task)
        # 第一次 echo b"hi" 计算,第二次直接命中缓存

    参数:
        task: 原 task 函数(签名 (bytes) -> bytes)
        maxsize: 缓存上限(超出按 dict 替换策略,教学项目不做 LRU)

    返回:
        新 task 函数,签名跟原 task 一致

    Q13 联动:每次调用 inc cache_hits 或 cache_misses
    """
    # Q13 metrics:cache 计数器
    _reg = get_registry()
    _hit = _reg.counter("task_cache_hits_total", "memoized task cache hits")
    _miss = _reg.counter("task_cache_misses_total", "memoized task cache misses")

    cache: dict[bytes, bytes] = {}

    def wrapper(data: bytes) -> bytes:
        if data in cache:
            _hit.inc()
            return cache[data]
        _miss.inc()
        result = task(data)
        # 缓存满了就清空(简单策略,教学项目够用)
        if len(cache) >= maxsize:
            cache.clear()
        cache[data] = result
        return result

    # 保留函数元信息(便于调试)
    functools.update_wrapper(wrapper, task, assigned=("__name__", "__doc__"))
    wrapper.cache = cache  # type: ignore[attr-defined]
    wrapper.cache_hits = lambda: _hit.value  # type: ignore[attr-defined]
    wrapper.cache_misses = lambda: _miss.value  # type: ignore[attr-defined]
    wrapper.cache_size = lambda: len(cache)  # type: ignore[attr-defined]
    return wrapper


def memoize_builtin_tasks(tasks: dict, maxsize: int = 128) -> dict:
    """给内置 task 字典里的所有 task 加缓存。

    用法:
        from src.proj.core.task import BUILTIN_TASKS
        from src.proj.memoize import memoize_builtin_tasks
        fast = memoize_builtin_tasks(BUILTIN_TASKS)
        # fast["echo"]("hi") 走缓存
    """
    return {name: memoize_task(t, maxsize=maxsize) for name, t in tasks.items()}