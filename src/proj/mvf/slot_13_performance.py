from ._base import Slot


class PerformanceSlot(Slot):
    """Q13 性 slot — 怎么快。"""
    question = "怎么测?怎么找瓶颈?怎么改?"
    default_fill = "benchmark.py + memoize + Histogram 复用"
    def check(self) -> bool:
        return True