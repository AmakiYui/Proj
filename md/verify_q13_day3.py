# md/verify_q13_day3.py
# Q13 Day3 端到端验证矩阵
# ============================================================
# 跑 4 类性能功能,确认 Q13 Day2 落地没漏
#   1. memoize_task 基础 + 缓存命中
#   2. memoize_builtin_tasks 全量包装
#   3. benchmark.run_benchmark 端到端(用 mock server)
#   4. __all__ 完整性
# ============================================================

import os
import sys
import json
import socket
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

os.environ["PROJ_METRICS"] = "1"

import proj  # noqa
from proj import memoize_task, memoize_builtin_tasks
from proj.core.task import echo_task, BUILTIN_TASKS
from proj.observability import dump_metrics

# 引入 benchmark.py 的 run_benchmark
sys.path.insert(0, ROOT)
from benchmark import run_benchmark

passed = 0
failed = 0


def check(name, ok, detail=""):
    global passed, failed
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {name}", flush=True)
    if detail and not ok:
        print(f"         {detail}", flush=True)
    if ok:
        passed += 1
    else:
        failed += 1


# ============================================================
# 1. memoize_task 基础
# ============================================================
print("\n=== 1. memoize_task 基础 ===", flush=True)

fast = memoize_task(echo_task)
r1 = fast(b"hi")
check("首次调用返回正确", r1 == b"echo: hi")
check("首次 miss", fast.cache_misses() == 1)
check("首次 hit=0", fast.cache_hits() == 0)

r2 = fast(b"hi")
check("二次调用同输入返回同结果", r2 == r1)
check("二次 hit=1", fast.cache_hits() == 1)

r3 = fast(b"bye")
check("不同输入走 miss", fast.cache_misses() == 2)

# 函数元信息保留
check("__name__ 保留", fast.__name__ == "echo_task")
check("cache 属性", hasattr(fast, "cache"))


# ============================================================
# 2. memoize_builtin_tasks 全量
# ============================================================
print("\n=== 2. memoize_builtin_tasks ===", flush=True)

fast_all = memoize_builtin_tasks(BUILTIN_TASKS)
check("返回 dict", isinstance(fast_all, dict))
check("包含 5 个 task", len(fast_all) == 5)
check("键名一致", set(fast_all.keys()) == set(BUILTIN_TASKS.keys()))

# 调用 5 个 task 各一次
for name in fast_all:
    out = fast_all[name](b"test")
    assert isinstance(out, bytes), f"{name} should return bytes"


# ============================================================
# 3. benchmark 端到端(mock server)
# ============================================================
print("\n=== 3. benchmark 端到端 ===", flush=True)

# 启一个最简单的 server(收 1 byte 回 echo)
srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind(("127.0.0.1", 0))
port = srv.getsockname()[1]
srv.listen(50)


def _echo_serve():
    while True:
        try:
            conn, _ = srv.accept()
            data = conn.recv(4096)
            if data:
                # 简单 echo + 换行
                conn.sendall(b"echo:" + data.lstrip(b"x").rstrip(b"\n") + b"\n")
            conn.close()
        except OSError:
            return


t = threading.Thread(target=_echo_serve, daemon=True)
t.start()
time.sleep(0.1)

# 小压测(2 worker / 2 秒 / payload 16 byte)
report = run_benchmark(
    host="127.0.0.1", port=port,
    concurrency=2, duration=2.0,
    payload_size=16, label="verify",
)
check("报告含 label", report.get("label") == "verify")
check("报告含 concurrency", report.get("concurrency") == 2)
check("报告含 rps", isinstance(report.get("rps"), (int, float)))
check("rps > 0", report.get("rps", 0) > 0, f"rps={report.get('rps')}")
check("total_requests > 0", report.get("total_requests", 0) > 0)
check("latency 含 6 字段", len(report["latency_ms"]) == 6)
check("p50 < p95 < p99",
      report["latency_ms"]["p50"] <= report["latency_ms"]["p95"] <= report["latency_ms"]["p99"])

srv.close()


# ============================================================
# 4. metrics 联动(cache_hits/misses 进 snapshot)
# ============================================================
print("\n=== 4. metrics 联动 ===", flush=True)

# 再触发几次缓存
for _ in range(3):
    fast(b"trigger")
dump = dump_metrics()
parsed = json.loads(dump)
counter_names = {c["name"] for c in parsed["counters"]}
check("metrics 含 task_cache_hits_total", "task_cache_hits_total" in counter_names)
check("metrics 含 task_cache_misses_total", "task_cache_misses_total" in counter_names)


# ============================================================
# 5. __all__ 完整性
# ============================================================
print("\n=== 5. __all__ 完整性 ===", flush=True)

expected = {"memoize_task", "memoize_builtin_tasks"}
actual = set(proj.__all__)
missing = expected - actual
check("__all__ 含 Q13 全部 2 项", not missing, f"missing={missing}")
check("__all__ 共 >=54 项", len(proj.__all__) >= 54, f"got {len(proj.__all__)}")


# ============================================================
# 总结
# ============================================================
print(f"\n=== 总结 ===", flush=True)
print(f"PASS: {passed}", flush=True)
print(f"FAIL: {failed}", flush=True)
sys.exit(0 if failed == 0 else 1)