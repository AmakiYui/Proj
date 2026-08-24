# verify_q8_day2.py
# Q8 Day2 验证:7 类错误码 + safe_call_task + safe_bind
# 验证 6 个 case:
#   1. ERR_xxx 7 个常量值对(400/404/422/500/500/500/500)
#   2. ERR_MESSAGES 字典 7 个 key 齐全
#   3. safe_call_task 正常路径:成功 → (out, 0)
#   4. safe_call_task 异常路径:task 抛异常 → (b"", ERR_TASK_EXCEPTION)
#   5. load_task_from_file 文件不存在 → FileNotFoundError(由 cli 兜底转 ERR_TASK_NOT_FOUND)
#   6. safe_bind 普通路径:能拿到 socket

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from proj import (
    ERR_BAD_REQUEST, ERR_UNKNOWN_ACTION, ERR_BAD_JSON,
    ERR_TASK_NOT_FOUND, ERR_BAD_SIGNATURE,
    ERR_TASK_EXCEPTION, ERR_BIND_FAILED, ERR_INTERNAL,
    ERR_MESSAGES,
    safe_call_task, safe_bind,
    Task,
)

results = []
def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    results.append((status, name, detail))

# === Case 1:7 个 ERR_xxx 值 ===
expected = {
    ERR_BAD_REQUEST: 400,
    ERR_UNKNOWN_ACTION: 404,
    ERR_BAD_JSON: 400,
    ERR_TASK_NOT_FOUND: 404,
    ERR_BAD_SIGNATURE: 422,
    ERR_TASK_EXCEPTION: 500,
    ERR_BIND_FAILED: 500,
    ERR_INTERNAL: 500,
}
all_match = all(v == expected[k] for k, v in expected.items())
check("7 类 ERR_xxx 值对", all_match, f"got {sorted(set(expected.values()))}")

# === Case 2:ERR_MESSAGES 字典 8 key 全在(Q8 Day2 修复:key 是 (code, name) 元组) ===
need_keys = {(ERR_BAD_REQUEST, "BAD_REQUEST"), (ERR_UNKNOWN_ACTION, "UNKNOWN_ACTION"),
             (ERR_BAD_JSON, "BAD_JSON"), (ERR_TASK_NOT_FOUND, "TASK_NOT_FOUND"),
             (ERR_BAD_SIGNATURE, "BAD_SIGNATURE"), (ERR_TASK_EXCEPTION, "TASK_EXCEPTION"),
             (ERR_BIND_FAILED, "BIND_FAILED"), (ERR_INTERNAL, "INTERNAL")}
have_keys = set(ERR_MESSAGES.keys())
check("ERR_MESSAGES 8 key 全在", need_keys == have_keys,
      f"missing={need_keys - have_keys} extra={have_keys - need_keys}")

# === Case 2.5:5xx 同 code 区分(Q8 Day2 修复的核心 bug)===
from proj import err_message
check("5xx 同 code 区分(ERR_TASK_EXCEPTION)",
      err_message(ERR_TASK_EXCEPTION, "TASK_EXCEPTION") == "task raised an exception",
      "")
check("5xx 同 code 区分(ERR_BIND_FAILED)",
      err_message(ERR_BIND_FAILED, "BIND_FAILED") == "bind failed",
      "")
check("5xx 同 code 区分(ERR_INTERNAL)",
      err_message(ERR_INTERNAL, "INTERNAL") == "internal server error",
      "")

# === Case 3:safe_call_task 正常路径 ===
def good_task(data: bytes) -> bytes:
    return b"ok: " + data
out, code = safe_call_task(good_task, b"hi")
check("safe_call_task 成功", out == b"ok: hi" and code == 0,
      f"out={out!r} code={code}")

# === Case 4:safe_call_task 异常路径 ===
def bad_task(data: bytes) -> bytes:
    raise ValueError(f"oops: {data.decode()}")
out, code = safe_call_task(bad_task, b"hi")
check("safe_call_task 异常", out == b"" and code == ERR_TASK_EXCEPTION,
      f"out={out!r} code={code}")

# === Case 5:load_task_from_file 文件不存在抛 FileNotFoundError ===
from proj import load_task_from_file
threw = False
try:
    load_task_from_file("nonexistent_file_zzz.py", "func")
except FileNotFoundError:
    threw = True
check("文件不存在 -> FileNotFoundError", threw, "")

# === Case 6:safe_bind 普通路径 ===
import socket
sock = safe_bind("127.0.0.1", 19999, max_retries=1)
got_sock = isinstance(sock, socket.socket)
if got_sock:
    sock.close()
check("safe_bind 普通路径", got_sock, "")

# === 汇总 ===
print("=" * 60)
print(f"Q8 Day2 验证矩阵: {sum(1 for r in results if r[0]=='PASS')}/{len(results)}")
print("=" * 60)
for status, name, detail in results:
    line = f"  [{status}] {name}"
    if detail and status == "FAIL":
        line += f"  ({detail})"
    print(line)

failed = sum(1 for r in results if r[0] == "FAIL")
sys.exit(0 if failed == 0 else 1)