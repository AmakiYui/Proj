# verify_q8_day3.py
# Q8 Day3 端到端测试矩阵:覆盖 Q8 Day1 列的 10 个出错点
#
# 用 subprocess 启 server,客户端 tcp 连,跑各种"出错的输入"看响应。
# 验证策略:
#   - 退出码 0 = 通过
#   - 收到正确错误格式 = 通过
#   - server 不崩 = 通过

import os
import sys
import json
import socket
import subprocess
import time

PROJ_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(PROJ_ROOT, 'src'))

from proj import (
    ERR_BAD_REQUEST, ERR_UNKNOWN_ACTION, ERR_BAD_JSON,
    ERR_TASK_NOT_FOUND, ERR_BAD_SIGNATURE,
    ERR_TASK_EXCEPTION, ERR_BIND_FAILED, ERR_INTERNAL,
    safe_bind, safe_call_task,
)

results = []
def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    results.append((status, name, detail))


def recv_line(sock, timeout=2):
    """收一行(以 \n 结尾)。"""
    sock.settimeout(timeout)
    buf = b""
    try:
        while True:
            ch = sock.recv(1)
            if not ch:
                break
            buf += ch
            if ch == b"\n":
                break
    except socket.timeout:
        pass
    return buf


def start_server(*args, port=9876, env_extra=None):
    """启 server subprocess。"""
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.join(PROJ_ROOT, "src")
    if env_extra:
        env.update(env_extra)
    full = [sys.executable, "-m", "proj.cli", "simple", "--task=echo"] + list(args)
    # 改端口(避免跟默认 8765 冲突)
    # 简单做法:不起 server,直接调 cli 函数测
    return subprocess.Popen(
        full,
        cwd=PROJ_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        # 改 PYTHONUNBUFFERED 避免中文 stdout 缓存
    )


# ============================================================
# Case 1: serve_loop socket 断 / data 空(client 主动关)
# ============================================================
# 启 server,client 连上不发数据直接关,看 server 是否不崩 + 关闭连接
def test_case1_socket_close():
    """启 server,client 连上不发数据就 close,server 应优雅关闭。"""
    proc = start_server()
    time.sleep(1)
    try:
        s = socket.socket()
        s.connect(('127.0.0.1', 8765))
        s.close()  # 立即关
        time.sleep(0.5)
        # 检查进程还在
        check("Case1: server 不崩(socket close 后进程仍 alive)", proc.poll() is None,
              f"poll={proc.poll()}")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()


# ============================================================
# Case 2: bytes_to_dict JSON 解码失败(非 JSON 输入)
# ============================================================
def test_case2_bad_json():
    """client 发 'not json',json_wrapper 返回 400。"""
    proc = start_server("--data-format=json")
    time.sleep(1)
    try:
        s = socket.socket()
        s.connect(('127.0.0.1', 8765))
        s.sendall(b"not json at all\n")
        resp = recv_line(s, timeout=2)
        try:
            d = json.loads(resp)
            check("Case2: JSON 解码失败 → ERR_BAD_REQUEST(400)",
                  d.get("error", {}).get("code") == ERR_BAD_REQUEST,
                  f"resp={resp!r}")
        except Exception as e:
            check("Case2: JSON 解码失败", False, f"无法解析: {resp!r}")
        s.close()
    finally:
        proc.terminate()
        try: proc.wait(timeout=2)
        except: proc.kill()


# ============================================================
# Case 3: validate_request 校验失败(action 不是 str)
# ============================================================
def test_case3_validate_fail():
    """client 发 {action:42, text:'x'},validate 返回 400。"""
    proc = start_server("--data-format=json")
    time.sleep(1)
    try:
        s = socket.socket()
        s.connect(('127.0.0.1', 8765))
        s.sendall(b'{"action":42,"text":"x"}\n')
        resp = recv_line(s, timeout=2)
        try:
            d = json.loads(resp)
            check("Case3: 校验失败 → ERR_BAD_REQUEST(400)",
                  d.get("error", {}).get("code") == ERR_BAD_REQUEST,
                  f"resp={resp!r}")
        except Exception:
            check("Case3: 校验失败", False, f"无法解析: {resp!r}")
        s.close()
    finally:
        proc.terminate()
        try: proc.wait(timeout=2)
        except: proc.kill()


