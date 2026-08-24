from ._base import Slot


class DesignSlot(Slot):
    """Q2 设计 slot — 关键架构决策。"""
    question = "关键架构决策?哪些 trade-off?"
    default_fill = "包边界 + 任务契约 + 错误协议(L1/L2/L3 4 层划分)"
    def check(self) -> bool:
        return True