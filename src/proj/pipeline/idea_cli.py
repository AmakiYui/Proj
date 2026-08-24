# src/proj/pipeline/idea_cli.py
# ============================================================
# Pipeline CLI:接受 stdin/--file/--text 输入,生成 MVF.md
# ============================================================

import argparse
import sys
import os

from .idea_parser import parse_idea


def format_mvf_md(app_name: str, slots) -> str:
    """生成 MVF.md 文档。"""
    lines = [
        f"# {app_name} MVF(自动生成)",
        "",
        "> 本文档由 Pipeline idea_to_mvf 启发式生成。",
        "> 用户可在此基础上人工补充、修改。",
        "",
        "## 14 维分析",
        "",
    ]
    for q in range(1, 15):
        slot = slots[q]
        status = "✅ 已填" if slot.check() else "⚠️ 待人工填"
        lines.append(f"### Q{q}:{slot.question}  {status}")
        lines.append("")
        lines.append(f"**填法**:{slot.default_fill}")
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"**生成对象**:`{app_name}`  ")
    lines.append(f"**生成来源**:Pipeline idea_to_mvf 启发式  ")
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        prog="idea-to-mvf",
        description="Pipeline A1:想法 -> MVF.md",
    )
    parser.add_argument("--text", help="直接传文本(单行)")
    parser.add_argument("--file", help="从文件读取")
    parser.add_argument("--name", default="myapp", help="应用名")
    parser.add_argument("--out", help="输出文件(默认 stdout)")
    args = parser.parse_args()

    # 1. 拿文本
    if args.file:
        if not os.path.exists(args.file):
            print(f"file not found: {args.file}", file=sys.stderr)
            sys.exit(2)
        idea = open(args.file, "r", encoding="utf-8").read()
    elif args.text:
        idea = args.text
    elif not sys.stdin.isatty():
        idea = sys.stdin.read()
    else:
        print("用法:--text 或 --file 或 stdin", file=sys.stderr)
        sys.exit(2)

    # 2. parse
    try:
        slots = parse_idea(idea, args.name)
    except Exception as e:
        print(f"parse error: {e}", file=sys.stderr)
        sys.exit(1)

    # 3. 格式化
    md = format_mvf_md(args.name, slots)

    # 4. 输出
    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"MVF -> {args.out}", file=sys.stderr)
    else:
        print(md)


if __name__ == "__main__":
    main()