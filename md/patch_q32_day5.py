"""patch_q32_day5.py — 2026-08-24 Q3.2 进阶 Day5:手搓 threading 版
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
    bak = os.path.join(BK_DIR, f"14x14_{ts}_before_day5_append.md")
    if os.path.exists(MD_FILE):
        shutil.copy2(MD_FILE, bak)
        print(f"[backup] {bak}")
    return bak


APPEND = r"""
---

## 🆕 2026-08-24 实操补遗 Day5:Q3.2 进阶 #5 手搓 threading 版

### 一、动机:为什么需要并发?

`server.py` 是串行版 —— 一个 client 占住,后面的全排队。要支持多用户同时在线,
必须"接客 + 服务"分离:**主线程只 accept,每个 client 派生一个线程去服务**。

### 二、server_thread.py 完整代码(1754 B)

```python
# server_thread.py  —— Q3.2 进阶 #5:手搓多线程版
import os, sys, socket, threading

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HOST = "127.0.0.1"
PORT = 8765


def handle_client(conn, addr):
    # 每个客户端一个线程:独立 while True + 独立 try/finally
    print(f"[thread-{addr[1]}] start", flush=True)
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
        print(f"[thread-{addr[1]}] closed", flush=True)


def run():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PORT))
    srv.listen(5)
    print(f"[server] listening on {HOST}:{PORT} (threading)", flush=True)

    while True:
        conn, addr = srv.accept()
        t = threading.Thread(
            target=handle_client,
            args=(conn, addr),
            daemon=True,                            # 主线程死,线程跟着死
        )
        t.start()
        print(f"[server] spawned thread for {addr}", flush=True)


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\n[server] Ctrl+C -> shutdown", flush=True)
        sys.exit(0)
```

### 三、对比 server.py 的"2 处变化"

| 位置 | server.py(串行) | server_thread.py(并发) |
|---|---|---|
| 函数 | `while True` 里直接处理 | 抽出 `handle_client(conn, addr)` |
| accept 后 | `conn.recv()` 阻塞主线程 | `threading.Thread(target=handle_client).start()` |
| daemon | 不需要 | `daemon=True`(主线程 Ctrl+C 退出时,服务线程一起死) |

### 四、自动化验证(3 client 并发)

用一次性 `test_thread.py`(已删)起 3 个不同节奏的 client:

```
[bob]   0.1s/msg  -> ['echo: A', 'echo: B', 'echo: C', 'bye']
[alice] 0.2s/msg  -> ['echo: proj', 'echo: world', 'bye']
[carol] 0.3s/msg  -> ['echo: 你好', 'echo: 再见', 'bye']   ← UTF-8 跨线程 OK
```

server stdout 显示线程**几乎同时 start**(58619 / 58620 / 58621 交错启动),
证明串行版"排队等"已变成并发版"各自接客"。

### 五、串行版 vs 并发版 5 维对比

| 维度 | server.py(串行) | server_thread.py(并发) |
|---|---|---|
| 等待源 | `accept()` + `recv()` 主线程 | accept 在主线程,recv 在子线程 |
| 阻塞谁 | accept 等下一个 client | accept 永远不阻塞 |
| 用户数 | 一次 1 个(排队) | 多个并行(实测 3 个并发) |
| 资源谁管 | 主线程 | 每线程独立 try/finally |
| 出错谁管 | 一个 try | 每线程独立 try |

### 六、Q3.2 进阶清单更新

| # | 任务 | 状态 |
|---|---|---|
| 1 | 命令行版 while True | ✅ |
| 2 | boot.bat 引导 | ✅ |
| 3 | pyinstaller 打包 exe | ✅ |
| 4 | socket 监听端口 | ✅ Day4 |
| 5 | **手搓多线程版** | ✅ **Day5** |
| 6 | 手搓 vs ThreadingTCPServer 对比 | ⬜ Day6 |
| 7 | 守护进程化(脱离终端) | ⬜ |
| 8 | PID 文件 | ⬜ |
| 9 | 日志输出到文件 | ⬜ |
| 10 | 端口冲突处理(EADDRINUSE) | ⬜ |
| 11 | 优雅关闭(信号处理) | ⬜ |
| 12 | server.py 加进 boot.bat | ⬜ |
| 13 | server.py 也打包成 exe | ⬜ |
| 14 | md 追加 Q3.2 进阶章节 | ✅ |

### 七、关键代码模式提炼

#### threading.Thread 4 个核心点
1. **`target=handle_client`** — 要执行的函数,必须是 callable
2. **`args=(conn, addr)`** — 位置参数(不传 kwargs)
3. **`daemon=True`** — 主线程退,服务线程跟着退;不设的话 Ctrl+C 会卡住
4. **`t.start()` 不是 `t.run()`** — `start()` 才会真起线程;`run()` 是同步调用

#### handle_client 必须独立 try/finally
- 跟串行版的逻辑一样,但**每个线程一份**
- 一个 client 抛异常只影响它自己,不会拖垮整个 server

### 八、3 个坑(必看)

1. **共享状态小心** —— 多线程同时改全局变量 race condition,要 `threading.Lock`
2. **`recv` 仍阻塞** —— 但只阻塞自己那个线程,主线程继续 accept(已实测)
3. **FD 上限 1024** —— 每个 client 占 1 个 FD + 1 个 socket,真高并发要调 ulimit 或改 async
4. **GIL 不是问题** —— 我们是 I/O bound(等网络),不是 CPU bound,threading 完全够用

### 九、用户亲手验证清单(还没做)

> ⚠️ Day5 这步是模型自动跑的(模拟3 个 client 并发),用户没亲手验证。

- [ ] 用户开终端 A 跑 `python server_thread.py`
- [ ] 用户开 3 个终端 B/C/D 各跑 `python client.py`
- [ ] 看到 3 个 client 几乎同时拿到 echo(不是排队)
- [ ] 终端 A 按 Ctrl+C → 看到 `Ctrl+C -> shutdown` + 服务线程一起退

### 十、教训(Day5 新增)

- **`daemon=True` 是生产救命稻草** — 不设的话 Ctrl+C 关不掉,主线程等子线程退出才走
- **`start()` 不是 `run()`** — 第一次写多线程常踩
- **并发验证要"不同节奏"** — 3 个 client 同节奏看不出并发,故意错开(0.1/0.2/0.3s)才能证伪串行
- **utf-8 跨线程无问题** — Python str 本身是 unicode,字节只走 socket,threading 切换不破

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