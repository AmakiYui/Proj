# src/proj/mvf/compare.py
# ============================================================
# MVF 跨项目对照工具
# ============================================================
# 用法:
#   from proj.mvf.compare import compare_projects
#   print(compare_projects(['Proj', 'OpenClaw'], q=5))
#
# CLI:
#   python -m src.proj.mvf.compare --projects=Proj,OpenClaw --q=5
# ============================================================

import sys
from typing import Iterable

from .template_factory import generate_scaffold


def compare_projects(projects: Iterable[str], q: int) -> str:
    """对比若干项目在 Q 维度下的填法。"""
    lines = [f"=== Q{q} 跨项目对照 ==="]
    for name in projects:
        sc = generate_scaffold(name)
        slot = sc[q]
        lines.append(f"\n--- {name} ---")
        lines.append(f"  Q: {slot.question}")
        lines.append(f"  Fill: {slot.default_fill}")
    return "\n".join(lines)


def compare_all(projects: Iterable[str]) -> str:
    """对比若干项目在所有 14 维度的填法。"""
    names = list(projects)
    scaffolds = {n: generate_scaffold(n) for n in names}
    out = [f"=== 跨项目 14 维对照: {' vs '.join(names)} ===\n"]
    for q in range(1, 15):
        out.append(f"\n--- Q{q} ---")
        out.append(f"  Q: {scaffolds[names[0]][q].question}")
        for n in names:
            out.append(f"\n  [{n}]:")
            out.append(f"    {scaffolds[n][q].default_fill}")
    return "\n".join(out)


def main():
    import argparse
    parser = argparse.ArgumentParser(prog="mvf-compare")
    parser.add_argument("--projects", required=True, help="逗号分隔的项目名")
    parser.add_argument("--q", type=int, default=None, help="只看某个 Q(默认全 14 维)")
    args = parser.parse_args()

    projects = args.projects.split(",")
    if args.q:
        print(compare_projects(projects, args.q))
    else:
        print(compare_all(projects))


if __name__ == "__main__":
    main()