# src/proj/cli.py
# Q4 Day2:统一启动入口
# Q5 Day2:加 --task 参数
# Q5 Day3:加 --task-file / --task-name(单文件加载)
# Q5 Day4:加 --tasks-dir(目录扫描模式)
#
# 用法:python -m src.proj.cli [simple|thread|pool|pro] \
#       [--task=<name> | --task-file=<path> --task-name=<func> | --tasks-dir=<dir>]
# 不带参数 = 打印菜单

import os
import sys
import argparse

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from .core.echo_server import STYLES, set_current_task
from .core.task import (
    BUILTIN_TASKS, load_task_from_file, scan_tasks_dir, get_task,
    BUILTIN_TASKS_JSON, get_json_task, Task2,
)
import logging

# Q6 Day3 补 logger(Q11 观提前介入):记录协议错误
_logger = logging.getLogger("proj.cli.json")
# 确保 logger 有 handler(没 basicConfig 时 WARNING 默认丢)
if not _logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("[%(name)s] %(levelname)s: %(message)s"))
    _logger.addHandler(_h)
    _logger.setLevel(logging.WARNING)


def main():
    parser = argparse.ArgumentParser(
        prog="src.proj.cli",
        description="Proj 统一 server 启动入口(Q5 Day4:支持 --tasks-dir)",
    )
    parser.add_argument(
        "style",
        nargs="?",
        choices=list(STYLES.keys()) + ["menu"],
        default="menu",
        help="server 并发风格(默认 menu 打印菜单)",
    )
    parser.add_argument(
        "--task",
        default="",   # 空 = 用户没指定,后续默认 echo
        help="任务类型(默认 echo);在 --tasks-dir 模式下格式为 '文件名::函数名'",
    )
    # Q5 Day3
    parser.add_argument(
        "--task-file", default=None,
        help="外部 task .py 文件路径(配合 --task-name)",
    )
    parser.add_argument(
        "--task-name", default=None,
        help="外部 task 函数名(--task-file 模式下必填)",
    )
    # Q5 Day4
    parser.add_argument(
        "--tasks-dir", default=None,
        help="扫描目录下的所有 .py 作为 task(--task 填 '文件名::函数名')",
    )
    # Q6 Day2:数据格式(bytes 旧 / json 新)
    parser.add_argument(
        "--data-format", default="bytes",
        choices=["bytes", "json"],
        help="数据格式(bytes 老 / json 结构化新,默认 bytes)",
    )
    args = parser.parse_args()

    # --task-file 和 --tasks-dir 互斥(--task 在两者模式下都用来指定具体 task 名)
    if args.task_file and args.tasks_dir:
        parser.error("--task-file 和 --tasks-dir 互斥")
    if args.tasks_dir and not args.task:
        parser.error("--tasks-dir 模式下必须 --task=<file>::<func>")

    if args.task_file and not args.task_name:
        parser.error("--task-file 必须配合 --task-name")

    if args.style == "menu":
        print("=" * 60)
        print("  Proj server 启动菜单(Q5 Day4)")
        print("=" * 60)
        for k, fn in STYLES.items():
            label = {
                "simple": "串行 socket",
                "thread": "手搓多线程",
                "pool":   "ThreadingMixIn",
                "pro":    "终极版(PID+日志)",
            }[k]
            print(f"  [{k:7}] {label}")
        print()
        print("  任务模式:")
        print("    内置:   --task=echo | upper | lower | reverse | count")
        print("    单文件: --task-file=<path> --task-name=<func>")
        print("    目录:   --tasks-dir=<dir>  (--task=<file>::<func>)")
        print("=" * 60)
        return 0

    # 解析最终 task
    if args.task_file:
        task = load_task_from_file(args.task_file, args.task_name)
        task_label = f"{args.task_file}::{args.task_name}"
        set_current_task(task)
    elif args.tasks_dir:
        scanned = scan_tasks_dir(args.tasks_dir)
        if args.task not in scanned:
            print(f"[cli] --tasks-dir={args.tasks_dir} 下没找到 task '{args.task}'")
            print(f"[cli] 可用的: {list(scanned.keys())}")
            return 1
        task = scanned[args.task]
        task_label = args.task
        set_current_task(task)
    elif args.data_format == "json":
        # Q6 Day2:JSON 模式——把 dict→dict task 包成 bytes→bytes
        # Q6 Day3:加 schema 校验 + logger
        # Q6 Day4:加 action 白名单 + 错误码字段
        from .core.task import (
            bytes_to_dict, dict_to_bytes, validate_request,
            make_error, ERR_BAD_REQUEST, ERR_UNKNOWN_ACTION,
        )
        json_inner = get_json_task(args.task or "echo")
        # Q6 Day4:用 BUILTIN_TASKS_JSON.keys() 当白名单
        allowed = set(BUILTIN_TASKS_JSON.keys())

        def json_wrapper(data: bytes) -> bytes:
            try:
                d = bytes_to_dict(data)
            except Exception as e:
                _logger.warning(f"json decode failed: {e}  raw={data!r}")
                return dict_to_bytes(make_error(ERR_BAD_REQUEST, f"json decode failed: {e}"))
            ok, err = validate_request(d, allowed_actions=allowed)
            if not ok:
                _logger.warning(f"validate failed: {err}  req={d}")
                # Q6 Day4:区分 400(BAD_REQUEST) vs 404(UNKNOWN_ACTION)
                code = ERR_UNKNOWN_ACTION if "not allowed" in err else ERR_BAD_REQUEST
                return dict_to_bytes(make_error(code, err))
            result = json_inner(d)
            return dict_to_bytes(result)

        task = json_wrapper
        task_label = f"json:{args.task or 'echo'}"
        set_current_task(task)
    else:
        task_label = args.task or "echo"  # 没指定 = 默认 echo
        # 内置 bytes task 不用注入,_resolve_task 会回退到 get_task

    print(f"[cli] 启动风格: {args.style}  task: {task_label}", flush=True)
    STYLES[args.style](args.task or "echo")
    return 0


if __name__ == "__main__":
    sys.exit(main())