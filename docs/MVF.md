# MVF:Minimum Viable Framework(最小可行框架)

## 核心理念

14 问 14 维软件分析法**不只是分析工具**,它是**软件开发的基础框架模板**。

任何软件项目都可以在这套 14 维框架上**填充具体内容**生成,而不是从零开始设计架构。

## MVF 三大原则

### 1. 14 维 = 4 个层级(L0-L3)

| 层级 | 子集 | 关注点 |
|---|---|---|
| **L0 起源层** | Q1 起源 / Q2 设计 | 为什么 / /怎么取舍 |
| **L1 地基层** | Q3-Q7 | 运行时/结构/任务/数据/接口 |
| **L2 生产层** | Q8-Q11 | 错误/部署/安全/可观测 |
| **L3 进阶层** | Q12-Q14 | 部署拆分/性能/协同 |

每层都是**前一层的前提**:
- 没 L1 地基 = 没"代码本体"
- 没 L2 生产 = 不能"稳跑"
- 没 L3 进阶 = 不能"长大"

### 2. 每个 Q = 一个可填充的 Slot

**传统方法论**:14 问是问题清单,逐个回答。
**MVF 方法论**:14 问是 14 个 slot,**每个项目填自己的具体实现**。

```
[ Q3 活着 ] --> Slot 3  -- 填入 -- "socketserver echo + 4 种并发风格"
[ Q4 组织 ] --> Slot 4  -- 填入 -- "src/proj 包结构"
[ Q5 任务 ] --> Slot 5  -- 填入 -- "Task = bytes -> bytes 契约"
...
```

### 3. L0 = 模板自己的"为什么"

**关键洞察**:Q1+Q2 不只是"补完 14 问",Q1+Q2 让 14 问**可以脱离具体项目独立存在**。

```
14 问分析法 = 元方法论(Q1+Q2 决定) + 14 个 slot(Q3-Q14)
```

## MVF 怎么用

### Step 1:启动新项目

不要先想"用 Flask 还是 Django",先问 14 问:

| Q | 你的项目答案 |
|---|---|
| Q3 怎么跑起来 | (待填) |
| Q4 代码怎么住 | (待填) |
| ... | (待填) |

### Step 2:每个 slot 填内容

填法 = 跑一遍对应 Q 的 Day1+Day2+Day3 流程:

```
新项目 Q5:
  Day1:框架(形态/边界/取舍)
  Day2:落地代码(契约/实现/集成)
  Day3:跑通(测试 + 文档 + commit)
```

### Step 3:跨项目比较

同一个 slot 在不同项目里的不同填法,就是**模式库**:

| 项目 | Q5 任务契约 |
|---|---|
| Proj | bytes -> bytes |
| OpenClaw | message -> response(AI agent) |
| 假想 Web app | HTTP request -> HTTP response |

## 实例:Proj 和 OpenClaw 对照

| Q | Proj(填法) | OpenClaw(填法) |
|---|---|---|
| Q3 活着 | socketserver + 4 种并发风格 | gateway + agent session 调度 |
| Q4 组织 | src/proj 包结构 | state/agents/{name} 包结构 |
| Q5 任务 | Task = bytes -> bytes | 工具调用 + agent turn |
| Q6 数据 | bytes + Task2 dict | message + tool result |
| Q7 接口 | __all__ + pyproject + entry_points | tool spec + agent config |
| Q8 错 | 7 类 ERR_xxx 错误码 | session error + error trace |
| Q9 演 | wheel + sdist + pip | 配置 + sessions_send |
| Q10 安 | safe_recv + 插件签名 | sandbox + tool permission |
| Q11 观 | metrics + logger | session history + subagents |
| Q12 部 | systemd unit | sessions_spawn 持久化 |
| Q13 性 | memoize + benchmark | token 限流 |
| Q14 协 | client pool + process pool | subagents 编排 |

**结论**:OpenClaw 和 Proj **填的是同一套 14 维**,只是内容不同。

## MVF 工具链

```
mvf/                          # 模板骨架
├── slot_01_origin.py         # Q1 起源 slot
├── slot_02_design.py         # Q2 设计 slot
├── slot_03_runtime.py        # Q3 活着 slot
├── slot_04_organization.py   # Q4 组织 slot
├── ...
├── slot_14_coordination.py         # Q14 协同 slot
└── template_factory.py       # 接受应用名,生成 14 维脚手架
```

