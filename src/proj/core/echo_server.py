# src/server/core/echo_server.py
# Q5 Day1:把"做什么"和"怎么做"分家
#
# 之前(Q4 Day2):
#   handle_echo 自己写 socket 循环,4 种并发风格各自抄一遍
#   run_pro 里还藏着一份内联的 echo 逻辑(历史包袱)
#
# 现在(Q5 Day1):
#   serve_loop 负责"怎么调度"——socket 收字节,丢给 task,发回去
#   task       负责"做什么"——在 task.py 里,echo_task 是默认实现
#   4 种风格只决定"如何分发新连接给 serve_loop",业务逻辑只剩一份

import os
import sys
import time
import socket
import threading
import socketserver

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from .. import _config as cfg
from ..health_check import init_server_start_time, health_check_handler
from ..observability import get_registry
from ..security import safe_recv, set_recv_timeout
from .task import Task, get_task, safe_call_task, ERR_TASK_EXCEPTION, ERR_INTERNAL
from .task import make_error_v2, err_message, dict_to_bytes


# ============================================================
# 业务本体的两层结构
# ============================================================

def serve_loop(conn, addr, task: Task, prefix: str = "echo") -> None:
    """
    外层调度(原 handle_echo 的 socket 部分)
    - 收字节 → 调 task → 发回去
    - "q" 协议依然在这里(Q5 Day2 再考虑要不要也搬到 task 里)
    - 不知道 task 在做什么,只知道"接到字节 → 给 task"

    Q5 Day4 决定:"q" 留在 serve_loop,理由见下方 __doc__

    Q8 Day2 改造:
        - task 调用走 safe_call_task(task, data),捕获 task 异常
        - 出错不回 OK,改发 ERR_FORMAT_V2 错误响应(dict→bytes)
        - 不 break,连接继续收下一个请求(任务异常≠连接异常)

    Q11 Day2 改造:
        - 每次请求 inc 4 个 metric(连接/请求/错误/延迟)
        - 用 get_registry() 全局共享,关闭则 metric 不增
        - 请求延迟用 Histogram observe(简单分桶)

    Q12 Day2 改造:
        - 加 HEALTH 命令(走协议层,跟 "q" 同级,不污染 task)
        - 启动时 init_server_start_time() 记录 uptime
    """
    print(f"[{prefix}-{addr[1]}] start", flush=True)
    # Q10 Day2:加 socket 超时(防 Slowloris)
    set_recv_timeout(conn, seconds=30.0)
    # Q12 Day2:首次连接时记录 server 启动时间(uptime 起点)
    init_server_start_time()

    # Q11 Day2:拿 4 个 metric 句柄
    _reg = get_registry()
    _conn_total = _reg.counter("connections_total", "total connections accepted")
    _req_total = _reg.counter("requests_total", "total requests handled")
    _err_total = _reg.counter("errors_total", "total error responses sent")
    _active = _reg.gauge("active_connections", "current open connections")
    _latency = _reg.histogram("request_duration_ms", "request processing time")

    _conn_total.inc()
    _active.inc()
    try:
        while True:
            # Q10 Day2:用 safe_recv 代替裸 conn.recv(1024)
            # - 上限 64KB(防内存爆炸)
            # - 返回 None 表示对端关闭/出错
            data = safe_recv(conn)
            if data is None:
                break
            if not data:
                break
            msg = data.decode("utf-8", "replace").strip()
            if msg.lower() == "q":
                # Q5 Day4 决定:"q" 是传输层"管道协议",所有 task 共用。
                # 不污染 task 契约(task 保持纯 bytes -> bytes,不背退出信号)。
                conn.sendall(b"bye\n")
                break
            if msg.upper() == "HEALTH":
                # Q12 Day2:健康检查协议,跟 "q" 同一层级
                conn.sendall(health_check_handler())
                continue  # HEALTH 不算请求,不动 metrics
            # Q8 Day2:用 safe_call_task 包 task 调用
            # 返回 (out_bytes, error_code):成功 (out, 0),失败 ("", 5xx)
            # Q11 Day2:加延迟统计
            _t0 = time.perf_counter()
            out, code = safe_call_task(task, data.rstrip(b"\r\n"))
            _latency.observe((time.perf_counter() - _t0) * 1000.0)
            _req_total.inc()
            if code == 0:
                conn.sendall(out + b"\n")
            else:
                # 5xx 系列 → 发 ERR_FORMAT_V2 错误响应,不杀连接
                # Q8 Day2 修复:用 err_message(code, name) 精确查,避免 5xx 同 code 互覆盖
                err_msg = err_message(code)
                err_resp = make_error_v2(code, err_msg)
                conn.sendall(dict_to_bytes(err_resp) + b"\n")
                _err_total.inc()
    finally:
        _active.dec()
        conn.close()
        print(f"[{prefix}-{addr[1]}] closed", flush=True)


