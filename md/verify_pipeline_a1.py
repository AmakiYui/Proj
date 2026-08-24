# md/verify_pipeline_a1.py
# Pipeline A1 verify:想法 -> MVF
# ============================================================

import os
import sys
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

import proj

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


# 1. parse_idea 基础
print("\n=== 1. parse_idea 基础 ===", flush=True)
try:
    fills = proj.parse_idea("I want a CLI todo tool", "demo")
    check("parse_idea 返回 dict", isinstance(fills, dict))
    check("返回 14 项", len(fills) == 14)
    for q in range(1, 15):
        check(f"Q{q} 是 Slot", isinstance(fills[q], proj.mvf._base.Slot))
except Exception as e:
    check("parse_idea 基础", False, str(e))


# 2. empty 报错
print("\n=== 2. empty 输入 ===", flush=True)
try:
    proj.parse_idea("", "x")
    check("空串抛错", False)
except proj.IdeaToMVFError:
    check("空串抛 IdeaToMVFError", True)
except Exception as e:
    check("空串抛错", False, f"got {type(e).__name__}: {e}")


# 3. 启发式英文匹配
print("\n=== 3. 英文启发式 ===", flush=True)
idea_en = ("I want a CLI todo tool with encrypted sync, JSON storage, "
           "fast performance and Docker deployment.")
fills_en = proj.parse_idea(idea_en, "todo_cli")
# 期望:Q1 OK, Q3 OK(cli), Q6 OK(JSON storage), Q12 OK(Docker deployment)
for q in [1, 3, 6, 12]:
    check(f"Q{q} 启发式 OK", fills_en[q].check())


# 4. 启发式中文匹配
print("\n=== 4. 中文启发式 ===", flush=True)
idea_cn = ("我想做一个命令行 todo 工具,支持加密同步,数据存在 json 文件,"
           "需要日志和监控,部署到 docker")
fills_cn = proj.parse_idea(idea_cn, "todo_cn")
for q in [1, 3, 6, 11, 12]:
    check(f"Q{q} 启发式 OK", fills_cn[q].check())


# 5. CLI stdout
print("\n=== 5. CLI stdout ===", flush=True)
r = subprocess.run(
    [sys.executable, "-m", "src.proj.pipeline.idea_cli",
     "--text=A CLI tool with metrics, Docker deploy, JSON storage",
     "--name=cli_test"],
    cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
    env={**os.environ, "PYTHONIOENCODING": "utf-8"},
)
check("CLI 返 0", r.returncode == 0, f"stderr={r.stderr[:200]}")
check("CLI 含 MVF 标题", "MVF" in r.stdout)
check("CLI 含 Q1", "Q1:" in r.stdout)
check("CLI 含 Q14", "Q14:" in r.stdout)
check("CLI 含 cli_test", "cli_test" in r.stdout)


# 6. CLI --file
print("\n=== 6. CLI --file ===", flush=True)
tmp = os.path.join(ROOT, "var")
os.makedirs(tmp, exist_ok=True)
sample_path = os.path.join(tmp, "_sample_idea.txt")
with open(sample_path, "w", encoding="utf-8") as f:
    f.write("A web service with REST API, sqlite storage, Docker deploy")

r2 = subprocess.run(
    [sys.executable, "-m", "src.proj.pipeline.idea_cli",
     "--file", sample_path, "--name=websvc"],
    cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
    env={**os.environ, "PYTHONIOENCODING": "utf-8"},
)
check("--file CLI 返 0", r2.returncode == 0)
check("--file CLI 含 websvc", "websvc" in r2.stdout)

# --out 模式
out_path = os.path.join(tmp, "_out_mvf.md")
r3 = subprocess.run(
    [sys.executable, "-m", "src.proj.pipeline.idea_cli",
     "--text=cli tool with logs and json",
     "--name=outtest", "--out", out_path],
    cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
    env={**os.environ, "PYTHONIOENCODING": "utf-8"},
)
check("--out CLI 返 0", r3.returncode == 0)
check("--out 写文件", os.path.exists(out_path))
if os.path.exists(out_path):
    out_content = open(out_path, "r", encoding="utf-8").read()
    check("--out 含 MVF 标题", "MVF" in out_content)
    os.remove(out_path)


# 7. __all__
print("\n=== 7. __all__ ===", flush=True)
expected = {"parse_idea", "IdeaToMVFError", "HEURISTIC_Q_KEYWORDS", "format_mvf_md"}
actual = set(proj.__all__)
missing = expected - actual
check("__all__ 含 Pipeline A1 全部 4 项", not missing, f"missing={missing}")
check("__all__ >= 70", len(proj.__all__) >= 70, f"got {len(proj.__all__)}")


# 总结
print(f"\n=== 总结 ===", flush=True)
print(f"PASS: {passed}", flush=True)
print(f"FAIL: {failed}", flush=True)

# 清理
try:
    os.remove(sample_path)
except OSError:
    pass

sys.exit(0 if failed == 0 else 1)