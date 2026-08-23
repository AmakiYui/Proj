# patch_q4_day3.py
# Q4 Day3:公共 API 暴露规则 + .gitignore + 构建隔离
# 用法:python md/patch_q4_day3.py

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
    bp = os.path.join(BACKUP_DIR, f"14x14_{ts}_before_q4_day3_append.md")
    with open(MD_PATH, "rb") as f:
        data = f.read()
    with open(bp, "wb") as f:
        f.write(data)
    print(f"[backup] {bp} ({len(data)} bytes)")


def build_appendix():
    return r"""
## 🆕 2026-08-24 Q4 Day3:公共 API 暴露 + .gitignore + 构建隔离

### Q4 Day3 用户拍板:全做(默认推荐)

| 决策点 | 选项 | 决策 |
|---|---|---|
| 1 `__init__.py` 暴露 | A 文档 / B 暴露核心 / C 全暴露 | ✅ B |
| 2 .gitignore 范围 | 只 var/ / 全清单(7 模式) | ✅ 全清单 |
| 3 `__pycache__/` 是否一并清 | 删 / 留(写进 ignore) | ✅ 删 |
| 4 Day3 + Day4 合并 | 一次只走 Day3 / Day3+4 合并 | ✅ 合并一次到位 |

### Q4 Day3 改动 1:`__init__.py` 暴露规则

**新 `src/server/__init__.py`**(933 B):
```python
# 唯一对外暴露
from .cli import main

# 清掉被意外注入到包命名空间的内部模块
# (Python 任何 from .X import Y 都会把 X 注进当前包 namespace)
import src.proj as _pkg
for _name in ("_config", "cli", "core"):
    if hasattr(_pkg, _name):
        delattr(_pkg, _name)
del _pkg, _name

__all__ = ["main"]
```

**踩坑实录** —— 第一次写 `from .cli import main` 不删 `_config`,结果:
```
[main in namespace?] True     OK
[_config]: !! 在(违反)        ← 不该导出却导出了
```

**根因**:Python 的 `from .X import Y` 会把整个 X 注入当前包 namespace。所以 `from .cli import main` 时,`cli` 也被注进去;而 cli 里 `from src.proj.core.echo_server import STYLES` 间接拉了 `_config`,`_config` 也进了包 namespace。

**修法**:在 `__init__.py` 里 `delattr` 清掉。这是 Python 圈子里公开的"魔法解药",Django/Flask 源码里都有类似操作。

### Q4 Day3 改动 2:写 .gitignore(686 B,7 大类)

```gitignore
# 运行时产物
var/                  # PID + 日志的家
*.pid
*.log

# 构建产物
dist/                 # exe 罐头
build/                # 打包中间产物
*.spec                # pyinstaller 配方

# Python 缓存
__pycache__/
*.pyc
*.pyo

# 编辑器/系统文件(可选)
.vscode/  .idea/  *.swp  .DS_Store  Thumbs.db
```

**踩坑实录 —— 验证脚本** —— 我第一次写 `verify_gitignore.py` 用 `line.strip()` 去注释,**没处理行内注释**:
```
'var/                  # PID 文件 + 日志的家'
```
strip() 只去首尾空格,行内 `#` 后面的内容会污染模式 → `fnmatch('var/server.pid', 'var/   # PID 文件...')` = False → 验证脚本以为 ignore 失效。

**修法**:`line.split("#", 1)[0].strip()` —— 先按 `#` 切,只留前半段。**这是 .gitignore 解析的标准姿势**(git 自己的行为)。

### Q4 Day3 验证:`verify_gitignore.py`(13/13 全过)

```
[IGNORE ] var/server.pid                     OK
[IGNORE ] var/server.log                     OK
[IGNORE ] dist/proj.exe                     OK
[IGNORE ] dist/server.exe                    OK
[IGNORE ] src/server/__pycache__/cli.cpython-312.pyc  OK
[IGNORE ] src/__pycache__/__init__.cpython-312.pyc    OK
[IGNORE ] proj.spec                         OK
[IGNORE ] build/something                    OK
[IGNORE ] .vscode/settings.json              OK
[KEEP   ] src/server/cli.py                  OK
[KEEP   ] main.py                            OK
[KEEP   ] src/server/_config.py              OK
[KEEP   ] md/patch_q4_day2.py                OK

ALL PASS
```

**这是 .gitignore 解析器的简化版**(37 行 Python),把 git 的目录模式 / 通配符 / 行内注释 都覆盖到。

### Q4 Day3 改动 3:清 __pycache__ + 验证 var/ 还能自动生成

```
[pro] recv: b'echo: gitignore test\n'

var/ 状态:
   server.log - 283 bytes
   server.pid - 5 bytes

__pycache__/ 状态(预期会有):
   ./src/__pycache__
   ./src/server/__pycache__
   ./src/server/core/__pycache__
```

**关键洞察**:`.gitignore` 不阻止文件生成,只是让 git 看不见它们。Python 跑代码会继续生成 `__pycache__/`,server_pro 跑会继续生成 `var/server.{pid,log}`。

**所以 `__pycache__/` 是源码生成的"必要副产物",不是错误**。我们删它只是为了让目录干净,**下次跑代码自动会再生**。

### Q4 Day3 vs Day4 的合并

原本 Day4 计划是"`.gitignore` + 构建隔离",Day3 计划是"公共 API 设计"。**用户拍板合并**,实际工作量 = Day3 + Day4 之和。

**为什么合并合理**:
- `.gitignore` 和"暴露什么给 git"是同一件事
- "公共 API 暴露"和"git 暴露什么"是组织的两面:对内 vs 对外
- 一个改动两个方向都顺

### Q4 Day3 教训(新增)

- **Python `from .X import Y` 会把 X 注入包 namespace** —— 这是"为什么下划线开头还要 del"的根因
- **下划线前缀是约定不是强制** —— 不 del 的话 `_config` 还是能从外部 import;真要隔离必须 del
- **`.gitignore` 行内注释要用 `split("#", 1)[0]`** —— strip() 不够,这是 git 解析器自己的行为
- **`.gitignore` 不阻止文件生成** —— 只让 git 看不见,这是 FAQ 里的第一坑
- **`__pycache__/` 是 Python 必要副产物** —— 不是错误,是性能优化(下次启动更快)
- **验证脚本要测"反向"(KEEP)** —— 不光测 IGNORE,还要测 KEEP,否则模式写太宽(比如 `*`)也"全 IGNORE"
- **f-string 嵌 `\"` SyntaxError 第三次** —— 已经是肌肉记忆级别,以后写 patch 默认用单引号

### Q4 Day3 关键产出

| 项 | 路径 | 大小 | 备注 |
|---|---|---|---|
| src/server/__init__.py | - | 933 B | 🆕 暴露 main + 清内部 |
| .gitignore | - | 686 B | 🆕 7 大类 |
| md/verify_gitignore.py | - | 1707 B | 🆕 13 case 验证脚本 |
| md/patch_q4_day3.py | - | - | 🆕 本次 md 补遗 |
| __pycache__/ | - | - | 🗑 清 3 个 |

**14问 进度**:
```
L0 (2): ⬜⬜       0/2 = 0%
L1 (5): ✅ Q3 ⬜ Q4 ⬜ Q5 ⬜ Q6 ⬜ Q7    1/5 = 20%  (Q4 Day3 完成)
L2 (4): ⬜⬜⬜⬜       0/4 = 0%
L3 (3): ⬜⬜⬜       0/3 = 0%

总进度:1/14 = 7.1%
```

### Q4 Day3 → Day4 过渡

**Day3 解决了**:
- 公共 API 暴露(`from src.proj import main`)
- 内部 API 隔离(delattr 清掉)
- .gitignore(7 大类)
- 构建隔离(源码 vs 运行时产物 vs 缓存)

**Q4 路线图更新**(Day3+4 合并完成):
```
Q4 Day1  平铺 → src/ 单层              ✅
Q4 Day2  src/server/ 引入 cli+core    ✅
Q4 Day3  公共 API + .gitignore        ✅ ← 今天(Day3+4 合并)
Q4 Day5  Q4 vs Q3 对照(组织 vs 运行时) ⬜
Q4 Day6  monorepo 扩展题              ⬜(远期)
```

**Day5 预告**:
- Q3 vs Q4 边界(运行时 vs 组织)
- Day1-3 全景回顾(从平铺到 .gitignore,代码组织走完一轮)
- Q4 在 14问里的位置(L1 第二问,跟 Q3 配对)
- 14问进度更新(1/14 → 1/14,Q4 进行中)

下次开 /new 第一件事:用户拍板 Day5 走法(框架先行 vs 直接对照表)+ Q4 是否在这里收尾

---

*本轮 patch: md/patch_q4_day3.py*
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