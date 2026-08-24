from ._base import Slot


class OrganizationSlot(Slot):
    """Q4 组织 slot — 代码怎么住。"""
    question = "包怎么分?模块边界在哪?"
    default_fill = "src/<package>/ 包结构 + 单层业务隔离"
    def check(self) -> bool:
        return True