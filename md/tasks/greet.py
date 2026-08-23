# md/tasks/greet.py
# Q5 Day4:目录扫描模式下的 task 文件之一
# 这整个目录都不会住在 src.proj 里——纯用户扩展

def hello(data: bytes) -> bytes:
    """打招呼:回 'hello: <原文>'"""
    return b"hello: " + data


def shout(data: bytes) -> bytes:
    """喊叫:大写 + !!!"""
    return b"SHOUT: " + data.upper() + b"!!!"