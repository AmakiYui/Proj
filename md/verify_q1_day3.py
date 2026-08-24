# md/verify_q1_day3.py
# Q1 Day3 + MVF 端到端验证
# ============================================================
# 验证 4 件事:
#   1. MVF 14 个 slot 可导入
#   2. Scaffold 容器:fill / describe / check_all
#   3. CLI --name / --out
#   4. OpenClaw 对照表(模拟一个非 Proj 填法)
# ============================================================

import os
import sys
import json
import subprocess
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

import proj  # noqa
from proj import generate_scaffold, Scaffold

passed = 0
failed = 0


def check(name, ok, detail=""):
    global passed, failed
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {name}", flush=True)
    if detail and not ok:
        print(f"         {detail}", flush=True)
    if ok:
        passed += 1
    else:
        failed += 1


# ============================================================
# 1. 14 slot 全部可导入
# ============================================================
print("\n=== 1. 14 slot import ===", flush=True)

slot_modules = [
    "proj.mvf.slot_01_origin", "proj.mvf.slot_02_design",
    "proj.mvf.slot_03_runtime", "proj.mvf.slot_04_organization",
    "proj.mvf.slot_05_task", "proj.mvf.slot_06_data",
    "proj.mvf.slot_07_interface", "proj.mvf.slot_08_error",
    "proj.mvf.slot_09_grow", "proj.mvf.slot_10_security",
    "proj.mvf.slot_11_observe", "proj.mvf.slot_12_deploy",
    "proj.mvf.slot_13_performance", "proj.mvf.slot_14_coordination",
]
for m in slot_modules:
    try:
        __import__(m)
        check(f"{m} import", True)
    except Exception as e:
        check(f"{m} import", False, str(e))


# ============================================================
# 2. Scaffold 容器
# ============================================================
print("\n=== 2. Scaffold 容器 ===", flush=True)

sc = generate_scaffold("test_app")
check("Scaffold type", isinstance(sc, Scaffold))
check("name = test_app", sc.name == "test_app")
check("14 slots", len(sc.slots) == 14)

# __getitem__
check("sc[1] = OriginSlot", type(sc[1]).__name__ == "OriginSlot")
check("sc[14] = CoordinationSlot", type(sc[14]).__name__ == "CoordinationSlot")

# describe
desc = sc.describe()
check("describe 含 MVF Scaffold", "MVF Scaffold: test_app" in desc)
check("describe 含 Q1", "Q1" in desc)
check("describe 含 Q14", "Q14" in desc)

# check_all
results = sc.check_all()
check("check_all 返回 14 项", len(results) == 14)
check("check_all 全部 True", all(results.values()))


# ============================================================
# 3. fill:自定义 slot
# ============================================================
print("\n=== 3. 自定义 slot fill ===", flush=True)


class AITaskSlot(type(sc[5])):
    """自定义:Q5 改成 AI agent 任务契约。"""
    def __init__(self):
        self.question = "AI agent 任务契约"
        self.default_fill = "message -> response(LLM 调用)"
    def check(self) -> bool:
        return True


# AITaskSlot 是动态类,先简单测描述
ai_task = AITaskSlot()
sc.fill(5, ai_task)

check("fill Q5 后 sc[5] = AITaskSlot", sc[5].question == "AI agent 任务契约")
check("fill 后 slot 名变了", "AI" in sc[5].describe() or "message" in sc[5].describe())


# ============================================================
# 4. CLI
# ============================================================
print("\n=== 4. CLI ===", flush=True)

# stdout 模式
r = subprocess.run(
    [sys.executable, "-m", "src.proj.mvf.template_factory", "--name=cli_test"],
    cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
    env={**os.environ, "PYTHONIOENCODING": "utf-8"},
)
check("CLI 返回 0", r.returncode == 0, f"stderr={r.stderr[:200]}")
check("CLI 输出 scaffold", "MVF Scaffold: cli_test" in r.stdout)

# --out 模式
with tempfile.TemporaryDirectory() as tmp:
    r2 = subprocess.run(
        [sys.executable, "-m", "src.proj.mvf.template_factory", "--name=out_test", "--out", tmp],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    check("--out 返回 0", r2.returncode == 0)
    files = os.listdir(tmp)
    check("--out 写文件", len(files) == 1 and files[0].endswith("_mvf.md"),
          f"got {files}")


# ============================================================
# 5. OpenClaw 对照(模拟跨项目 slot)
# ============================================================
print("\n=== 5. 跨项目 slot 对照 ===", flush=True)

# Proj 默认
proj_sc = generate_scaffold("Proj")
proj_q5 = proj_sc[5].describe()
check("Proj Q5 = bytes->bytes", "bytes" in proj_q5)

# 模拟 OpenClaw
oc_sc = generate_scaffold("OpenClaw")

class AIAgentTaskSlot(proj.mvf._base.Slot):
    def __init__(self):
        self.question = "AI agent turn"
        self.default_fill = "messages -> response(LLM)"
    def check(self) -> bool:
        return True

oc_sc.fill(5, AIAgentTaskSlot())
check("OpenClaw Q5 = AI agent", "AI" in oc_sc[5].describe())

# 验证同一 slot 不同填法:关键 slot 抽象基类允许替换
check("Proj 和 OpenClaw slot 5 不同",
      proj_sc[5].describe() != oc_sc[5].describe())


# ============================================================
# 6. __all__ 完整性
# ============================================================
print("\n=== 6. __all__ 完整性 ===", flush=True)

expected = {"generate_scaffold", "Scaffold"}
actual = set(proj.__all__)
missing = expected - actual
check("__all__ 含 Q1 全部 2 项", not missing, f"missing={missing}")
check("__all__ 共 >=64 项", len(proj.__all__) >= 64, f"got {len(proj.__all__)}")


# ============================================================
# 总结
# ============================================================
print(f"\n=== 总结 ===", flush=True)
print(f"PASS: {passed}", flush=True)
print(f"FAIL: {failed}", flush=True)
sys.exit(0 if failed == 0 else 1)


# ============================================================
# Helper:tempfile 兼容
# ============================================================
# (moved to top import block)