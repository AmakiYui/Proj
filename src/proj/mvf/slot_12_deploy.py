from ._base import Slot


class DeploySlot(Slot):
    """Q12 部 slot — 怎么部署。"""
    question = "怎么装?怎么启?怎么查健康?"
    default_fill = "systemd unit + HEALTH 命令 + PROJ_HOST/PORT 环境变量"
    def check(self) -> bool:
        return True