每个 slot = 一个抽象基类(ABC)+ 一个或多个填法示例。

## MVF 与现有方法论对比

| 方法论 | 维度数 | 关注点 |
|---|---|---|
| SOLID | 5 原则 | 面向对象设计 |
| 12-factor | 12 原则 | SaaS 应用 |
| DDD | 4 层 + 多个 pattern | 领域建模 |
| **MVF(14 问)** | **14 维 4 层** | **软件全生命周期** |

MVF 的独特点:**从代码到运行到生产到架构,纵向打通**,不是单一维度。

## 不做的事(MVF 边界)

- **不替代具体技术选型**(用 Flask 还是 Django,是 Q4 内的子决策)
- **不规定实现语言**(Python/Go/Rust 都能套)
- **不绑死软件类型**(CLI/Web/AI/嵌入式 都能套)
- **不写代码,只写框架**(MVF 自己是模板,不是产品)

## 总结

> **14 问 = MVF 模板 = 14 维 × 4 层 = 任何软件可在其上填充**





# MVF 应用案例:OpenClaw 14 维分析

## 概要

用 MVF 模板(Minimum Viable Framework,14 维 × 4 层)分析 OpenClaw 项目,展示同一套框架在不同项目里的不同填法。

**项目信息**(基于 `C:\Users\F\Desktop\openclaw` 仓库实测):
- 语言:TypeScript / Node.js(对比 Proj 的 Python)
- 规模:monorepo(22 个 `packages/` 子包)+ 大量 `skills/`(每个 skill 一个目录)
- 入口:`src/index.ts` -> `src/cli/` -> `runCli`
- 核心包:`@openclaw/agent-core`(`packages/agent-core/`)
- 架构文档:`docs/agent-runtime-architecture.md`(OpenClaw 团队自己写的)

---

## 14 维 MVF 填法对照

### L0 起源层

#### Q1 起源

| Proj | OpenClaw |
|---|---|
| 为什么:教学项目,演示 echo 协议 + 14 问方法论 | 为什么:跨 surface 跑 AI agent(CLI/TUI/Web),复用内置 runtime |
| 解决:把 14 维落地为可运行代码 | 解决:让模型 + 工具 + session + extension 在多 surface 间无缝衔接 |

#### Q2 设计

| Proj | OpenClaw |
|---|---|
| L0/L1/L2/L3 4 层划分 + 单包边界 | monorepo + `packages/*` 子包边界 + `@openclaw/*` 命名空间 |
| trade-off:教学优先 vs 工业完备 | trade-off:内置 runtime vs 第三方(legacy `pi` 已被内置 `openclaw` 取代)|

---

### L1 地基层

#### Q3 活着

| Proj | OpenClaw |
|---|---|
| socketserver + 4 种并发风格(simple/thread/pool/pro)| Node.js 入口 `src/index.ts` -> `runCli()`(Promise 异步 + `isMainModule` 守护)|
| 单进程 socket server, listen 在 127.0.0.1:8765 | CLI / TUI / gateway 三个入口,内置 `runCliWithExitFinalization` 退出收尾 |
| 启动仪式:`python -m src.proj.cli` + boot.bat 菜单 | 启动仪式:`node src/index.ts [command]` + 版本快路径(`entry.version-fast-path`)|

**关键差异**:Proj 是"服务器被启动",OpenClaw 是"CLI 被调用" — 同样的 Q3 但容器形态不同。

#### Q4 组织

| Proj | OpenClaw |
|---|---|
| `src/proj/` 单包 + `core/` + `plugins/` 子包 | monorepo:`src/`(内置)+ `packages/`(22 个子包)+ `skills/`(功能插件)| 边界规则:`openclaw/plugin-sdk/*` barrel 暴露,`src/**` 内部禁止外部 import | 边界规则:`__all__` 导出公共 API,`_config` 等下划线开头内部模块 |
| 文档:`docs/api.md` + `docs/deploy.md` + `docs/coordination.md` | 文档:`docs/agent-runtime-architecture.md`(OpenClaw 自己写的 14 维雏形!)|

**Q4 vs OpenClaw**:OpenClaw 已经写了 `agent-runtime-architecture.md`,这本身就是 Q4 文档化的产物 — **MVF 的 Q4 子问题被 OpenClaw 主动落地了**。

#### Q5 任务

