# patch_q32_day8_and_q4.py
# 一次性补遗:Q3.2 Day8 工程化收尾 + Q4 组织框架开篇
# 写进桌面 14问14维软件分析法.md
# 用法:python md/patch_q32_day8_and_q4.py

import os
import sys

MD_PATH = r"C:\Users\F\Desktop\14问14维软件分析法.md"
BACKUP_DIR = r"C:\Users\F\Desktop\BK"

# UTF-8 强转(防 exe 跑出来中文乱码)
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def backup():
    """写之前先备份 md"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    from datetime import datetime
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"14x14_{ts}_before_day8_q4_append.md")
    with open(MD_PATH, "rb") as f:
        data = f.read()
    with open(backup_path, "wb") as f:
        f.write(data)
    print(f"[backup] {backup_path} ({len(data)} bytes)")
    return backup_path


def build_appendix():
    """构造本次要追加的内容"""

    part_a = r"""
## 🆕 2026-08-24 实操补遗 Day8:Q3.2 进阶 #12-13 工程化收尾

### A.1 boot.bat 菜单化(对应 Q3.2 进阶 #12)

**旧 boot.bat**:死板地 `python boot.py`(只能跑命令行版 main.py)

**新 boot.bat**:双击弹出 5 选项菜单
```
============================================================
  Proj 启动菜单 (Q3.2 Day8 工程化收尾版)
============================================================
  [1] 命令行版 (main.py)  -- while True input/print
  [2] 服务器版 (server.py) -- socket 127.0.0.1:8765
  [3] 服务器版 (server_thread.py) -- 手搓多线程
  [4] 服务器版 (server_pool.py) -- 标准库 ThreadingMixIn
  [5] 服务器版 (server_pro.py) -- 终极版(PID+日志+信号)
  [0] 退出
============================================================
请选择 [0-5]:
```

**关键模式**(bat 引导通用写法):
```bat
@echo off                           REM 关闭命令回显
chcp 65001 > nul                    REM 控制台 UTF-8
set PYTHONIOENCODING=utf-8          REM Python stdout UTF-8
cd /d "%~dp0"                       REM 切到 bat 所在目录
:MENU                               REM 标签
echo ...                            REM 打印菜单
set /p CHOICE=请选择 [0-5]:        REM 读用户输入
if "%CHOICE%"=="1" goto CMD         REM 分支跳转
:CMD                                REM 子标签
python boot.py
goto DONE                           REM 跳回 MENU(可重选)
```

**为什么不用 bat 写业务** —— bat 的 `if`/`for` 弱爆,菜单分发是它的甜区,业务逻辑交给 Python。

### A.2 pyinstaller 打包 server.py(对应 Q3.2 进阶 #13)

```
pyinstaller --onefile --name server --console server.py
```

| 参数 | 含义 | 对比 proj.exe |
|---|---|---|
| `--onefile` | 单文件 exe(不打成目录) | 同 |
| `--name server` | 产物叫 server.exe | proj.exe |
| `--console` | 保留黑色控制台窗口 | 同 |

**产物**:`dist/server.exe`(7,266,766 B ≈ 7.2 MB,跟 proj.exe 几乎一样大)

**pyinstaller 的"中间产物"清单**:
| 产物 | 是不是缓存 | 删了能再生吗 | 删前能不能改 |
|---|---|---|---|
| `*.spec` | ❌ 是**配置文件**(配方) | ✅ 能,但配方没了 | ✅ 能(改打包参数用) |
| `build/` | ✅ 编译中间产物 | ✅ 能 | ❌ 没必要 |
| `__pycache__/` | ✅ Python 字节码缓存 | ✅ 跑 .py 自动生成 | ❌ 没必要 |
| `dist/*.exe` | ❌ **最终产物,不能删** | 删了要重打包 | ❌ 删了用户就跑不动了 |

**记忆口诀**:spec = 配方(改打包用)、build = 工地(用完就拆)、__pycache__ = 厨房留的半成品、dist = 上桌的菜。

### A.3 spec 清理 + Q3.2 进阶 13/13 完整闭环

**清理动作**:`Remove-Item server.spec -Force`(顺手 build/ 本轮不存在,Day5/6 已清)

