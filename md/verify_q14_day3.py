# md/verify_q14_day3.py
# Q14 Day3 端到端验证矩阵
# ============================================================
# 跑 6 类协同功能,确认 Q14 Day2 落地没漏
#   1. ClientPool 基础(3 策略 + alive 标记)
#   2. ClientPool 端到端(mock server 池 + failover)
#   3. SafeTask 子进程隔离
#   4. AlertEngine 触发 + 后台
#   5. CLI --hosts 集成
#   6. __all__ 完整性
# ============================================================

import os
import sys
import json
import socket
import threading
import time
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

os.environ["PROJ_METRICS"] = "1"

import proj  # noqa
from proj import (
    ClientPool, ServerEndpoint, parse_endpoints,
    call_in_subprocess, SafeTask,
    AlertEngine, DEFAULT_THRESHOLDS,
)

passed = 0
failed = 0


def check(name, ok, detail=""):
    global passed, failed
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {name}", flush=True)
    if detail and not ok:
        print(f"         {detail}", flush=True)
    if ok:
        passed += 1
    else:
        failed += 1


# ============================================================
# 1. ClientPool 基础
# ============================================================
print("\n=== 1. ClientPool 基础 ===", flush=True)

# 1.1 parse_endpoints
ep = parse_endpoints("h1:80,h2:81 h3:82")
check("parse_endpoints 混合分隔符", ep == ["h1:80", "h2:81", "h3:82"], f"got {ep}")

# 1.2 ServerEndpoint
se = ServerEndpoint(host="1.2.3.4", port=80)
check("ServerEndpoint alive=True 默认", se.alive is True)
check("ServerEndpoint fail_count=0", se.fail_count == 0)
se.alive = False
check("ServerEndpoint 可标记 dead", se.alive is False)

# 1.3 ClientPool 3 策略构造
for s in ("round-robin", "random", "least-fail"):
    p = ClientPool(["a:1", "b:2", "c:3"], strategy=s)
    check(f"ClientPool strategy={s}", len(p.endpoints) == 3)

# 1.4 empty endpoints 抛错
try:
    ClientPool([])
    check("空 endpoints 抛错", False)
except ValueError:
    check("空 endpoints 抛错", True)


# ============================================================
# 2. ClientPool 端到端(failover)
# ============================================================
print("\n=== 2. ClientPool 端到端 ===", flush=True)

# 启 2 个 mock server:端口 18751 (alive) / 18752 (will close)
srv1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv1.bind(("127.0.0.1", 18751))
srv1.listen(20)
srv1_alive = True


def _echo_serve(sock, flag_ref):
    while flag_ref[0]:
        try:
            c, _ = sock.accept()
            data = c.recv(4096)
            if data:
                c.sendall(b"echo:" + data.lstrip(b"h").rstrip(b"\n") + b"\n")
            c.close()
        except OSError:
            return

srv1_flag = [True]
t1 = threading.Thread(target=_echo_serve, args=(srv1, srv1_flag), daemon=True)
t1.start()
time.sleep(0.1)

# 2.1 单 endpoint
pool1 = ClientPool(["127.0.0.1:18751"])
out = pool1.send(b"hello from pool\n")
check("单 endpoint send 返回", out.startswith(b"echo:"))
check("alive_endpoints=1", len(pool1.alive_endpoints()) == 1)

# 2.2 拉黑 server1(临时)
srv1_flag[0] = False
srv1.close()
time.sleep(0.05)

# 现在只剩 srv1,但已死
pool2 = ClientPool(["127.0.0.1:18751"], max_fails=1)
try:
    pool2.send(b"hi\n")
    check("全 dead 抛错", False)
except ConnectionError:
    # 多 fail 后标记 dead
    pass
check("dead 后 endpoint 被标记", pool2.endpoints[0].fail_count >= 1 or not pool2.endpoints[0].alive,
      f"fail_count={pool2.endpoints[0].fail_count}, alive={pool2.endpoints[0].alive}")


# ============================================================
# 3. SafeTask 子进程隔离(用 subprocess 跑,避开 main module 问题)
# ============================================================
print("\n=== 3. SafeTask 隔离 ===", flush=True)

