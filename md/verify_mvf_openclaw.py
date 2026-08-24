# md/verify_mvf_openclaw.py
# MVF 跨项目分析 verify(Q1 Day2 扩展)
# ============================================================
# 验证 4 件事:
#   1. 已知项目注册表可查
#   2. generate_scaffold 对 OpenClaw 返回非默认填法
#   3. compare_projects 跨项目对照
#   4. OpenClaw Q5/Q12 不与 Proj 撞内容
# ============================================================

import os
import sys
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


# 1. 注册表
print("\n=== 1. 已知项目注册表 ===", flush=True)
check("KNOWN_PROJECTS 含 Proj", "Proj" in proj.KNOWN_PROJECTS)
check("KNOWN_PROJECTS 含 OpenClaw", "OpenClaw" in proj.KNOWN_PROJECTS)
check("is_known('OpenClaw')", proj.is_known("OpenClaw"))
check("not is_known('xxxx')", not proj.is_known("xxxx"))
check("get_fills('OpenClaw') 返回 dict", isinstance(proj.get_fills("OpenClaw"), dict))


# 2. generate_scaffold 对已知项目
print("\n=== 2. OpenClaw scaffold ===", flush=True)
oc = proj.generate_scaffold("OpenClaw")
check("14 slots", len(oc.slots) == 14)
oc_q5 = oc[5].default_fill
check("OpenClaw Q5 = Agent turn", "Agent turn" in oc_q5 or "agent" in oc_q5.lower())
oc_q3 = oc[3].default_fill
check("OpenClaw Q3 = runCli / Node.js",
      "runCli" in oc_q3 or "Node.js" in oc_q3)
oc_q9 = oc[9].default_fill
check("OpenClaw Q9 = monorepo", "monorepo" in oc_q9.lower())


# 3. compare_projects
print("\n=== 3. compare_projects ===", flush=True)
result = proj.compare_projects(["Proj", "OpenClaw"], q=5)
check("compare 含 Proj", "Proj" in result)
check("compare 含 OpenClaw", "OpenClaw" in result)
check("compare 含 Q5", "Q5" in result)
check("compare 含 bytes->bytes", "bytes" in result)
check("compare 含 Agent turn", "Agent turn" in result or "agent" in result.lower())


# 4. compare_all
print("\n=== 4. compare_all ===", flush=True)
result_all = proj.compare_all(["Proj", "OpenClaw"])
check("compare_all 含 Q1..Q14",
      all(f"Q{i}" in result_all for i in range(1, 15)))


# 5. 跨项目独立性(同一个 Q 不同填法)
print("\n=== 5. 跨项目独立性 ===", flush=True)
proj_sc = proj.generate_scaffold("Proj")
oc_sc = proj.generate_scaffold("OpenClaw")
for q in [3, 5, 9]:
    check(f"Q{q} Proj != OpenClaw",
          proj_sc[q].default_fill != oc_sc[q].default_fill)


# 6. CLI 验证
print("\n=== 6. CLI compare ===", flush=True)
import subprocess
r = subprocess.run(
    [sys.executable, "-m", "src.proj.mvf.compare", "--projects=Proj,OpenClaw", "--q=5"],
    cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
    env={**os.environ, "PYTHONIOENCODING": "utf-8"},
)
check("CLI compare 返 0", r.returncode == 0, f"stderr={r.stderr[:200]}")
check("CLI 输出 OpenClaw Agent turn",
      "Agent turn" in r.stdout or "agent" in r.stdout.lower())


# 7. __all__
print("\n=== 7. __all__ ===", flush=True)
expected = {"generate_scaffold", "Scaffold",
            "KNOWN_PROJECTS", "is_known", "get_fills",
            "compare_projects", "compare_all"}
actual = set(proj.__all__)
missing = expected - actual
check("__all__ 含 MVF 全部 7 项", not missing, f"missing={missing}")
check("__all__ >= 66", len(proj.__all__) >= 66, f"got {len(proj.__all__)}")


# 总结
print(f"\n=== 总结 ===", flush=True)
print(f"PASS: {passed}", flush=True)
print(f"FAIL: {failed}", flush=True)
sys.exit(0 if failed == 0 else 1)