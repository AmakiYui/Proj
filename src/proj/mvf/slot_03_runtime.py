from ._base import Slot


class RuntimeSlot(Slot):
    """Q3 活着 slot — 怎么跑起来。"""
    question = "进程怎么起来?怎么接收输入?"
    default_fill = "socketserver + 4 种并发风格(simple/thread/pool/pro)"
    def check(self) -> bool:
        return True