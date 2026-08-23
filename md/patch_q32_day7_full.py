"""patch_q32_day7_full.py — 2026-08-24 Q3.2 进阶 #6 源码剖析 + 全景回顾
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
    bak = os.path.join(BK_DIR, f"14x14_{ts}_before_day7full_append.md")
    if os.path.exists(MD_FILE):
        shutil.copy2(MD_FILE, bak)
        print(f"[backup] {bak}")
    return bak


APPEND = r"""
---

## 🆕 2026-08-24 实操补遗 Day7-Full:Q3.2 进阶 #6 源码剖析 + 全景回顾

### A. Day6 附录:socketserver 源码剖析

#### A.1 4 个核心角色

```python
socketserver.BaseRequestHandler      # 第 1 角色:handler 模板(用户继承)
socketserver.TCPServer               # 第 2 角色:网络协议(socket + bind + listen)
socketserver.ThreadingMixIn          # 第 3 角色:并发模型(每连接一线程)
class ThreadedServer(...):           # 第 4 角色:组合(Mixin 注入 TCPServer)
```

**类比**:
- BaseRequestHandler = 厨师(做事)
- TCPServer = 餐厅(接客)
- ThreadingMixIn = 调度(一个厨师服务一桌,多桌并发)

#### A.2 源码剖析(精简版,只看主线)

##### BaseRequestHandler —— 用户继承的"做事模板"

```python
# Lib/socketserver.py 源码精简
class BaseRequestHandler:
    def __init__(self, request, client_address, server):
        self.request = request            # 就是 socket 连接(conn)
        self.client_address = client_address   # (ip, port)
        self.server = server              # 那个 ThreadedServer 实例
        self.setup()
        try:
            self.handle()                 # ← 用户重写这里
        finally:
            self.finish()
```

**用户写**:
```python
class EchoHandler(BaseRequestHandler):
    def handle(self):                     # ← 唯一要重写的方法
        # self.request 就是 conn,self.client_address 就是 (ip, port)
        ...
```

##### TCPServer —— 网络协议层(socket/bind/listen/accept)

```python
# Lib/socketserver.py 源码精简
class TCPServer(BaseServer):
    address_family = socket.AF_INET
    socket_type = socket.SOCK_STREAM
    request_queue_size = 5

    def __init__(self, server_address, RequestHandlerClass):
        self.server_address = server_address
        self.RequestHandlerClass = EchoHandler
        # 这里就是用户看到的 setsockopt(SO_REUSEADDR, 1)
        self.socket = socket.socket(self.address_family, self.socket_type)
        if self.allow_reuse_address:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(server_address)
        self.socket.listen(self.request_queue_size)

    def server_close(self):                # 释放 socket
        self.socket.close()

    def serve_forever(self, poll_interval=0.5):
        self.__is_shut_down.clear()
        try:
            while not self.__shutdown_request:
                ready = selector.select(poll_interval)
                if ready:
                    self._handle_request_noblock()
        finally:
            self.__shutdown_request = False
            self.server_close()
```

**关键**:`serve_forever()` 是单循环,自己只做 accept + dispatch,不做业务。事在 handler 里。

##### ThreadingMixIn —— 并发模型(每连接一线程)

```python
# Lib/socketserver.py 源码精简
class ThreadingMixIn:
    daemon_threads = False                # 默认 False!用户要手动 True

    def process_request(self, request, client_address):
        # 这是 TCPServer 调用的钩子
        # 串行版里这里直接 finish_request,没有 start_new_thread
        t = threading.Thread(
            target=self.process_request_thread,
            args=(request, client_address),
            daemon=self.daemon_threads,    # ← 对应你写的 daemon_threads = True
        )
        t.start()

    def process_request_thread(self, request, client_address):
        # ← 每个线程跑这里
        try:
            self.finish_request(request, client_address)
        finally:
            self.shutdown_request(request)
```

