"""patch_q32_day7_correction.py — 2026-08-24 用户纠错:"源码哪来的 500 行"
数字核实验证 + 教训固化
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
    bak = os.path.join(BK_DIR, f"14x14_{ts}_before_day7correction_append.md")
    if os.path.exists(MD_FILE):
        shutil.copy2(MD_FILE, bak)
        print(f"[backup] {bak}")
    return bak


APPEND = r"""
---

## 🆕 2026-08-24 纠错补遗:"源码 ~500 行"是哪的源码?(用户纠错)

### 一、用户原话
> "源码哪来的 500 行,不就写了三个脚本嘛"

### 二、厘清两层"源码"

| 层 | 文件 | 实测行数 | 之前我说 | 误差 |
|---|---|---|---|---|
| **你的项目** | server.py + server_thread.py + server_pool.py | **158 行**(47+59+52) | 没提 | —— |
| **Python 标准库** | `C:\Program Files\Python312\Lib\socketserver.py` | **858 行** | "~500 行" | **低估 ~70%** |

**核心**:**我之前剖析的是 Python 标准库(858 行),不是 Proj 项目里的源码(158 行)**。

### 三、当场验证(用 `python -c` 跑了)

```python
import socketserver
print(socketserver.BaseRequestHandler)   # <class '...BaseRequestHandler'>
print(socketserver.TCPServer)             # <class '...TCPServer'>
print(socketserver.ThreadingMixIn)        # <class '...ThreadingMixIn'>
print(socketserver.ThreadingMixIn.daemon_threads)         # False
print(socketserver.TCPServer.allow_reuse_address)         # False
```

**3 个验证点全部对**:
- ✅ 3 个类都在标准库(不是我编的)
- ✅ `daemon_threads` 默认 False
- ✅ `allow_reuse_address` 默认 False

### 四、行数实测脚本

```python
import os
project = r'C:\Users\F\Desktop\Proj'
for n in ['server.py', 'server_thread.py', 'server_pool.py']:
    full = os.path.join(project, n)
    lines = sum(1 for _ in open(full, encoding='utf-8'))
    print(f'  {n}: {lines} 行')

import socketserver, inspect
std_path = inspect.getsourcefile(socketserver)
with open(std_path, encoding='utf-8') as f:
    std_lines = sum(1 for _ in f)
print(f'  Python 标准库 {std_path}: {std_lines} 行')
```

输出:
```
  server.py: 47 行
  server_thread.py: 59 行
  server_pool.py: 52 行
  Python 标准库 C:\Program Files\Python312\Lib\socketserver.py: 858 行
```

### 五、教训(数字要核实,歧义要厘清)

1. **说"源码"必须先说"谁的源码"** —— 用户项目源码 vs Python 标准库源码,完全两个层次
2. **数字要核实** —— 我说"~500 行"是拍脑袋,实测 858 行,误差 ~70%。以后引用行数先验证
3. **用户的元认知** —— "不就写了三个脚本嘛" —— 用户清楚自己只有 3 个 server 脚本,**任何含糊都会被揪出来**
4. **含糊表述 = 用户痛点** —— "源码"、"框架"、"那个东西" 等模糊词,用户一定会追问
5. **纠错写进 md** —— 不要在对话里轻飘飘认错,把"我错在哪 + 怎么不再犯"固化到知识库
6. **教学原则:数字必须当场可验证** —— 跑 `python -c` 5 行就能验证的事,不该拍脑袋

### 六、Q3.2 进阶 Day7-Full 章节勘误

- ❌ 原说"源码 ~500 行" → ✅ 实测 858 行(Python 标准库 `socketserver.py`)
- ❌ 没强调是标准库源码 vs 用户项目源码 → ✅ 现在厘清:剖析的是标准库,不是你的项目
- ✅ Day6 附录里的 4 角色 / 调用链 / 架构图仍然有效,因为它们都是真实存在的源码结构

### 七、14问框架里的元教训(L0 灵魂问)

这次纠错其实暴露了一个更大的问题:

> **当我说"源码"的时候,我到底在指谁?** —— 是 L2 工程的"代码"(用户写的)还是 L0 灵魂的"标准"(社区定的)?

类比到 14问:
- **Q4 组织(代码结构)** —— 你项目怎么分层 → **158 行代码的真相**
- **Q14 协议(协议维度)** —— 你用谁的协议 → **标准库 858 行的真相**

两个层级要分清,**含糊 = 失专业**。

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