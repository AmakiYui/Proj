"""patch_q32_day3.py — 2026-08-24 Q3.2 进阶 + md 脚本归档规则
写入桌面 14问14维软件分析法.md
"""
import os
import shutil
from datetime import datetime

DESKTOP = r"C:\Users\F\Desktop"
BK_DIR = os.path.join(DESKTOP, "BK")
MD_FILE = os.path.join(DESKTOP, "14问14维软件分析法.md")

# 备份(滚动 7 天)
def backup():
    os.makedirs(BK_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = os.path.join(BK_DIR, f"14x14_{ts}_before_day3_append.md")
    if os.path.exists(MD_FILE):
        shutil.copy2(MD_FILE, bak)
        print(f"[backup] {bak}")
    return bak

# 要追加的内容
APPEND = r"""
---

## 🆕 2026-08-24 实操补遗 Day3:Q3.2 进阶(socket 监听端口)+ md 脚本归档规则

### 一、Q3.2 进阶:socket 监听端口(网络版 while True)

#### 1. 核心思路
把"命令行版 while True"升级成"网络版 while True"——
不再是 `input()` 等键盘,而是 `socket.accept()` 等别人连进来。

#### 2. 5 个核心子问题(对照命令行版)

| # | 子问题 | 命令行版 | 网络版 |
|---|---|---|---|
| 1 | 进程还在吗? | while True 不死 | while True 不死 |
| 2 | 等待源? | `input()` | `srv.accept()` + `conn.recv()` |
| 3 | 谁连进来? | 一个人(键盘) | 多个 client(addr) |
| 4 | 跟谁说话? | `print()` | `conn.sendall()` 字节流 |
| 5 | 怎么关? | Ctrl+C / EOF | Ctrl+C / 客户端断开 |

#### 3. 极简 server.py(教学版)

```python
# server.py  —— 网络版 while True:等连接、收一行、回一行、断开
import socket, os, sys
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

HOST = "127.0.0.1"   # 只听自己(loopback,安全)
PORT = 8765          # 任选空闲端口

def run():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PORT))
    srv.listen(5)
    print(f"[server] listening on {HOST}:{PORT}", flush=True)
    while True:
        conn, addr = srv.accept()
        print(f"[server] client connected: {addr}", flush=True)
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
            print(f"[server] client closed: {addr}", flush=True)

if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\n[server] Ctrl+C -> shutdown", flush=True)
        sys.exit(0)
```

#### 4. 怎么测(两个终端)

**终端 A(开服务器)**:
```powershell
cd C:\Users\F\Desktop\Proj
python server.py
# -> [server] listening on 127.0.0.1:8765
```

**终端 B(当客户端)**:
```powershell
$env:PYTHONIOENCODING="utf-8"
python -c "import socket;s=socket.socket();s.connect(('127.0.0.1',8765));s.sendall(b'proj\n');print(s.recv(1024).decode())"
# -> echo: proj
```

#### 5. 命令行版 vs 网络版 5 维对比

| 维度 | 命令行版 | 网络版 |
|---|---|---|
| 等待 | input() 阻塞 | accept() 阻塞 |
| 通信 | 进程内 stdin/stdout | TCP 字节流 |
| 用户数 | 1 | 多个串行 |
| 距离 | 同一台机器 | 跨机器(理论上) |
| 安全 | OS 用户权限 | 端口 + IP 过滤 |

#### 6. Q3.2 进阶完整清单(13 项)

| # | 任务 | 状态 |
|---|---|---|
| 1 | 命令行版 while True | ✅ |
| 2 | boot.bat 引导 | ✅ |
| 3 | pyinstaller 打包 exe | ✅ |
| 4 | **socket 监听端口** | ◀️ 现在 |
| 5 | 多客户端并发(用 threading) | ⬜ |
| 6 | 守护进程化(脱离终端) | ⬜ |
| 7 | PID 文件 | ⬜ |
| 8 | 日志输出到文件 | ⬜ |
| 9 | 端口冲突处理 | ⬜ |
| 10 | 优雅关闭(信号处理) | ⬜ |
| 11 | server.py 加进 boot.bat | ⬜ |
| 12 | server.py 也打包成 exe | ⬜ |
| 13 | md 追加 Q3.2 进阶章节 | ✅ |

### 二、🆕 项目目录约定:md 脚本统一归档到 md/ 子目录

**问题**:之前 patch_q32.py / patch_q32_day2.py / verify_md.py 散落在 Proj/ 根目录,污染项目主目录。

**规则**(2026-08-24 用户拍板):

> **任何用于操作 md 的脚本(patch / verify / append / commit 等)统一放进 `md/` 子目录,不进项目根。**

#### 当前结构(`C:\Users\F\Desktop\Proj\`)

```
Proj/
├── main.py            ← 入口脚本(while True 常驻)
├── boot.py            ← Python 引导(UTF-8 强转)
├── boot.bat           ← Windows 批处理引导(双击即用)
├── server.py          ← ⬜️ Q3.2 进阶 socket 版(待加)
├── dist/
│   └── proj.exe      ← ✅ pyinstaller 打包产物
├── md/                ← 🆕 所有 md 工具脚本统一在这里
│   ├── patch_q32.py
│   ├── patch_q32_day2.py
│   ├── patch_q32_day3.py   ← 🆕 本次(归档规则 + Q3.2 进阶)
│   └── verify_md.py
├── build/             ← 🗑 pyinstaller 中间产物
└── proj.spec         ← 🗑 pyinstaller 配置
```

#### 好处
1. **项目根清爽** — 用户进 Proj/ 只看到代码,看不到工具脚本
2. **md 工具可复用** — patch/verify 系列脚本天然成组
3. **备份更省心** — BK/ 目录的备份对应一个版本的脚本集合
4. **未来复制项目** — 整个 `md/` 拷走就能还原所有笔记写入工具

#### 写新 md 脚本的固定流程
1. 文件名:`patch_*.py` / `append_*.py` / `verify_*.py` 命名清晰
2. 路径:`C:\Users\F\Desktop\Proj\md\`
3. 备份:写到 BK/ 之前先 `shutil.copy2(MD_FILE, bak)`,文件名带时间戳
4. 写入:用 `with open(MD_FILE, "a", encoding="utf-8") as f:` 追加,避免覆盖
5. 校验:跑完 `verify_md.py` 看字节数变化

### 三、Q3.2 进阶待办(继续推进)

- [ ] 跑通极简 server.py(单客户端串行)
- [ ] 上多客户端并发(`socketserver.ThreadingTCPServer`)
- [ ] 加 PID 文件 + 日志输出到文件
- [ ] 端口冲突处理(EADDRINUSE)
- [ ] 优雅关闭(SIGTERM / SIGINT)
- [ ] server.py 加进 boot.bat / 也打包成 exe

### 四、教训(本轮新增)

- **PowerShell `cd` + 相对路径有诡异行为** — 之前 `Move-Item -Path .\patch_q32.py -Destination .\md\` 时,如果当前目录已被 cd 进 `.\md`,PowerShell 会从 md/ 里再找 patch_q32.py,看似失败实际可能在别处。要用 `Test-Path <abs>` 确认。
- **写 md 脚本要建 md/ 子目录**(用户拍板,2026-08-24)— 不再污染项目根。
- **"网络版 while True"是 14 问 Q3.2 进阶第一步** — 后面才是多客户端/守护进程化/PID/日志。

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