# src/proj/log_setup.py
# ============================================================
# Proj 统一日志配置(Q11 Day2 怎么看见 之 log 整合)
# ============================================================
# 之前(Q6 Day3 / Q10 Day2):
#   - proj.core.task.safe_call 有自己的 StreamHandler
#   - proj.security 有 logger 但没 handler
#   - server_pro 有自己的 logger + RotatingFileHandler
#   - proj.observability(新)有 logger 但没 handler
# 问题:
#   - 多 logger 多 handler,日志格式不一致
#   - 某些模块没 handler,WARNING 默认丢
#
# Q11 决定:
#   - 所有 proj.* logger 统一接到 root 配置
#   - 默认只输出到 stderr(简单)
#   - 设 PROJ_LOG_FILE 后追加 RotatingFileHandler
#   - 设 PROJ_LOG_LEVEL 改 level(默认 INFO)
#
# 设计原则(Q11):
#   - 幂等(多次 setup 不重复加 handler)
#   - 不破坏既有 handler(只补缺的)
#   - setup_logging() 一次性,后续各模块 getLogger 即可
# ============================================================

import os
import sys
import logging
from logging.handlers import RotatingFileHandler


def setup_logging(
    level: str | None = None,
    log_file: str | None = None,
    max_bytes: int = 1_048_576,  # 1MB
    backup_count: int = 3,
) -> logging.Logger:
    """
    配置 proj.* logger tree 的统一日志。

    参数:
        level: 日志级别(DEBUG/INFO/WARNING/ERROR),默认 INFO
        log_file: 日志文件路径,默认 None(只输出到 stderr)
        max_bytes: 单文件最大字节
        backup_count: 备份文件数

    返回:
        proj 根 logger(供调用方检查)

    用法:
        from src.proj.log_setup import setup_logging
        setup_logging()             # 默认 INFO + stderr
        setup_logging(level="DEBUG")
        setup_logging(log_file="var/proj.log")
    """
    if level is None:
        level = os.environ.get("PROJ_LOG_LEVEL", "INFO")
    if log_file is None:
        log_file = os.environ.get("PROJ_LOG_FILE")

    # proj 根 logger
    proj_logger = logging.getLogger("proj")
    proj_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # 格式
    fmt = logging.Formatter(
        "%(asctime)s [%(name)s] [%(levelname)s] %(message)s"
    )

    # 1. StreamHandler(stderr)— 默认就加
    if not any(isinstance(h, logging.StreamHandler) and h.stream == sys.stderr
               for h in proj_logger.handlers):
        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(fmt)
        proj_logger.addHandler(sh)

    # 2. FileHandler(可选)
    if log_file:
        if not any(isinstance(h, RotatingFileHandler) and h.baseFilename == os.path.abspath(log_file)
                   for h in proj_logger.handlers):
            os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)
            fh = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            fh.setFormatter(fmt)
            proj_logger.addHandler(fh)

    # 不让消息冒泡到 root(避免重复输出)
    proj_logger.propagate = False

    return proj_logger


def get_proj_logger(name: str) -> logging.Logger:
    """便捷函数:返回 proj.<name> logger,调用方应先 setup_logging()。

    name: 子模块名(不带 proj. 前缀),如 "core.task" -> "proj.core.task"
    """
    if not name.startswith("proj."):
        name = f"proj.{name}"
    return logging.getLogger(name)