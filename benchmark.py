# benchmark.py (项目根,Q13 Day2 性能基准工具)
# ============================================================
# Proj 性能基准(Q13 Day2 怎么快 之 测)
# ============================================================
# 跑法:
#   1. 启 server:python -m src.proj.cli pro --task=echo
#   2. 跑压测:python benchmark.py --host=127.0.0.1 --port=8765 \
#              --concurrency=10 --duration=10
#   3. 看报告(JSON 到 stdout)
#
# 不做的事(Q13 边界):
#   - 不做分布式压测(Q14 协同)
#   - 不做 CPU profile(教学项目够用就行)
#   - 不做内存快照(留 Q14 工业级)
# ============================================================

import os
import sys
import json
import time
import socket
import argparse
import threading
import statistics

# 加 src 到 path
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "src"))


def worker(host, port, duration, payload, results, idx, barrier):
    """单线程 worker,跑 duration 秒,统计请求数和延迟。

    results[idx] = {"sent": int, "errors": int, "latencies_ms": list[float]}
    """
    latencies: list[float] = []
    sent = 0
    errors = 0
    deadline = time.monotonic() + duration
    barrier.wait()  # 等所有 worker 一起开始

    while time.monotonic() < deadline:
        cli = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cli.settimeout(5.0)
        try:
            cli.connect((host, port))
            t0 = time.perf_counter()
            cli.sendall(payload)
            # 读直到 newline
            chunks = []
            while True:
                try:
                    chunk = cli.recv(4096)
                except socket.timeout:
                    break
                if not chunk:
                    break
                chunks.append(chunk)
                if b"\n" in chunk:
                    break
            if chunks:
                latencies.append((time.perf_counter() - t0) * 1000.0)
                sent += 1
            else:
                errors += 1
        except (ConnectionRefusedError, socket.timeout, OSError):
            errors += 1
        finally:
            cli.close()
    results[idx] = {"sent": sent, "errors": errors, "latencies_ms": latencies}


def run_benchmark(host, port, concurrency, duration, payload_size, label):
    """跑一轮基准,返回报告 dict。"""
    payload = b"x" * payload_size + b"\n"
    results: list = [None] * concurrency
    barrier = threading.Barrier(concurrency)

    threads = []
    t_start_setup = time.perf_counter()
    for i in range(concurrency):
        t = threading.Thread(
            target=worker,
            args=(host, port, duration, payload, results, i, barrier),
            daemon=True,
        )
        t.start()
        threads.append(t)
    for t in threads:
        t.join(timeout=duration + 10)
    t_end = time.perf_counter()

    # 汇总
    total_sent = sum(r["sent"] for r in results if r)
    total_errors = sum(r["errors"] for r in results if r)
    all_latencies: list[float] = []
    for r in results:
        if r:
            all_latencies.extend(r["latencies_ms"])

    if all_latencies:
        all_latencies.sort()
        p50 = all_latencies[len(all_latencies) // 2]
        p95 = all_latencies[int(len(all_latencies) * 0.95)]
        p99 = all_latencies[int(len(all_latencies) * 0.99)]
        avg = statistics.mean(all_latencies)
        mx = max(all_latencies)
        mn = min(all_latencies)
    else:
        p50 = p95 = p99 = avg = mx = mn = 0.0

    actual_duration = t_end - t_start_setup
    rps = total_sent / actual_duration if actual_duration > 0 else 0

    return {
        "label": label,
        "concurrency": concurrency,
        "duration_sec": round(actual_duration, 3),
        "payload_size": payload_size,
        "total_requests": total_sent,
        "total_errors": total_errors,
        "rps": round(rps, 2),
        "latency_ms": {
            "avg": round(avg, 3),
            "min": round(mn, 3),
            "max": round(mx, 3),
            "p50": round(p50, 3),
            "p95": round(p95, 3),
            "p99": round(p99, 3),
        },
    }


def main():
    parser = argparse.ArgumentParser(
        prog="benchmark",
        description="Proj 性能基准(Q13 Day2)",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--duration", type=float, default=10.0, help="压测时长(秒)")
    parser.add_argument("--payload-size", type=int, default=64, help="请求字节数")
    parser.add_argument("--label", default="default", help="本轮标签")
    parser.add_argument("--warmup", type=float, default=1.0, help="预热时间(秒)")
    args = parser.parse_args()

    # 预热(防首次连接开销污染数据)
    if args.warmup > 0:
        time.sleep(args.warmup)

    report = run_benchmark(
        args.host, args.port, args.concurrency,
        args.duration, args.payload_size, args.label,
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()