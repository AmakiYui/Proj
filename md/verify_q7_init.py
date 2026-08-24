import sys
sys.path.insert(0, 'src')
sys.path.insert(0, '.')   # 让 src.proj.* absolute import 找到 src 包
import proj
print('__version__:', proj.__version__)
print('__all__:', proj.__all__)
print()
print('=== proj.* 顶层 dir() (只列非下划线) ===')
for name in sorted(dir(proj)):
    if not name.startswith('_'):
        obj = getattr(proj, name)
        print(f'  {name:30s} -> {type(obj).__name__}')

print()
print('=== 反向检查:内部模块应该不可见 ===')
for bad in ['_config', 'cli', 'core']:
    exists = hasattr(proj, bad)
    status = '❌ 还可见' if exists else '✅ 已隐藏'
    print(f'  proj.{bad}: {exists}  {status}')

print()
print('=== 内部尝试:应该都报错 ===')
for bad in ['_config', 'cli', 'core']:
    try:
        m = getattr(proj, bad)
        print(f'  proj.{bad} = {m}  ❌ 没拦住')
    except AttributeError:
        print(f'  proj.{bad}: AttributeError ✅')

print()
print('=== 跑一遍业务:main() 菜单模式不报错 ===')
from src.proj.cli import main as _main
print('cli.main 函数:', _main)
print('通过 proj.main 也可:', proj.main)

print()
print('=== 内部 task 函数能取到吗 ===')
print('BUILTIN_TASKS keys:', list(proj.BUILTIN_TASKS.keys()))
print('BUILTIN_TASKS_JSON keys:', list(proj.BUILTIN_TASKS_JSON.keys()))
echo = proj.get_task('echo')
print('get_task("echo")("hello") =', echo(b'hello'))
json_echo = proj.get_json_task('echo')
print('get_json_task("echo")({"action":"echo","text":"hi"}) =', json_echo({'action':'echo','text':'hi'}))

print()
print('=== 错误码 ===')
print('ERR_BAD_REQUEST:', proj.ERR_BAD_REQUEST)
print('ERR_UNKNOWN_ACTION:', proj.ERR_UNKNOWN_ACTION)
err = proj.make_error(proj.ERR_BAD_REQUEST, '测试')
print('make_error 样例:', err)