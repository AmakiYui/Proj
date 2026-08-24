from ._base import Slot


class ObserveSlot(Slot):
    """Q11 观 slot — 怎么看见。"""
    question = "运行时指标?日志?告警?"
    default_fill = "Counter/Gauge/Histogram + setup_logging + dump_metrics"
    def check(self) -> bool:
        return True