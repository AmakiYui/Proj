from ._base import Slot


class OriginSlot(Slot):
    """Q1 起源 slot — 为什么有这个软件。"""
    question = "为什么有这个软件?解决什么问题?"
    default_fill = "教学项目:演示 echo 协议 + 14 问方法论"
    def check(self) -> bool:
        return True