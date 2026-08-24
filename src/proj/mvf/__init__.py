# src/proj/mvf/__init__.py
# ============================================================
# MVF(Minimum Viable Framework)模板骨架
# ============================================================
# 14 问 14 维 = 14 个 slot,每个项目填自己的内容。
#
# 用法:
#   from src.proj.mvf import slot_03_runtime, slot_14_coordination
#   # 继承抽象基类,实现你的具体 slot
#
#   class MyRuntime(slot_03_runtime.RuntimeSlot):
#       def boot(self): ...
#       def listen(self): ...
#
# 设计原则(MVF):
#   - ABC 抽象,不规定具体实现
#   - 每个 slot 都有"默认填法"(Q3-Q14 已沉淀的 Proj 模式)
#   - template_factory 一键生成新项目骨架
# ============================================================

from . import slot_01_origin
from . import slot_02_design
from . import slot_03_runtime
from . import slot_04_organization
from . import slot_05_task
from . import slot_06_data
from . import slot_07_interface
from . import slot_08_error
from . import slot_09_grow
from . import slot_10_security
from . import slot_11_observe
from . import slot_12_deploy
from . import slot_13_performance
from . import slot_14_coordination

__all__ = [
    "slot_01_origin", "slot_02_design",
    "slot_03_runtime", "slot_04_organization",
    "slot_05_task", "slot_06_data", "slot_07_interface",
    "slot_08_error", "slot_09_grow",
    "slot_10_security", "slot_11_observe",
    "slot_12_deploy", "slot_13_performance",
    "slot_14_coordination",
]