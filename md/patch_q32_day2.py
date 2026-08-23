# -*- coding: utf-8 -*-
"""
向 14维14问分析法.md 追加今天的完整实操日志：
1. 3 层结构定义（已写，确认在 Q3.2）
2. boot.py / boot.bat / proj.exe 完整步骤
3. 中间产物清理清单
4. PowerShell 两个坑（$env:USERPROFILE / cp1252）
先备份原文件，再读 → append，禁止覆盖。
"""
import shutil, os, sys, datetime, io

# 强制 stdout 用 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# 找目标文件
src_dir = r"C:\Users\F\Desktop"
target = None
current_size = None
for f in os.listdir(src_dir):
    if f.startswith("14") and f.endswith(".md"):
        full = os.path.join(src_dir, f)
        sz = os.path.getsize(full)
        if sz > 29000:  # 昨天是 28815，今天之前是 29992
            target = full
            current_size = sz
            break

if not target:
    print("ERROR: 找不到目标 md")
    sys.exit(1)

print(f"目标文件: {target}  当前大小: {current_size} 字节")

# 1. 备份
backup_dir = r"C:\Users\F\Desktop\BK"
os.makedirs(backup_dir, exist_ok=True)
ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = os.path.join(backup_dir, f"14x14_{ts}_before_day2_append.md")
shutil.copy2(target, backup_path)
print(f"已备份: {backup_path}")

# 2. 读原文件
raw = None
for enc in ("utf-8", "gbk", "gb2312"):
    try:
        with open(target, "r", encoding=enc) as fp:
            raw = fp.read()
        print(f"用编码 {enc} 读取成功,{len(raw)} 字符")
        break
    except UnicodeDecodeError:
        continue

if raw is None:
    print("ERROR: 读取失败")
    sys.exit(1)