**关键**:`process_request` 是 MixIn 注入的钩子,替换掉 TCPServer 的同步版本。

##### 组合 —— ThreadedServer 把 3 件事粘起来

```python
class ThreadedServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    allow_reuse_address = True
```

**MRO(方法解析顺序)**:`ThreadedServer → ThreadingMixIn → TCPServer → BaseServer → object`

`serve_forever()` 来自 TCPServer,内部会调 `process_request()`,
MRO 找到 ThreadingMixIn 的版本(因为 ThreadingMixIn 在前),所以**自动变成多线程**。

#### A.3 完整调用链(用户连一次发生了什么)

```
client.connect()
    ↓
[主线程] ThreadedServer.serve_forever()    ← TCPServer.serve_forever
    ↓ selector.select() 发现 ready
[主线程] ThreadedServer._handle_request_noblock()
    ↓
[主线程]   ThreadedServer.accept() = self.socket.accept()    ← 拿到 conn, addr
    ↓
[主线程]   ThreadedServer.process_request(conn, addr)         ← MixIn 注入的钩子
    ↓ threading.Thread(...).start()
[新线程] ThreadedServer.process_request_thread(conn, addr)
    ↓
[新线程]   ThreadedServer.finish_request(conn, addr)
    ↓
[新线程]     handler = self.RequestHandlerClass(conn, addr, self)
[新线程]     handler.__init__()
    ↓
[新线程]       handler.setup()            # 默认啥也不做
    ↓
[新线程]       handler.handle()           # ← 你写的 while True + recv + sendall
    ↓
[新线程]       handler.finish()           # 默认啥也不做(conn.close() 你自己写在 finally 里)
[新线程]   ThreadedServer.shutdown_request(conn)    # 关闭 socket 连接
    ↓
[主线程] 回到 selector.select(),等下一个 client
```

#### A.4 一张图看完整架构

```
              ┌──────────────────────────────────────┐
              │        ThreadedServer (用户)          │
              │  ┌──────────────────────────────┐    │
              │  │   serve_forever() loop   │    │
              │  │ (TCPServer.serve_forever)    │    │
              │  └──────────────────────────────┘    │
              └────────────────┬─────────────────────┘
                          │
        ┌─────────────────┴─────────────────┐
        ▼                                   ▼
┌────────────────────┐         ┌──────────────────────┐
│ 串行调度            │         │ 多线程调度           │
│ TCPServer 默认      │         │ ThreadingMixIn 注入  │
│ process_request() │         │ process_request()  │
│  ├ accept         │         │  ├ threading.Thread │
│  ├ handle         │         │  ├ process_request_thread │
│  └ close          │         │  │  ├ finish_request   │
└─────────┬──────────┘         │  │  │  ├ handler.handle()│
          ▼                    │  │  └ shutdown_request │
┌────────────────────┐         │  └ finish_request      │
│   业务             │         └─────────┬──────────────┘
│   (用户写)         │◀───共用────┘
│   handler.handle() │             ▼
└────────────────────┘         ┌──────────────────────┐
                              │   业务(用户写)        │
                              │   handler.handle()   │
                              └──────────────────────┘
```

**核心洞察**:**换并发模型时,业务代码(handler)一行不改** —— 这就是封装的价值。

#### A.5 7 个 takeaway(看完源码才能说的话)

| # | takeaway | 出处 |
|---|---|---|
| 1 | **handler 永远 1 个实例/连接** | `finish_request` 里 `self.RequestHandlerClass(...)` |
| 2 | **主线程只做 accept + dispatch** | `serve_forever` 是单 select 循环 |
| 3 | **Mixin 替换 process_request 钩子** | MRO 让 ThreadingMixIn 接管 |
| 4 | **`daemon_threads` 默认 False** | 必须用户手动 True |
| 5 | **selector.select() 是 I/O 多路复用** | Linux 是 epoll,Windows 是 select(底层不同) |
| 6 | **handle() 抛异常不会杀线程** | try/finally 在 process_request_thread 里 |
| 7 | **with 自动 server_close** | `__exit__` → `server_close` → 解绑端口 |

