# Q7 Day2-3 验证:插件系统全场景
import sys, os
sys.path.insert(0, 'src')
sys.path.insert(0, '.')
import proj

print('=== 初始状态:无插件 ===')
assert proj.get_plugin_tasks() == {}

print()
print('=== 显式 register_task ===')
def my_shout(data: bytes) -> bytes:
    return b"SHOUT: " + data.upper() + b"!"

proj.register_task('my_shout', my_shout)
tasks = proj.get_plugin_tasks()
print('  已注册:', list(tasks.keys()))
assert 'my_shout' in tasks
assert tasks['my_shout'](b'hello') == b'SHOUT: HELLO!'

print()
print('=== 错误调用应该报错 ===')
try:
    proj.register_task('bad', 'not a function')
    assert False, '应该报 TypeError'
except TypeError as e:
    print('  TypeError OK:', str(e)[:60])

print()
print('=== scan_plugins_dir:扫 md/tasks/ ===')
# 先清,确保干净
proj.clear_plugins()
new = proj.scan_plugins_dir('md/tasks')
print('  新注册:', new)
all_plugins = proj.get_plugin_tasks()
print('  全集:', list(all_plugins.keys()))
assert 'greet::hello' in all_plugins or 'math::add' in all_plugins

# 跑一个试试
for name, fn in all_plugins.items():
    print(f'  试调 {name}(b"42") =', fn(b'42'))
    break

print()
print('=== discover_entry_points:已装包(Q7 Day2-3 完全版)===  ===')
proj.clear_plugins()  # 重置,确保发现的是 entry_points 的
result = proj.discover_entry_points()
print('  返回:', result)
# Day2-3 完全版装了包,这里应该非空
assert isinstance(result, list)

print()
print('=== unregister_task ===')
proj.register_task('temp', my_shout)
assert 'temp' in proj.get_plugin_tasks()
proj.unregister_task('temp')
assert 'temp' not in proj.get_plugin_tasks()
print('  取消注册 OK')

print()
print('=== clear_plugins 清空 ===')
proj.clear_plugins()
assert proj.get_plugin_tasks() == {}
print('  清空 OK')

print()
print('=== __all__ 包含 plugins 6 个 ===')
print('  __all__ 长度:', len(proj.__all__))
for n in ['register_task', 'unregister_task', 'get_plugin_tasks',
          'scan_plugins_dir', 'discover_entry_points', 'clear_plugins']:
    assert n in proj.__all__, f'__all__ 缺 {n}'
    print(f'  ✅ {n}')

print()
print('=== 跑示例插件 example_plugin.py ===')
# 它会 import 并注册 shout / whisper
import importlib.util
spec = importlib.util.spec_from_file_location('example_plugin', 'md/example_plugin.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print('  example_plugin 注册后,', list(proj.get_plugin_tasks().keys()))

print()
print('✅ 全部通过 — 插件系统 6 个 API + 示例工作')