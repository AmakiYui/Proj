# Q7 Day2-3 完全版验证:discover_entry_points 真能跑
import proj
print('proj version:', proj.__version__)
print()

# entry_points 真能跑
proj.clear_plugins()
loaded = proj.discover_entry_points()
print('discover_entry_points 返回:', loaded)
print()

plugins = proj.get_plugin_tasks()
print('已加载插件数:', len(plugins))
for name in sorted(plugins.keys()):
    fn = plugins[name]
    print('  ' + name.ljust(15) + ' -> ' + fn.__module__ + ':' + fn.__name__)
print()

print('试调 shout(b"hi"):       ', plugins['shout'](b'hi'))
print('试调 whisper(b"HI"):     ', plugins['whisper'](b'HI'))
print('试调 math_double(b"21"): ', plugins['math_double'](b'21'))
print('试调 greet_hello(b"alice"):', plugins['greet_hello'](b'alice'))
print('试调 math_len(b"abcdef"):', plugins['math_len'](b'abcdef'))
print()
print('=== 命令行入口 proj 命令 ===')
print('已注册:`proj` cmd 命令(等价 `python -m proj.cli`)')
print('试试:`proj menu` 会打印启动菜单')

# 把 subprocess 也跑一下确认 `proj` 命令能跑
import subprocess
try:
    out = subprocess.check_output(['proj', 'menu'], text=True, timeout=5)
    print()
    print('=== proj menu 输出 ===')
    print(out[:500])
except FileNotFoundError:
    print()
    print('proj cmd 不在 PATH(Windows 用户级安装可能不立即可用)')
except subprocess.CalledProcessError as e:
    print('proj 跑了但返回非零:', e)