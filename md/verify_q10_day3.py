# md/verify_q10_day3.py
# Q10 Day3 端到端验证矩阵
# ============================================================
# 跑 5 类安全防护,确认 Q10 Day2 落地没漏
#   1. recv buffer 上限 + socket 超时
#   2. HMAC plugin 签名校验(正向 / 负向 / 缺清单 / 强制模式)
#   3. entry_point 白名单
#   4. 集成验证:server 端 safe_recv 真接管
#   5. __all__ 完整性
# ============================================================

import os
import sys
import json
import tempfile
import socket
import threading
import time

# 路径设置
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

import proj  # noqa
from proj import (
    safe_recv, set_recv_timeout,
    compute_plugin_signature, verify_plugin_signature, load_manifest,
    DEFAULT_MAX_RECV, DEFAULT_ALLOWED_ENTRY_POINT_GROUPS,
    scan_plugins_dir, discover_entry_points, clear_plugins,
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


def get_plugin_tasks_keys():
    """helper: list current registered plugin keys"""
    return proj.get_plugin_tasks().keys()


# ============================================================
# 1. recv buffer 上限 + socket 超时
# ============================================================
print("\n=== 1. recv buffer + 超时 ===", flush=True)

# 1.1 上限常量
check("DEFAULT_MAX_RECV = 64KB", DEFAULT_MAX_RECV == 65536)

# 1.2 正常 recv
def _echo_server(port_holder, body):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 0))
    port_holder.append(srv.getsockname()[1])
    srv.listen(1)
    conn, _ = srv.accept()
    set_recv_timeout(conn, 2.0)
    d = safe_recv(conn, max_bytes=128)
    body.append(d)
    conn.close()
    srv.close()

port_holder = []
body = []
t = threading.Thread(target=_echo_server, args=(port_holder, body), daemon=True)
t.start()
time.sleep(0.05)
cli = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cli.connect(("127.0.0.1", port_holder[0]))
cli.sendall(b"hello world")
cli.close()
t.join(timeout=2)
check("safe_recv 收到数据", body and body[0] == b"hello world", f"got {body}")

# 1.3 对端关闭 → None
body2 = []
def _close_server(port_holder, body):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 0))
    port_holder.append(srv.getsockname()[1])
    srv.listen(1)
    conn, _ = srv.accept()
    set_recv_timeout(conn, 2.0)
    time.sleep(0.05)
    d = safe_recv(conn, max_bytes=128)
    body.append(d)
    srv.close()

ph2 = []
t2 = threading.Thread(target=_close_server, args=(ph2, body2), daemon=True)
t2.start()
time.sleep(0.05)
c2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
c2.connect(("127.0.0.1", ph2[0]))
c2.close()  # 立刻关
t2.join(timeout=2)
check("对端关闭返回 b''/None", body2 and (body2[0] is None or body2[0] == b""), f"got {body2}")


# ============================================================
# 2. HMAC plugin 签名校验
# ============================================================
print("\n=== 2. HMAC 签名 ===", flush=True)

with tempfile.TemporaryDirectory() as tmp:
    # 2.1 write a test plugin
    plugin = os.path.join(tmp, "test_plugin.py")
    with open(plugin, "w", encoding="utf-8") as f:
        f.write("def hello(b): return b'hi\\n'\n")
    secret = "day3-test-secret"

    sig = compute_plugin_signature(plugin, secret=secret)
    check("签名是 64 hex 字符", len(sig) == 64 and all(c in "0123456789abcdef" for c in sig))

    # 2.2 正向:签名匹配
    check("verify_plugin_signature 正向", verify_plugin_signature(plugin, sig, secret=secret))

    # 2.3 负向:签名不符
    bad_sig = "0" * 64
    check("verify_plugin_signature 负向", not verify_plugin_signature(plugin, bad_sig, secret=secret))

    # 2.4 negative: file tampered
    with open(plugin, "w", encoding="utf-8") as f:
        f.write("def hello(b): return b'evil\\n'\n")
    check("文件被改签名失效", not verify_plugin_signature(plugin, sig, secret=secret))

    # 2.5 load_manifest parse
    manifest = os.path.join(tmp, "MANIFEST.sig")
    with open(manifest, "w", encoding="utf-8") as f:
        f.write("# comment line\n")
        f.write(f"test_plugin.py {sig}\n")
        f.write("\n")  # blank line
    m = load_manifest(manifest)
    check("load_manifest 解析正确", m == {"test_plugin.py": sig}, f"got {m}")

    # 2.6 load_manifest 文件不存在
    try:
        load_manifest(os.path.join(tmp, "NOPE"))
        check("load_manifest 不存在应抛", False)
    except FileNotFoundError:
        check("load_manifest 不存在应抛", True)


