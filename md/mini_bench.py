# md/mini_bench.py
# Q13 Day3 mini benchmark demo
import sys, time, socket, threading
sys.path.insert(0, 'src')

from proj.core.task import echo_task, BUILTIN_TASKS
from proj.memoize import memoize_builtin_tasks
from proj.core.echo_server import serve_loop
import proj.core.echo_server as es

sys.path.insert(0, '.')
from benchmark import run_benchmark

# baseline
cfg_PORT = 18761
srv1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv1.bind(('127.0.0.1', cfg_PORT))
srv1.listen(50)

def serve1():
    while True:
        try:
            c, a = srv1.accept()
            serve_loop(c, a, echo_task, prefix='base')
        except:
            return

t1 = threading.Thread(target=serve1, daemon=True); t1.start()
time.sleep(0.3)

rep1 = run_benchmark('127.0.0.1', cfg_PORT, concurrency=5, duration=2.0, payload_size=32, label='baseline')
srv1.close()
print('baseline:', rep1['rps'], 'rps, p99=', rep1['latency_ms']['p99'])

# memoize
cfg_PORT = 18762
srv2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv2.bind(('127.0.0.1', cfg_PORT))
srv2.listen(50)

fast_all = memoize_builtin_tasks(BUILTIN_TASKS)
fast_echo = fast_all['echo']

def serve2():
    while True:
        try:
            c, a = srv2.accept()
            serve_loop(c, a, fast_echo, prefix='memo')
        except:
            return

t2 = threading.Thread(target=serve2, daemon=True); t2.start()
time.sleep(0.3)

rep2 = run_benchmark('127.0.0.1', cfg_PORT, concurrency=5, duration=2.0, payload_size=32, label='memoize')
srv2.close()
print('memoize:', rep2['rps'], 'rps, p99=', rep2['latency_ms']['p99'])

if rep1['rps'] > 0 and rep2['rps'] > 0:
    speedup = rep2['rps'] / rep1['rps']
    print('speedup:', round(speedup, 2), 'x')

print('cache hits:', fast_echo.cache_hits(), 'misses:', fast_echo.cache_misses())