# patch_q4_day1.py
# Q4 Day1 落地补遗:平铺 → src/ 单层(server 子包化)
# 写进桌面 14问14维软件分析法.md
# 用法:python md/patch_q4_day1.py

import os
import sys
from datetime import datetime

# UTF-8 强转
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
    backup_path = os.path.join(BACKUP_DIR, f"14x14_{ts}_before_q4_day1_append.md")
    with open(MD_PATH, "rb") as f:
        data = f.read()
    with open(backup_path, "wb") as f:
        f.write(data)
    print(f"[backup] {backup_path} ({len(data)} bytes)")
    return backup_path


def build_appendix():
    return r"""
## 🆕 2026-08-24 Q4 Day1:平铺 → src/ 单层(server 子包化)

### Q4.0 路线图更新(monorepo 列入扩展题)

**原路线图**(Day8 已写):
```
Q4 Day1  平铺 → src/ 单层
Q4 Day2  src/ → 包化
Q4 Day3  公共 API 设计
Q4 Day4  .gitignore + 构建隔离
Q4 Day5  Q4 vs Q3 对照
```

**新路线图**(monorepo 列入 Day5+ 之后):
```
Q4 Day1  平铺 → src/ 单层           ← 今天
Q4 Day2  src/ → 包化
Q4 Day3  公共 API 设计(__init__ 暴露规则)
Q4 Day4  .gitignore + 构建隔离
Q4 Day5  Q4 vs Q3 对照(组织 vs 运行时)
Q4 Day6  monorepo 扩展题(预留,远期议题)
```

**monorepo 在 14 问里的位置** —— 它是 Q4 走完之后的 **横向扩展**,不是 14 问之内的纵向问题:
- 14 问是"怎么读懂一个软件"的纵向维度
- monorepo 是"多个软件怎么住在一起"的横向问题
- 当你只有 1 个软件(我们目前),monorepo 不适用
- 当你有 N 个共用代码的软件,才需要考虑 monorepo
- 所以我们把它放在 Q4 Day6,作为"多软件组织"的延伸题

### Q4 Day1 用户拍板:方案 B(温和)

| 方案 | 决策 | 备注 |
|---|---|---|
| A 激进 | ❌ | 全 7 个 .py 进 src/,根目录太空 |
| **B 温和** | ✅ **采纳** | server*.py 进 src/server/,其他留根 |
| C 观望 | ❌ | Q4 已经开了,不能不动 |

**B 方案的边界**:
- **进 src/**:server.py / server_thread.py / server_pool.py / server_pro.py(4 个网络服务)
- **留根**:
  - `main.py`(命令行版业务入口,跟 boot.py/boot.bat 配对)
  - `boot.py` `boot.bat`(引导层,跟 .py 业务不同维度)
  - `client.py`(客户端,跟服务端不是同一回事)
- **根目录永远留**:dist/ md/ .gitignore(将来)

### Q4 Day1 落地步骤

**1. 建目录**
```powershell
New-Item -ItemType Directory src -Force
New-Item -ItemType Directory src\server -Force
```

**2. 搬 4 个 server*.py**
```powershell
Move-Item server.py,server_thread.py,server_pool.py,server_pro.py -Destination src\server\
```

**3. 加 `__init__.py`(包边界标记)**
- `src/__init__.py`(65 B,空):让 src/ 成为 Python 包
- `src/server/__init__.py`(323 B):写包说明,列 4 个 server + 约定

**4. 改 boot.bat 路径(`python -m src.proj.xxx`)**

**为什么用 `-m` 而不是直接 `python src/server/server.py`?**

| 方式 | 写法 | 效果 |
|---|---|---|
| 直接脚本 | `python src/server/server.py` | sys.path[0] = `src/server/`,import 全看这个目录,跟 src 包无关 |
| **模块模式** | `python -m src.proj.server` | sys.path[0] = 项目根,import 时 `src.proj.server` 能正确解析 |

**`-m` 的关键**:**让 import 边界和项目结构对齐**。后续 Day2 包化后,server.py 内部 `from src.proj._config import X` 才能 import 到。

**5. 验证(自动化跑通)**
```python
python -c "from src.proj import server, server_thread, server_pool, server_pro"
→ [OK] 4 个 server 包导入成功
→ [list] src.proj.server src.proj.server_thread src.proj.server_pool src.proj.server_pro

python -c <subprocess 启动 server_pro + 客户端连一次 + 优雅关闭>
→ [client recv] b'echo: hello from Q4 Day1\n'
→ [OK] server_pro 启动+通信+关闭 全过
```

### Q4 Day1 新结构对照表

```
之前(平铺)                之后(Q4 Day1 src/ 单层)
Proj/               Proj/
├── main.py                ├── main.py            ← 留根
├── boot.py                ├── boot.py            ← 留根
├── boot.bat               ├── boot.bat           ← 留根
├── client.py              ├── client.py          ← 留根
├── server.py              ├── src/
├── server_thread.py       │   ├── __init__.py    ← 🆕 src 包边界
├── server_pool.py         │   └── server/        ← 🆕 server 子包
└── server_pro.py          │       ├── __init__.py
                           │       ├── server.py
                           │       ├── server_thread.py
                           │       ├── server_pool.py
                           │       └── server_pro.py
```

**留根的 3 个理由**(为什么 main.py / boot.* / client.py 不进 src/):
1. **main.py** = 命令行业务入口,跟 boot.py/boot.bat 是"业务+引导"配对,放一起
2. **boot.py / boot.bat** = 引导层,职责跟业务完全不同,放根目录显眼
3. **client.py** = 客户端不是服务端,放根目录就跟 server 包对称

### Q4 Day1 出现的新产物(待 Day3 处理)

跑 server_pro 后,在 src/server/ 里出现两个文件:
- `src/server/server.pid`(PID 文件)
- `src/server/server.log`(日志文件)

**问题**:这俩是 server_pro 的运行时产物,**不应该跟源码混在一起**。

**Day3 公共 API 设计时要解决的**:
- 把 server_pro.py 里的 `LOG_FILE = "server.log"` 改成 `LOG_FILE = "var/server.log"`
- 跑前 `os.makedirs("var", exist_ok=True)`
- PID 文件同理 → `var/server.pid`
- **var/ 目录加进 .gitignore**(Day4 处理)

**Day1 先记账**,Day3 改。

### Q4 Day1 教训(新增)

- **`-m` 比直接脚本重要** —— 直接 `python src/server/server.py` 会让 src 包白建,因为 sys.path 不对
- **`__init__.py` 不仅是空文件** —— 它是包文档,告诉读代码的人"这层有什么、约定什么"
- **包边界 = 边界双方各留根 vs 进 src** —— 这次 main.py/boot.py 留根有 3 个理由,不能一刀切
- **运行时产物(PID/log)跟源码混居是 Day1 的"事故现场"** —— 这是组织问题的真实复现,先记账,Day3 解决
- **搬文件 ≠ 包化** —— 搬完还要加 `__init__.py` + 改启动方式(`-m`),否则包白建
- **`from src.proj import server` 是检验包化的金标准** —— 跑通这个,说明 import 边界生效

### Q4 Day1 关键产出

| 项 | 路径 | 大小 | 备注 |
|---|---|---|---|
| src/ | `C:\Users\F\Desktop\Proj\src\` | 目录 | 🆕 包边界 |
| src/__init__.py | - | 65 B | 空,包标记 |
| src/server/ | - | 目录 | 🆕 server 子包 |
| src/server/__init__.py | - | 323 B | 包文档 |
| src/server/server.py | - | 1596 B | 搬迁 |
| src/server/server_thread.py | - | 1754 B | 搬迁 |
| src/server/server_pool.py | - | 1635 B | 搬迁 |
| src/server/server_pro.py | - | 5166 B | 搬迁 |
| boot.bat | - | 2034 B | 改用 `python -m src.proj.xxx` |
| md 备份 | `C:\Users\F\Desktop\BK\14x14_<ts>_before_q4_day1_append.md` | - | 写前自动 |

**14问 进度**:
```
L0 (2): ⬜⬜       0/2 = 0%
L1 (5): ✅ Q3 ⬜ Q4 ⬜ Q5 ⬜ Q6 ⬜ Q7    1/5 = 20%  (Q4 进行中)
L2 (4): ⬜⬜⬜⬜       0/4 = 0%
L3 (3): ⬜⬜⬜       0/3 = 0%

总进度:1/14 = 7.1%
```

### Q4 Day1 → Day2 过渡

**Day1 解决了**:"代码有没有 src 边界"(yes)
**Day2 要解决的**:"src 包内怎么再分层 + 怎么对外暴露 API"

Day2 预告:
- `src/server/` 现在 4 个平铺的 .py → 是否要再分 `core/` `cli/` `_internal/`?
- `__init__.py` 当前是文档,要不要暴露 `run_server()` 统一入口?
- 4 个 server.py 里都有 `HOST/PORT` 常量 → 要不要抽 `src/server/_config.py`?
- **决策点**:是引入 `cli.py` 包 4 个 server,还是维持平铺?

下次开 /new 第一件事:用户拍板 Day2 走向 + Day1 残留 PID/log 文件处理

---

*本轮 patch: md/patch_q4_day1.py*
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