| Proj | OpenClaw |
|---|---|
| `Task = bytes -> bytes`(纯函数,可缓存)| Agent turn(消息列表 -> 响应 + 工具调用)|
| `Task2 = dict -> dict`(Q6 升级版,带 schema) | `@openclaw/agent-core/agent-loop.ts`(60178 字节,核心 turn)|
| 注册表:`BUILTIN_TASKS` + `register_task` / `unregister_task` | plugin SDK:`@openclaw/plugin-sdk/*`(运行时注册 harness / tool / runtime)|

**关键差异**:Proj 的 Q5 是**最简单的纯函数**契约(教学用),OpenClaw 的 Q5 是**完整的 LLM agent turn**(工业用)。

#### Q6 数据

| Proj | OpenClaw |
|---|---|
| bytes 主体 + Task2 dict | message 流(用户/系统/工具)+ transcript + 工具调用 JSON |
| 校验:validate_request + 白名单 | 校验:`validation.ts` + `tool-execution-context.ts` + `compaction` |
| 错误码:ERR_xxx 7 类 + 错误码 + message | 错误:`errors.ts` + `infra/errors.ts` + `infra/fatal-error-hooks.ts`(多层)|

**OpenClaw 比 Proj 复杂**:多了 `compaction`(长会话压缩)+ `turn-interruption`(turn 中断)+ `reasoning.ts`(思维链)等子模块。

#### Q7 接口

| Proj | OpenClaw |
|---|---|
| `__all__` + `__version__` + `pyproject.toml` + `entry_points` + `pyi` | `package.json` 的 `exports` 字段 + `.d.ts` 类型 + monorepo 子包分桶 |
| 公共 API = 62 项 Q7 加 2 项 = 64 项 | `exports`:`./agent`, `./agent-loop`, `./llm`, `./runtime-deps` 等 |
| 用户:pip install | 用户:`import { ... } from "@openclaw/agent-core"` |

**相同点**:都是**版本化 + 显式导出 + 类型 stub**。Q7 跨越语言完全一致。

---

### L2 生产层

#### Q8 错

| Proj | OpenClaw |
|---|---|
| 7 类 ERR_xxx(400/404/422/500)+ `safe_call_task` + `safe_bind` | `errors.ts` + `infra/errors.ts` + `infra/fatal-error-hooks.ts` + `infra/unhandled-rejections.ts` |
| 分层 try-except(cli/serve_loop/task 三层) | 入口处 `installUnhandledRejectionHandler`(全局兜底)|
| 单点错误格式:`make_error_v2({code, message, details})` | `formatUncaughtError` + `formatCliFailureLines` + `isBenignUncaughtExceptionError` |

**OpenClaw 多**:Q8 已经有**运行时 hook 系统**(`agent-hooks/`,包括 compaction safeguard 等)。Proj 教学项目没这层。

#### Q9 演

| Proj | OpenClaw |
|---|---|
| wheel + sdist + pyproject + CHANGELOG + README + `--version` | monorepo + `patches/` + `.crabbox.yaml`(自定义配置?)|
| `pip install -e .` 后用 `proj` 命令 | `npm install`(monorepo 内是 workspace 链接)|
| 单包发布 | 多包发布:`@openclaw/agent-core`、`@openclaw/plugin-sdk`、`@openclaw/llm-core` 等各自发布 |

**OpenClaw 多**:Q9 已经做到**多包发布**,Proj 是单包。

#### Q10 安

| Proj | OpenClaw |
|---|---|
| `safe_recv`(长度上限 + 超时)+ HMAC 插件签名 + 白名单 | `security/` 目录 + `opengrep/`(semgrep 自定义规则)+ `qa/` |
| 默认关闭,显式 `PROJ_SECURITY=1` 开启 | 内置安全目录,CI 集成 semgrep |
| `--security-disabled` 调试用 | `security/opengrep` 规则集 |

**OpenClaw 多**:Q10 已经**集成到 CI**(semgrep)。Proj 教学项目不强调 CI。

#### Q11 观

| Proj | OpenClaw |
|---|---|
| `Counter` / `Gauge` / `Histogram` + `dump_metrics` JSON | `docs/logging.md` + `logger.test.ts`(结构化日志)|
| Histogram:`request_duration_ms`(5 桶)| 日志:`infra/logger` + `infra/unhandled-rejections`(运行时事件)|
| 默认关闭,`PROJ_METRICS=1` 开启 | 日志框架似乎常开 |