# ============================================================
# Case 4: get_task 找不到(bytes task)
# ============================================================
# Q5 Day2 设计:未知 task 走 echo_task(不报错)
# Q8 Day3 测:确认这是 graceful degradation
def test_case4_unknown_bytes_task():
    """--task=notexist 走 echo 兜底,不崩。"""
    proc = start_server("--task=notexist")
    time.sleep(1)
    try:
        s = socket.socket()
        s.connect(('127.0.0.1', 8765))
        s.sendall(b"hi\n")
        resp = recv_line(s, timeout=2)
        # 应该是 echo_task 输出 b"echo: hi"
        check("Case4: 未知 bytes task → echo 兜底",
              resp == b"echo: hi\n", f"resp={resp!r}")
        s.close()
    finally:
        proc.terminate()
        try: proc.wait(timeout=2)
        except: proc.kill()


# ============================================================
# Case 5: load_task_from_file 文件不存在 → ERR_TASK_NOT_FOUND
# (Q8 Day2 已测,这里只确认 subprocess 形式)
# ============================================================
def test_case5_file_not_found():
    """--task-file=nonexist.py 应该 exit 1 + ERR_TASK_NOT_FOUND。"""
    proc = start_server("--task-file=nonexistent_zzz.py", "--task-name=fn")
    proc.wait(timeout=3)
    out = proc.stdout.read().decode('utf-8', errors='replace')
    # Q8 Day3 修复:Python dict 输出用单引号,匹配 'code': 404 + 'message': 'task not found'
    has_err = "'code': 404" in out and "'message': 'task not found'" in out
    check("Case5: 文件不存在 → ERR_TASK_NOT_FOUND(404)+ exit 1",
          proc.returncode == 1 and has_err,
          f"rc={proc.returncode} out={out[:200]!r}")


# ============================================================
# Case 6: scan_tasks_dir 目录不存在 → ERR_TASK_NOT_FOUND
# ============================================================
def test_case6_dir_not_found():
    """--tasks-dir=nonexist_dir 应该 exit 1 + ERR_TASK_NOT_FOUND。"""
    proc = start_server("--tasks-dir=nonexistent_zzz_dir", "--task=f::f")
    proc.wait(timeout=3)
    out = proc.stdout.read().decode('utf-8', errors='replace')
    has_err = "'code': 404" in out and "'message': 'task not found'" in out
    check("Case6: 目录不存在 → ERR_TASK_NOT_FOUND(404)+ exit 1",
          proc.returncode == 1 and has_err,
          f"rc={proc.returncode} out={out[:200]!r}")


# ============================================================
# Case 7: cli parser.error() --task-file + --tasks-dir 互斥
# ============================================================
def test_case7_parser_error():
    """--task-file + --tasks-dir 互斥,argparse exit 2。"""
    proc = start_server("--task-file=f.py", "--tasks-dir=.", "--task-name=f")
    proc.wait(timeout=3)
    err = proc.stderr.read().decode('utf-8', errors='replace')
    check("Case7: argparse 互斥 → exit 2",
          proc.returncode == 2 and "互斥" in err,
          f"rc={proc.returncode} err={err[:200]!r}")


# ============================================================
# Case 8: 端口占用 → safe_bind 自动重试
# ============================================================
# Q8 Day3 改测策略:Windows 上真 socket bind 不可靠(REUSEADDR 太宽松 / listen 阶段错),
# 改用 mock socket 测 safe_bind 的核心逻辑 —— bind 失败自动换 port 重试
def test_case8_safe_bind_retry():
    """safe_bind 端口占用 → mock EADDRINUSE 验证自动重试逻辑。"""
    import socket as _socket_mod

    class MockSocket:
        """全局前 N 次 bind 失败(EADDRINUSE),之后成功。"""
        bind_count = 0
        fail_until = 1

        def __init__(self):
            self.bound_port = None
            self.closed = False

        def setsockopt(self, *a, **kw):
            pass

        def bind(self, addr):
            MockSocket.bind_count += 1
            if MockSocket.bind_count <= MockSocket.fail_until:
                err = OSError(f"mock EADDRINUSE on {addr[1]} (call {MockSocket.bind_count})")
                err.errno = 98
                raise err
            self.bound_port = addr[1]

        def listen(self, n):
            pass

        def getsockname(self):
            return ('127.0.0.1', self.bound_port)

        def close(self):
            self.closed = True

    # 重置全局计数器(防止多次跑测试时污染)
    MockSocket.bind_count = 0
    MockSocket.fail_until = 1  # 第 1 次 bind 失败,第 2 次成功

    calls = []

    def fake_socket_factory(*args, **kwargs):
        calls.append(MockSocket())
        return calls[-1]

    original_socket = _socket_mod.socket
    _socket_mod.socket = fake_socket_factory
    try:
        sock = safe_bind('127.0.0.1', 18888, max_retries=3)
        # 期望:第 1 个 socket bind 18888 失败,close;第 2 个 socket bind 18889 成功
        check("Case8: safe_bind 端口占用 → 自动重试下一个",
              len(calls) == 2 and sock.bound_port == 18889,
              f"calls={len(calls)} port={sock.bound_port}")
    finally:
        _socket_mod.socket = original_socket


