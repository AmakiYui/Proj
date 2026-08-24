# Proj 部署文档(Q12 Day2)

## 部署概览

Proj 是单进程 Python 应用,Q12 阶段目标:
- **单机生产**:wheel 装 + systemd 守护 + 健康检查
- **多机协同**:留 Q14 协同范畴

## 1. 安装

### 1.1 从 PyPI
```bash
pip install proj
proj --help
```

### 1.2 从本地 wheel(Q9 产出的 dist/)
```bash
cd Proj
python -m build
pip install dist/proj-0.1.0-py3-none-any.whl
```

### 1.3 开发模式(代码改动即时生效)
```bash
pip install -e .
```

## 2. 启动

### 2.1 命令行菜单
```bash
proj
# 或
python -m src.proj.cli
```

### 2.2 选风格
```bash
proj pro                    # 终极版(PID 文件 + 守护日志)
proj thread                 # 手搓多线程
proj pool                   # ThreadingMixIn
proj simple                 # 串行
```

### 2.3 选任务
```bash
proj pro --task=upper                    # 内置 task
proj pro --task-file=my.py --task-name=fn # 外部 task
proj pro --tasks-dir=tasks/ --task=greet::hello  # 目录扫描
proj pro --data-format=json --task=echo  # JSON 协议
```

## 3. 环境变量(Q12 部署切换)

| 变量 | 默认值 | 作用 |
|---|---|---|
| `PROJ_HOST` | `127.0.0.1` | server 绑定 host |
| `PROJ_PORT` | `8765` | server 绑定 port |
| `PROJ_METRICS` | (空) | `1` 启用 metrics 采集 |
| `PROJ_LOG_LEVEL` | `INFO` | 日志级别(DEBUG/INFO/WARNING/ERROR) |
| `PROJ_LOG_FILE` | (空) | 日志文件路径(空=只 stderr) |
| `PROJ_PLUGIN_SECRET` | (空) | 插件签名密钥(空=不校验) |

### 用法
```bash
# 部署到 0.0.0.0 + 8888
PROJ_HOST=0.0.0.0 PROJ_PORT=8888 proj pro --task=echo

# 启用 metrics + 日志落盘
PROJ_METRICS=1 PROJ_LOG_FILE=/var/log/proj.log proj pro
```

## 4. 健康检查(Q12 Day2)

### 4.1 协议(走现有 socket)
```
client -> server:  "HEALTH\n"
server -> client:  {"status":"ok","version":"0.1.0","uptime_seconds":123,...}\n
```

### 4.2 CLI 检查
```bash
# 检查本地 server
proj --health-check
# 输出:[OK] status=ok version=0.1.0 uptime=123.456s
# 退出码:0=健康 / 1=down

# 检查远程
proj --health-check --host=10.0.0.5 --port=8765
```

### 4.3 编程接口
```python
from src.proj import check_server, format_check_result

ok, payload = check_server(host="10.0.0.5", port=8765, timeout=5.0)
print(format_check_result(ok, payload))
```

## 5. systemd unit(进阶)

```ini
# /etc/systemd/system/proj.service
[Unit]
Description=Proj echo server
After=network.target

[Service]
Type=simple
User=proj
WorkingDirectory=/opt/proj
Environment="PROJ_HOST=0.0.0.0"
Environment="PROJ_PORT=8765"
Environment="PROJ_METRICS=1"
Environment="PROJ_LOG_FILE=/var/log/proj.log"
ExecStart=/usr/local/bin/proj pro --task=echo
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

启用:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now proj.service
sudo systemctl status proj.service

# 健康检查
proj --health-check --host=127.0.0.1 --port=8765
```

## 6. 升级流程(Q12 Day2)

1. **备份当前版本**:`pip freeze | grep proj`
2. **升级到新版本**:`pip install --upgrade proj==0.2.0`
3. **健康检查**:`proj --health-check`,确认 status=ok
4. **失败回滚**:`pip install proj==0.1.0`
5. **重启服务**:`sudo systemctl restart proj.service`

## 7. 监控(Q11 集成)

启用 metrics 后,Q11 的 dump_metrics() 可定时拉取:

```bash
# 简易轮询脚本
while true; do
  proj --health-check
  sleep 60
done
```

正式生产建议接 Prometheus / Grafana(留 Q14+ 工业级)。

## 8. 已知限制(Q12 边界)

- **单进程**:不支持水平扩展,横向协同留 Q14
- **无 TLS**:本地/内网用,公网部署前要加反向代理(Nginx/Caddy)
- **无访问控制**:Q10 只防了输入层,谁都能连 — 留 Q14
- **无自动升级**:手动 trigger,留 Q14

## 9. 故障排查

| 现象 | 可能原因 | 排查 |
|---|---|---|
| 健康检查 down | server 没起 | `systemctl status proj` |
| 连接被拒 | host/port 不对 | `netstat -an | grep 8765` |
| 任务找不到 | task 文件没加载 | `proj pro --task=...` 看菜单 |
| 指标没数据 | PROJ_METRICS 没开 | `env | grep PROJ` |
| 日志没文件 | PROJ_LOG_FILE 没设 | `journalctl -u proj.service` |