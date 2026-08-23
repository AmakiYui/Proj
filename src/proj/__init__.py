# src/proj 包入口
# ============================================================
# 公共 API(Q4 Day3 暴露规则)
# ============================================================
# 用户用 src.proj 时的稳定接口:
#   from src.proj import main
#   main()         # 启动 CLI,等价于 python -m src.proj.cli
#
# 用户不要用(下划线开头 = 内部):
#   from src.proj import _config     ← 不推荐,包外别碰
#
# 内部模块(从 src.proj 包外别直接 import):
#   src.proj._config                ← 内部常量
#   src.proj.cli                    ← 走 main() 别走 cli.main()
#   src.proj.core.echo_server       ← 业务本体,改时小心
# ============================================================

# 先触发子模块 import(cli 和 echo_server 会拉 _config)
from .cli import main

# 清掉被意外注入到包命名空间的内部模块
# (Python 任何 from .X import Y 都会把 X 注进当前包 namespace)
import src.proj as _pkg
for _name in ("_config", "cli", "core"):
    if hasattr(_pkg, _name):
        delattr(_pkg, _name)
del _pkg, _name

__all__ = ["main"]      # 显式声明公共 API