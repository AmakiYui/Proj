# src/proj/client_pool.py
# ============================================================
# Proj 多 server 客户端池(Q14 Day2 怎么协同 之 客户端层)
# ============================================================
# 场景:
#   多个 Proj server(可能不同机器、不同端口)同时跑
#   客户端不再写死 host:port,而是给一个列表
#   内部轮询(round-robin)/最少连接/随机 三种策略
#
# 跟 Q12 health_check 集成:
#   - 每个 server 启动前可先 HEALTH 检查
#   - 失败标记 dead 跳过,下次轮询再试
#   - 连续 N 次失败 = 永久移除(留 Q14+ 工业级:动态加回)
#
# 设计原则(Q14):
#   - 透明替换 socket 客户端调用方
#   - 失败转移:server A 挂了自动切 B
#   - 不引入外部依赖(纯 stdlib)
# ============================================================

import os
import socket
import random
import threading
import time
from dataclasses import dataclass, field
from typing import Iterable

from .observability import get_registry


# ============================================================
# 1. ServerEndpoint(地址 + 状态)
# ============================================================

@dataclass
class ServerEndpoint:
    host: str
    port: int
    fail_count: int = 0
    last_fail_time: float = 0.0
    alive: bool = True

    def addr(self) -> tuple[str, int]:
        return (self.host, self.port)

    def __repr__(self) -> str:
        flag = "alive" if self.alive else "DEAD"
        return f"<{self.host}:{self.port} {flag} fails={self.fail_count}>"


# ============================================================
# 2. 负载均衡策略
# ============================================================

Strategy = str  # "round-robin" | "random" | "least-fail"


# ============================================================
# 3. ClientPool(主类)
# ============================================================

class ClientPool:
    """多 server 客户端池。

    用法:
        pool = ClientPool(["127.0.0.1:8765", "127.0.0.1:8766"])
        data = pool.send(b"hello")

    参数:
        endpoints: ["host:port", "host:port"] 列表
        strategy: "round-robin"(默认)/ "random" / "least-fail"
        timeout: 单次连接超时(秒),默认 5
        max_fails: 连续失败 N 次标记 dead,默认 3
    """

    def __init__(
        self,
        endpoints: Iterable[str],
        strategy: Strategy = "round-robin",
        timeout: float = 5.0,
        max_fails: int = 3,
    ):
        self._endpoints: list[ServerEndpoint] = []
        for ep in endpoints:
            host, port = self._parse(ep)
            self._endpoints.append(ServerEndpoint(host=host, port=port))
        if not self._endpoints:
            raise ValueError("endpoints 不能为空")
        self._strategy = strategy
        self._timeout = timeout
        self._max_fails = max_fails
        self._lock = threading.Lock()
        self._rr_index = 0  # round-robin 游标

        # Q14 metrics
        _reg = get_registry()
        self._req_total = _reg.counter("client_pool_requests_total", "client pool total requests")
        self._fail_total = _reg.counter("client_pool_failures_total", "client pool total failures")
        self._switch_total = _reg.counter("client_pool_switches_total", "client pool failover switches")

    @staticmethod
    def _parse(addr: str) -> tuple[str, int]:
        if ":" not in addr:
            raise ValueError(f"无效地址格式: {addr}(应为 host:port)")
        host, port_s = addr.rsplit(":", 1)
        return host, int(port_s)

    @property
    def endpoints(self) -> list[ServerEndpoint]:
        return list(self._endpoints)

    def alive_endpoints(self) -> list[ServerEndpoint]:
        return [e for e in self._endpoints if e.alive]

    def _pick(self) -> ServerEndpoint | None:
        """按 strategy 选一个 endpoint。alive=False 跳过。"""
        alive = self.alive_endpoints()
        if not alive:
            return None
        if self._strategy == "random":
            return random.choice(alive)
        if self._strategy == "least-fail":
            return min(alive, key=lambda e: e.fail_count)
        # default: round-robin
        with self._lock:
            ep = alive[self._rr_index % len(alive)]
            self._rr_index += 1
            return ep

    def _mark_fail(self, ep: ServerEndpoint) -> None:
        ep.fail_count += 1
        ep.last_fail_time = time.time()
        if ep.fail_count >= self._max_fails:
            ep.alive = False

    def _mark_ok(self, ep: ServerEndpoint) -> None:
        ep.fail_count = 0

    def send(self, data: bytes, expect_newline: bool = True) -> bytes:
        """发数据到某个 alive server,收响应。

        返回 bytes。
        抛 ConnectionError:所有 server 都不可用。
        """
        self._req_total.inc()
        last_err: Exception | None = None
        tried = set()
        # 最多试 len(alive) 次,失败切下一个
        for _ in range(len(self.alive_endpoints())):
            ep = self._pick()
            if ep is None or id(ep) in tried:
                break
            tried.add(id(ep))
            try:
                cli = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                cli.settimeout(self._timeout)
                cli.connect(ep.addr())
                cli.sendall(data)
                chunks: list[bytes] = []
                while True:
                    try:
                        chunk = cli.recv(4096)
                    except socket.timeout:
                        break
                    if not chunk:
                        break
                    chunks.append(chunk)
                    if expect_newline and b"\n" in chunk:
                        break
                cli.close()
                if chunks:
                    self._mark_ok(ep)
                    return b"".join(chunks)
                last_err = ConnectionError(f"{ep} 返回空")
            except (ConnectionRefusedError, socket.timeout, OSError) as e:
                last_err = e
                self._mark_fail(ep)
                self._switch_total.inc()
                continue
        # 所有 server 都失败
        self._fail_total.inc()
        raise ConnectionError(f"所有 server 都失败: {last_err}")

    def health_check_all(self, timeout: float = 2.0) -> dict[str, str]:
        """对所有 endpoint 发 HEALTH,返回 {addr: status}。"""
        from .health_check import check_server
        result: dict[str, str] = {}
        for ep in self._endpoints:
            ok, payload = check_server(ep.host, ep.port, timeout=timeout)
            result[f"{ep.host}:{ep.port}"] = payload.get("status", "down") if ok else "down"
        return result


def parse_endpoints(s: str) -> list[str]:
    """CLI helper:解析 "h1:p1,h2:p2" 或 "h1:p1 h2:p2" 为 ["["1:p1", "h2:p2"]."""
    if not s:
        return []
    # 先按逗号分,再按空白分
    parts = s.replace(",", " ").split()
    return [p for p in parts if p]