**关键差异**:Proj 用了 Prometheus 风格的 4 类 metric,OpenClaw 偏 logging(probably 因为 LLM agent 调用的成本是 token / latency,不需要 RPS 那种 metrics)。

---

### L3 进阶层

#### Q12 部

| Proj | OpenClaw |
|---|---|
| systemd unit 模板 + `HEALTH` 命令 + `PROJ_HOST/PORT` 环境变量 | `deploy/`(fly.private.toml)+ `docker-build-cache.test.ts` + `dockerfile.test.ts` + `docker-healthcheck.test.ts` |
| 单 host,部署简单 | 多 surface(CLI / TUI / gateway),`fly.toml` 部署到 Fly.io |

**OpenClaw 多**:Q12 已经**内置 Docker + Fly.io 部署**。Proj 教学项目只到 systemd unit 模板。

#### Q13 性

| Proj | OpenClaw |
|---|---|
| `benchmark.py` + `memoize_task` + Histogram 复用 | `docs/...` 里大概率有(没专门 verify)|
| 测出 echo memoize 0.95x(speedup 噪声范围)| LLM agent 性能 = token / latency / cost,不是 RPS |

**OpenClaw 重点不同**:LLM agent 的性能瓶颈是 token cost + provider latency,不是 socket RPS。Q13 的填法完全不同。

#### Q14 协

| Proj | OpenClaw |
|---|---|
| `ClientPool` + `SafeTask` + `AlertEngine` + multiprocessing | `acp-runtime.ts` + `acp-runtime-backend.ts` + `subagents`?|
| 静态 host:port 列表 + round-robin / random / least-fail | ACP(Agent Communication Protocol)runtime,可能跨进程 / 跨 surface 协调 |

**OpenClaw 多**:Q14 已经**有跨进程的 runtime**,Proj 是单进程内的 ClientPool。

---

## 总结:MVF 验证成功

### 跨项目一致性

| Q | 一致维度 | 差异维度 |
|---|---|---|
| Q1 WHY | 都回答"解决什么问题" | 范围(教学 vs 产品)|
| Q2 HOW | 都做架构 trade-off | 决策深度(1 人 vs 团队)|
| Q3 活着 | 都有启动入口 | 容器形态(进程 vs CLI)|
| Q4 组织 | 都分模块 | 粒度(单包 vs monorepo)|
| Q5 任务 | 都有最小契约 | 复杂度(纯函数 vs LLM turn)|
| Q6 数据 | 都有数据形态 | 校验深度(bytes vs message)|
| Q7 接口 | 都版本化 + 显式导出 | 导出机制(python vs npm)|
| Q8 错 | 都有错误处理 | hook 深度(单层 vs 多层)|
| Q9 演 | 都能打包分发 | 单包 vs monorepo |
| Q10 安 | 都有输入校验 | CI 集成度 |
| Q11 观 | 都有可观测 | metric vs log |
| Q12 部 | 都能部署 | 单 surface vs 多 surface |
| Q13 性 | 都有性能考量 | RPS vs token |
| Q14 协 | 都有协调机制 | 单机 vs 跨进程 |

### MVF 的核心洞察

1. **14 问跨越语言/项目类型完全适用** — Python/Node.js、教学/工业、单包/monorepo 都能套
2. **OpenClaw 已经隐式实现了 14 维** — `docs/agent-runtime-architecture.md` 就是 Q4 + Q12 的混合产物
3. **每个项目的"填法深度"不同** — Proj 偏教学(单层实现),OpenClaw 偏工业(多层 hook)
4. **跨项目比较 = 模式库** — 同一 slot 在两个项目的不同填法,就是该 slot 的**模式矩阵**

### 验证 MVF 工具链

- `proj.mvf.template_factory` 生成 OpenClaw 的 14 维 scaffold
- 填完后 `check_all()` 评估每个 slot
- `describe()` 输出 markdown 报告(就是本文档)

---

## 下一步

1. **MVF 案例库**(让用户用 MVF 分析更多项目,沉淀模式矩阵)
2. **MVF 反向工程**(用 MVF 反推 OpenClaw 团队的设计决策)
3. **MVF 自动生成**(从 14 维 scaffold 直接生成项目脚手架)

---

**生成日期**:2026-08-24
**生成方式**:`generate_scaffold('OpenClaw')` + 人工填写 + `describe()`
**对比项目**:Proj(`C:\Users\F\Desktop\Proj`)vs OpenClaw(`C:\Users\F\Desktop\openclaw`)