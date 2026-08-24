# md/mvf_describe.py
# 用 MVF 打印某个 scaffold 的全 14 维

import os
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

import argparse
from proj.mvf._base import Slot


def make_slot(q, question, fill):
    class _S(Slot):
        def __init__(self, q=q, qu=question, f=fill):
            self.question = qu
            self.default_fill = f
        def check(self):
            return True
    return _S()


# Proj 的 14 维(基于 Q3-Q14 收官后)
PROJ = {
    1: ("为什么有这个软件?解决什么问题?", "教学项目:演示 echo 协议 + 14 问方法论"),
    2: ("关键架构决策?哪些 trade-off?", "包边界 + 任务契约 + 错误协议(L1/L2/L3 4 层划分)"),
    3: ("进程怎么起来?怎么接收输入?", "socketserver + 4 种并发风格(simple/thread/pool/pro)"),
    4: ("包怎么分?模块边界在哪?", "src/proj 包结构 + 单层业务隔离"),
    5: ("任务的最小契约是什么?输入输出?", "Task = bytes -> bytes(纯函数,可缓存)"),
    6: ("数据在内存/磁盘/线上是什么形态?", "bytes 主体 + Task2 dict 升级(schema 校验 + 错误码)"),
    7: ("对外 API 是什么?怎么保证稳定?", "__all__ + __version__ + pyproject.toml + entry_points + pyi"),
    8: ("错误怎么分类?怎么响?怎么恢复?", "7 类 ERR_xxx 错误码 + safe_call_task + safe_bind"),
    9: ("怎么打包?怎么分发?怎么升级?", "wheel + sdist + pyproject + CHANGELOG + README + --version"),
    10: ("谁能调?谁能改?谁能发?", "safe_recv + HMAC 插件签名 + entry_point 白名单"),
    11: ("运行时指标?日志?告警?", "Counter/Gauge/Histogram + setup_logging + dump_metrics"),
    12: ("怎么装?怎么启?怎么查健康?", "systemd unit + HEALTH 命令 + PROJ_HOST/PORT 环境变量"),
    13: ("怎么测?怎么找瓶颈?怎么改?", "benchmark.py + memoize + Histogram 复用"),
    14: ("多机怎么通信?怎么分流?怎么隔离?", "ClientPool + SafeTask + AlertEngine + multiprocessing"),
}


def describe(name, fills):
    print(f"\n=== {name}:14 维 MVF 分析 ===\n")
    for q in range(1, 15):
        q_text, fill = fills[q]
        print(f"--- Q{q} ---")
        print(f"  Q: {q_text}")
        print(f"  Fill: {fill}")
        print()
    print(f"=== 总结 ===")
    print(f"  {name} 14 维全部填了具体实现,跨项目可以共用同一套框架")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("name", nargs="?", default="Proj")
    args = parser.parse_args()
    if args.name == "Proj":
        describe("Proj", PROJ)
    else:
        # 其他项目先用 Proj 当 fallback
        describe(args.name, PROJ)