#### A.6 跟手搓版的核心差异

| 维度 | 手搓 server_thread.py | 标准库 server_pool.py |
|---|---|---|
| accept 主循环 | 自己写 `while True: srv.accept()` | `serve_forever()` 封装好 |
| 派生线程 | 自己 `threading.Thread(target=...).start()` | `process_request` 钩子自动 |
| 异常隔离 | 自己写 try/finally | `process_request_thread` 里帮你 try |
| I/O 多路复用 | 同步 accept | `selector.select(poll_interval)` |
| 关停资源 | Ctrl+C + sys.exit | `with srv:` 自动 server_close |

---

### B. Q3.2 进阶全任务预告(接下来走什么)

#### B.1 完整清单(13 项 + 1 个 md 收尾)

| # | 任务 | 状态 |
|---|---|---|
| 1 | 命令行版 while True | ✅ Day2 |
| 2 | boot.bat 引导 | ✅ Day2 |
| 3 | pyinstaller 打包 exe | ✅ Day2 |
| 4 | socket 监听端口 | ✅ Day4 |
| 5 | 手搓多线程版 | ✅ Day5 |
| 6 | ThreadingTCPServer 对比 | ✅ Day6 |
| 7 | **守护进程化(脱离终端)** | ⬜ Day7 |
| 8 | **PID 文件(单实例检查)** | ⬜ Day7 |
| 9 | **日志输出到文件** | ⬜ Day7 |
| 10 | 端口冲突处理(EADDRINUSE) | ⬜ Day7 |
| 11 | 优雅关闭(信号处理) | ⬜ Day7 |
| 12 | server.py 加进 boot.bat | ⬜ Day7 |
| 13 | server.py 也打包成 exe | ⬜ Day7 |
| 14 | md 追加 Q3.2 进阶章节 | ✅ Day7 |

#### B.2 Day7 三大件预告(守护进程 + PID + 日志)

**7. 守护进程化** —— 让 server 脱离终端跑
- Windows:`pythonw.exe` / pyinstaller `--noconsole`
- Linux:`python server.py &` / `nohup ... &` / systemd
- macOS:launchd
- **目标**:双击启动后无黑色窗口,后台安静跑

**8. PID 文件** —— 单实例检查
- 启动时检查 `server.pid` 是否已存在
- 存在 → 读 PID,检查进程是否真在跑(防"僵尸 PID")
- 不在跑 → 覆盖 PID;在跑 → 报错退出
- 优雅退出时删除 PID 文件

**9. 日志输出到文件** —— `print` 重定向到 `server.log`
- 不靠 `tee` 也不用 `nohup.out`
- Python 内置 `logging` 模块
- 自动加时间戳 / 级别 / 多 handler(文件 + 控制台)
- 日志轮转(`RotatingFileHandler`)是 Day8+

#### B.3 Q3.2 进阶全景图

```
Q3.2 启动程序
├─ 入门:while True + input + break   ✅ Day2(main.py)
├─ 引导:boot.py / boot.bat            ✅ Day2
├─ 打包:pyinstaller → proj.exe       ✅ Day2
│
└─ 进阶:网络版 while True
   ├─ 串行 socket 版(server.py)          ✅ Day4
   ├─ 手搓 threading 版(server_thread.py) ✅ Day5
   ├─ 标准库版(server_pool.py)            ✅ Day6
   ├─ 源码剖析(socketserver 4 角色)        ✅ Day6 附录
   │
   └─ 生产级 3 件套
      ├─ 守护进程化(脱离终端)              ⬜ Day7
      ├─ PID 文件(单实例)                  ⬜ Day7
      ├─ 日志输出(文件 + 轮转)             ⬜ Day7
      └─ 信号处理 / 端口冲突 / 优雅关闭     ⬜ Day7-8
```