**Q3.2 进阶最终战报**:
```
✅ #1  while True 常驻              Day1
✅ #2  boot.py + boot.bat 引导      Day1
✅ #3  pyinstaller 打包 proj.exe   Day1
✅ #4  socket 监听端口              Day3-4 (串行 server.py)
✅ #5  手搓 threading               Day5 (server_thread.py)
✅ #6  socketserver.ThreadingMixIn  Day6-7 (server_pool.py + 源码剖析)
✅ #7  守护进程化                   Day7-Pro
✅ #8  PID 文件 + atexit 清理       Day7-Pro
✅ #9  日志输出(双 handler + 轮转)  Day7-Pro
✅ #10 端口冲突处理(SO_REUSEADDR)   Day7-Pro
✅ #11 优雅关闭(SIGTERM + 标志位)   Day7-Pro
✅ #12 boot.bat 菜单化              Day8 ← 今天
✅ #13 server.exe 打包              Day8 ← 今天
```

**Q3.2 进阶 13 项 = 一个微型 TCP 服务器的全栈能力**:从命令行 echo 到工业级守护进程,中间只差"代码组织"和"接口设计"。

### A.4 Q3 完整收官:Q3.1 + Q3.2 全部走通

**Q3 活着 = 系统生命周期** —— 完整闭环
- Q3.1 安装仪式:8 件事 / 5 种形态 / 7 个子问题(框架层)
- Q3.2 启动程序:从 proj.py 单文件 → boot.py/boot.bat 引导 → server_pro.py 工业级守护进程

**14问 L1 进度更新**:
```
L1 五问 (基础):
✅ Q3 活着    ⬜ Q4 组织    ⬜ Q5 任务    ⬜ Q6 数据    ⬜ Q7 接口
   100%         0%           0%          0%           0%
   至此 1/5 = 20%
```

### A.5 Day8 教训(新增)

- **bat 适合"菜单分发",不适合"业务逻辑"** —— 引导层用 bat,业务层用 Python
- **`%~dp0` 是 bat 的"我自己的目录"** —— 关键魔法,双击时 cwd 是 %USERPROFILE%,不切走就找不到 .py
- **`goto MENU` 让 bat 可重入** —— 跑完一个程序还能选下一个,不像单次脚本
- **spec 是配方不是缓存** —— 但工程上跟 build/cache 一起归为"中间产物可删",因为 exe 打出来配方就失效
- **`pyinstaller ... 2>&1 | tail` 在 PS 看不到错** —— `tail` 是 bash 别名,PS 用 `Select-Object -Last N`
- **PS 不吃 `&&` 语句分隔符** —— 用 `;`(同一行)或换行(两步)

### A.6 Day8 关键产出

| 项 | 路径 | 大小 |
|---|---|---|
| boot.bat | `C:\Users\F\Desktop\Proj\boot.bat` | 1613 B(菜单化) |
| server.exe | `C:\Users\F\Desktop\Proj\dist\server.exe` | 7,266,766 B(7.2 MB) |
| md 备份 | `C:\Users\F\Desktop\BK\14x14_<ts>_before_day8_q4_append.md` | - |

**项目最终结构**(Q3 完整收官版):
```
Proj/                              ← 项目根(代码+配置)
├── main.py                  798 B        ← Q3.2 入门:命令行版 while True
├── boot.py                 1071 B        ← Python 引导层
├── boot.bat                1613 B        ← 🆕 Windows 批处理引导层(菜单化)
├── client.py                665 B        ← 网络客户端
├── server.py               1596 B        ← Q3.2 进阶 #4:串行 socket
├── server_thread.py        1754 B        ← Q3.2 进阶 #5:手搓 threading
├── server_pool.py          1635 B        ← Q3.2 进阶 #6:ThreadingMixIn
├── server_pro.py           5166 B        ← Q3.2 进阶 #7-11:终极版(守护+PID+日志+信号)
├── dist/
│   ├── proj.exe        7,266,635 B      ← #3 打包:命令行版
│   └── server.exe       7,266,766 B      ← 🆕 #13 打包:服务器版
└── md/                                   ← 10 个 patch 脚本
    ├── patch_q32.py             3872 B
    ├── patch_q32_day2.py        7557 B
    ├── patch_q32_day3.py        7181 B
    ├── patch_q32_day4.py        7595 B
    ├── patch_q32_day5.py        6821 B
    ├── patch_q32_day6.py        6907 B
    ├── patch_q32_day7_correction.py  4596 B
    ├── patch_q32_day7_full.py  15606 B
    ├── patch_q32_day7_pro.py   11968 B
    ├── patch_q32_day8_and_q4.py   🆕 ← 本次
    └── verify_md.py             968 B
```