# ============================================================
# 4 种并发风格:同样的 serve_loop,4 种"如何把新连接喂给 serve_loop"
# ============================================================

def run_simple(task_name: str = "echo"):
    """#4 串行 socket —— 一个一个处理"""
    task = _resolve_task(task_name)
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((cfg.HOST, cfg.PORT))
    srv.listen(5)
    print(f"[server] listening on {cfg.HOST}:{cfg.PORT} (simple)", flush=True)
    try:
        while True:
            conn, addr = srv.accept()
            serve_loop(conn, addr, task, prefix="simple")
    except KeyboardInterrupt:
        print("\n[server] Ctrl+C -> shutdown", flush=True)
    finally:
        srv.close()


def run_thread(task_name: str = "echo"):
    """#5 手搓多线程 —— 每连接一个 daemon 线程"""
    task = _resolve_task(task_name)

    def handle(conn, addr):
        serve_loop(conn, addr, task, prefix="thread")

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((cfg.HOST, cfg.PORT))
    srv.listen(5)
    print(f"[server] listening on {cfg.HOST}:{cfg.PORT} (threading)", flush=True)
    try:
        while True:
            conn, addr = srv.accept()
            t = threading.Thread(target=handle, args=(conn, addr), daemon=True)
            t.start()
    except KeyboardInterrupt:
        print("\n[server] Ctrl+C -> shutdown", flush=True)
    finally:
        srv.close()


class _EchoHandler(socketserver.BaseRequestHandler):
    """ThreadingMixIn 用到的 handler 类(私有)"""
    def handle(self):
        task = _resolve_task(self.server.task_name)
        serve_loop(self.request, self.client_address, task, prefix="pool")


def run_pool(task_name: str = "echo"):
    """#6 标准库 ThreadingMixIn"""
    class ThreadedServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
        daemon_threads = True
        allow_reuse_address = True

    ThreadedServer.task_name = task_name
    with ThreadedServer((cfg.HOST, cfg.PORT), _EchoHandler) as srv:
        print(f"[server] listening on {cfg.HOST}:{cfg.PORT} (ThreadingMixIn)", flush=True)
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print("\n[server] Ctrl+C -> shutdown", flush=True)


def run_pro(task_name: str = "echo"):
    """#7-11 终极版:守护进程 + PID 文件 + 日志 + 信号
    Q5 Day1 改造:删掉内联的 echo 逻辑,改用 serve_loop + task。
    Q5 Day2 改造:接 task_name 参数。
    """
    import atexit
    import logging
    from logging.handlers import RotatingFileHandler

    os.makedirs(cfg._VAR_DIR, exist_ok=True)

    # PID 文件
    with open(cfg.PID_FILE, "w") as f:
        f.write(str(os.getpid()))
    atexit.register(lambda: os.path.exists(cfg.PID_FILE) and os.remove(cfg.PID_FILE))

    # 日志
    logger = logging.getLogger("server_pro")
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(threadName)s] %(message)s")
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    fh = RotatingFileHandler(
        cfg.LOG_FILE,
        maxBytes=cfg.LOG_MAX_BYTES,
        backupCount=cfg.LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    fh.setFormatter(fmt)
    logger.addHandler(sh)
    logger.addHandler(fh)
    logger.info(f"server_pro 启动 PID={os.getpid()} task={task_name}")

    task = _resolve_task(task_name)

    def logged_serve(conn, addr):
        """薄薄一层,只加日志,业务全交给 serve_loop"""
        prefix = f"pro-{addr[1]}"
        logger.info(f"{prefix} start")
        try:
            serve_loop(conn, addr, task, prefix=prefix)
        finally:
            logger.info(f"{prefix} closed")

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((cfg.HOST, cfg.PORT))
    srv.listen(5)
    logger.info(f"listening on {cfg.HOST}:{cfg.PORT}")
    try:
        while True:
            conn, addr = srv.accept()
            t = threading.Thread(target=logged_serve, args=(conn, addr), daemon=True)
            t.start()
    except KeyboardInterrupt:
        logger.info("Ctrl+C shutdown")
    finally:
        srv.close()


# ============================================================
# 统一入口(给 cli.py 用)
# ============================================================

STYLES = {
    "simple": run_simple,
    "thread": run_thread,
    "pool":   run_pool,
    "pro":    run_pro,
}


# Q5 Day3:支持外部 task 注入
# cli 在调 run_X 之前,先把 task 函数 set 进来,run_X 从这里取
_CURRENT_TASK: Task | None = None


def set_current_task(task: Task) -> None:
    """cli 用:把外部 task 函数注入到 echo_server"""
    global _CURRENT_TASK
    _CURRENT_TASK = task


def _resolve_task(task_name: str) -> Task:
    """优先用注入的 task,否则回退到内置 get_task"""
    if _CURRENT_TASK is not None:
        return _CURRENT_TASK
    return get_task(task_name)