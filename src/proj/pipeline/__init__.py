# src/proj/pipeline/__init__.py
# ============================================================
# Pipeline:想法 -> MVF -> 完整软件
# ============================================================
# 4 步:
#   1. idea_to_mvf:文本想法 -> 14 维填法(本轮:A1 阶段)
#   2. mvf_to_mvp:14 维填法 -> 最小脚手架代码(未来)
#   3. add_module:给 MVP 加单个 slot 模块(未来)
#   4. finalize:跑通 verify + 文档 + commit(未来)
#
# 设计原则:
#   - 启发式优先,不依赖 LLM
#   - 关键词匹配覆盖最常见软件形态
#   - 每个 Q 有明确的关键词集合
# ============================================================

from . import idea_parser
from .idea_parser import parse_idea, IdeaToMVFError, HEURISTIC_Q_KEYWORDS