---

## 🆕 2026-08-24 Q4 开篇:组织(代码结构)

> **Q4 在 L1 里的位置**:Q3 答"软件怎么活着"(运行时维度),Q4 答"代码怎么住"(组织维度)。

### Q4.1 为什么需要"组织"

**反例 —— Proj 当前状态**(9 个 .py 平铺):
```
Proj/
├── main.py            ← 命令行业务
├── boot.py            ← Python 引导
├── boot.bat           ← Windows 引导
├── client.py          ← 客户端
├── server.py          ← 串行 socket
├── server_thread.py   ← 多线程
├── server_pool.py     ← 标准库
└── server_pro.py      ← 终极版
```

**3 个症状**:
1. **命名空间扁平** —— `server*.py` 一堆,加新东西只能加前缀(无 `import` 边界)
2. **入口/业务混杂** —— `main.py`(业务)+ `boot.py`(引导)+ `boot.bat`(引导)职责不同
3. **看不见"包"** —— 不是 Python 包,没 `__init__.py` 没 `import` 边界,只有文件

### Q4.2 4 种组织形态(由轻到重)

| 形态 | 长什么样 | 适用阶段 | 我们的对应 |
|---|---|---|---|
| **平铺** | 全在根目录 | 学习态、<10 文件 | ✅ 当前 |
| **src/ 单层** | `src/server.py` + 根目录留 entry | 小工具、单入口服务 | Day1 目标 |
| **包化** | `src/proj/` 子包 + `__init__.py` 边界 | 中型项目、多模块 | Day2 目标 |
| **monorepo** | 多个包并列,各自 `setup.py` | 大公司、多产品 | 远期 |

### Q4.3 Q4 关键子问题(7 个)

