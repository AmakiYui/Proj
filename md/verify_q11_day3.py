# md/verify_q11_day3.py
# Q11 Day3 端到端验证矩阵
# ============================================================
# 跑 5 类可观测功能,确认 Q11 Day2 落地没漏
#   1. Counter / Gauge / Histogram 基础操作
#   2. Registry 全局共享 + dump JSON
#   3. PROJ_METRICS 环境变量切换启用
#   4. setup_logging 幂等 + 不重复加 handler
#   5. __all__ 完整性
# ============================================================

import os
import sys
import json
import logging
import threading

# 路径设置
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

# 启用 metrics(Q11 默认关闭)
os.environ["PROJ_METRICS"] = "1"

import proj  # noqa
from proj import (
    Counter, Gauge, Histogram, Registry,
    get_registry, reset_registry, dump_metrics,
    setup_logging, get_proj_logger,
)

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
# 1. Counter / Gauge / Histogram 基础操作
# ============================================================
print("\n=== 1. Counter / Gauge / Histogram 基础 ===", flush=True)

reset_registry()
reg = get_registry()

# 1.1 Counter
c = reg.counter("test_counter", "test")
check("Counter 初始 0", c.value == 0)
c.inc()
check("Counter inc() +1", c.value == 1)
c.inc(amount=5)
check("Counter inc(5)", c.value == 6)
c.inc(amount=-1)
check("Counter 负值静默", c.value == 6)

# 1.2 Gauge
g = reg.gauge("test_gauge", "test")
check("Gauge 初始 0", g.value == 0)
g.inc()
check("Gauge inc() +1", g.value == 1)
g.dec(amount=2)
check("Gauge dec(2) -2", g.value == -1)
g.set(42)
check("Gauge set(42)", g.value == 42)

# 1.3 Histogram
h = reg.histogram("test_hist", "test")
h.observe(0.5)     # < 1ms
h.observe(5.0)     # < 10ms
h.observe(50.0)    # < 100ms
h.observe(500.0)   # < 1000ms
h.observe(5000.0)  # >= 1s (le_inf)
snap = h.snapshot()
check("Histogram count=5", snap["count"] == 5)
check("Histogram 5 桶均有值", all(v > 0 for v in snap["buckets"].values()))


# ============================================================
# 2. Registry 全局共享 + dump JSON
# ============================================================
print("\n=== 2. Registry 全局 + dump ===", flush=True)

reset_registry()
reg1 = get_registry()
reg2 = get_registry()
check("Registry 单例", reg1 is reg2, "reg1 is reg2")

c1 = reg1.counter("shared_counter")
c1.inc()
c2 = reg2.counter("shared_counter")
check("Counter 全局共享", c2.value == 1, f"c2.value={c2.value}")

# dump JSON
dump = dump_metrics()
parsed = json.loads(dump)
check("dump 是合法 JSON", "counters" in parsed and "gauges" in parsed)
check("dump 含 enabled/timestamp", "enabled" in parsed and "timestamp" in parsed)
check("dump enabled=True", parsed["enabled"] is True)


# ============================================================
# 3. PROJ_METRICS 环境变量切换
# ============================================================
print("\n=== 3. PROJ_METRICS 切换 ===", flush=True)

# 3.1 不设环境变量 = 默认关闭
os.environ.pop("PROJ_METRICS", None)
reset_registry()
r_off = Registry()
check("默认 metrics 关闭", r_off.enabled is False)

# 3.2 设环境变量 = 开启
os.environ["PROJ_METRICS"] = "1"
reset_registry()
r_on = Registry()
check("PROJ_METRICS=1 开启", r_on.enabled is True)

# 3.3 真值集合
for v in ("true", "yes", "on"):
    os.environ["PROJ_METRICS"] = v
    reset_registry()
    r = Registry()
    check(f"PROJ_METRICS={v} 开启", r.enabled is True, f"v={v}")


# ============================================================
# 4. setup_logging 幂等
# ============================================================
print("\n=== 4. setup_logging 幂等 ===", flush=True)

# 4.1 setup 1 次
setup_logging()
proj_logger = logging.getLogger("proj")
n1 = len(proj_logger.handlers)
check("setup_logging 1 次有 handler", n1 > 0, f"handlers={n1}")

# 4.2 setup 多次 = 不重复加 handler
setup_logging()
setup_logging()
setup_logging()
n2 = len(proj_logger.handlers)
check("setup_logging 幂等", n1 == n2, f"before={n1}, after={n2}")

# 4.3 get_proj_logger 正确加前缀
lg = get_proj_logger("core.task")
check("get_proj_logger 加 proj. 前缀", lg.name == "proj.core.task", f"got {lg.name}")


# ============================================================
# 5. __all__ 完整性
# ============================================================
print("\n=== 5. __all__ 完整性 ===", flush=True)

expected = {
    "Counter", "Gauge", "Histogram", "Registry",
    "get_registry", "reset_registry", "dump_metrics",
    "setup_logging", "get_proj_logger",
}
actual = set(proj.__all__)
missing = expected - actual
check("__all__ 含 Q11 全部 9 项", not missing, f"missing={missing}")
check("__all__ 共 >=48 项", len(proj.__all__) >= 48, f"got {len(proj.__all__)}")


# ============================================================
# 总结
# ============================================================
print(f"\n=== 总结 ===", flush=True)
print(f"PASS: {passed}", flush=True)
print(f"FAIL: {failed}", flush=True)
sys.exit(0 if failed == 0 else 1)