---

### C. 14 问框架全景(Q3.2 进阶后的进度)

L1 五问进度(任何软件先过这五问):

| # | 问题 | 状态 | 备注 |
|---|---|---|---|
| Q3 | 活着(系统生命周期) | ✅ 完成 | Q3.1 安装仪式 + Q3.2 启动程序(含进阶) |
| Q4 | 组织(代码结构) | ⬜ 下一站 | 平铺 → src 分层 → 子包化 → monorepo |
| Q5 | 任务(任务执行) | ⬜ 待走 | 单循环 / pipeline / 状态机 / Saga |
| Q6 | 数据(数据维度) | ⬜ 待走 | 状态分离 / 凭证加密 / BlobStore / KeyedStore |
| Q7 | 接口(接口维度) | ⬜ 待走 | RPC / 公开 API / 插件契约 / 通道协议 |

**L1 五问进度:1/5 = 20%**

### D. 14问 全景图

```
L0 顶层(2 问)
├─ Q1 Why   ⬜ 选问 — "这个软件的灵魂是什么?"
└─ Q2 What  ⬜ 选问 — "它长什么样(5 件形态)?"

L1 基础(5 问)
├─ Q3 活着   ✅ 完成 — Q3.1 安装仪式 + Q3.2 启动程序(含 13 项进阶)
├─ Q4 组织   ⬜ 下一站 — Proj/ 现在是平铺,接下来分层?
├─ Q5 任务   ⬜ 待走
├─ Q6 数据   ⬜ 待走
└─ Q7 接口   ⬜ 待走

L2 生产(4 问)  ⬜ 待走
├─ Q8 错误
├─ Q9 进化
├─ Q10 安全
└─ Q11 可观测

L3 进阶(3 问)  ⬜ 待走
├─ Q12 部署
├─ Q13 性能
└─ Q14 协议
```

### E. 项目结构最终版(截至 Day7)

```
Proj/
├── main.py            ← Q3.2 入门:命令行 while True(798 B)
├── boot.py            ← Q3.2 引导(1071 B)
├── boot.bat           ← Windows 批处理(844 B)
├── client.py          ← 极简客户端(665 B)
├── server.py          ← Q3.2 进阶 #4 串行 socket(1596 B)
├── server_thread.py   ← Q3.2 进阶 #5 手搓多线程(1754 B)
├── server_pool.py     ← Q3.2 进阶 #6 标准库 ThreadingMixIn(1635 B)
├── server_daemon.py   ← ⬜ Day7 守护进程版
├── server_pro.py      ← ⬜ Day7 PID + 日志 + 优雅关闭 终极版
├── dist/proj.exe     ← pyinstaller 打包(7.2 MB)
├── build/             ← 🗑 pyinstaller 中间产物
└── md/                ← 所有 md 工具脚本(7 个 + verify)
    ├── patch_q32.py / patch_q32_day2.py / patch_q32_day3.py
    ├── patch_q32_day4.py / patch_q32_day5.py / patch_q32_day6.py
    ├── patch_q32_day7_full.py   ← 🆕 本次(源码剖析 + 全景)
    └── verify_md.py
```

### F. 教训(Day7-Full 新增)

- **源码剖析 = 看清封装** —— "封装不改变行为,只改变代码组织方式"
- **`with srv:` 触发的是 `__exit__` → `server_close`** —— 跟 `with open(f)` 同源
- **Mixin 是 Python 多继承的"插件模式"** —— 换 MixIn 换并发模型,业务代码不动
- **MRO 决定 MixIn 是否生效** —— 继承顺序里 MixIn 必须在 TCPServer 前
- **`daemon_threads = True` 是生产救命稻草** —— Day5/Day6 反复强调
- **未来的 Day7-8:从"教学 demo"到"生产级 server"** —— PID + 日志 + 信号 + 守护 是分水岭

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