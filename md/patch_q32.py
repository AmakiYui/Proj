# -*- coding: utf-8 -*-
"""
向 14维14问分析法.md 的 Q3.2 启动程序 节插入"引导程序→入口脚本"3层结构子节。
先备份原文件，再读 → 写，禁止覆盖。
"""
import shutil, os, sys, datetime, io

# 强制 stdout 用 UTF-8,绕开 Windows console cp1252
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

src_dir = r"C:\Users\F\Desktop"
target = None
for f in os.listdir(src_dir):
    if f.startswith("14") and f.endswith(".md"):
        full = os.path.join(src_dir, f)
        if os.path.getsize(full) == 28815:
            target = full
            break

if not target:
    print("ERROR: 找不到 28815 字节的 14*.md")
    sys.exit(1)

print(f"目标文件: {target}")

# 1. 备份
backup_dir = r"C:\Users\F\Desktop\BK"
os.makedirs(backup_dir, exist_ok=True)
ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = os.path.join(backup_dir, f"14x14_{ts}_before_q32_insert.md")
shutil.copy2(target, backup_path)
print(f"已备份: {backup_path}")

# 2. 读原文件（尝试多种编码）
raw = None
for enc in ("utf-8", "gbk", "gb2312", "utf-8-sig"):
    try:
        with open(target, "r", encoding=enc) as fp:
            raw = fp.read()
        print(f"用编码 {enc} 读取成功，{len(raw)} 字符")
        break
    except UnicodeDecodeError:
        continue

if raw is None:
    print("ERROR: 所有编码都失败")
    sys.exit(1)

# 3. 定位 Q3.2 标题行
# 真实文本（乱码是因为 GBK 文件名 + console 编码无关，内容我们用 Python 读原文）
lines = raw.splitlines(keepends=True)
q32_line_idx = None
for i, line in enumerate(lines):
    if "#### Q3.2" in line and "启动程序" in line:
        q32_line_idx = i
        print(f"找到 Q3.2 标题在第 {i+1} 行: {line.strip()}")
        break

if q32_line_idx is None:
    print("ERROR: 找不到 Q3.2 标题行")
    sys.exit(1)

# 4. 在 Q3.2 标题之后、下一段非空内容之前插入新子节
# 找 Q3.2 标题后面紧跟的"启动仪式..."或"3 大标志"那行（实际是这节的第一段内容）
insert_after = q32_line_idx  # 默认插在标题后第一行前

# 新子节内容（用 GBK 解码显示没问题，但 md 是 UTF-8 编码，所以插入 UTF-8 文本）
new_section = """
> **🆕 引导程序 → 入口脚本的 3 层结构**(用户 2026-08-24 补):
>
> | 层级 | openclaw 例子 | 一般 exe 应用 | 你的 proj.py |
> |---|---|---|---|
> | **exe / 门面** | `bin: openclaw.mjs`(npm link 全局注册) | `MyApp.exe` | `python.exe`(OS 自带) |
> | **引导程序** | `openclaw.mjs` 本身——只做一件事:加载 main | exe 里的启动代码(找 dll/环境初始化) | `python.exe` 兼任 |
> | **入口脚本** | `main: dist/index.js`(package.json#main) | `entry.py` / `main.py` | `proj.py` |
>
> **3 层关系**:
> 1. **exe 层** = OS 找谁:用户双击 / `.lnk` / `npm bin` / `cron` 决定启动谁
> 2. **引导程序层** = 加载者:打开文件、初始化环境、然后把控制权交给 main
> 3. **入口脚本层** = 业务大脑:while True / daemon / 处理输入输出 / 业务逻辑
>
> **判断规则**:
> - `package.json` 里 `bin` 字段 = 引导程序(openclaw.mjs)
> - `package.json` 里 `main` 字段 = 入口脚本(dist/index.js)
> - proj.py 现状:`python.exe` 当引导 + `proj.py` 当 main,**省了 exe 这一层**
> - 想让 proj.py 也变 exe:pyinstaller / cx_Freeze / nuitka 打包

"""

# 5. 拼接
new_lines = lines[: insert_after + 1] + [new_section] + lines[insert_after + 1 :]
new_content = "".join(new_lines)

# 6. 写回(UTF-8 编码,匹配原文件编码)
with open(target, "w", encoding="utf-8") as fp:
    fp.write(new_content)

new_size = os.path.getsize(target)
print(f"写入完成,新大小: {new_size} 字节 (原 {os.path.getsize(backup_path)} 字节,差 {new_size - os.path.getsize(backup_path)})")