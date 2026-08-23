# main.py -- 入口脚本（业务大脑）
# Q3.2 启动程序：被 boot.py 引导调用

def run():
    """业务入口函数：boot.py 会调用这个"""
    print("proj from main.py 入口脚本")
    print("我现在是 while True 常驻服务,等你输入 q 退出")
    while True:
        try:
            user_input = input(">>> 说点什么（输 q 退出）：")
        except EOFError:
            print("\n[main.py] 检测到 EOF,优雅退出")
            break
        if user_input == "q":
            print("[main.py] 收到 q,准备退出 while True 循环")
            break
        print(f"[main.py] 你说的是: {user_input}")


if __name__ == "__main__":
    # 双击或直接 python main.py 时走这里
    print("[main.py] 直接执行模式,跳过 boot.py")
    run()