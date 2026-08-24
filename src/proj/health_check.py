# src/proj/health_check.py
# ============================================================
# Proj 健康检查(Q12 Day2 怎么拆 之 健康)
# ============================================================
# 协议:
#   client 发 "HEALTH\\n" -> server 回 JSON + \\n
#   不污染 task 契约(走 serve_loop 协议层,跟 "q" 同级)
#
# 返回格式:
#   {
#     "status": "ok" | "degraded" | "down",
#     "version": "0.1.0",
#     "uptime_seconds": 123.45,
#     "metrics_snapshot": { ... dump_metrics() ... }
#   }
#
# 设计原则(Q12):
#   - 默认开启(跟 Q10/Q11 默认关闭不同 — 健康检查是部署必要)
#   - 客户端超时 5s,服务端响应 < 100ms
#   - 失败 = down,绝不让 health check 把 server 弄崩
# ============================================================

import os
import sys
import json
import socket
import time

from . import __version__
from .observability import dump_metrics


# ============================================================
# 1. server 端:health_check_handler
# ============================================================

_SERVER_START_TIME: float | None = None


def init_server_start_time() -> None:
    """在 serve_loop 入口调用,记录启动时间。"""
    global _SERVER_START_TIME
    _SERVER_START_TIME = time.time()


def health_check_handler() -> bytes:
    """处理 HEALTH 命令,返回 JSON bytes + 换行。

    用法:serve_loop 在收到 "HEALTH" 时调用本函数,不要直接调用。
    """
    if _SERVER_START_TIME is None:
        init_server_start_time()
    uptime = time.time() - _SERVER_START_TIME

    payload = {
        "status": "ok",
        "version": __version__,
        "uptime_seconds": round(uptime, 3),
        "metrics_snapshot": json.loads(dump_metrics()),
    }
    return (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")


# ============================================================
# 2. client 端:check_server
# ============================================================

def check_server(
    host: str = "127.0.0.1",
    port: int = 8765,
    timeout: float = 5.0,
) -> tuple[bool, dict]:
    """通过 socket 发 HEALTH 命令,验证 server 是否活着。

    返回:
        (ok, payload)
        - ok = True 收到 HEALTH 响应 + 解析成功
        - ok = False 连接失败/超时/解析失败
        - payload: 成功时是 server 返回的 dict,失败时是 {"error": ...}
    """
    try:
        cli = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        cli.settimeout(timeout)
        cli.connect((host, port))
        cli.sendall(b"HEALTH\n")
        # 读一行
        chunks: list[bytes] = []
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
        cli.close()
        raw = b"".join(chunks).strip()
        if not raw:
            return False, {"error": "empty response"}
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as e:
            return False, {"error": f"json decode failed: {e}", "raw": raw.decode("utf-8", "replace")}
        return True, payload
    except (ConnectionRefusedError, socket.timeout, OSError) as e:
        return False, {"error": f"connection failed: {e}"}


# ============================================================
# 3. 命令行格式(format_check_result)
# ============================================================

def format_check_result(ok: bool, payload: dict) -> str:
    """把 check_server 结果格式化成人类可读字符串。"""
    if ok:
        status = payload.get("status", "?")
        version = payload.get("version", "?")
        uptime = payload.get("uptime_seconds", 0)
        return f"[OK] status={status} version={version} uptime={uptime}s"
    return f"[DOWN] {payload.get('error', 'unknown')}"