# ============================================================
# Case 9: client sendall 'q' → server 关连接(Q5 Day4 设计)
# Q8 Day3 改测:Windows 上 SIGTERM 不一定触发 KeyboardInterrupt,
# 但 serve_loop 的 'q' 协议是明确的 graceful 退出路径
# ============================================================
def test_case9_q_protocol():
    """client 发 'q',server 回 'bye' + 关连接。"""
    proc = start_server()
    time.sleep(1)
    try:
        s = socket.socket()
        s.connect(('127.0.0.1', 8765))
        s.sendall(b"q\n")
        resp = recv_line(s, timeout=2)
        check("Case9: 'q' 协议 → server 回 bye",
              resp == b"bye\n", f"resp={resp!r}")
        s.close()
    finally:
        proc.terminate()
        try: proc.wait(timeout=2)
        except: proc.kill()


# ============================================================
# Case 10: task 函数本身抛异常 → ERR_TASK_EXCEPTION
# (Q8 Day2 已测,这里只确认 subprocess 形式)
# ============================================================
def test_case10_task_exception():
    """task 抛 ValueError,client 收到 ERR_FORMAT_V2 错误响应 + server 不崩。"""
    # 先写一个 boom task
    boom_path = os.path.join(PROJ_ROOT, "md", "boom_task_q8d3.py")
    with open(boom_path, "w", encoding="utf-8") as f:
        f.write("def boom(data: bytes) -> bytes:\n    raise ValueError('boom')\n")
    try:
        proc = start_server(f"--task-file={boom_path}", "--task-name=boom")
        time.sleep(1)
        try:
            s = socket.socket()
            s.connect(('127.0.0.1', 8765))
            s.sendall(b"hello\n")
            resp = recv_line(s, timeout=2)
            try:
                d = json.loads(resp)
                check("Case10: task 异常 → ERR_FORMAT_V2 错误响应 + server 不崩",
                      d.get("error", {}).get("code") == ERR_TASK_EXCEPTION
                      and proc.poll() is None,
                      f"resp={resp!r} poll={proc.poll()}")
            except Exception:
                check("Case10: task 异常", False, f"无法解析: {resp!r}")
            s.close()
        finally:
            proc.terminate()
            try: proc.wait(timeout=2)
            except: proc.kill()
    finally:
        if os.path.exists(boom_path):
            os.remove(boom_path)


# ============================================================
# 主流程
# ============================================================
if __name__ == "__main__":
    tests = [
        test_case1_socket_close,
        test_case2_bad_json,
        test_case3_validate_fail,
        test_case4_unknown_bytes_task,
        test_case5_file_not_found,
        test_case6_dir_not_found,
        test_case7_parser_error,
        test_case8_safe_bind_retry,
        test_case9_q_protocol,
        test_case10_task_exception,
    ]
    for t in tests:
        try:
            t()
        except Exception as e:
            check(f"{t.__name__}", False, f"异常: {e}")

    print("=" * 60)
    total = len(results)
    passed = sum(1 for r in results if r[0] == "PASS")
    print(f"Q8 Day3 端到端测试矩阵: {passed}/{total}")
    print("=" * 60)
    for status, name, detail in results:
        line = f"  [{status}] {name}"
        if detail and status == "FAIL":
            line += f"  ({detail})"
        print(line)

    failed = sum(1 for r in results if r[0] == "FAIL")
    sys.exit(0 if failed == 0 else 1)