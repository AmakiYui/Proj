# client.py  —— 极简客户端:连一次、收一行、断开
import os
import sys
import socket

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HOST = "127.0.0.1"
PORT = 8765


def send(msg: str) -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    s.sendall(msg.encode("utf-8") + b"\n")
    data = s.recv(1024)
    s.close()
    return data.decode("utf-8", "replace").strip()


if __name__ == "__main__":
    # 默认发 proj,允许命令行参数覆盖
    msg = sys.argv[1] if len(sys.argv) > 1 else "proj"
    print(send(msg))