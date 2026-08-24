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
- `src.proj.cli` — argparse 实现,业务走 `main()`
- `src.proj.core.echo_server` — serve_loop + 4 种并发风格实现
- `src.proj.core.task` — task 实现细节,但契约已在 `__all__` 暴露

## 设计决策记录

| Day | 决策 | 原因 |
|---|---|---|
| Q4 Day2 | 集中 `_config.py` | 常量集中地,避免散落 |
| Q4 Day3 | `from .X import Y` 后 delattr | Python 会把 X 注进包 namespace,要手动清 |
| Q5 Day1 | task = bytes→bytes 纯函数 | 跟 serve_loop 解耦,task 不依赖 socket |
| Q5 Day2 | BUILTIN_TASKS 注册表 | 数据驱动派发,加新 task 零改 serve_loop |
| Q5 Day3 | importlib 不污染 sys.modules | 外部 task 用唯一 module_name |
| Q5 Day4 | "q" 协议留在 serve_loop | 管道协议不污染 task 契约 |
| Q6 Day1 | 数据三维框架(形态/边界/格式) | 任何序列化问题都套这个 |
| Q6 Day2 | 双契约(Task/Task2)共存 | 向后兼容,老接口不破 |
| Q6 Day3 | 校验返回 (bool, str) 元组 | 优雅路径,不抛异常 |
| Q6 Day4 | 错误码 + 错误消息 双字段 | code 给机器,message 给人 |

## 升级指南

**从 Q6 升到 Q7(API 视角):**
- 无破坏性变更
- 新增 `__version__`(任何用户脚本可读)
- 新增 `__all__` 显式公共清单
- `from src.proj import _config` 不再工作(改用 `proj.main()` 走默认配置,或从 `src.proj._config` 直接 import)

**未来版本(规划):**
- Q8 错 / Q9 演 / Q10 安 / Q11 观 会决定 `__version__` 演进策略(可能加 `__version_info__`)
- 第三方插件系统会引入 `entry_points`,见未来 API 提案