# src/proj/mvf/_base.py
# MVF 所有 slot 的抽象基类

from abc import ABC, abstractmethod


class Slot(ABC):
    """14 问 slot 的根抽象基类。

    每个 slot 都需要回答:
        - 这维度问什么(self.question)
        - 默认填法是什么(self.default_fill)
        - 怎么检查填没填好(self.check)
    """

    question: str = ""
    default_fill: str = ""

    @abstractmethod
    def check(self) -> bool:
        """检查当前填法是否合格(留给子类实现)。"""
        ...

    def describe(self) -> str:
        return f"Q={self.question}\n  default={self.default_fill}\n  filled={type(self).__name__}"