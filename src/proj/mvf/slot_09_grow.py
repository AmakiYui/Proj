from ._base import Slot


class GrowSlot(Slot):
    """Q9 演 slot — 怎么长大。"""
    question = "怎么打包?怎么分发?怎么升级?"
    default_fill = "wheel + sdist + pyproject + CHANGELOG + README + --version"
    def check(self) -> bool:
        return True