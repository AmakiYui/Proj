# 示例插件(Q7 Day2-3):shout / whisper
# 用 register_task 注册演示

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, '.')

import proj


def shout(data: bytes) -> bytes:
    """大写 + 加感叹号。"""
    return b"SHOUND: " + data.upper() + b"!"


def whisper(data: bytes) -> bytes:
    """小写 + 加 ...。"""
    return b"whisper: " + data.lower() + b"..."


# 显式注册
proj.register_task("shout", shout)
proj.register_task("whisper", whisper)

# 也演示直接调用(注册后跟 BUILTIN_TASKS 等价)
if __name__ == "__main__":
    print("已注册插件 task:", list(proj.get_plugin_tasks().keys()))
    print("shout('hi')    =", proj.get_plugin_tasks()["shout"](b"hi"))
    print("whisper('HI')  =", proj.get_plugin_tasks()["whisper"](b"HI"))