# md/tasks/math.py
# Q5 Day4:目录扫描模式下的 task 文件之二
# 演示一个 .py 多函数都能被发现

def double(data: bytes) -> bytes:
    """重复两遍"""
    return b"x2: " + data + data


def len_count(data: bytes) -> bytes:
    """字节数(跟内置 count 不同:这里返回纯数字无前缀)"""
    return str(len(data)).encode("utf-8")


# 这个故意不签名合规,看扫描会不会跳过
def not_a_task():
    return "ignored"