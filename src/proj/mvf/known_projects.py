# src/proj/mvf/known_projects.py
# ============================================================
# 已知的"项目填法" — 跨项目 MVF 对照
# ============================================================
# 每次分析一个新项目,就新增一个 entry,沉淀到 MVF 模式库。
# ============================================================

from ._base import Slot


def _make_slot(question: str, fill: str) -> Slot:
    class _S(Slot):
        def __init__(self):
            self.question = question
            self.default_fill = fill
        def check(self) -> bool:
            return True
    return _S()


# ============================================================
# Proj:14 问方法论的教学实例(Python,单包)
# ============================================================
PROJ_FILLS = {
    1: _make_slot("为什么有这个软件?解决什么问题?", "教学项目:演示 echo 协议 + 14 问方法论"),
    2: _make_slot("关键架构决策?哪些 trade-off?", "包边界 + 任务契约 + 错误协议(L1/L2/L3 4 层划分)"),
    3: _make_slot("进程怎么起来?怎么接收输入?", "socketserver + 4 种并发风格(simple/thread/pool/pro)"),
    4: _make_slot("包怎么分?模块边界在哪?", "src/proj 包结构 + 单层业务隔离"),
    5: _make_slot("任务的最小契约是什么?输入输出?", "Task = bytes -> bytes(纯函数,可缓存)"),
    6: _make_slot("数据在内存/磁盘/线上是什么形态?", "bytes 主体 + Task2 dict 升级(schema 校验 + 错误码)"),
    7: _make_slot("对外 API 是什么?怎么保证稳定?", "__all__ + __version__ + pyproject.toml + entry_points + pyi"),
    8: _make_slot("错误怎么分类?怎么响?怎么恢复?", "7 类 ERR_xxx 错误码 + safe_call_task + safe_bind"),
    9: _make_slot("怎么打包?怎么分发?怎么升级?", "wheel + sdist + pyproject + CHANGELOG + README + --version"),
    10: _make_slot("谁能调?谁能改?谁能发?", "safe_recv + HMAC 插件签名 + entry_point 白名单"),
    11: _make_slot("运行时指标?日志?告警?", "Counter/Gauge/Histogram + setup_logging + dump_metrics"),
    12: _make_slot("怎么装?怎么启?怎么查健康?", "systemd unit + HEALTH 命令 + PROJ_HOST/PORT 环境变量"),
    13: _make_slot("怎么测?怎么找瓶颈?怎么改?", "benchmark.py + memoize + Histogram 复用"),
    14: _make_slot("多机怎么通信?怎么分流?怎么隔离?", "ClientPool + SafeTask + AlertEngine + multiprocessing"),
}


# ============================================================
# OpenClaw:跨 surface AI agent 框架(TypeScript / monorepo)
# ============================================================
OPENCLAW_FILLS = {
    1: _make_slot("为什么有这个软件?解决什么问题?",
                  "跨 surface(CLI/TUI/Web/Gateway)AI agent,内置 runtime 统一多端体验"),
    2: _make_slot("关键架构决策?哪些 trade-off?",
                  "monorepo + packages/* 子包边界 + openclaw/plugin-sdk barrel 暴露;legacy pi runtime 已被 openclaw 取代"),
    3: _make_slot("进程怎么起来?怎么接收输入?",
                  "Node.js 入口 src/index.ts -> runCli() (Promise 异步 + isMainModule 守护); 版本快路径 entry.version-fast-path"),
    4: _make_slot("包怎么分?模块边界在哪?",
                  "src/(内置)+ packages/(22 子包)+ skills/(功能插件);边界规则:plugin-sdk/* barrel 暴露,src/** 禁止外部 import"),
    5: _make_slot("任务的最小契约是什么?输入输出?",
                  "Agent turn(消息列表 -> 响应 + 工具调用);packages/agent-core/agent-loop.ts 60178 字节核心 turn"),
    6: _make_slot("数据在内存/磁盘/线上是什么形态?",
                  "message 流 + transcript + 工具调用 JSON;compaction 长会话压缩 + turn-interruption + reasoning 思维链"),
    7: _make_slot("对外 API 是什么?怎么保证稳定?",
                  "package.json exports 字段 + .d.ts 类型 + monorepo 子包分桶(@openclaw/agent-core 等)"),
    8: _make_slot("错误怎么分类?怎么响?怎么恢复?",
                  "errors.ts + infra/errors.ts + infra/fatal-error-hooks.ts + infra/unhandled-rejections.ts;运行时 hook 系统 agent-hooks/(compaction safeguard 等)"),
    9: _make_slot("怎么打包?怎么分发?怎么升级?",
                  "monorepo + patches/ + .crabbox.yaml;多包发布(@openclaw/agent-core/plugin-sdk/llm-core 等各自发)"),
    10: _make_slot("谁能调?谁能改?谁能发?",
                  "security/ 目录 + opengrep/(semgrep 自定义规则)+ qa/;内置 CI 集成"),
    11: _make_slot("运行时指标?日志?告警?",
                  "docs/logging.md 结构化日志;infra/logger + infra/unhandled-rejections;LLM agent 关注 token/latency 而非 RPS"),
    12: _make_slot("怎么装?怎么启?怎么查健康?",
                  "deploy/fly.private.toml(Fly.io)+ docker-build-cache + dockerfile + docker-healthcheck;多 surface(CLI/TUI/gateway)"),
    13: _make_slot("怎么测?怎么找瓶颈?怎么改?",
                  "LLM agent 性能 = token cost + provider latency,不是 socket RPS;docs 里应该有 token 测速脚本"),
    14: _make_slot("多机怎么通信?怎么分流?怎么隔离?",
                  "acp-runtime.ts + acp-runtime-backend.ts(ACP = Agent Communication Protocol);跨进程/跨 surface 协调"),
}


# ============================================================
# 注册表:已知项目名 -> fills
# ============================================================
KNOWN_PROJECTS = {
    "Proj": PROJ_FILLS,
    "OpenClaw": OPENCLAW_FILLS,
}


def is_known(name: str) -> bool:
    return name in KNOWN_PROJECTS


def get_fills(name: str):
    return KNOWN_PROJECTS.get(name)