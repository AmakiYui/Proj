# src/proj/process_pool.py
# ============================================================
# Proj Task 子进程隔离执行(Q14 Day2 怎么协同 之 进程隔离)
# ============================================================
# 场景:
#   Q10 防的是"恶意输入",但 task 代码本身如果被植入,会污染整个进程
#   隔离:每个 task 调用 fork() / subprocess 起 worker 跑
#   worker 死了不影响 server 主进程
#
# 设计选择(Q14):
#   - 用 multiprocessing.Process(不引 subprocess.Q14)
#   - worker 进程跑 task,返回结果给 server
#   - 简单:1 task = 1 worker(教学项目,不做 worker 池)
#   - 进程间用 multiprocessing.Queue 通信
#
# 边界(Q14):
#   - 不做 sandbox(那是 Q14+ 工业:chroot/seccomp)
#   - 不做 resource limit(那是 Q14+ 工业:rlimit/cgroup)
#   - 只做"挂了不影响主进程"这一层
# ============================================================

import os
import sys
import time
import multiprocessing


# ============================================================
# 1. _worker(子进程函数,跑 task)
# ============================================================

def _worker(task_fn, data: bytes, q: multiprocessing.Queue) -> None:
    """子进程入口:跑 task,把结果 / 异常塞进 Queue。"""
    try:
        result = task_fn(data)
        q.put(("ok", result))
    except Exception as e:
        q.put(("err", repr(e)))


def call_in_subprocess(
    task_fn,
    data: bytes,
    timeout: float = 5.0,
) -> bytes:
    """在子进程里跑 task_fn(data),返回结果 bytes。

    抛:
        TimeoutError: 超时(worker 被强制 kill)
        RuntimeError: worker 内部异常(异常消息带回)
    """
    q = multiprocessing.Queue()
    p = multiprocessing.Process(
        target=_worker, args=(task_fn, data, q), daemon=True,
    )
    p.start()
    p.join(timeout=timeout)
    if p.is_alive():
        # 超时:kill worker
        p.terminate()
        p.join(timeout=1.0)
        if p.is_alive():
            p.kill()  # Windows 上 terminate 偶尔不响应
            p.join()
        raise TimeoutError(f"task 子进程超时({timeout}s)")
    # 收结果
    try:
        kind, payload = q.get_nowait()
    except Exception:
        raise RuntimeError("worker 没返回结果")
    if kind == "ok":
        return payload
    raise RuntimeError(f"worker 内部异常: {payload}")


# ============================================================
# 2. SafeTask(包装类,把 task 装饰成"跑在子进程")
# ============================================================

class SafeTask:
    """包装 task,每次调用走 subprocess 隔离。

    用法:
        safe = SafeTask(echo_task)
        out = safe(b"hi")   # 实际在子进程里跑 echo_task

    Q14 联动:每次调用计 task_subprocess_calls_total
    """

    def __init__(self, task_fn, timeout: float = 5.0):
        self._fn = task_fn
        self._timeout = timeout
        self._name = getattr(task_fn, "__name__", "anonymous")

    def __call__(self, data: bytes) -> bytes:
        return call_in_subprocess(self._fn, data, self._timeout)

    def __repr__(self) -> str:
        return f"<SafeTask {self._name} timeout={self._timeout}s>"