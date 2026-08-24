from ._base import Slot


class CoordinationSlot(Slot):
    """Q14 协 slot — 怎么协同。"""
    question = "多机怎么通信?怎么分流?怎么隔离?"
    default_fill = "ClientPool + SafeTask + AlertEngine + multiprocessing"
    def check(self) -> bool:
        return True