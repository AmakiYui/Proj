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

from .security import (
    verify_plugin_signature,
    load_manifest,
    DEFAULT_ALLOWED_ENTRY_POINT_GROUPS,
)

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


def scan_plugins_dir(
    dir_path: str,
    manifest_path: str | None = None,
    require_signature: bool = False,
) -> list[str]:
    """扫描目录下所有 .py,把签名合规的 task 函数注册进全局表。

    参数:
        dir_path: 插件目录路径
        manifest_path: 签名清单路径(可选,默认 None)
        require_signature: 是否强制校验签名
            - False(默认): 有 manifest 就校验,没 manifest 也放行
            - True: 没 manifest 或签名不匹配 → 全部拒绝

    返回:新注册的名字列表(已存在的同名 task 不算新)

    跟 Q5 Day4 scan_tasks_dir 的区别:
        - scan_tasks_dir:返回 dict,不注册
        - scan_plugins_dir: 注册到全局,返回新增名列表

    Q10 Day2 改造:
        - 可选 HMAC 签名校验(manifest_path + require_signature)
        - 默认不校验,保持向后兼容(Q7 Day2-3 已部署的 plugin 照常工作)
        - 校验失败 → 跳过该文件,不抛错(单个文件坏掉不影响其他)

    抛出:
        FileNotFoundError: 目录不存在
    """
    if not os.path.isdir(dir_path):
        raise FileNotFoundError(f"plugin 目录不存在: {dir_path}")

    # Q10 Day2:加载签名清单(若有)
    manifest: dict[str, str] = {}
    if manifest_path is not None:
        try:
            manifest = load_manifest(manifest_path)
        except FileNotFoundError:
            if require_signature:
                raise  # 强制模式:清单不存在直接抛错

    new_names: list[str] = []

    for fname in os.listdir(dir_path):
        if not fname.endswith(".py") or fname.startswith("_"):
            continue
        fpath = os.path.join(dir_path, fname)
        module_stem = fname[:-3]

        # Q10 Day2:签名校验(若有 manifest 且强制模式)
        if manifest and require_signature:
            expected_sig = manifest.get(f"{module_stem}.py")
            if not expected_sig:
                continue  # 清单没列,跳过
            if not verify_plugin_signature(fpath, expected_sig):
                continue  # 签名不匹配,跳过

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


def discover_entry_points(
    group: str | list[str] = "proj.plugins",
    allowed_groups: frozenset[str] | None = DEFAULT_ALLOWED_ENTRY_POINT_GROUPS,
) -> list[str]:
    """从已安装包发现 entry_points 声明的插件。

    参数:
        group: 要发现的 entry_point group(默认 "proj.plugins")
            - 字符串:单个 group
            - 列表:多个 group(都会扫描)
        allowed_groups: 白名单(Q10 Day2 防第三方包投毒)
            - 默认:只允许 proj.plugins
            - None:不做白名单校验(危险,仅测试用)

    返回:成功加载的插件 task 名列表。

    行为:
        - 没装 importlib.metadata 或没装第三方插件:返回 [],不报错
        - 用户用 `pip install -e .` 后,pyproject.toml 里声明的 entry_points 会生效
        - 不在白名单的 group:返回 [],不报错(Q10 静默拒绝)

    Q10 Day2 改造:
        - 加 allowed_groups 白名单(默认只接 proj.plugins)
        - 白名单校验失败 → 静默返回 [],不报错
        - 跟 Q8 Day2 一致:出错就近处理,不向调用方抛

    这是 Day2-3 轻量版:Q9 演(部署)正式引入 packaging 时,这里自动激活。
    """
    # 统一成列表
    groups = [group] if isinstance(group, str) else list(group)

    # Q10 Day2:白名单校验
    if allowed_groups is not None:
        groups = [g for g in groups if g in allowed_groups]
        if not groups:
            return []  # 全都不在白名单,静默拒绝

    try:
        from importlib import metadata as _md
    except ImportError:
        return []

    new_names: list[str] = []
    for g in groups:
        try:
            eps = _md.entry_points(group=g)
        except Exception:
            continue

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