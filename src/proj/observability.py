# src/proj/observability.py
# ============================================================
# Proj 可观测模块(Q11 Day2 怎么看见)
# ============================================================
# 4 类产出:
#   1. Counter  -> 只能递增的计数(连接数 / 请求数 / 错误数)
#   2. Gauge    -> 可增可减的瞬时值(活跃连接数 / 延迟)
#   3. Registry -> 指标容器(全局单例)
#   4. dump_metrics() -> 导出 JSON 快照
#
# 设计原则(Q10 一脉相承):
#   - 默认关闭,显式开启(环境变量 PROJ_METRICS=1)
#   - 进程内存储(教学项目,不开外部端口)
#   - 线程安全(threading.Lock)
#   - 失败不抛错(Q8 / Q10 三态处理原则)
#
# 不做的事(Q11 边界):
#   - 不做 Prometheus exporter(Q11+ 工业级)
#   - 不做分布式 trace(Q14 协同范畴)
#   - 不做 alert(那是 Q14 协同)
#   - 不做 dashboard(那是可视化工具,教学项目不展开)
# ============================================================

import os
import json
import time
import threading
import logging

# ============================================================
# 1. 默认 logger(name = "proj.observability")
# ============================================================
_logger = logging.getLogger("proj.observability")


def get_logger() -> logging.Logger:
    return _logger


# ============================================================
# 2. Counter(只能递增)
# ============================================================

class Counter:
    """线程安全的计数器。

    用法:
        c = Counter("requests_total")
        c.inc()                # +1
        c.inc(amount=5)        # +5
        c.value                # 当前值
    """

    def __init__(self, name: str, help_text: str = ""):
        self.name = name
        self.help = help_text
        self._value = 0
        self._lock = threading.Lock()

    def inc(self, amount: int = 1) -> None:
        if amount < 0:
            return  # Counter 不能减,负值静默忽略
        with self._lock:
            self._value += amount

    @property
    def value(self) -> int:
        with self._lock:
            return self._value

    def snapshot(self) -> dict:
        return {
            "type": "counter",
            "name": self.name,
            "help": self.help,
            "value": self.value,
        }


# ============================================================
# 3. Gauge(可增可减)
# ============================================================

class Gauge:
    """线程安全的瞬时值。

    用法:
        g = Gauge("active_connections")
        g.inc()                # +1
        g.dec()                # -1
        g.set(42)              # 直接设
        g.value                # 当前值
    """

    def __init__(self, name: str, help_text: str = ""):
        self.name = name
        self.help = help_text
        self._value = 0
        self._lock = threading.Lock()

    def inc(self, amount: int = 1) -> None:
        with self._lock:
            self._value += amount

    def dec(self, amount: int = 1) -> None:
        with self._lock:
            self._value -= amount

    def set(self, value: int) -> None:
        with self._lock:
            self._value = value

    @property
    def value(self) -> int:
        with self._lock:
            return self._value

    def snapshot(self) -> dict:
        return {
            "type": "gauge",
            "name": self.name,
            "help": self.help,
            "value": self.value,
        }


# ============================================================
# 4. Histogram(简化版,固定桶的延迟统计)
# ============================================================
# Q11 决定:不做全功能 Histogram(分位数计算复杂)
# 简化版 = 一组 Gauge,记录 "<1ms" "<10ms" "<100ms" "<1s" ">=1s"
# 适用:看分布,不看精确 P99

_BUCKET_BOUNDS_MS = (1, 10, 100, 1000)


class Histogram:
    """简化版直方图,固定桶(1ms / 10ms / 100ms / 1s / +Inf)。

    用法:
        h = Histogram("request_duration_ms")
        h.observe(5.2)         # 5.2ms -> <10ms 桶
        h.observe(1500)        # 1500ms -> >=1s 桶
    """

    def __init__(self, name: str, help_text: str = ""):
        self.name = name
        self.help = help_text
        # 桶:label -> 计数
        self._buckets: dict[str, int] = {
            f"le_{b}ms": 0 for b in _BUCKET_BOUNDS_MS
        }
        self._buckets["le_inf"] = 0
        self._count = 0
        self._sum = 0.0
        self._lock = threading.Lock()

    def observe(self, value_ms: float) -> None:
        with self._lock:
            self._count += 1
            self._sum += value_ms
            placed = False
            for b in _BUCKET_BOUNDS_MS:
                if value_ms <= b:
                    self._buckets[f"le_{b}ms"] += 1
                    placed = True
                    break
            if not placed:
                self._buckets["le_inf"] += 1

    @property
    def count(self) -> int:
        with self._lock:
            return self._count

    @property
    def sum_ms(self) -> float:
        with self._lock:
            return self._sum

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "type": "histogram",
                "name": self.name,
                "help": self.help,
                "count": self._count,
                "sum_ms": round(self._sum, 3),
                "buckets": dict(self._buckets),
            }


# ============================================================
# 5. Registry(全局容器)
# ============================================================

class Registry:
    """指标注册表,全局单例。

    用法:
        r = get_registry()
        r.counter("requests_total").inc()
        r.gauge("active_conn").set(3)
    """

    def __init__(self):
        self._counters: dict[str, Counter] = {}
        self._gauges: dict[str, Gauge] = {}
        self._histograms: dict[str, Histogram] = {}
        self._lock = threading.Lock()
        self._enabled = self._check_enabled()

    @staticmethod
    def _check_enabled() -> bool:
        """检查 PROJ_METRICS 环境变量。Q11 决定:默认关闭。"""
        return os.environ.get("PROJ_METRICS", "").lower() in ("1", "true", "yes", "on")

    @property
    def enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, value: bool) -> None:
        """运行时切换(测试用)。"""
        with self._lock:
            self._enabled = value

    def counter(self, name: str, help_text: str = "") -> Counter:
        with self._lock:
            if name not in self._counters:
                self._counters[name] = Counter(name, help_text)
            return self._counters[name]

    def gauge(self, name: str, help_text: str = "") -> Gauge:
        with self._lock:
            if name not in self._gauges:
                self._gauges[name] = Gauge(name, help_text)
            return self._gauges[name]

    def histogram(self, name: str, help_text: str = "") -> Histogram:
        with self._lock:
            if name not in self._histograms:
                self._histograms[name] = Histogram(name, help_text)
            return self._histograms[name]

    def snapshot(self) -> dict:
        """导出当前所有指标的快照。"""
        with self._lock:
            return {
                "enabled": self._enabled,
                "timestamp": time.time(),
                "counters": [c.snapshot() for c in self._counters.values()],
                "gauges": [g.snapshot() for g in self._gauges.values()],
                "histograms": [h.snapshot() for h in self._histograms.values()],
            }

    def dump_json(self) -> str:
        """导出 JSON 字符串(便于打印/落盘)。"""
        return json.dumps(self.snapshot(), indent=2, ensure_ascii=False)

    def reset(self) -> None:
        """清空所有指标(测试用)。"""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()


_REGISTRY: Registry | None = None
_REGISTRY_LOCK = threading.Lock()


def get_registry() -> Registry:
    """获取全局 Registry(线程安全单例)。"""
    global _REGISTRY
    if _REGISTRY is None:
        with _REGISTRY_LOCK:
            if _REGISTRY is None:
                _REGISTRY = Registry()
    return _REGISTRY


def reset_registry() -> None:
    """重置全局 Registry(测试用)。"""
    global _REGISTRY
    _REGISTRY = None


def dump_metrics() -> str:
    """便捷函数:dump 当前所有指标的 JSON。"""
    return get_registry().dump_json()