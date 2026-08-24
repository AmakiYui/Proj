# benchmark_compare.py (项目根,Q13 Day2 4 风格对比)
# ============================================================
# 自动启 server(pro 风格 + echo task)→ 压测 → 收 report
# 对比:启 server 后立刻压 vs 关 server 后启 memoize 后再压
#
# 用法:
#   python benchmark_compare.py
# 输出:2 轮 JSON 报告,标签 baseline / memoized
# ============================================================

import os
import sys
import time
import json
import subprocess

# 加 src 到 path
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "src"))


# 复用 benchmark.py 的 run_benchmark
sys.path.insert(0, HERE)
from benchmark import run_benchmark


def start_server(port, memoize=False, task="echo"):
    """启 server 子进程,返回 Popen。"""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PROJ_METRICS"] = "1"
    if memoize:
        # memoize 模式:用一个小 wrapper 启动
        # 简单做法:用 --task-file + 一个 memoize 包装的 .py
        # 这里用更简单的:python -c "..." 走 sys.path
        cmd = [
            sys.executable, "-c",
            "import sys; sys.path.insert(0, r'src'); "
            "from proj.core.task import BUILTIN_TASKS; "
            "from proj.memoize import memoize_builtin_tasks; "
            "from proj.core.echo_server import run_pro; "
            "import proj.core.echo_server as es; "
            "es.set_current_task(memoize_builtin_tasks(BUILTIN_TASKS)['echo']); "
            "run_pro('echo')",
        ]
    else:
        cmd = [sys.executable, "-m", "src.proj.cli", "pro", f"--task={task}"]

    return subprocess.Popen(
        cmd, cwd=HERE, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )


def wait_server(host, port, timeout=10.0):
    """等 server 起来。"""
    import socket
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            cli = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            cli.settimeout(0.5)
            cli.connect((host, port))
            cli.close()
            return True
        except (ConnectionRefusedError, socket.timeout, OSError):
            time.sleep(0.2)
    return False


def stop_server(proc):
    """温柔关 server(Windows 用 CTRL_C_EVENT,跟 Q8 Day3 一致)。"""
    import signal
    try:
        if sys.platform == "win32":
            proc.send_signal(signal.CTRL_C_EVENT)
        else:
            proc.send_signal(signal.SIGINT)
        proc.wait(timeout=5)
    except Exception:
        proc.kill()


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--duration", type=float, default=5.0)
    parser.add_argument("--payload-size", type=int, default=64)
    args = parser.parse_args()

    host = "127.0.0.1"
    reports = []

    # 第一轮:baseline
    print(f"[1/2] baseline (no memoize)...", flush=True)
    p1 = start_server(args.port, memoize=False)
    if not wait_server(host, args.port):
        print("server 启动超时", file=sys.stderr)
        p1.kill()
        sys.exit(1)
    rep1 = run_benchmark(host, args.port, args.concurrency, args.duration,
                         args.payload_size, label="baseline")
    reports.append(rep1)
    stop_server(p1)
    time.sleep(1.0)

    # 第二轮:memoize
    print(f"[2/2] memoize... ", flush=True)
    p2 = start_server(args.port, memoize=True)
    if not wait_server(host, args.port):
        print("server 启动超时", file=sys.stderr)
        p2.kill()
        sys.exit(1)
    rep2 = run_benchmark(host, args.port, args.concurrency, args.duration,
                         args.payload_size, label="memoized")
    reports.append(rep2)
    stop_server(p2)

    # 打印 + 对比
    print("\n=== 对比 ===")
    print(json.dumps(reports, indent=2, ensure_ascii=False))

    # 简易加速比
    if rep1["rps"] > 0 and rep2["rps"] > 0:
        speedup = rep2["rps"] / rep1["rps"]
        print(f"\nspeedup: {speedup:.2f}x  ({rep1['rps']:.0f} -> {rep2['rps']:.0f} rps)")


if __name__ == "__main__":
    main()