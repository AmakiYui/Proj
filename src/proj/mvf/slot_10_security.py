from ._base import Slot


class SecuritySlot(Slot):
    """Q10 安 slot — 谁都能干什么。"""
    question = "谁能调?谁能改?谁能发?"
    default_fill = "safe_recv + HMAC 插件签名 + entry_point 白名单"
    def check(self) -> bool:
        return True