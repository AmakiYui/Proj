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
import socket
import threading
import socketserver

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from .. import _config as cfg
from .task import Task, get_task


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
    """
    print(f"[{prefix}-{addr[1]}] start", flush=True)
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            msg = data.decode("utf-8", "replace").strip()
            if msg.lower() == "q":
                # Q5 Day4 决定:"q" 是传输层"管道协议",所有 task 共用。
                # 不污染 task 契约(task 保持纯 bytes -> bytes,不背退出信号)。
                conn.sendall(b"bye\n")
                break
            # 这里调 task:把 task 应该处理的字节交给它
            # Q5 Day1 暂用 msg(去掉了"echo: "前缀),保持协议最简
            out = task(data.rstrip(b"\r\n"))
            conn.sendall(out + b"\n")
    finally:
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