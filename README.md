# Proj Public API(Q7 Day1 固化)

> 本文档是 Proj(Q7 Day1 起)对外承诺的稳定接口。任何不在本文档里的符号,都属于"内部实现",可能在未来版本中变动。

## 快速上手

```python
import sys
sys.path.insert(0, 'src')   # 或直接 pip install
import proj

# 1. 启动 CLI(Q4 Day2 入口)
proj.main()

# 2. 查内置 task
echo_task = proj.get_task('echo')       # bytes→bytes
json_echo = proj.get_json_task('echo')  # dict→dict

# 3. 加载外部 task(Q5 Day3-4)
task = proj.load_task_from_file('./md/my_tasks.py', 'my_func')
scanned = proj.scan_tasks_dir('./md/tasks/')

# 4. 构造错误响应(Q6 Day4)
err = proj.make_error(proj.ERR_BAD_REQUEST, 'json decode failed')
# → {"error": {"code": 400, "message": "json decode failed"}}
```

## 稳定 API 清单(14 项)

### 版本
| 名字 | 类型 | 说明 |
|---|---|---|
| `__version__` | `str` | 当前版本号(Q7 Day1:`"0.1.0"`) |

### 入口
| 名字 | 类型 | 说明 |
|---|---|---|
| `main` | `() -> int` | CLI 启动入口,等价于 `python -m src.proj.cli`,返回 exit code |

### Task 契约(Q5)
| 名字 | 类型 | 说明 |
|---|---|---|
| `Task` | `Callable[[bytes], bytes]` | 老契约:bytes → bytes,serve_loop 调的就是这个 |
| `Task2` | `Callable[[dict], dict]` | 新契约:dict → dict,Q6 JSON 协议用 |
| `BUILTIN_TASKS` | `dict[str, Task]` | 5 个内置 task:`echo / upper / lower / reverse / count` |
| `BUILTIN_TASKS_JSON` | `dict[str, Task2]` | 3 个内置 JSON task:`echo / upper / reverse` |
| `get_task(name)` | `(str) -> Task` | 按名取内置 task,未知回退 `echo` |
| `get_json_task(name)` | `(str) -> Task2` | 按名取内置 JSON task,未知回退 `json_echo` |

### 外部 Task 加载(Q5 Day3-4)
| 名字 | 类型 | 说明 |
|---|---|---|
| `load_task_from_file(path, func_name)` | `(str, str) -> Task` | 动态加载 .py 文件里的 task 函数,签名必须是 `(bytes) -> bytes` |
| `scan_tasks_dir(dir_path)` | `(str) -> dict[str, Task]` | 扫描目录下所有 .py,把签名合规的函数收成 task,key 格式 `"文件名::函数名"` |

### 错误码(Q6 Day4)
| 常量 | 值 | 含义 |
|---|---|---|
| `ERR_BAD_REQUEST` | `400` | 协议 / schema 错误(json 解析失败、字段类型错等) |
| `ERR_UNKNOWN_ACTION` | `404` | `action` 不在白名单(业务合法但未授权) |
| `ERR_BAD_JSON` | `400` | json 解析失败(复用 BAD_REQUEST 数字) |
| `make_error(code, message)` | `(int, str) -> dict` | 统一错误格式 `{"error":{"code":<int>,"message":"<str>"}}` |

## 错误码协议格式(Q6 Day4)

成功响应(以 echo 为例):
```json
{"echo": "hi"}
```

错误响应(三种格式,Q6 演进路径):
```
Q6 Day2:  {"error": "json decode failed"}            ← 字符串
Q6 Day4:  {"error": {"code": 400, "message": "..."}}  ← 字典(当前)
```

## 内部模块(用户不要碰)

虽然 `from src.proj import _config` 之类已被 Q7 Day1 拦截,但以下属于"已知内部":
- `src.proj._config` — 集中常量(HOST/PORT/PID 路径等)
