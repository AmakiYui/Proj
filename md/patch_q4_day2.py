# patch_q4_day2.py
# Q4 Day2:src/server/ 引入 cli.py + core/ + _config.py,删 4 个 server.py
# 用法:python md/patch_q4_day2.py

import os
import sys
from datetime import datetime

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

MD_PATH = r"C:\Users\F\Desktop\14问14维软件分析法.md"
BACKUP_DIR = r"C:\Users\F\Desktop\BK"


def backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bp = os.path.join(BACKUP_DIR, f"14x14_{ts}_before_q4_day2_append.md")
    with open(MD_PATH, "rb") as f:
        data = f.read()
    with open(bp, "wb") as f:
        f.write(data)
    print(f"[backup] {bp} ({len(data)} bytes)")


def build_appendix():
    return r"""
## 🆕 2026-08-24 Q4 Day2:src/server/ 引入 cli + core + _config

### Q4 Day2 用户拍板:方案 C(统一 CLI 入口)

| 方案 | 含义 | 决策 |
|---|---|---|
| A | 维持 src/server/ 平铺,只补 _config.py | ❌ |
| B | src/server/ 内再分 core/ cli/ _internal/ | ❌ |
| **C** | **统一启动入口 `python -m src.proj.cli <style>`** | ✅ 采纳 |

**C 方案的核心变化**:
- 4 个 server.py **删除**(被 cli + core 取代)
- 新增 `src/server/cli.py`(argparse 选 simple/thread/pool/pro)
- 新增 `src/server/core/echo_server.py`(业务本体 + 4 风格)
- 新增 `src/server/_config.py`(共享常量)
- 新增 `var/` 目录(运行时产物隔离)
- boot.bat 菜单化升级,只剩 `python -m src.proj.cli <style>` 一条命令

### Q4 Day2 关键洞察:业务本体 vs 并发模型

**Day1 时 4 个 server.py 各自独立,但内核相同**:
```
recv → decode → if q: bye → sendall echo
```

**Day2 抽出"业务本体"**:
```python
# src/server/core/echo_server.py
def handle_echo(conn, addr, prefix="echo"):
    '''业务内核(纯函数,不依赖并发模型)'''
    while True:
        data = conn.recv(1024)
        if not data: break
        msg = data.decode("utf-8", "replace").strip()
        if msg.lower() == "q":
            conn.sendall(b"bye\n"); break
        conn.sendall(f"echo: {msg}\n".encode("utf-8"))
```

**4 个 run_simple / run_thread / run_pool / run_pro 都调 handle_echo,只外层并发不同**。

**这个抽法的工业意义**:
- 业务改协议,4 个并发风格同步更新(只改 handle_echo)
- 新加风格(比如 asyncio),写 run_asyncio 调 handle_echo 即可
- 测试业务只看 handle_echo,不用关心并发

### Q4 Day2 文件结构变化

```
Q4 Day1 (平铺)              Q4 Day2 (cli + core + _config)
src/server/                  src/server/
├── __init__.py              ├── __init__.py
├── server.py                ├── _config.py     ← 🆕 共享常量
├── server_thread.py         ├── cli.py          ← 🆕 统一入口
├── server_pool.py           └── core/           ← 🆕 业务本体子包
├── server_pro.py               ├── __init__.py
                                   └── echo_server.py  ← 🆕 4 风格 + 1 内核
```

**职责切分**:
| 文件 | 职责 | 类比 |
|---|---|---|
| `_config.py` | 常量(HOST/PORT/PID 路径) | 配置文件(硬编码版) |
| `cli.py` | 命令行解析 + 派发 | 总入口、前台 |
| `core/echo_server.py` | 业务内核 + 4 种并发实现 | 工厂、车间 |

### Q4 Day2 var/ 目录登场(Q4 Day1 记账的"事故"解决)

**Day1 跑 server_pro 后的"事故现场"**:
- `src/server/server.pid`(PID 文件)
- `src/server/server.log`(日志)

→ 跟源码混居,**组织事故**。

**Day2 解决方案**:`_config.py` 把路径改成 `var/`:
```python
_VAR_DIR = "var"
PID_FILE = os.path.join(_VAR_DIR, "server.pid")
LOG_FILE = os.path.join(_VAR_DIR, "server.log")
```

**run_pro 自动 `os.makedirs("var", exist_ok=True)`** → 第一次跑就建好目录。

**新结构**:
```
Proj/
├── src/  ← 源码(纯代码)
├── var/  ← 🆕 运行时产物(PID/log,运行时生成,可清)
├── dist/ ← 构建产物(exe,打包生成)
└── md/   ← 工具脚本
```

**3 个"非源码目录"**:
- `src/` = 源码,git 进
- `var/` = 运行时产物,gitignore
- `dist/` = 构建产物,gitignore
- `md/` = 工具脚本,git 进(算项目资产)

### Q4 Day2 cli.py 设计:argparse + STYLES 注册表

```python
# src/server/cli.py
from src.proj.core.echo_server import STYLES

parser = argparse.ArgumentParser(...)
parser.add_argument("style", choices=list(STYLES.keys()) + ["menu"], default="menu")
STYLES[args.style]()  # 派发
```

**STYLES 注册表的妙处**:
- 加新风格,只在 `echo_server.py` 里加 `run_xxx()` 和 `STYLES["xxx"]`
- cli.py 一行不用改
- **数据驱动派发**,不是 if-elif 链

**默认参数 `default="menu"` + `choices=...+["menu"]`**:不带参数 = 打印菜单。

### Q4 Day2 4 风格端到端验证(自动化跑通)

```
[simple] b'echo: hello from cli simple\n'  OK
[thread] b'echo: hello from cli thread\n'  OK
[pool]   b'echo: hello from cli pool\n'    OK
[pro]    b'echo: hello from cli pro\n'     OK

[pro 验证] var/server.pid: 23348
[pro 验证] var/server.log 大小: 287 bytes
```

**4 风格同一协议,不同并发** → 内核统一 + 外层不同的活样本。

### Q4 Day2 boot.bat 升级

**新版 boot.bat**(1777 B):
```
============================================================
  Proj 启动菜单 (Q4 Day2)
============================================================
  [1] 命令行版 (main.py)        -- while True input/print
  [2] 网络 server (cli.py)     -- 选 style 跑服务端
  [3] 客户端 (client.py)       -- 测服务端是否活着
  [0] 退出
```

**Day8 那个 5 选项菜单**(选具体 server) → **Day2 改成 4 选项菜单**(选主菜单项,再选 style)。

**主菜单** → **二级菜单** 是常见 UI 模式,选项多了就要分层。

### Q4 Day2 教训(新增)

- **业务本体 vs 并发模型分家** —— 同一协议,4 个并发实现,只抽一个 handle_echo 就能改一处全改
- **`_` 前缀 = 内部 API 标记** —— `_config.py` 用下划线,告诉读代码的人"包外别 import"
- **STYLES 注册表 > if-elif 链** —— 数据驱动派发,加新风格只动 echo_server.py
- **3 个非源码目录分清楚**:
  - `src/`(源码,git 进)
  - `var/`(运行时产物,gitignore)
  - `dist/`(构建产物,gitignore)
- **argparse 的 `default="menu"`** —— 不带参数 = 打印菜单,符合 CLI 习惯(curl/kubectl 都这样)
- **boot.bat 二级菜单** —— 选项多了要分层,一级选大方向,二级选细节
- **f-string 嵌 `\"` 会 SyntaxError** —— 这次踩了,f-string 里转义要用 `\\\"` 或换写法
- **package 结构 vs script 结构的边界** —— Day2 之前是脚本集,Day2 之后是"小框架"

### Q4 Day2 关键产出

| 项 | 路径 | 大小 | 备注 |
|---|---|---|---|
| src/server/__init__.py | - | 427 B | 包文档 |
| src/server/_config.py | - | 620 B | 🆕 HOST/PORT/PID/LOG 常量 |
| src/server/cli.py | - | 1482 B | 🆕 argparse 统一入口 |
| src/server/core/__init__.py | - | 140 B | 🆕 子包标记 |
| src/server/core/echo_server.py | - | 6003 B | 🆕 handle_echo + 4 run |
| src/server/server.py 等 4 个 | - | - | 🗑 删除(被 cli+core 取代) |
| var/ | - | 目录 | 🆕 运行时产物 |
| boot.bat | - | 1777 B | 改二级菜单 |

**14问 进度**:
```
L0 (2): ⬜⬜       0/2 = 0%
L1 (5): ✅ Q3 ⬜ Q4 ⬜ Q5 ⬜ Q6 ⬜ Q7    1/5 = 20%  (Q4 Day2 完成)
L2 (4): ⬜⬜⬜⬜       0/4 = 0%
L3 (3): ⬜⬜⬬       0/3 = 0%

总进度:1/14 = 7.1%
```

### Q4 Day2 → Day3 过渡

**Day2 解决了**:"怎么用一条命令跑 4 个 server" + "源码 vs 运行时产物分家"
**Day3 要解决的**:`__init__.py` 暴露什么(公共 API 规则)+ .gitignore 写啥

Day3 预告:
- `src/server/__init__.py` 当前只是文档,要不要 `from .cli import main` 暴露?
- `_config.py` 里下划线开头,算不算"内部 API 标记"?
- 加 `from src.proj._config import HOST` 的话,跟"包外别引用"矛盾吗?
- .gitignore 模板:var/ dist/ build/ __pycache__/ *.spec / *.pid / *.log

下次开 /new 第一件事:用户拍板 Day3 公共 API 暴露范围 + .gitignore 内容

---

*本轮 patch: md/patch_q4_day2.py*
"""


def main():
    print("[1/3] 备份 md ...")
    backup()
    print("[2/3] 构造追加内容 ...")
    appendix = build_appendix()
    appendix_bytes = len(appendix.encode("utf-8"))
    print(f"[info] 追加内容约 {appendix_bytes} bytes")
    print("[3/3] 追加到 md ...")
    with open(MD_PATH, "a", encoding="utf-8") as f:
        f.write(appendix)
    new_size = os.path.getsize(MD_PATH)
    print(f"[done] md 新大小: {new_size} bytes (原 {new_size - appendix_bytes} + 追加 {appendix_bytes})")


if __name__ == "__main__":
    main()