"""patch_q32_day6.py — 2026-08-24 Q3.2 进阶 Day6:ThreadingTCPServer 标准库对比
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
    bak = os.path.join(BK_DIR, f"14x14_{ts}_before_day6_append.md")
    if os.path.exists(MD_FILE):
        shutil.copy2(MD_FILE, bak)
        print(f"[backup] {bak}")
    return bak


APPEND = r"""
---

## 🆕 2026-08-24 实操补遗 Day6:Q3.2 进阶 #6 ThreadingTCPServer 标准库对比

### 一、动机:为什么还要对比?

手搓 threading 跑通了,但生产项目一般不这么写。Python 标准库 `socketserver`
已经把这套逻辑封装好,关键是要看清**封装做了什么、牺牲了什么**。

### 二、server_pool.py 完整代码(1635 B)

```python
# server_pool.py  —— Q3.2 进阶 #6:标准库 ThreadingMixIn 版
import os, sys, socketserver

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HOST = "127.0.0.1"
PORT = 8765


class EchoHandler(socketserver.BaseRequestHandler):
    # 每来一个连接,socketserver 自动起一个线程跑 handle()
    def handle(self):
        conn = self.request
        addr = self.client_address
        print(f"[handler-{addr[1]}] start", flush=True)
        try:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                msg = data.decode("utf-8", "replace").strip()
                if msg.lower() == "q":
                    conn.sendall(b"bye\n")
                    break
                conn.sendall(f"echo: {msg}\n".encode("utf-8"))
        finally:
            conn.close()
            print(f"[handler-{addr[1]}] closed", flush=True)


class ThreadedServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    allow_reuse_address = True


if __name__ == "__main__":
    with ThreadedServer((HOST, PORT), EchoHandler) as srv:
        print(f"[server] listening on {HOST}:{PORT} (ThreadingMixIn)", flush=True)
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print("\n[server] Ctrl+C -> shutdown", flush=True)
```

### 三、3 个"封装做了什么"

| 标准库做的事 | 手搓版对应代码 | 价值 |
|---|---|---|
| 自动派生线程跑 `handle()` | `threading.Thread(target=handle_client, daemon=True).start()` | **少写 4 行** |
| `daemon_threads = True` | `daemon=True` | 关 server 时不会卡 |
| `allow_reuse_address = True` | `srv.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)` | Ctrl+C 后端口能马上复用 |
| `with srv:` 自动 shutdown | 没 with,Ctrl+C 时手动 `sys.exit(0)` | 资源安全 |

### 四、3 个"封装牺牲了什么"

| 损失 | 手搓版 | 标准库版 |
|---|---|---|
| 看得见 accept/thread 关系 | ✅ | ❌ 藏在 mixin |
| 灵活控制线程 | 想怎么写怎么写 | 只能传 `target=handle` |
| 自定义线程属性 | 可加锁 / 命名 / 池化 | 只能用 BaseRequestHandler |
| `with` 的代价 | 无 | `__exit__` 会 `server_close()`,清 socket FD |

### 五、自动化对比(2 个 server 跑同一组 client)

```
========== TEST: server_thread.py ==========
[OK] server_thread.py ready
[elapsed] 0.90s

========== TEST: server_pool.py ==========
[OK] server_pool.py ready
[elapsed] 0.91s
```

**关键观察**:
- 耗时几乎一致(0.90 vs 0.91)—— 0.01s 差异是测量噪声
- 行为完全相同:3 client 并发拿 echo、UTF-8 OK、各自 q 退出
- 日志格式不同:`[thread-xxx]` vs `[handler-xxx]`,仅是命名习惯

**结论**:**封装不改变并发语义,只改变写法**。

### 六、手搓版 vs 标准库版 6 维对比

| 维度 | server_thread.py | server_pool.py |
|---|---|---|
| 看得见 accept/thread | ✅ 完全暴露 | ❌ 藏在 mixin |
| 代码量 | 30 行 | 30 行(差不多) |
| `SO_REUSEADDR` | 手动 setsockopt | 类属性 `allow_reuse_address = True` |
| `daemon=True` | 手动设 | 类属性 `daemon_threads = True` |
| with 自动关闭 | ❌ 手动 sys.exit | ✅ `with srv:` |
| 生产推荐度 | ⭐⭐(教学) | ⭐⭐⭐(标准库) |

### 七、Q3.2 进阶清单更新

| # | 任务 | 状态 |
|---|---|---|
| 1 | 命令行版 while True | ✅ |
| 2 | boot.bat 引导 | ✅ |
| 3 | pyinstaller 打包 exe | ✅ |
| 4 | socket 监听端口 | ✅ Day4 |
| 5 | 手搓多线程版 | ✅ Day5 |
| 6 | **ThreadingTCPServer 对比** | ✅ **Day6** |
| 7 | 守护进程化(脱离终端) | ⬜ |
| 8 | PID 文件 | ⬜ |
| 9 | 日志输出到文件 | ⬜ |
| 10 | 端口冲突处理(EADDRINUSE) | ⬜ |
| 11 | 优雅关闭(信号处理) | ⬜ |
| 12 | server.py 加进 boot.bat | ⬜ |
| 13 | server.py 也打包成 exe | ⬜ |
| 14 | md 追加 Q3.2 进阶章节 | ✅ |

### 八、3 个 takeaway

1. **教学先手搓** — 看清 accept/thread 的关系,理解"派生线程接客"的真正含义
2. **生产用标准库** — `socketserver.ThreadingMixIn` 是工业级封装,跨平台 + 资源安全 + 上下文管理
3. **封装 = 约定** — `BaseRequestHandler.handle()` 是 Python 之"约",遵守它才能用 mixin
4. **性能等价** — 实测 0.90 vs 0.91,行为完全一致,选哪个是"工程偏好"

### 九、用户亲手验证清单(还没做)

> ⚠️ Day6 是模型自动对比测试的,用户没亲手跑。

- [ ] 用户开终端 A 跑 `python server_pool.py` → 看到 `[server] listening on 127.0.0.1:8765 (ThreadingMixIn)`
- [ ] 用户开 3 个终端 B/C/D 各跑 `python client.py`
- [ ] 用户在终端 A 按 Ctrl+C → 看到 `Ctrl+C -> shutdown` + handler 一起退

### 十、教训(Day6 新增)

- **对比测试要同一脚本同时跑** — 一个测试脚本分别驱动 2 个 server,共享 client 逻辑,才有可比性
- **`taskkill /F /IM python.exe /T` 会自杀** — 别在测试脚本里用,会杀掉 Python 父进程
- **`with ThreadedServer(...) as srv:` 是工业写法** — 自动 `server_close()`,清 socket FD,跟 `with open(file)` 一脉相承
- **`socketserver` 是 Python 2 时代的老库** — 199x 年就在了,稳定但风格老;新项目 asyncio 派更现代
- **对比 = 看清封装** — 教学版与生产版互为对照,新概念最容易在这时落地

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