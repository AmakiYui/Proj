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
    ERR_TASK_NOT_FOUND, ERR_BAD_SIGNATURE, err_message, make_error_v2,
)
from .health_check import check_server, format_check_result
from .client_pool import ClientPool, parse_endpoints
from . import __version__  # Q9 Day3: --version 参数需要
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
        epilog=f"当前版本: proj {__version__}",
    )
    # Q9 Day3: 标准 --version(Q9 演:版本可发现)
    parser.add_argument(
        "--version",
        action="version",
        version=f"proj {__version__}",
    )
    # Q12 Day2:健康检查模式(子进程检查 server 是否活着)
    parser.add_argument(
        "--health-check",
        action="store_true",
        help="Q12:对运行中的 server 发 HEALTH 命令,退出码 0=健康 / 1=down",
    )
    # Q12 Day2:host/port 覆盖(默认从环境变量 PROJ_HOST/PROJ_PORT)
    parser.add_argument(
        "--host", default=None,
        help="Q12:server host(默认 127.0.0.1,可用 PROJ_HOST 环境变量)",
    )
    parser.add_argument(
        "--port", type=int, default=None,
        help="Q12:server port(默认 8765,可用 PROJ_PORT 环境变量)",
    )
    # Q14 Day2:多 host 模式(客户端走 client pool)
    parser.add_argument(
        "--hosts", default=None,
        help="Q14:多 server 地址列表,逗号分隔如 'h1:p1,h2:p2',走 client pool",
    )
    parser.add_argument(
        "--client-message", default=None,
        help="Q14:--hosts 模式下发的内容(默认发 'hello from pool')",
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

    # Q12 Day2:健康检查分支(短路径,直接 exit)
    if args.health_check:
        from . import _config as cfg
        host = args.host or os.environ.get("PROJ_HOST") or cfg.HOST
        port = args.port or int(os.environ.get("PROJ_PORT", "0")) or cfg.PORT
        ok, payload = check_server(host=host, port=port, timeout=5.0)
        print(format_check_result(ok, payload), flush=True)
        return 0 if ok else 1

    # Q14 Day2:client pool 模式(短路径)
    if args.hosts:
        endpoints = parse_endpoints(args.hosts)
        pool = ClientPool(endpoints)
        msg = (args.client_message or "hello from pool").encode("utf-8") + b"\n"
        try:
            resp = pool.send(msg)
            print(f"[pool] -> {resp.decode('utf-8', 'replace').strip()}", flush=True)
            print(f"[pool] endpoints: {pool.alive_endpoints()}", flush=True)
            return 0
        except ConnectionError as e:
            print(f"[pool] FAILED: {e}", flush=True)
            return 1

    # Q12 Day2:host/port 环境变量覆盖(Q12 部 怎么部署)
    # 服务端启动时读取 PROJ_HOST/PROJ_PORT,_config 默认值兜底
    if args.host or os.environ.get("PROJ_HOST"):
        from . import _config as cfg
        cfg.HOST = args.host or os.environ["PROJ_HOST"]
    if args.port or os.environ.get("PROJ_PORT"):
        from . import _config as cfg
        try:
            cfg.PORT = args.port or int(os.environ["PROJ_PORT"])
        except ValueError:
            parser.error(f"invalid PROJ_PORT: {os.environ['PROJ_PORT']}")

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
        # Q8 Day2:文件 / 函数不存在给统一错误码,不再让进程崩
        try:
            task = load_task_from_file(args.task_file, args.task_name)
        except FileNotFoundError as e:
            err = make_error_v2(ERR_TASK_NOT_FOUND, err_message(ERR_TASK_NOT_FOUND, "TASK_NOT_FOUND"),
                                details={"file": args.task_file, "hint": "check --task-file path"})
            print(f"[cli] ERR {err}", flush=True)
            return 1
        except AttributeError as e:
            err = make_error_v2(ERR_TASK_NOT_FOUND, err_message(ERR_TASK_NOT_FOUND, "TASK_NOT_FOUND"),
                                details={"file": args.task_file, "func": args.task_name,
                                         "hint": "check --task-name spelling"})
            print(f"[cli] ERR {err}", flush=True)
            return 1
        except TypeError as e:
            # 签名不对(参数数量不对)
            err = make_error_v2(ERR_BAD_SIGNATURE, err_message(ERR_BAD_SIGNATURE, "BAD_SIGNATURE"),
                                details={"file": args.task_file, "func": args.task_name,
                                         "expected": "(bytes) -> bytes",
                                         "reason": str(e)})
            print(f"[cli] ERR {err}", flush=True)
            return 1
        task_label = f"{args.task_file}::{args.task_name}"
        set_current_task(task)
    elif args.tasks_dir:
        # Q8 Day2:目录不存在给统一错误码
        try:
            scanned = scan_tasks_dir(args.tasks_dir)
        except FileNotFoundError as e:
            err = make_error_v2(ERR_TASK_NOT_FOUND, err_message(ERR_TASK_NOT_FOUND, "TASK_NOT_FOUND"),
                                details={"dir": args.tasks_dir, "hint": "check --tasks-dir path"})
            print(f"[cli] ERR {err}", flush=True)
            return 1
        if args.task not in scanned:
            # Q8 Day2:已知 task 不在扫描结果里,统一错误码
            err = make_error_v2(ERR_TASK_NOT_FOUND, err_message(ERR_TASK_NOT_FOUND, "TASK_NOT_FOUND"),
                                details={"requested": args.task,
                                         "available": list(scanned.keys())[:10],
                                         "hint": "use --task=<file>::<func>"})
            print(f"[cli] ERR {err}", flush=True)
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