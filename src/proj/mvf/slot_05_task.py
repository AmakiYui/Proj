from ._base import Slot


class TaskSlot(Slot):
    """Q5 任务 slot — 做什么动作。"""
    question = "任务的最小契约是什么?输入输出?"
    default_fill = "Task = bytes -> bytes(纯函数,可缓存)"
    def check(self) -> bool:
        return True