1. **入口位置** —— main/CLI 在哪?(根目录 `main.py` vs `src/proj/__main__.py`)
2. **包边界** —— 哪些归一个包?`proj.server` 还是分 `proj.network` + `proj.cli`?
3. **公共 vs 内部 API** —— 哪些函数 `__init__.py` 暴露?哪些前面下划线?
4. **配置组织** —— `config.py` 还是 `config/` 子包?YAML/TOML/env?
5. **tests/** —— 测试放哪?平铺还是按镜像结构?
6. **docs/** —— 文档放哪?Markdown 还是 Sphinx?
7. **构建产物** —— `dist/` `build/` `__pycache__/` `*.spec` 怎么隔离?

### Q4.4 Q4 的判断规则(代码怎么住的黄金法则)

| 法则 | 解释 |
|---|---|
| **代码跟着功能走** | 一个职责 = 一个文件/包,别一个文件啥都干 |
| **入口薄、逻辑厚** | `main.py` 只做参数解析 + 调度,业务在 `core/` |
| **对外稳定对内自由** | `__init__.py` 暴露的是合同,内部随便改 |
| **构建产物不要混进源码** | `dist/` `__pycache__/` 应该被 `.gitignore` |

### Q4.5 Q3 vs Q4 的边界(对照表)

| 维度 | Q3 活着 | Q4 组织 |
|---|---|---|
| 问的是 | 软件运行时怎么活着 | 代码静态时怎么住 |
| 时间轴 | 进程启动 → 运行 → 关闭 | git clone → ls → 看代码 |
| 关注点 | 进程模型、daemon、PID、日志 | 目录结构、模块边界、import |
| 谁来看 | 运维、SRE | 开发者、新人 |
| 类比 | 房子的"住户"(活着时在干嘛) | 房子的"户型"(几室几厅) |

**关键洞察**:**户型(组织)好坏不影响住户(运行时)立刻死亡**,但影响新人搬进来时(读代码)的速度。Q3 是马上见效,Q4 是慢效。

### Q4.6 Q4 学习路线(预告)

| Day | 主题 | 产物 |
|---|---|---|
| **Q4 Day1** | 平铺 → src/ 单层 | `src/main.py` `src/server*.py`,根留 `boot.bat` `boot.py` `client.py` |
| Q4 Day2 | src/ → 包化 | `proj/__init__.py` `proj/cli.py` `proj/server.py` |
| Q4 Day3 | 公共 API 设计 | `__init__.py` 暴露哪些、`_internal/` 私有 |
| Q4 Day4 | .gitignore + 构建隔离 | 完整工程目录结构 |
| Q4 Day5 | Q4 vs Q3 对照 | "代码组织"和"系统生命周期"的边界 |

### Q4.7 当前可立刻动手的事(决策点)

**Q4 Day1 候选迁移方案**(待用户拍板):

| 方案 | src/ 内容 | 根目录留什么 | 工作量 |
|---|---|---|---|
| A. 激进 | 全 7 个 .py 进 src/ | 只留 `boot.bat` `client.py` `dist/` `md/` | 大 |
| B. 温和 | server*.py 进 src/server/ | `main.py` `boot.*` `client.py` 留根 | 中 |
| C. 观望 | 暂不动,只把 md/ 移到 docs/ | (现状) | 0 |

**用户拍板后,Q4 Day1 直接落地。**

---

## 📊 Q3 收官 + Q4 开篇:14 问全景图

```
L0 顶层(2 问):   ⬜ Q1 Why     ⬜ Q2 What                          0/2 = 0%
L1 基础(5 问):   ✅ Q3 活着    ⬜ Q4 组织   ⬜ Q5 任务              1/5 = 20%
                                ⬜ Q6 数据   ⬜ Q7 接口
L2 生产(4 问):   ⬜ Q8 错误    ⬜ Q9 演进                            0/4 = 0%
                                ⬜ Q10 安全  ⬜ Q11 可观测
L3 进阶(3 问):   ⬜ Q12 部署   ⬜ Q13 性能   ⬜ Q14 协议           0/3 = 0%

总进度:1/14 = 7.1%
```

**Q3 完整收官对 14问方法论的贡献**:
- L1 第一问(活着)全栈走通:从单文件脚本到工业级守护进程
- 13 个进阶子项 = 一个微型 TCP 服务器的全栈能力清单
- Q3 的产出(server_pro.py)已被 L2 部分覆盖:
  - **Q11 可观测** = 日志输出(Day7-Pro)
  - **Q10 安全** = PID 单实例 + SO_REUSEADDR(Day7-Pro)
- **下一站 Q4**:把现有 9 个 .py 从平铺变 src/ 单层,引入 `import` 边界

---

## 📝 本次会话教训总览(Day8 + Q4 开篇)

- **bat 适合"菜单分发"** —— 引导层用 bat,业务层用 Python,职责分明
- **`%~dp0` 是 bat 的"我自己的目录"** —— 不切走就找不到 .py
- **spec 是配方不是缓存** —— 但工程上跟 build/cache 一起归为"中间产物可删"
- **`pyinstaller` 退码非 0 但 build complete 是已知 false positive** —— 看 INFO 行,别看 exit code
- **PowerShell 不吃 `&&`** —— 用 `;` 同一行或换行两步
- **`tail` 在 PS 用 `Select-Object -Last N`** —— 别从 bash 习惯带过来
- **Q4 vs Q3 边界** —— Q3 是运行时,Q4 是静态组织;户型好坏不影响住户立刻死,影响新人搬入速度
- **md 增长曲线**:90143 → 90143+本轮

---

*本轮 patch: md/patch_q32_day8_and_q4.py*
*下次开 /new 第一件事:Day1 拍板迁移方案(A/B/C),然后真改文件*
"""

    return part_a


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

    # 验证
    new_size = os.path.getsize(MD_PATH)
    print(f"[done] md 新大小: {new_size} bytes (原 {new_size - appendix_bytes} + 追加 {appendix_bytes})")


if __name__ == "__main__":
    main()