# 把 SafeTask 测试写到独立脚本,subprocess 调
safetest_script = os.path.join(HERE, "_q14_safetest_worker.py")
with open(safetest_script, "w", encoding="utf-8") as f:
    f.write('''
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))
os.environ["PROJ_METRICS"] = "1"
from proj.process_pool import SafeTask, call_in_subprocess

def _good_task(b): return b"good:" + b
def _bad_task(b): raise ValueError("intentional error")
def _slow_task(b):
    import time; time.sleep(5); return b"slow"

if __name__ == "__main__":
    # 3.1 正常
    out = SafeTask(_good_task)(b"hi")
    print("GOOD:", out.decode())
    # 3.2 异常
    try:
        SafeTask(_bad_task)(b"hi")
        print("BAD: no exception")
    except RuntimeError as e:
        print("BAD_OK:", "intentional error" in str(e))
    # 3.3 直接
    out2 = call_in_subprocess(_good_task, b"hi")
    print("DIRECT:", out2.decode())
    # 3.4 超时
    try:
        call_in_subprocess(_slow_task, b"hi", timeout=0.5)
        print("TIMEOUT: no exception")
    except TimeoutError:
        print("TIMEOUT_OK")
''')

r = subprocess.run(
    [sys.executable, safetest_script],
    cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
    env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    timeout=15,
)
out_text = r.stdout
check("SafeTask 正常调用", "GOOD: good:hi" in out_text, f"got stdout={out_text}")
check("SafeTask 异常抛 RuntimeError", "BAD_OK: True" in out_text)
check("call_in_subprocess 直接", "DIRECT: good:hi" in out_text)
check("超时抛 TimeoutError", "TIMEOUT_OK" in out_text)

# 清理临时脚本
os.remove(safetest_script)


# ============================================================
# 4. AlertEngine
# ============================================================
print("\n=== 4. AlertEngine ===", flush=True)

# 4.1 默认阈值
check("默认阈值含 errors_total", "errors_total" in DEFAULT_THRESHOLDS)

# 4.2 手动 inc counter 到阈值以上
from proj.observability import get_registry
reg = get_registry()
err_counter = reg.counter("errors_total_test_unique")

# 先跑一次 check 把 baseline 记录下来
eng = AlertEngine()
eng.thresholds["errors_total_test_unique"] = 5
eng.check()  # baseline

# 然后猛增
for _ in range(10):
    err_counter.inc()

fired = eng.check()
check("errors_total_test_unique 触发", "errors_total_test_unique" in fired, f"fired={fired}")

# 4.3 没超阈值不触发
eng2 = AlertEngine()
# 用一个新的小阈值
small_counter = reg.counter("test_low_threshold")
for _ in range(2):
    small_counter.inc()
eng2.thresholds["test_low_threshold"] = 100  # 阈值很高
fired2 = eng2.check()
check("test_low_threshold 不触发", "test_low_threshold" not in fired2)

# 4.4 启动后台 + 停
eng3 = AlertEngine()
eng3.start_background(interval_sec=0.2)
time.sleep(0.3)
eng3.stop_background()
check("AlertEngine 后台启停", True)


# ============================================================
# 5. CLI --hosts 集成
# ============================================================
print("\n=== 5. CLI --hosts ===", flush=True)

# --help 含 --hosts
r = subprocess.run(
    [sys.executable, "-m", "src.proj.cli", "--help"],
    cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
    env={**os.environ, "PYTHONIOENCODING": "utf-8"},
)
check("--help 含 --hosts", "--hosts" in r.stdout)

# --hosts=无效地址(没 server)
r2 = subprocess.run(
    [sys.executable, "-m", "src.proj.cli", "--hosts=127.0.0.1:1"],
    cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
    env={**os.environ, "PYTHONIOENCODING": "utf-8"},
)
check("--hosts 无 server 返非 0", r2.returncode != 0, f"got {r2.returncode}")


# ============================================================
# 6. __all__ 完整性
# ============================================================
print("\n=== 6. __all__ 完整性 ===", flush=True)

expected = {
    "ClientPool", "ServerEndpoint", "parse_endpoints",
    "call_in_subprocess", "SafeTask",
    "AlertEngine", "get_default_engine", "DEFAULT_THRESHOLDS",
}
actual = set(proj.__all__)
missing = expected - actual
check("__all__ 含 Q14 全部 8 项", not missing, f"missing={missing}")
check("__all__ 共 >=62 项", len(proj.__all__) >= 62, f"got {len(proj.__all__)}")


# ============================================================
# 总结
# ============================================================
print(f"\n=== 总结 ===", flush=True)
print(f"PASS: {passed}", flush=True)
print(f"FAIL: {failed}", flush=True)
sys.exit(0 if failed == 0 else 1)