# 3. 要追加的内容（写在文件末尾，不覆盖原有）
append_content = """

---

## 🆕 2026-08-24 实操补遗:3 层启动结构 + 中间产物清理

> **用户原话(重复 2 次)**:
> 「我们打开应用都是 exe,然后引导程序启动,然后打开入口脚本 entry 或者 main」

### ① Q3.2 启动程序的 3 层结构(标准定义)

```
exe / 门面(OS 找谁)
 ↓
引导程序 / Bootstrap(加载并启动)
 ↓
入口脚本 / entry|main(业务大脑)
```

| 层级 | openclaw 例子 | 一般 exe 应用 | 你的 proj.py(极简特例) |
|---|---|---|---|
| **exe 层** | `bin: openclaw.mjs`(npm link 全局注册) | `MyApp.exe` | ❌ 没有(你手敲 `python proj.py` 代替) |
| **引导程序** | `openclaw.mjs` 本身——只做加载 main | exe 启动代码(找 dll/环境初始化) | ❌ 没有(`python.exe` 兼任) |
| **入口脚本** | `main: dist/index.js` | `entry.py` / `main.py` | ✅ `proj.py` |

**判断规则**:
- `package.json#bin` = 引导程序
- `package.json#main` = 入口脚本
- proj.py 现状 = 省了 exe 层 + 引导层,`python.exe` 兼任
- 让 proj.py 变真应用 = pyinstaller / cx_Freeze / nuitka 打包

### ② 今天落地的 3 个产物

**`main.py`** —— 入口脚本(已从 proj.py 改名)
```python
def run():
    print("hello from main.py 入口脚本")
    while True:
        try:
            user_input = input(">>> 说点什么(输 q 退出):")
        except EOFError:
            print("\\n[main.py] 检测到 EOF,优雅退出")
            break
        if user_input == "q":
            print("[main.py] 收到 q,准备退出 while True 循环")
            break
        print(f"[main.py] 你说的是: {user_input}")

if __name__ == "__main__":
    run()
```

**`boot.py`** —— Python 引导程序(关键:UTF-8 强转)
```python
import sys, os
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

print("[boot.py] 我是引导程序,启动中...")
import main
try:
    main.run()
except KeyboardInterrupt:
    print("\\n[boot.py] 收到 Ctrl+C,引导程序接管")
print("[boot.py] 引导程序退出")
```

**`boot.bat`** —— Windows 批处理引导(双击即用)
```bat
@echo off
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
echo [boot.bat] 我是批处理引导程序,启动中...
python boot.py
if errorlevel 1 pause
```

### ③ 打包成真 exe(pyinstaller)

**命令**:
```bash
pyinstaller --onefile --name proj --console boot.py
```

**参数拆解**:
| 参数 | 含义 |
|---|---|
| `--onefile` | 打成单个 exe(默认是一堆文件+一个 exe) |
| `--name proj` | exe 叫 proj(默认跟入口文件同名) |
| `--console` | 保留黑窗(能看 print 输出) |
| `boot.py` | 入口文件:从这里追踪 import 链 |

**pyinstaller 干了什么(你看不到但发生了)**:
1. 读 boot.py
2. 分析 import 链 → 发现 import main
3. 把 main.py 也包进去
4. 把 Python 解释器整个塞进 exe
5. 把用到的标准库塞进去
6. 写 bootloader(双击时第一个跑的小启动器)
7. 把 bootloader + Python + 你的代码打包成一个文件
8. 输出到 `dist/proj.exe`(7.2 MB)
9. 中间产物丢 `build/`

### ④ 中间产物清理清单

| 产物 | 谁建的 | 删了有事吗 | 路径 |
|---|---|---|---|
| `__pycache__/*.pyc` | Python 自动缓存 | ❌ 无事,下次 import 会再建 | `Proj/` 根目录 |
| `build/` | pyinstaller 中间产物 | ❌ 无事,重打时重建 | `Proj/build/` |
| `proj.spec` | pyinstaller 配置 | ❌ 无事,下次打 exe 重建 | `Proj/` 根目录 |
| `patch_q32*.py` | 我帮你写的 md 修补工具 | ⚠️ **脚本**,真业务,可删 | `Proj/` 根目录 |
| `main.py` `boot.py` `boot.bat` | 你/我写的代码 | ❌ **不能删** | `Proj/` 根目录 |
| `dist/proj.exe` | 真·打包产物 | ❌ **不能删** | `Proj/dist/` |

**一键清理命令**:
```bash
cd C:\\Users\\F\\Desktop\\Proj
Remove-Item __pycache__ -Recurse -Force
Remove-Item build -Recurse -Force
Remove-Item proj.spec
```

**清理后只剩**:
```
Proj\\
├── main.py        ← 入口脚本
├── boot.py        ← Python 引导
├── boot.bat       ← Windows 引导
├── patch_q32.py   ← 工具脚本(可选)
└── dist\\proj.exe  ← 真 exe
```

### ⑤ PowerShell 两个坑(写进教训)

**坑 A:`$env:USERPROFILE` 在 `cd` 里不展开**
```bash
# 错
cd $env:USERPROFILE\\Desktop\\Proj
# → The filename, directory name, or volume label syntax is incorrect.

# 对(3 选 1)
cd ~\\Desktop\\Proj
cd C:\\Users\\F\\Desktop\\Proj
echo $env:USERPROFILE  # 先看实际值再粘贴
```

**坑 B:中文 print 默认 cp1252 报错**
```python
UnicodeEncodeError: 'charmap' codec can't encode characters
```
- **PowerShell 里跑**:`$env:PYTHONIOENCODING="utf-8"`(每次新开 PowerShell 要重设)
- **打包后的 exe**:写进 boot.py 里 `os.environ.setdefault + sys.stdout.reconfigure`

### ⑥ Q3.2 启动程序的下一步

- [ ] 用户在 PowerShell 里跑 `python boot.py` 验证 while True 常驻
- [ ] 双击 `boot.bat` 验证双击即用
- [ ] 双击 `dist\\proj.exe` 验证打包后的 exe
- [ ] 输 `q` / `Ctrl+C` / EOF 三种退出方式分别测试
- [ ] 进 Q3.2 进阶:socket 监听端口(网络版 while True) / 守护进程化 / PID 文件 / 日志输出

---

> **状态**:今天 04:43 → 05:49,从 Q3.2 启动程序框架拆解 → 落地 main.py/boot.py/boot.bat → pyinstaller 打包真 exe,3 层结构跑通。
"""

# 4. append 模式追加(不覆盖原内容)
with open(target, "a", encoding="utf-8") as fp:
    fp.write(append_content)

new_size = os.path.getsize(target)
print(f"追加完成,新大小: {new_size} 字节(原 {current_size},差 {new_size - current_size})")
print(f"备份: {backup_path}")