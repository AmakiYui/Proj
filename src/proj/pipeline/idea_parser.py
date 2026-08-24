# src/proj/pipeline/idea_parser.py
# ============================================================
# 想法解析器(启发式)
# ============================================================
# 输入:一段文本(可中文/英文)
# 输出:14 维 MVF 填法(每维 question + default_fill)
#
# 不依赖 LLM,基于关键词匹配:
#   - 每个 Q 有"必含"和"可选"关键词
#   - 文本分句,匹配最佳
#   - 没匹配的 Q 走"待人工填"标记
#
# 用法:
#   from proj.pipeline.idea_parser import parse_idea
#   fills = parse_idea("我想做一个命令行 todo 工具,支持加密同步,...")
#   for q, slot in fills.items():
#       print(q, slot.question, slot.default_fill)
# ============================================================

import re
from typing import Dict, List, Tuple

from ..mvf._base import Slot


class IdeaToMVFError(Exception):
    """解析失败时抛。"""


# ============================================================
# 关键词表:每个 Q 一组中英文关键词 + 默认模板
# ============================================================
HEURISTIC_Q_KEYWORDS: Dict[int, Dict] = {
    1: {  # 起源
        "must": [],  # 不强匹配,所有想法都过
        "hints": ["为什么", "动机", "解决", "想法", "想要", "目的",
                  "why", "solve", "purpose", "goal", "need"],
        "template": "用户提供的想法,意图解决特定问题",
    },
    2: {  # 设计
        "must": [],
        "hints": ["架构", "选型", "包", "依赖", "设计", "决策",
                  "architecture", "stack", "framework", "choose"],
        "template": "项目类型待定(CLI / Web / AI / ...)+ 关键依赖待选",
    },
    3: {  # 运行时
        "must": [],
        "hints": ["服务器", "server", "启动", "入口", "进程", "listen",
                  "cli", "命令行", "tui", "web", "api"],
        "template": "默认 CLI 入口,具体并发模型待选(simple / async / thread)",
    },
    4: {  # 组织
        "must": [],
        "hints": ["包", "目录", "模块", "src/", "monorepo",
                  "package", "folder", "layout"],
        "template": "src/<pkg>/ 单包结构 + 单层业务隔离",
    },
    5: {  # 任务
        "must": [],
        "hints": ["命令", "功能", "动作", "操作", "do", "command",
                  "function", "action", "feature"],
        "template": "任务为最小动作单元,输入输出形态待定义",
    },
    6: {  # 数据
        "must": [],
        "hints": ["数据", "存储", "数据库", "文件", "json", "sqlite",
                  "data", "storage", "db", "file", "format"],
        "template": "内存数据结构 + 持久化方案待选(json / sqlite / db)",
    },
    7: {  # 接口
        "must": [],
        "hints": ["api", "sdk", "对外", "公开", "导出", "export",
                  "interface", "public"],
        "template": "__all__ 导出 + 版本号 + 入口文档",
    },
    8: {  # 错误
        "must": [],
        "hints": ["错误", "异常", "处理", "err", "error",
                  "exception", "handle", "retry"],
        "template": "基础错误捕获 + 错误码体系待定义",
    },
    9: {  # 长大
        "must": [],
        "hints": ["打包", "发布", "分发", "部署", "package",
                  "publish", "deploy", "wheel", "pypi", "npm"],
        "template": "wheel + sdist + pyproject + CHANGELOG",
    },
    10: {  # 安全
        "must": [],
        "hints": ["安全", "权限", "鉴权", "校验", "防护",
                  "security", "auth", "permission", "validate"],
        "template": "输入校验 + 默认安全策略(白名单 / 长度上限)",
    },
    11: {  # 观测
        "must": [],
        "hints": ["日志", "监控", "指标", "metric", "log",
                  "monitor", "trace", "alert"],
        "template": "基础日志 + 关键 metric(请求数 / 错误数 / 延迟)",
    },
    12: {  # 部署
        "must": [],
        "hints": ["部署", "docker", "systemd", "上线",
                  "deploy", "ci", "release"],
        "template": "systemd unit 模板 + 健康检查 + 环境变量映射",
    },
    13: {  # 性能
        "must": [],
        "hints": ["性能", "压测", "基准", "缓存", "优化",
                  "performance", "benchmark", "cache", "optimize"],
        "template": "benchmark.py 压测脚本 + memoize 缓存装饰器",
    },
    14: {  # 协同
        "must": [],
        "hints": ["多机", "多进程", "集群", "队列", "负载均衡",
                  "distributed", "queue", "load", "cluster"],
        "template": "ClientPool 多机客户端 + SafeTask 进程隔离 + AlertEngine",
    },
}


# ============================================================
# 启发式打分函数
# ============================================================

