# Proj 内置插件(Q7 Day2-3 完全版)
# ============================================================
# 这些 task 通过 pyproject.toml 的 entry_points 注册到 proj.plugins 组
# ============================================================

# shout:大写 + 感叹号
def shout(data: bytes) -> bytes:
    """Shout 任务:大写 + 加感叹号。"""
    return b"SHOUT: " + data.upper() + b"!"


# whisper:小写 + ...
def whisper(data: bytes) -> bytes:
    """Whisper 任务:小写 + 加 ...。"""
    return b"whisper: " + data.lower() + b"..."


# greet 模块
def hello(data: bytes) -> bytes:
    return b"hello: " + data


def bye(data: bytes) -> bytes:
    return b"bye: " + data


# math 模块
def double(data: bytes) -> bytes:
    try:
        n = int(data)
        return f"double: {n * 2}".encode("utf-8")
    except ValueError:
        return b"double: NaN"


def len_count(data: bytes) -> bytes:
    return f"len: {len(data)}".encode("utf-8")