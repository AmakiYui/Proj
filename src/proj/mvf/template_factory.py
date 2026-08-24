# src/proj/mvf/template_factory.py
# ============================================================
# MVF 模板工厂(MVF Day2 之 怎么用)
# ============================================================
# 用法:
#   from src.proj.mvf.template_factory import generate_scaffold
#   scaffold = generate_scaffold("myapp")    # 拿到 14 维空模板
#   scaffold[5].fill(...)                      # 填第 6 个 slot
#   ...
#
# 或 CLI:
#   python -m src.proj.mvf.template_factory --name=myapp --out=./myapp
# ============================================================

import os
import sys
from dataclasses import dataclass, field
from typing import Any

from ._base import Slot


@dataclass
class Scaffold:
    """14 维脚手架 — 14 个 slot 的容器。"""
    name: str
    slots: dict[int, Slot] = field(default_factory=dict)

    def __getitem__(self, q: int) -> Slot:
        return self.slots[q]

    def fill(self, q: int, slot: Slot) -> None:
        """填某个 slot。"""
        self.slots[q] = slot

    def describe(self) -> str:
        """打印所有 slot 的内容。"""
        lines = [f"=== MVF Scaffold: {self.name} ==="]
        for q in sorted(self.slots.keys()):
            slot = self.slots[q]
            lines.append(f"\n--- Q{q} ---")
            lines.append(slot.describe())
        return "\n".join(lines)

    def check_all(self) -> dict[int, bool]:
        """检查所有 slot 是否合格。"""
        return {q: slot.check() for q, slot in self.slots.items()}


def generate_scaffold(name: str = "myapp") -> Scaffold:
    """生成 14 维 scaffold。

    行为:
      - 已知项目(在 known_projects.KNOWN_PROJECTS)直接返回其 14 维填法
      - 未知项目返回 14 个默认 slot(OriginSlot 等)+ 默认 fill
    """
    # 1. 先查已知项目注册表
    from . import known_projects
    if known_projects.is_known(name):
        return Scaffold(name=name, slots=known_projects.get_fills(name))

    # 2. 未知项目:14 个默认 slot
    from . import (
        slot_01_origin, slot_02_design,
        slot_03_runtime, slot_04_organization,
        slot_05_task, slot_06_data, slot_07_interface,
        slot_08_error, slot_09_grow,
        slot_10_security, slot_11_observe,
        slot_12_deploy, slot_13_performance,
        slot_14_coordination,
    )
    pairs = [
        (1, slot_01_origin.OriginSlot()),
        (2, slot_02_design.DesignSlot()),
        (3, slot_03_runtime.RuntimeSlot()),
        (4, slot_04_organization.OrganizationSlot()),
        (5, slot_05_task.TaskSlot()),
        (6, slot_06_data.DataSlot()),
        (7, slot_07_interface.InterfaceSlot()),
        (8, slot_08_error.ErrorSlot()),
        (9, slot_09_grow.GrowSlot()),
        (10, slot_10_security.SecuritySlot()),
        (11, slot_11_observe.ObserveSlot()),
        (12, slot_12_deploy.DeploySlot()),
        (13, slot_13_performance.PerformanceSlot()),
        (14, slot_14_coordination.CoordinationSlot()),
    ]
    return Scaffold(name=name, slots=dict(pairs))


def main():
    """CLI 入口:接受 --name=xxx --out=./dir。"""
    import argparse
    parser = argparse.ArgumentParser(
        prog="mvf-template",
        description="MVF 模板生成器(Q1 Day2)",
    )
    parser.add_argument("--name", default="myapp", help="应用名")
    parser.add_argument("--out", default=None, help="输出目录(默认 stdout 打印)")
    args = parser.parse_args()

    scaffold = generate_scaffold(args.name)
    desc = scaffold.describe()
    if args.out:
        os.makedirs(args.out, exist_ok=True)
        path = os.path.join(args.out, f"{args.name}_mvf.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(desc)
        print(f"scaffold -> {path}", file=sys.stderr)
    else:
        print(desc)


if __name__ == "__main__":
    main()