def _tokenize(text: str) -> List[str]:
    """中英文简单分词(空格 + 字符)。"""
    text = text.lower()
    # 中文按字符切,英文按空格切
    tokens = []
    for part in text.split():
        tokens.extend(re.findall(r"[\u4e00-\u9fff]+|[a-z]+", part))
    return [t for t in tokens if t]


def _score_q(text: str, q: int) -> int:
    """给一个 Q 打分,匹配数越多分数越高。

    中英文都支持:
    - 中文 hint:在 text 里 substring 匹配(中文无空格)
    - 英文 hint:在 tokens 里精确匹配(避免子串误伤)
    """
    cfg = HEURISTIC_Q_KEYWORDS[q]
    text_lower = text.lower()
    tokens = set(text_lower.split())
    score = 0
    for h in cfg["hints"]:
        h_lower = h.lower()
        if not h_lower:
            continue
        # 中文 hint(有 CJK):substring
        if re.search(r"[\u4e00-\u9fff]", h_lower):
            if h_lower in text:
                score += 1
        # 英文 hint:精确 token 匹配
        else:
            if h_lower in tokens:
                score += 1
    return score


def _pick_best_q(text: str) -> int:
    """从所有 Q 里挑最高分的(用于语义不明的句子归类)。"""
    scores = {q: _score_q(text, q) for q in range(1, 15)}
    best_q = max(scores, key=scores.get)
    if scores[best_q] == 0:
        # 启发式不命中,归到 Q1 起源
        return 1
    return best_q


# ============================================================
# 主函数
# ============================================================

def parse_idea(idea: str, app_name: str = "myapp") -> Dict[int, Slot]:
    """把一段文本想法拆成 14 维 MVF 填法。

    Args:
        idea:用户想法(可长可短,支持中文/英文)
        app_name:应用名(用于生成的 slot 标识)

    Returns:
        dict[q, Slot]:14 个 slot,Q1-Q14 全覆盖

    Raises:
        IdeaToMVFError:输入为空或异常
    """
    if not idea or not idea.strip():
        raise IdeaToMVFError("idea 不能为空")

    # 1. 拆句(中文按。!? 拆,英文按 .!? 拆,逗号也拆)
    sentences = re.split(r"[。.!?\n,;]+", idea)
    sentences = [s.strip() for s in sentences if s.strip()]

    # 2. Q1 起源 = 第一句(或整段)
    q1_fill = idea[:200] + ("..." if len(idea) > 200 else "")

    # 3. 其余句子按关键词分桶到对应 Q
    q_buckets: Dict[int, List[str]] = {q: [] for q in range(1, 15)}
    q_buckets[1].append(q1_fill)
    for sent in sentences:
        best_q = _pick_best_q(sent)
        if best_q == 1:
            # 防止 Q1 重复(避免起源被分走)
            q_buckets[1].append(sent)
        else:
            q_buckets[best_q].append(sent)

    # 4. 装配 slot
    result: Dict[int, Slot] = {}
    for q in range(1, 15):
        cfg = HEURISTIC_Q_KEYWORDS[q]
        bucket = q_buckets[q]
        if bucket:
            fill = "; ".join(bucket[:3])  # 最多取 3 句
            if len(bucket) > 3:
                fill += f" (+{len(bucket) - 3} more)"
        else:
            fill = cfg["template"] + " [未匹配启发式,需人工填]"

        result[q] = _make_slot(q, cfg, fill, app_name)

    return result


def _make_slot(q: int, cfg: Dict, fill: str, app_name: str) -> Slot:
    """装配一个 slot。"""
    question = _question_text(q)

    class _S(Slot):
        def __init__(self):
            self.question = question
            self.default_fill = fill
            self._app_name = app_name
        def check(self) -> bool:
            return "未匹配" not in self.default_fill
        def describe(self) -> str:
            tag = "[USER]" if "未匹配" not in self.default_fill else "[TODO]"
            return (f"{tag} Q{q} {self.question}\n"
                    f"     fill: {self.default_fill}")
    return _S()


def _question_text(q: int) -> str:
    """Q 的问句文本。"""
    questions = {
        1: "为什么有这个软件?解决什么问题?",
        2: "关键架构决策?哪些 trade-off?",
        3: "进程怎么起来?怎么接收输入?",
        4: "包怎么分?模块边界在哪?",
        5: "任务的最小契约是什么?输入输出?",
        6: "数据在内存/磁盘/线上是什么形态?",
        7: "对外 API 是什么?怎么保证稳定?",
        8: "错误怎么分类?怎么响?怎么恢复?",
        9: "怎么打包?怎么分发?怎么升级?",
        10: "谁能调?谁能改?谁能发?",
        11: "运行时指标?日志?告警?",
        12: "怎么装?怎么启?怎么查健康?",
        13: "怎么测?怎么找瓶颈?怎么改?",
        14: "多机怎么通信?怎么分流?怎么隔离?",
    }
    return questions[q]