# patch_q4_day5.py
# Q4 Day5:组织 vs 生命周期 对照 + Day1-3 全景回顾 + Q4 收官
# 用法:python md/patch_q4_day5.py

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
    bp = os.path.join(BACKUP_DIR, f"14x14_{ts}_before_q4_day5_append.md")
    with open(MD_PATH, "rb") as f:
        data = f.read()
    with open(bp, "wb") as f:
        f.write(data)
    print(f"[backup] {bp} ({len(data)} bytes)")


def build_appendix():
    return r"""
## 🆕 2026-08-24 Q4 Day5:组织 vs 生命周期 + Q4 收官

### Q4 Day5 框架:Q3 vs Q4 的本质差异

**一句话总结**:
- **Q3 活着 = 房子的"住户"**(运行时,谁在干啥的)
- **Q4 组织 = 房子的"户型"**(静态时,几室几厅的)

| 维度 | Q3 活着 | Q4 组织 |
|---|---|---|
| **问的是** | 软件运行时怎么活着 | 代码静态时怎么住 |
| **时间轴** | 进程启动 → 运行 → 关闭 | git clone → ls → 看代码 |
| **关注点** | 进程模型、daemon、PID、日志 | 目录结构、模块边界、import |
| **谁来看** | 运维、SRE | 开发者、新人 |
| **类比** | 住户(做饭、睡觉、出门) | 户型(几室几厅、厨房多大) |
| **变化频率** | 高(每次部署都变) | 低(改完一次稳定很久) |
| **故障影响** | 立刻死(进程崩了) | 慢慢烂(新人看不懂走人) |
| **衡量指标** | uptime / MTTR | 新人 onboarding 时间 |

**关键洞察**:**户型好坏不影响住户立刻死亡**,但影响新人搬进来时(读代码)的速度。
- Q3 是马上见效的(进程启动失败=立刻崩)
- Q4 是慢效的(组织烂=半年后没人能改)

### Q4 Day5 框架:Day1-3 全景回顾

**Q4 走过的 3 步,每步答了一个具体问题**:

```
Day1: 平铺 → src/ 单层       答: "代码有没有 src 边界?"
Day2: src/ 引入 cli + core   答: "怎么用一条命令跑 4 个 server?" + "源码 vs 运行时产物分家"
Day3: 公共 API + .gitignore 答: "对内暴露什么?" + "对外暴露什么(给 git)?"
```

**Day1 → Day2 → Day3 的逻辑链**:
```
Day1: 有 src 包          → 给代码一个家
Day2: 有 cli + core      → 给家装上"前门"(启动入口)+ "卧室"(业务本体)
Day3: 有 __init__ 暴露   → 给前门装上"门牌"(公共 API)
      有 .gitignore       → 给家圈上"围墙"(隔离外部噪音)
```

**Q4 三步对应的工程动作**:
| Day | 工程动作 | 工业术语 |
|---|---|---|
| Day1 | 把散落的 .py 整理到 src/ | **包化**(packaging) |
| Day2 | 抽业务本体 + 统一入口 + 隔离产物 | **分层**(layering) + **分离关注点**(SoC) |
| Day3 | 暴露公共 API + 隔离内部 | **封装**(encapsulation) + **构建隔离**(build isolation) |

### Q4 Day5 框架:Q4 的核心子问题(完整 7 个 + 4 个 Day 答的标记)

| # | 子问题 | Day 答的 | 怎么答的 |
|---|---|---|---|
| 1 | 入口位置在哪? | Day1+2 | `src/server/cli.py` + `python -m` |
| 2 | 包边界怎么画? | Day1+2 | `src/server/core/` 子包装业务,`src/server/` 装启动 |
| 3 | 公共 API 暴露什么? | Day3 | `__init__.py` 暴露 `main`,del 掉内部 |
| 4 | 配置组织? | Day2 | `_config.py` 硬编码集中(后续 Day3+ 可演进) |
| 5 | 测试放哪? | ⬜ Day5+ 后续 | `tests/` 镜像 `src/` 结构 |
| 6 | 文档放哪? | ✅ md/ 已用 | 历史归档 + 当下工具 |
| 7 | 构建产物怎么隔离? | Day3 | `.gitignore` 7 大类 |

**剩余 2 个子问题**(留给后续会话或 14 问之外):
- **测试放哪** —— 加 pytest 时统一进 `tests/`,镜像 `src/server/` 结构
- **配置组织深一步** —— Day2 用 `_config.py` 是最简形态,生产项目会用 YAML/TOML/env + `config/` 子包

### Q4 Day5 框架:Day1-3 留下的 5 个工程资产

| 资产 | 位置 | 状态 | 价值 |
|---|---|---|---|
| **统一启动入口** | `python -m src.proj.cli <style>` | ✅ | 1 条命令跑 4 风格 |
| **业务本体抽离** | `src/server/core/echo_server.py:handle_echo` | ✅ | 改协议只改 1 处 |
| **运行时产物隔离** | `var/` | ✅ | PID/log 跟源码分家 |
| **公共 API 暴露** | `from src.proj import main` | ✅ | 外部只看见 main,看不见 _config |
| **.gitignore** | 7 大类 | ✅ | var/dist/__pycache__/build/spec 全 ignore |

### Q4 Day5 框架:Q4 vs Q3 的产出对照

```
Q3.2 进阶 13 项                  Q4 三步走
✅ #1 while True 常驻            ✅ Day1 src 边界
✅ #2 boot.py + boot.bat         ✅ Day2 业务抽离 + CLI
✅ #3 pyinstaller 打 proj.exe   ✅ Day2 var/ 隔离
✅ #4 socket 监听端口            ✅ Day3 __init__ 暴露
✅ #5 手搓 threading             ✅ Day3 .gitignore
✅ #6 ThreadingMixIn
✅ #7-11 守护+PID+日志+信号+单实例
✅ #12 boot.bat 菜单化
✅ #13 server.exe 打包
13/13 100%                       3/3 100%(Day1+2+3,Q4 主体完成)
```

**Q3 答的是"运行时能力",Q4 答的是"组织能力"。**
两个 Q 都走完后,L1 前两问(Q3+Q4)= 项目的"骨架 + 肉身"。

### Q4 Day5:为什么 Q4 Day1-3 是"主体完成"

**Q4 路线图 6 步**:
```
✅ Day1 平铺 → src/ 单层
✅ Day2 引入 cli+core+_config+var/
✅ Day3 公共 API + .gitignore
⬜ Day5 Q4 vs Q3 对照 + 收官(今天)
⬜ Day6 monorepo 扩展题(远期,1 个项目用不上)
```

**Day4 已被 Day3 合并**(用户拍板),所以 Day1+2+3 是 Q4 主体,Day5 是收官,Day6 是远期预留。

**Q4 进度**:
```
0/6 Day ━━━━━━━━━━━━━━━━━━━ 6/6 Day
  Day1 ✅ Day2 ✅ Day3 ✅ Day4=Day3 ✅ Day5 ⬜ Day6 ⬜
                          ↑
                    进度 50%(今天跳到 4/6)
```

### Q4 Day5 教训(收官级)

- **组织烂不立刻死,新人看不懂走人** —— Q4 的真正风险不是"崩",是"半年没人能改"
- **Q3 是骨架(马上见效),Q4 是肉身(慢效)** —— 但缺一不可
- **Day1+2+3 三个动作缺一不可**:
  - 只 Day1:有边界没入口 → 用户不知道咋跑
  - 只 Day1+2:有入口没暴露规则 → 内部全暴露,改啥都怕
  - 只 Day1+3:有边界+暴露但业务散 → 还是各 .py 独立
- **`__init__.py` 是"门牌"不是"招牌"** —— 只放 docstring 是文档,真做隔离要 `from .X import Y + del`
- **`.gitignore` 不阻止文件生成** —— 只让 git 看不见,这点 FAQ 第一坑
- **封装的目的不是"藏起来"** —— 是"留稳定的,内部随便改";不是"不让人用",是"用错了我不负责"
- **Q4 Day6 monorepo 远期** —— 1 个项目用不上,等有 3+ 共用代码的项目再说
- **Q3+Q4 配对 = L1 前两问 = 项目骨架+肉身** —— 后面 Q5-Q7 是更细的维度(Q5 任务怎么走 / Q6 数据怎么存 / Q7 怎么对话)

### Q4 Day5 关键产出

| 项 | 路径 | 大小 | 备注 |
|---|---|---|---|
| (本轮无文件改动,纯框架) | - | - | Q4 Day5 是收官 Day,不写代码 |
| md/patch_q4_day5.py | - | - | 🆕 本次 md 补遗 |

**Q4 完成度**:
```
主体:Day1+2+3 ✅ (3/3 = 100%)
收官:Day5 ✅ (今天,1/1 = 100%)
远期:Day6 ⬜ monorepo(预留)
总评:Q4 主体+收官 完成,Day6 等有 N>1 项目再开
```

### Q4 Day5 → Q4 Day6 过渡

**Day5 解决了**:
- Q3 vs Q4 边界(运行时 vs 组织)
- Day1-3 全景回顾(3 步走的逻辑链)
- Q4 7 子问题进度表(5 答了,2 留给后续)
- Q4 vs Q3 产出对照(Q3=13/13,Q4=3/3 主体)

**Day6 远期预留** —— **1 个项目用不上**,等有 N>1 项目再开。当下不需要做任何事。

### Q4 Day5:14 问 L1 进度更新

```
L0 顶层(2 问): ⬜ Q1 Why     ⬜ Q2 What                0/2 = 0%
L1 基础(5 问):
  ✅ Q3 活着  ← L1 第一问 100%
  ✅ Q4 组织  ← L1 第二问 100% (今天收官)
  ⬜ Q5 任务  ← L1 第三问(下一站)
  ⬜ Q6 数据
  ⬜ Q7 接口
                                                2/5 = 40%
L2 生产(4 问): ⬜⬜⬜⬜                               0/4 = 0%
L3 进阶(3 问): ⬜⬜⬜                                0/3 = 0%

总进度:2/14 = 14.3%
```

**L1 已完成 40%**(Q3+Q4),Q5 是 L1 第三问,跟 Q3+Q4 是递进关系:
- **Q3** = 软件活着时(运行时)
- **Q4** = 代码静态时(组织)
- **Q5** = 一个任务怎么走完(任务流)—— 介于两者之间

下次开 /new 第一件事:用户拍板 Q5 走法
- 选 A:小任务(命令行解析 → 调度 → 输出)流程串一遍
- 选 B:从 main.py 改造出发,把"输什么 → 做什么 → 输出什么"串成任务
- 选 C:从 Q3+Q4 的产出反推,Q5 应该问什么子问题

---

*本轮 patch: md/patch_q4_day5.py*
*Q4 收官(主体+Day5),Day6 monorepo 远期预留*
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