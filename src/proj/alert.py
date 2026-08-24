# src/proj/alert.py
# ============================================================
# Proj 阈值告警(Q14 Day2 怎么协同 之 alert)
# ============================================================
# 场景:
#   Q11 metrics 收集了,但没人盯着就 = 没看见
#   alert:每 X 秒拉一次 metrics,触发阈值就 WARNING/ERROR
#
# 设计原则(Q14 + Q11 一脉相承):
#   - 阈值可配(默认保守值,教学项目够用)
#   - 触发后去重(同一阈值连续触发只 WARN 一次)
#   - 不引外部依赖,默认只写 logger
#
# 边界:
#   - 不做 alert 持久化(Q14+ 工业:写到 file/redis)
#   - 不做 alert 通道(Q14+:email/slack)
#   - 不做自动恢复(那是 Q14+ 自愈)
# ============================================================

import time
import logging
import threading

from .observability import get_registry, dump_metrics


_logger = logging.getLogger("proj.alert")


# ============================================================
# 1. 默认阈值(教学项目保守值)
# ============================================================

DEFAULT_THRESHOLDS = {
    # counter 名字: 阈值(每秒增量超此值触发)
    "errors_total": 10,
    "client_pool_failures_total": 5,
}


# ============================================================
# 2. AlertEngine(主类)
# ============================================================

class AlertEngine:
    """阈值告警引擎。

    用法:
        engine = AlertEngine()
        engine.check()  # 跑一次
        # 或者后台跑
        engine.start_background(interval_sec=10)

    参数:
        thresholds: {counter_name: per_second_threshold} 字典
    """

    def __init__(self, thresholds: dict[str, int] | None = None):
        self.thresholds = thresholds or DEFAULT_THRESHOLDS.copy()
        self._last_counts: dict[str, int] = {}
        self._firing: set[str] = set()  # 当前正在触发的阈值名
        self._lock = threading.Lock()
        self._bg_thread: threading.Thread | None = None
        self._bg_stop = threading.Event()

    def check(self) -> list[str]:
        """跑一次检查,返回触发的告警名列表。"""
        snap = get_registry().snapshot()
        fired: list[str] = []

        for counter in snap["counters"]:
            name = counter["name"]
            if name not in self.thresholds:
                continue
            current = counter["value"]
            threshold = self.thresholds[name]
            # 取上次差值算速率
            with self._lock:
                last = self._last_counts.get(name, current)
                delta = current - last
                self._last_counts[name] = current
                rate = delta  # 简化:每次 check 算总差(可改 time-based)

            if rate > threshold:
                fired.append(name)
                with self._lock:
                    if name not in self._firing:
                        _logger.warning(
                            "ALERT: %s rate=%d threshold=%d",
                            name, rate, threshold,
                        )
                        self._firing.add(name)
            else:
                with self._lock:
                    self._firing.discard(name)

        return fired

    def start_background(self, interval_sec: float = 10.0) -> None:
        """后台跑 check 循环。"""
        if self._bg_thread is not None and self._bg_thread.is_alive():
            return
        self._bg_stop.clear()
        self._bg_thread = threading.Thread(
            target=self._bg_loop, args=(interval_sec,),
            daemon=True, name="alert-engine",
        )
        self._bg_thread.start()

    def _bg_loop(self, interval_sec: float) -> None:
        while not self._bg_stop.is_set():
            try:
                self.check()
            except Exception as e:
                _logger.error("alert check failed: %s", e)
            self._bg_stop.wait(interval_sec)

    def stop_background(self) -> None:
        """停后台循环。"""
        self._bg_stop.set()
        if self._bg_thread is not None:
            self._bg_thread.join(timeout=2.0)


# ============================================================
# 3. 便捷函数
# ============================================================

_default_engine: AlertEngine | None = None


def get_default_engine() -> AlertEngine:
    """获取默认 alert engine(单例)。"""
    global _default_engine
    if _default_engine is None:
        _default_engine = AlertEngine()
    return _default_engine