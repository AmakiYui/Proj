from ._base import Slot


class ErrorSlot(Slot):
    """Q8 错 slot — 出错怎么办。"""
    question = "错误怎么分类?怎么响?怎么恢复?"
    default_fill = "7 类 ERR_xxx 错误码 + safe_call_task + safe_bind"
    def check(self) -> bool:
        return True