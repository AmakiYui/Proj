from ._base import Slot


class DataSlot(Slot):
    """Q6 数据 slot — 数据什么形态。"""
    question = "数据在内存/磁盘/线上是什么形态?"
    default_fill = "bytes 主体 + Task2 dict 升级(schema 校验 + 错误码)"
    def check(self) -> bool:
        return True