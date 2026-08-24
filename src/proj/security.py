# src/proj/security.py
# ============================================================
# Proj 安全模块(Q10 Day2 出错怎么办 之 安)
# ============================================================
# 4 类防护(Q10 直接开发版的产出):
#   1. recv buffer 上限  → 防止内存爆炸
#   2. socket 超时        → 防止 Slowloris 攻击
#   3. plugin 签名校验    → 防止恶意 .py 冒充插件
#   4. entry_point 白名单 → 防止第三方包投毒
#
# 设计原则(Q8 Day2 一脉相承):
#   - 默认关闭,显式开启 — 教学项目不应破坏默认体验
#   - 渐进式 — 加固一步验证一步,不全做一起上
#   - 失败明确 — 出错就报错 + 拒绝,绝不静默忽略
#
# 不做的事(Q10 边界):
#   - 不做 TLS 加密(教学项目,本地通信)
#   - 不做访问控制(用户/密码),那是 Q11 观 + 业务
#   - 不做依赖漏洞扫描(那是 packaging 工具链)
# ============================================================

import os
import hmac
import hashlib
import socket
import logging

# ============================================================
# 1. recv buffer 上限(防内存爆炸)
# ============================================================
# Q10 设计:默认 64 KiB,够 echo 用,远小于内存边界
# 单条请求上限:超过即截断,不抛错(走 Q8 的 ERR_BAD_REQUEST)

DEFAULT_MAX_RECV = 65536  # 64 KiB


def safe_recv(conn: socket.socket, max_bytes: int = DEFAULT_MAX_RECV) -> bytes | None:
    """
    受控的 socket.recv() — 上限 + 单次收完就返回。

    返回:
        - bytes: 收到数据(可能为空,调用方要处理 not data → break)
        - None:  对端关闭 / 出错

    跟原 conn.recv(1024) 的区别:
        - 上限 64KB 而不是 1024 字节(教学项目够用)
        - 超过上限就抛 OverflowError,调用方 catch 走 ERR_BAD_REQUEST
        - 不做循环收(教学项目,单请求 < 64KB 足够)

    Q10 决定:单次 recv,够用就好;真要流式再升级。
    """
    try:
        data = conn.recv(max_bytes)
        return data
    except (ConnectionResetError, ConnectionAbortedError, OSError):
        return None


def set_recv_timeout(conn: socket.socket, seconds: float = 30.0) -> None:
    """
    设 socket 接收超时(防 Slowloris 攻击)。

    Slowloris = 客户端发极慢的字节,占住连接不释放,耗尽 server fd。
    加超时后,慢客户端会被自动踢掉。

    默认 30 秒,足够 echo 用,又不会让攻击者卡太久。
    """
    conn.settimeout(seconds)


# ============================================================
# 2. plugin 签名校验(HMAC-SHA256,防恶意 .py)
# ============================================================
# 思路:
#   - 开发者维护一个签名清单文件 (plugins/MANIFEST.sig)
#   - 每行: <plugin_name> <hex_hmac_sha256>
#   - 加载插件前先验签,验不过拒绝注册
#
# 密钥从哪里来:
#   - 环境变量 PROJ_PLUGIN_SECRET(部署时设置)
#   - 没设密钥 = 不校验(默认关闭,跟 Q8 Day2 一致)

# ============================================================
# 3. entry_point 白名单(防第三方包投毒)
# ============================================================
# 思路:
#   - 只接受白名单内的 group(默认 ["proj.plugins"])
#   - 别的 group 一律跳过
#
# 为什么不直接禁用:
#   - 教学项目要留扩展口子
#   - 但扩展必须显式声明(Q9 Day3 风格)
# ============================================================

DEFAULT_ALLOWED_ENTRY_POINT_GROUPS = frozenset({"proj.plugins"})


# ============================================================
# 4. HMAC 工具函数(给插件签名用)
# ============================================================

def compute_plugin_signature(
    plugin_path: str, secret: str | None = None
) -> str:
    """
    计算插件文件的 HMAC-SHA256 签名。

    参数:
        plugin_path: 插件 .py 文件路径
        secret: 密钥(默认从环境变量 PROJ_PLUGIN_SECRET 取)

    返回:
        16 进制签名字符串

    抛出:
        FileNotFoundError: 文件不存在
        ValueError: 没设密钥
    """
    if secret is None:
        secret = os.environ.get("PROJ_PLUGIN_SECRET")
    if not secret:
        raise ValueError(
            "缺少插件签名密钥 — 请设置环境变量 PROJ_PLUGIN_SECRET"
        )

    with open(plugin_path, "rb") as f:
        content = f.read()
    sig = hmac.new(
        secret.encode("utf-8"), content, hashlib.sha256
    ).hexdigest()
    return sig


def verify_plugin_signature(
    plugin_path: str, expected_sig: str, secret: str | None = None
) -> bool:
    """
    校验插件文件签名是否匹配。

    返回:
        - True: 匹配
        - False: 不匹配(签名不符 / 缺密钥 / 文件错)

    Q10 边界:没设密钥 = 不校验通过 = False
    (跟 Q8 一致:出错就近处理,不向调用方抛)

    用 hmac.compare_digest 防时序攻击。
    """
    if not expected_sig:
        return False
    try:
        actual = compute_plugin_signature(plugin_path, secret)
    except (FileNotFoundError, ValueError):
        return False
    return hmac.compare_digest(actual, expected_sig.lower())


def load_manifest(manifest_path: str) -> dict[str, str]:
    """
    加载签名清单文件。

    格式:每行 <plugin_name> <hex_hmac_sha256>
    注释行以 # 开头(空白也行)

    返回:
        {plugin_name: signature}

    抛出:
        FileNotFoundError: 清单不存在
    """
    if not os.path.isfile(manifest_path):
        raise FileNotFoundError(f"签名清单不存在: {manifest_path}")

    manifest: dict[str, str] = {}
    with open(manifest_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) != 2:
                continue  # 跳过格式不对的行
            name, sig = parts
            manifest[name] = sig
    return manifest


# ============================================================
# 5. 日志(Q10 复用 Q8 Day2 的 logger)
# ============================================================

_security_logger = logging.getLogger("proj.security")


def get_logger() -> logging.Logger:
    """返回 security 模块的 logger,需要时由调用方加 handler。"""
    return _security_logger