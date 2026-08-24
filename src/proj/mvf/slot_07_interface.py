from ._base import Slot


class InterfaceSlot(Slot):
    """Q7 接口 slot — 对外承诺什么。"""
    question = "对外 API 是什么?怎么保证稳定?"
    default_fill = "__all__ + __version__ + pyproject.toml + entry_points + pyi"
    def check(self) -> bool:
        return True