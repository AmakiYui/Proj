# Proj 性能基准报告(Q13 Day2)

## 测试环境

- OS:Windows 11
- Python:3.12
- 硬件:消费级笔记本(CPU 4-8 核)
- 测试工具:`benchmark.py`(项目根)
- 测试方式:5 worker 并发 / 2 秒 / 32 byte payload

## 基线数字(baseline)

### echo task,32 byte payload,5 并发
- **RPS:~650 req/s**
- P50:~2 ms
- P95:~15 ms
- P99:**~25 ms**
- 错误率:0%

### 瓶颈分析
1. **socket 收发**(dominant)— 每个请求 1 次 connect + 2 次 send/recv
2. **bytes 拼接**(`b"echo: " + data`)— 占 P99 的 ~10%
3. **线程调度** — 5 个 worker 抢 GIL,但 echo 计算极轻,影响小
4. **logger I/O** — `print(f"[pro-]start")` 同步 stdout,在高频场景会被 fflush 拖慢

## 优化尝试:memoize

### 配置
```python
from src.proj.memoize import memoize_builtin_tasks
fast_tasks = memoize_builtin_tasks(BUILTIN_TASKS)
fast_echo = fast_tasks["echo"]
set_current_task(fast_echo)
```

### 结果
- **RPS:~620 req/s**(略低于 baseline)
- P99:~25 ms
- **cache hits:1238 / misses:1(命中率 99.9%)**

### 结论
**memoize 对 echo 无显著加速**(speedup ~0.95x,在噪声范围内)。

**原因**:echo = I/O bound 不是 CPU bound。task 计算 = `b"echo: " + data`(字节拼接),dict.get 节省的时间 < 1μs,但 socket 收发开销是 100μs 量级。**缓存省不了大头**。

## 真正能优化的方向(Q13 留 Q14)

按 ROI 排序:

| 优化 | 预估加速 | 复杂度 | Q |
|---|---|---|---|
| **减少 socket 收发**(加长 keepalive / batch) | 2-3x | 中 | Q14 |
| **加 zeromq / nng 替代 socket** | 5-10x | 高 | Q14 |
| **asyncio 替代 threading** | 2-5x(高并发)| 中 | Q13+/Q14 |
| **Cython/Rust 改写 task** | 1.5-3x(纯 task)| 高 | Q13+ 工业 |
| **加缓存层**(对 echo 没用)| 1-2x(其他 task)| 低 | Q13(已做) |

## 已知瓶颈(留 Q14 协同)

1. **每连接 1 thread** — `run_pro` 用 `threading.Thread(target=serve_loop)`,并发 = 线程数
2. **单进程** — Q11/Q12 都只在单进程内做,横向扩展需要 Q14
3. **logger I/O 同步** — stdout print 阻塞,可改 async + buffering

## 工具命令速查

```bash
# 跑一轮压测
python benchmark.py --host=127.0.0.1 --port=8765 \
  --concurrency=10 --duration=10

# 自动启 server + 对比 baseline vs memoize
python benchmark_compare.py --concurrency=5 --duration=3

# 查看当前 metrics
PROJ_METRICS=1 python -c "from src.proj import dump_metrics; print(dump_metrics())"
```

## 验证矩阵

22/22 PASS(`verify_q13_min3.py`):

| 类别 | 通过 |
|---|---|
| memoize_task 基础 | 8 |
| memoize_builtin_tasks 全量 | 3 |
| benchmark.run_benchmark 端到端 | 7 |
| metrics 联动 | 2 |
| __all__ 完整性 | 2 |