# src/proj/plugin_loader.py
# ============================================================
# Proj 插件加载器(Q7 Day2-3 完全版)
# ============================================================
# 文件名说明:
#   plugin_loader.py 是模块(加载器 API)
#   plugins/         是子包(内置 task 实现)
# Python 不允许同名模块和包共存,所以分开命名
# ============================================================
# 设计原则:
#   1. 不依赖 packaging / setuptools / pip — 纯 stdlib
#   2. 三种发现方式,按优先级:
#      a) 显式 register_task(name, fn) 注册(最快,适合应用代码)
#      b) scan_plugins_dir(dir_path) 扫描目录(Q5 Day4 同款机制)
#      c) discover_entry_points(group="proj.plugins") 走 packaging
#         (若用户已装包,这里生效;未装包则跳过,不报错)
#   3. 统一通过 get_plugin_tasks() 拿所有发现的 task
#
# 与 Q5 Day4 scan_tasks_dir 的关系:
#   - scan_tasks_dir  → 临时一次性,加载后无痕迹
#   - scan_plugins_dir → 走 register_task 注册到全局,跨调用共享
# ============================================================

import os
import importlib
import importlib.util
import inspect

# 插件 task 全局注册表(name -> Task 函数)
_PLUGIN_TASKS: dict[str, "Task"] = {}


def register_task(name: str, fn) -> None:
    """显式注册一个 task 到全局插件表。

    参数:
        name: task 名(如 "upper_shout"、"greet::hello")
        fn:   Task 函数(签名必须是 (bytes) -> bytes)

    同名覆盖:后注册覆盖先注册(简单粗暴,跟 scan_tasks_dir 一致)
    """
    if not callable(fn):
        raise TypeError(f"plugin task {name!r} 必须是 callable")
    _PLUGIN_TASKS[name] = fn


def unregister_task(name: str) -> None:
    """取消注册(测试用)。"""
    _PLUGIN_TASKS.pop(name, None)


def get_plugin_tasks() -> dict[str, "Task"]:
    """返回当前所有已注册插件 task 的快照(拷贝,不影响全局)。"""
    return dict(_PLUGIN_TASKS)


def scan_plugins_dir(dir_path: str) -> list[str]:
    """扫描目录下所有 .py,把签名合规的 task 函数注册进全局表。

    返回:新注册的名字列表(已存在的同名 task 不算新)

    跟 Q5 Day4 scan_tasks_dir 的区别:
        - scan_tasks_dir:返回 dict,不注册
        - scan_plugins_dir: 注册到全局,返回新增名列表

    抛出:
        FileNotFoundError: 目录不存在
    """
    if not os.path.isdir(dir_path):
        raise FileNotFoundError(f"plugin 目录不存在: {dir_path}")

    new_names: list[str] = []

    for fname in os.listdir(dir_path):
        if not fname.endswith(".py") or fname.startswith("_"):
            continue
        fpath = os.path.join(dir_path, fname)
        module_stem = fname[:-3]

        spec = importlib.util.spec_from_file_location(
            f"_plugin_{module_stem}", fpath,
        )
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception:
            continue  # 单个文件坏掉不影响其他

        for name in dir(module):
            if name.startswith("_"):
                continue
            obj = getattr(module, name)
            if not callable(obj):
                continue
            try:
                params = list(inspect.signature(obj).parameters.values())
                if len(params) != 1:
                    continue
            except (ValueError, TypeError):
                continue

            # 注册名格式: "文件名::函数名"(避免冲突)
            full_name = f"{module_stem}::{name}"
            if full_name not in _PLUGIN_TASKS:
                new_names.append(full_name)
            _PLUGIN_TASKS[full_name] = obj

    return new_names


def discover_entry_points(group: str = "proj.plugins") -> list[str]:
    """从已安装包发现 entry_points 声明的插件。

    返回:成功加载的插件 task 名列表。

    行为:
        - 没装 importlib.metadata 或没装第三方插件:返回 [],不报错
        - 用户用 `pip install -e .` 后,pyproject.toml 里声明的 entry_points 会生效
        - 本仓库目前没 pyproject.toml,所以这里永远返回 [](但 API 已留好)

    这是 Day2-3 轻量版:Q9 演(部署)正式引入 packaging 时,这里自动激活。
    """
    try:
        from importlib import metadata as _md
    except ImportError:
        return []

    new_names: list[str] = []
    try:
        eps = _md.entry_points(group=group)
    except Exception:
        return []

    for ep in eps:
        try:
            obj = ep.load()
            name = f"{ep.name}"  # 用 entry_point 的 name
            _PLUGIN_TASKS[name] = obj
            new_names.append(name)
        except Exception:
            continue  # 单个插件坏掉不影响其他

    return new_names


def clear_plugins() -> None:
    """清空所有插件(测试用)。"""
    _PLUGIN_TASKS.clear()