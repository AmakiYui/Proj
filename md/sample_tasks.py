# md/sample_tasks.py
# Q5 Day3 演示:用户自定义 task 函数
# 这个文件不住在 src.proj 里,CLI 用 --task-file 动态加载

def upper_shout(data: bytes) -> bytes:
    """大声喊:全大写 + 三个感叹号"""
    return b"SHOUT: " + data.upper() + b"!!!"


def snake_reverse(data: bytes) -> bytes:
    """蛇形反转:小写 + 反转 + 点分隔"""
    return b"snake." + data.lower()[::-1] + b".end"


# 故意写个签名错的,看 Q5 Day3 校验能不能抓到
def bad_task(data: bytes, extra: str) -> bytes:
    """两个参数,会被 load_task_from_file 拒绝"""
    return data