# boot.py -- 引导程序（bootstrap / loader）
# Q3.2 启动程序的第 2 层：只负责"加载并启动入口脚本"，不写业务逻辑

import sys, os
# pyinstaller 打包后默认 cp1252,这里强制 UTF-8 解码中文 print
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

print("[boot.py] 我是引导程序,启动中...")
print(f"[boot.py] Python 版本: {sys.version}")

# 第 1 步：加载入口脚本
print("[boot.py] 正在加载入口脚本 main.py ...")
import main   # ← 这里会执行 main.py 顶层代码(if __name__ 不算)

# 第 2 步：调用入口脚本的业务函数
print("[boot.py] main.py 加载完成,准备调用 main.run() ...")
try:
    main.run()
except KeyboardInterrupt:
    print("\n[boot.py] 收到 Ctrl+C,引导程序接管,优雅退出")
except Exception as e:
    print(f"[boot.py] main.run() 出错: {e}")

# 第 3 步：引导程序收尾
print("[boot.py] 引导程序 run() 执行完毕,退出")