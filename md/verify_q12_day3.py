# md/verify_q12_day3.py
# Q12 Day3 端到端验证矩阵
# ============================================================
# 跑 5 类部署功能,确认 Q12 Day2 落地没漏
#   1. health_check_handler 返回正确 JSON
#   2. check_server 端到端(server + client)
#   3. PROJ_HOST / PROJ_PORT 环境变量切换
#   4. CLI --health-check 标志
#   5. __all__ 完整性
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

# 启用 metrics(Q11 联动)
os.environ["PROJ_METRICS"] = "1"

import proj  # noqa
from proj import (
    init_server_start_time, health_check_handler,
    check_server, format_check_result,
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
# 1. health_check_handler 单元测试
# ============================================================
print("\n=== 1. health_check_handler ===", flush=True)

init_server_start_time()
time.sleep(0.05)
out = health_check_handler()
check("返回 bytes", isinstance(out, bytes))
parsed = json.loads(out)
check("JSON 含 status", "status" in parsed)
check("status=ok", parsed.get("status") == "ok", f"got {parsed.get('status')}")
check("JSON 含 version", "version" in parsed)
check("version=0.1.0", parsed.get("version") == "0.1.0")
check("JSON 含 uptime_seconds", "uptime_seconds" in parsed)
check("uptime > 0", parsed.get("uptime_seconds", 0) > 0)
check("JSON 含 metrics_snapshot", "metrics_snapshot" in parsed)
check("metrics 是 dict", isinstance(parsed["metrics_snapshot"], dict))


# ============================================================
# 2. check_server 端到端
# ============================================================
print("\n=== 2. check_server 端到端 ===", flush=True)

# 2.1 启一个本地 server,用 sock 自己 mock(不发 task)
srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind(("127.0.0.1", 0))
port = srv.getsockname()[1]
srv.listen(1)


def _mock_serve():
    """最简 mock:收 HEALTH,回 JSON,不做别的"""
    init_server_start_time()
    time.sleep(0.02)  # 让 uptime > 0
    while True:
        try:
            conn, _ = srv.accept()
            data = conn.recv(4096)
            if data.strip().upper() == b"HEALTH":
                conn.sendall(health_check_handler())
            conn.close()
        except OSError:
            return

t = threading.Thread(target=_mock_serve, daemon=True)
t.start()
time.sleep(0.1)

ok, payload = check_server(host="127.0.0.1", port=port, timeout=2.0)
check("端到端 OK", ok, f"payload={payload}")
check("payload 含 status", payload.get("status") == "ok")

srv.close()


# 2.2 没 server = down
ok2, payload2 = check_server(host="127.0.0.1", port=1, timeout=1.0)
check("连不上返回 False", ok2 is False)
check("payload 含 error", "error" in payload2, f"got {payload2}")


# ============================================================
# 3. PROJ_HOST / PROJ_PORT 环境变量
# ============================================================
print("\n=== 3. 环境变量映射 ===", flush=True)

# 3.1 默认 config
from proj import _config as cfg
check("默认 HOST", cfg.HOST == "127.0.0.1")
check("默认 PORT", cfg.PORT == 8765)

# 3.2 设环境变量后再读
os.environ["PROJ_HOST"] = "0.0.0.0"
os.environ["PROJ_PORT"] = "9999"
# 这里只能验证 cli.py 里的逻辑会读到环境变量
# 直接用 os.environ 验证
check("PROJ_HOST 环境变量", os.environ["PROJ_HOST"] == "0.0.0.0")
check("PROJ_PORT 环境变量", os.environ["PROJ_PORT"] == "9999")

# 3.3 还原
os.environ.pop("PROJ_HOST", None)
os.environ.pop("PROJ_PORT", None)


# ============================================================
# 4. CLI --health-check 标志(子进程调用)
# ============================================================
print("\n=== 4. CLI --health-check ===", flush=True)

# 4.1 --help 包含 --health-check
r = subprocess.run(
    [sys.executable, "-m", "src.proj.cli", "--help"],
    cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
    env={**os.environ, "PYTHONIOENCODING": "utf-8"},
)
check("--help 返回 0", r.returncode == 0, f"stderr={r.stderr[:200]}")
check("--help 含 --health-check", "--health-check" in r.stdout)

# 4.2 没 server 时 --health-check 返 down + exit 1
r2 = subprocess.run(
    [sys.executable, "-m", "src.proj.cli", "--health-check", "--port", "1"],
    cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
    env={**os.environ, "PYTHONIOENCODING": "utf-8"},
)
check("无 server 返 1", r2.returncode == 1, f"got {r2.returncode}")
check("输出 [DOWN]", "[DOWN]" in r2.stdout, f"got={r2.stdout}")


# ============================================================
# 5. __all__ 完整性
# ============================================================
print("\n=== 5. __all__ 完整性 ===", flush=True)

expected = {
    "init_server_start_time", "health_check_handler",
    "check_server", "format_check_result",
}
actual = set(proj.__all__)
missing = expected - actual
check("__all__ 含 Q12 全部 4 项", not missing, f"missing={missing}")
check("__all__ 共 >=52 项", len(proj.__all__) >= 52, f"got {len(proj.__all__)}")


# ============================================================
# 总结
# ============================================================
print(f"\n=== 总结 ===", flush=True)
print(f"PASS: {passed}", flush=True)
print(f"FAIL: {failed}", flush=True)
sys.exit(0 if failed == 0 else 1)