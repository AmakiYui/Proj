# Proj 协同设计文档(Q14 Day2)

## 协同场景

Proj 从单机进程(单 server / 单进程 / 单 host)升级到多机协同,涉及三层:

```
[ Client ]                              [ Server Farm ]
   |                                         |
   |  ClientPool (round-robin)         +---- server A:8765 (alive)
   +--->-------------------------------+---- server B:8766 (alive)
                                        +---- server C:8767 (DEAD)
```

## 1. 服务发现(Q14 决策:静态列表 + health check)

### 1.1 策略
- **静态列表**(当前实现):客户端持有 `["h1:p1", "h2:p2"]`,启动前先 health check
- **动态发现**(Q14+ 工业):Consul/etcd,server 启动时注册,client 查询

### 1.2 健康检查集成
```python
pool = ClientPool(["h1:8765", "h2:8766"])
pool.health_check_all()  # 跑一次 HEALTH 命令,返回 {"h1:8765": "ok", ...}
```

每个 endpoint 有 `alive` 标志,失败 N 次后自动标记 dead,Q14+ 可做"复活机制"(留 Q14+)。

## 2. 负载均衡(3 种策略)

| 策略 | 实现 | 适合 |
|---|---|---|
| `round-robin`(默认) | 游标 +1 | server 同质 |
| `random` | random.choice | server 数多 + 简单 |
| `least-fail` | 按 fail_count 排序 | server 异构 / 容灾 |

```python
pool = ClientPool(endpoints, strategy="round-robin")
```

## 3. 失败转移(Failover)

server A 挂了,客户端自动切 B:

```
request -> [A: alive] -> send OK? return
           | fails 3x -> mark dead -> pick [B: alive] -> send OK? return
                                       | all dead -> raise ConnectionError
```

`fail_count` 阈值默认 3(`max_fails=3` 参数可调)。

## 4. 进程隔离(SafeTask / call_in_subprocess)

### 4.1 场景
恶意 task 代码(`import os; os.system('rm -rf /')`)不应该污染 server 主进程。

### 4.2 实现
- `SafeTask(task_fn)` 包装原 task
- 每次调用 `multiprocessing.Process` 起 worker 跑
- worker 死了不影响 server

```python
from src.proj.process_pool import SafeTask
safe = SafeTask(echo_task, timeout=5.0)
out = safe(b"hi")  # 实际在子进程跑
```

### 4.3 边界(Q14)
- **不做 sandbox**:没有 chroot/seccomp(那是 Q14+ 工业)
- **不做 rlimit**:没有 CPU/内存限制(那是 Q14+ 工业)
- **不做 worker 池**:1 task = 1 process(教学项目)

## 5. 告警(AlertEngine)

### 5.1 触发条件
Q11 收集 metrics,AlertEngine 定期 check,超阈值 WARNING:

```python
DEFAULT_THRESHOLDS = {
    "errors_total": 10,                    # 每检查周期超 10 触发
    "client_pool_failures_total": 5,
}
```

### 5.2 后台运行
```python
from src.proj.alert import AlertEngine
engine = AlertEngine()
engine.start_background(interval_sec=10)  # 每 10s check 一次
```

### 5.3 输出
默认写 `proj.alert` logger,可在 `log_setup.setup_logging()` 里统一配。

## 6. 部署拓扑

### 6.1 单机(默认)
```
127.0.0.1:8765
```

### 6.2 单机多 server(开发模拟)
```bash
# terminal 1
PROJ_PORT=8765 proj pro
# terminal 2
PROJ_PORT=8766 proj pro
# terminal 3 (client pool)
proj --hosts=127.0.0.1:8765,127.0.0.1:8766 --client-message=hi
```

### 6.3 多机(教学项目远景)
```
[ client ] -> [ h1:8765 ]
             -> [ h2:8765 ]
             -> [ h3:8765 ]
```

每个 host 跑 `proj pro`,client 用 `--hosts=h1:8765,h2:8765,h3:8765`。

## 7. 不做的事(Q14 边界)

- **服务网格**(Istio/Linkerd)— Q14+ 工业
- **mTLS** — Q14+ 安全
- **动态服务发现**(etcd/Consul)— Q14+ 工业
- **自动恢复**(自愈)— Q14+ 工业
- **告警通道**(email/slack)— Q14+ 工业

## 8. 验证矩阵

23/22 PASS(`verify_q14_day3.py`):

| 类别 | 通过 |
|---|---|
| ClientPool 基础 | 7 |
| ClientPool 端到端(mock server)| 4 |
| SafeTask 子进程隔离 | 4 |
| AlertEngine 触发 | 4 |
| CLI --hosts 集成 | 2 |
| __all__ 完整性 | 2 |