# src/server/_config.py
# 所有 server 共享的配置(Q4 Day2 引入)
# 下划线开头 = 内部 API(包外别引用)

import os

# === 网络 ===
HOST = "127.0.0.1"      # loopback,只听本机(Q3.2 Day4 安全姿势)
PORT = 8765             # 默认端口

# === 运行时产物 ===
# 隔离到 var/ 目录,跟源码分开(Q4 Day1 记账的 PID/log 混居问题,Day2 落地解决)
_VAR_DIR = "var"
PID_FILE = os.path.join(_VAR_DIR, "server.pid")
LOG_FILE = os.path.join(_VAR_DIR, "server.log")

# === 日志 ===
LOG_MAX_BYTES = 10 * 1024 * 1024   # 10 MB
LOG_BACKUP_COUNT = 3               # 保留 3 个轮转文件