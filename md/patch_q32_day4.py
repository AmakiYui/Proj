"""patch_q32_day4.py — 2026-08-24 Q3.2 进阶 Day4:server.py + client.py 落地 + 自动化验证
写入桌面 14问14维软件分析法.md
"""
import os
import shutil
from datetime import datetime

DESKTOP = r"C:\Users\F\Desktop"
BK_DIR = os.path.join(DESKTOP, "BK")
MD_FILE = os.path.join(DESKTOP, "14问14维软件分析法.md")


def backup():
    os.makedirs(BK_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = os.path.join(BK_DIR, f"14x14_{ts}_before_day4_append.md")
    if os.path.exists(MD_FILE):
        shutil.copy2(MD_FILE, bak)
        print(f"[backup] {bak}")
    return bak


APPEND = r"""
---

## 🆕 2026-08-24 实操补遗 Day4:Q3.2 进阶网络版落地 + 自动化验证

### 一、server.py(网络版 while True)落地

文件位置:`C:\Users\F\Desktop\Proj\server.py`(1596 B)

#### 完整代码
```python
# server.py  —— Q3.2 进阶:网络版 while True(极简版)
# 等连接 -> 收一行 -> 回一行 -> 断开
import os
import sys
import socket

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HOST = "127.0.0.1"   # loopback(只听自己,安全)
PORT = 8765          # 任选空闲端口


def run():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PORT))
    srv.listen(5)                                  # 最多排队 5 个连接
    print(f"[server] listening on {HOST}:{PORT}", flush=True)

    while True:
        conn, addr = srv.accept()                  # 阻塞,等客户端连
        print(f"[server] client connected: {addr}", flush=True)
        try:
            while True:                            # 同一连接内可多轮对话
                data = conn.recv(1024)             # 阻塞,等一行
                if not data:                       # 客户端断开
                    break
                msg = data.decode("utf-8", "replace").strip()
                if msg.lower() == "q":
                    conn.sendall(b"bye\n")
                    break
                conn.sendall(f"echo: {msg}\n".encode("utf-8"))
        finally:
            conn.close()
            print(f"[server] client closed: {addr}", flush=True)


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\n[server] Ctrl+C -> shutdown", flush=True)
        sys.exit(0)
```

#### client.py(配套极简客户端,665 B)
```python
# client.py  —— 极简客户端:连一次、收一行、断开
import os, sys, socket

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HOST = "127.0.0.1"
PORT = 8765


def send(msg: str) -> str:
    s = socket.socket()
    s.connect((HOST, PORT))
    s.sendall(msg.encode("utf-8") + b"\n")
    data = s.recv(1024)
    s.close()
    return data.decode("utf-8", "replace").strip()


if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else "proj"
    print(send(msg))
```

### 二、自动化验证(4 个 case 全过)

我用一个一次性脚本 `test_server.py`(跑完已删)模拟两个终端,跑通了 4 个 case:

```
== launching server ==
[OK] 127.0.0.1:8765 is up
[case 1] proj  -> 'echo: proj'
[case 2] 你好    -> 'echo: 你好'    ← UTF-8 中文通过
[case 3] q      -> 'bye'           ← 优雅退出
[case 4] world  -> 'echo: world'   ← 多客户端串行通过

== ALL CASES PASSED ==
```

server stdout 显示 5 次 connect/close,串行处理每个客户端。

### 三、命令行版 vs 网络版 5 维对比(实战验证版)

| 维度 | 命令行版 | 网络版 | 验证 |
|---|---|---|---|
| 等待 | `input()` 阻塞 | `srv.accept()` + `conn.recv()` | ✅ case 1-4 |
| 通信 | stdin/stdout | TCP 字节流 | ✅ case 2 中文 |
| 用户数 | 1 | 多个串行 | ✅ case 4 多连 |
| 距离 | 同台机器 | 跨机器(理论上) | ⬜ 未测(loopback) |
| 安全 | OS 用户权限 | IP + 端口 | ✅ 127.0.0.1 loopback |

### 四、Q3.2 进阶清单更新

| # | 任务 | 状态 |
|---|---|---|
| 1 | 命令行版 while True | ✅ |
| 2 | boot.bat 引导 | ✅ |
| 3 | pyinstaller 打包 exe | ✅ |
| 4 | **socket 监听端口** | ✅ Day4 落地 |
| 5 | 多客户端并发(用 threading) | ⬜ |
| 6 | 守护进程化(脱离终端) | ⬜ |
| 7 | PID 文件 | ⬜ |
| 8 | 日志输出到文件 | ⬜ |
| 9 | 端口冲突处理(EADDRINUSE) | ⬜ |
| 10 | 优雅关闭(信号处理) | ⬜ |
| 11 | server.py 加进 boot.bat | ⬜ |
| 12 | server.py 也打包成 exe | ⬜ |
| 13 | md 追加 Q3.2 进阶章节 | ✅ |

### 五、最终项目结构(`C:\Users\F\Desktop\Proj\`)

```
Proj/
├── main.py            ← 命令行版 while True(798 B)
├── boot.py            ← Python 引导(1071 B)
├── boot.bat           ← Windows 批处理引导(844 B)
├── server.py          ← 🆕 网络版 while True(1596 B)
├── client.py          ← 🆕 极简客户端(665 B)
├── dist/
│   └── proj.exe      ← pyinstaller 打包(命令行版)
├── build/  proj.spec ← 🗑 pyinstaller 中间产物
└── md/                ← 所有 md 工具
    ├── patch_q32.py
    ├── patch_q32_day2.py
    ├── patch_q32_day3.py
    ├── patch_q32_day4.py   ← 🆕 本次
    └── verify_md.py
```

### 六、关键代码模式提炼

#### server.py 4 个核心点
1. `srv.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)` — **TIME_WAIT 状态允许快速重启**(端口复用)
2. `srv.listen(5)` — **backlog=5**(内核为这个 socket 排队的未 accept 连接数)
3. **嵌套 while True** — 外层等连接,内层同连接多轮对话
4. `try / finally` 包 `conn.close()` — **客户端异常断开也保证释放 FD**(不写 finally = 资源泄漏)

#### client.py 3 个核心点
1. `s.connect((HOST, PORT))` — 同步等连接成功
2. `s.sendall(msg + b"\n")` — **必须加换行**,server 用 `recv` 是流式协议
3. `s.close()` — 显式关(短连接无所谓,长连接要更精细)

### 七、用户亲手验证清单(还没做)

> ⚠️ **Day4 这步是模型自动跑的,用户没亲手验证**。记录在此提醒:

- [ ] 用户开终端 A 跑 `python server.py` → 看到 `[server] listening on 127.0.0.1:8765`
- [ ] 用户开终端 B 跑 `python client.py proj` → 看到 `echo: proj`
- [ ] 用户跑 `python client.py 你好` → 看到 `echo: 你好`
- [ ] 用户跑 `python client.py q` → 看到 `bye`
- [ ] 用户在终端 A 按 Ctrl+C → 看到 `Ctrl+C -> shutdown`

### 八、教训(Day4 新增)

- **`recv` 是流式协议**,不是按"行"切的 — 一行 1024 字节够用,真生产要加 length-prefix 或用 `makefile()` 包成行迭代器
- **`SO_REUSEADDR` 是调试期救命稻草**,不然 Ctrl+C 之后端口还在 TIME_WAIT,马上重启会 EADDRINUSE
- **finally 包 close** — Q3.2 进阶第一课的"安全维度"缩影(资源边界)
- **`127.0.0.1` 默认 loopback** — 安全的网络入门姿势,跟 HA / openclaw 默认 `bind=loopback` 一脉相承

---

"""


def main():
    if not os.path.exists(MD_FILE):
        print(f"[error] {MD_FILE} not found")
        return
    backup()
    size_before = os.path.getsize(MD_FILE)
    with open(MD_FILE, "a", encoding="utf-8") as f:
        f.write(APPEND)
    size_after = os.path.getsize(MD_FILE)
    print(f"[ok] appended {size_after - size_before} bytes")
    print(f"[ok] file now {size_after} bytes (was {size_before})")


if __name__ == "__main__":
    main()