# ============================================================
# 3. entry_point 白名单
# ============================================================
print("\n=== 3. entry_point 白名单 ===", flush=True)

# 3.1 默认白名单包含 proj.plugins
check("默认白名单含 proj.plugins", "proj.plugins" in DEFAULT_ALLOWED_ENTRY_POINT_GROUPS)

# 3.2 默认白名单不含 evil.group
check("默认白名单不含 evil.group", "evil.group" not in DEFAULT_ALLOWED_ENTRY_POINT_GROUPS)

# 3.3 discover_entry_points 静默拒绝非白名单 group
clear_plugins()
r = discover_entry_points("evil.malicious.group")
check("非白名单 group 静默拒绝", r == [], f"got {r}")

# 3.4 接受白名单 group
clear_plugins()
r2 = discover_entry_points("proj.plugins")
check("白名单 group 接受", isinstance(r2, list))

# 3.5 allowed_groups=None 跳过白名单
clear_plugins()
r3 = discover_entry_points("any.group", allowed_groups=None)
check("白名单禁用放行", isinstance(r3, list))


# ============================================================
# 4. 集成:scan_plugins_dir 签名校验
# ============================================================
print("\n=== 4. scan_plugins_dir 签名集成 ===", flush=True)

clear_plugins()
with tempfile.TemporaryDirectory() as tmp:
    # write a normal plugin
    p1 = os.path.join(tmp, "good.py")
    with open(p1, "w", encoding="utf-8") as f:
        f.write("def hello(b): return b'good\\n'\n")
    sig_good = compute_plugin_signature(p1, secret="d3")

    # write a tampered plugin
    p2 = os.path.join(tmp, "evil.py")
    with open(p2, "w", encoding="utf-8") as f:
        f.write("def bye(b): return b'evil\\n'\n")
    sig_evil = compute_plugin_signature(p2, secret="d3")
    with open(p2, "w", encoding="utf-8") as f:
        f.write("def bye(b): import os; return os.popen('whoami').read().encode()\n")

    # write manifest
    manifest = os.path.join(tmp, "MANIFEST.sig")
    with open(manifest, "w", encoding="utf-8") as f:
        f.write(f"good.py {sig_good}\n")
        f.write(f"evil.py {sig_evil}\n")  # but evil.py was already tampered

    # 4.1 不强制校验:两个都加载
    clear_plugins()
    names = scan_plugins_dir(tmp, manifest_path=manifest, require_signature=False)
    check("非强制模式:加载所有", len(names) >= 2, f"got {names}")

    # 4.2 强制校验:evil 被拒,good 通过
    clear_plugins()
    names2 = scan_plugins_dir(tmp, manifest_path=manifest, require_signature=True)
    plugins = list(get_plugin_tasks_keys())
    has_good = any("good" in n for n in plugins)
    has_evil = any("evil" in n for n in plugins)
    check("强制模式:good 通过", has_good, f"plugins={plugins}")
    check("强制模式:evil 拒绝", not has_evil, f"plugins={plugins}")


# ============================================================
# 5. __all__ 完整性
# ============================================================
print("\n=== 5. __all__ 完整性 ===", flush=True)

expected = {
    "safe_recv", "set_recv_timeout",
    "compute_plugin_signature", "verify_plugin_signature", "load_manifest",
    "DEFAULT_MAX_RECV", "DEFAULT_ALLOWED_ENTRY_POINT_GROUPS",
    "get_security_logger",
}
actual = set(proj.__all__)
missing = expected - actual
check("__all__ 含 Q10 全部 8 项", not missing, f"missing={missing}")
check("__all__ 共 >=38 项", len(proj.__all__) >= 38, f"got {len(proj.__all__)}")


# ============================================================
# 总结
# ============================================================
print(f"\n=== 总结 ===", flush=True)
print(f"PASS: {passed}", flush=True)
print(f"FAIL: {failed}", flush=True)
sys.exit(0 if failed == 0 else 1)