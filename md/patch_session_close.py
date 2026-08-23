# patch_session_close.py
# 本次会话收官:Q4 完成 + Q3→Q4 衔接 + 下次进 Q5 的引导
# 用法:python md/patch_session_close.py

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
    bp = os.path.join(BACKUP_DIR, f"14x14_{ts}_before_session_close_append.md")
    with open(MD_PATH, "rb") as f:
        data = f.read()
    with open(bp, "wb") as f:
        f.write(data)
    print(f"[backup] {bp} ({len(data)} bytes)")


def build_appendix():
    return r"""
## 🏁 2026-08-24 06:33 会话收官:Q4 完成 + Q5 起点

### 本次会话(2026-08-24 04:43 ~ 06:33)总结

**总时长**:1 小时 50 分钟
**主线**:Q3 收尾 → Q4 开篇 + Day1+2+3+5 完整闭环
**Q3.2 进阶最终**:13/13(补完 #12 boot.bat 菜单化 + #13 server.exe 打包)
**Q4 完成**:Day1(平铺 → src/ 单层)+ Day2(cli+core+_config+var/)+ Day3(公共 API+.gitignore)+ Day5(收官)

### 本次会话 md 增长曲线

```
开始(用户开始学 Q3.1 时):          23426 bytes
Q3.2 Day8 boot.bat 菜单化 + spec:   +5389 → 28815
(中间多次写入,Q3.2 进阶 11 个 Day)
Q4 开篇前:                          90143 bytes
Q4 Day1 (src 边界):                  +7312 → 103178
Q4 Day2 (cli+core+_config):          +7452 → 118319
Q4 Day3 (公共 API+.gitignore):       +6639 → 125136
Q4 Day5 (Q4 收官):                  +8041 → 133362
本次收官(本补遗):                  +XXXX → 133362+

Day 累计:23426 → 133362 = +109936 字节(+469%)
```

### Q3 → Q4 衔接逻辑

```
Q3 活着(L1 第一问):
  "软件怎么活着" - 运行时维度
  产出:9 个 .py(平铺) + 1 个 proj.exe + 1 个 server.exe

Q4 组织(L1 第二问):
  "代码怎么住" - 组织维度
  产出:src/server/{cli,core,_config,__init__} + .gitignore + var/
```

**Q3+Q4=L1 前两问=项目骨架+肉身**:
- Q3 答"会做什么"——9 个 server 跑起来能做 echo 服务
- Q4 答"代码长什么样"——src 边界 + cli 入口 + 暴露规则 + 构建隔离

### Q5 起点预告(L1 第三问)

**Q5 任务(任务执行)**:一个任务怎么走完?

**核心问题**:
- 单循环 / pipeline / 状态机 / Saga
- 任务怎么拆?怎么调度?怎么重试?怎么超时?
- 同步 vs 异步?并发怎么管?
- 任务状态怎么记?失败怎么回滚?

**Q5 在 L1 的位置**:
```
Q3 运行时 / Q4 组织 / Q5 任务流 / Q6 数据 / Q7 接口
  ↑骨架     ↑肉身      ↑          ↑         ↑
```

**Q5 跟 Q3/Q4 的边界**:
- Q3 答"进程怎么活"
- Q4 答"代码怎么住"
- **Q5 答"一个任务怎么跑完"**——介于两者之间,是骨架+肉身的动作

**Q5 候选走法**(等下次会话拍板):
| 方案 | 含义 |
|---|---|
| A | **框架先行** —— 先列 Q5 7 子问题 + 4 种形态,不动代码 |
| B | **从 main.py 改造** —— 把"输什么 → 做什么 → 输出什么"串成任务 |
| C | **从 Q3+Q4 产出反推** —— Q5 应该问什么子问题(更深的元方法论) |

### 本次会话的关键工程资产

**文件结构**(Q4 收官后):
```
Proj/
├── main.py / boot.py / boot.bat / client.py       ← 根入口
├── src/server/
│   ├── __init__.py        933 B                  ← 暴露 main
│   ├── _config.py         620 B                  ← 共享常量
│   ├── cli.py            1482 B                  ← 统一入口
│   └── core/
│       ├── __init__.py     140 B
│       └── echo_server.py 6003 B                 ← 业务本体+4 风格
├── var/                  (运行时产物)
├── dist/
│   ├── proj.exe          7.2 MB                 ← 命令行版
│   └── server.exe         7.2 MB                 ← 网络版
├── .gitignore            686 B                   ← 7 大类
└── md/                   (12 个 patch + 1 verify)
```

**踩过的坑总览(本次会话)**:
1. **PowerShell `cd $env:USERPROFILE\...` 不展开**(Day1 已修)
2. **PowerShell 中文输出 cp1252**(用 PYTHONIOENCODING)
3. **`taskkill /F /IM python.exe /T` 会自杀**(Day6 已避)
4. **pyinstaller exe 中文乱码**(UTF-8 强转写进代码)
5. **GBK 乱码文件名**(os.listdir + 大小匹配)
6. **raw string 嵌 `'''` 提前结束**(Day3 / Day7-pro / Day8 共 3 次)
7. **raw string 嵌 `\U` unicode 转义**(Day8 → 加 r 前缀)
8. **f-string 嵌 `\"` SyntaxError**(Day2 / Day3 共 3 次)
9. **`from .X import Y` 注入 X 到 namespace → `_config` 被意外导出**(Day3 修)
10. **`.gitignore` 行内注释要 `split("#",1)[0]`**(Day3 修)
11. **`&&` PowerShell 不吃**(用 `;` 或换行)
12. **`tail` PowerShell 不存在**(用 `Select-Object -Last N`)

### Q4 完成时的用户拍板记录

**Day1 拍板**:B 温和方案(server*.py 进 src/server/,其他留根)
**Day2 拍板**:C 统一 CLI 入口方案(python -m src.proj.cli <style>)
**Day3 拍板**:B 公共 API 暴露 + 全清单 .gitignore + Day3+Day4 合并
**Day5 拍板**:对照 Q3 + 收官(本次)

### 下次开 /new 后的第一件事(明确)

1. **读 SOUL.md / USER.md / memory/2026-08-24.md(今天)+ MEMORY.md**
2. **确认 Q4 收官**(看 L1 进度 2/5,Q3✅ + Q4✅)
3. **问用户**:"Q5 走 A/B/C 哪个?"
4. **A 框架先行 → 列 Q5 子问题 + 形态,不动代码**
5. **B/C → 看用户拍板后落地**

### L1 进度图(本次会话结束时)

```
L0 顶层(2 问): ⬜ Q1 Why     ⬜ Q2 What                0/2 = 0%
L1 基础(5 问):
  ✅ Q3 活着  ← L1 第一问 100%
  ✅ Q4 组织  ← L1 第二问 100% (本次收官)
  ⬜ Q5 任务  ← L1 第三问(下次起点)
  ⬜ Q6 数据
  ⬜ Q7 接口
                                                2/5 = 40%
L2 生产(4 问): ⬜⬜⬜⬜                               0/4 = 0%
L3 进阶(3 问): ⬜⬜⬜                                0/3 = 0%

总进度:2/14 = 14.3%
```

### 元元教训(本次会话新加)

- **"先存后切"是用户的固定节奏** —— 学一段 → 固化 → /new → 新会话继续
- **Q3 → Q4 是递进的"骨架+肉身"** —— 不能跳,跳了 Q5 没法接
- **Q4 Day3 + Day4 合并合理** —— 因为"暴露给内部"和"暴露给 git"是同一件事的两面
- **Q4 Day6 monorepo 远期** —— 1 个项目用不上,等 N>1 再开
- **Q5 是 L1 第三问** —— 介于 Q3(运行时)和 Q4(组织)之间,是"动作"维度
- **Q5 跟 Q3/Q4 的边界**:Q3 答"进程怎么活",Q4 答"代码怎么住",**Q5 答"一个任务怎么跑完"**
- **md 增长曲线**:23426 → 133362(+469%),12 个 patch + 1 verify 脚本全归档 md/
- **12 次 patch 踩过的坑全在教训里** —— 每次都直接固化,下次同一类问题不重犯

---

*本轮 patch: md/patch_session_close.py*
*本次会话正式收官:2026-08-24 04:43 ~ 06:33,Q3→Q4 完成,L1 进度 2/5 = 40%*
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