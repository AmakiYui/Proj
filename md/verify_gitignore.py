# verify_gitignore.py
# 验证 .gitignore 的 12 个测试路径,期望匹配规则

import os
import fnmatch

patterns = []
with open(".gitignore", encoding="utf-8") as f:
    for line in f:
        # 去掉行内注释 + 首尾空白
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        patterns.append(line)


def is_ignored(path):
    norm = path.replace("\\", "/")
    parts = norm.split("/")
    for pat in patterns:
        if pat.endswith("/"):
            d = pat[:-1]
            if norm == d or norm.startswith(d + "/") or d in parts:
                return pat
        else:
            if fnmatch.fnmatch(norm, pat) or fnmatch.fnmatch(os.path.basename(norm), pat):
                return pat
    return None


CASES = [
    ("var/server.pid", "IGNORE"),
    ("var/server.log", "IGNORE"),
    ("dist/proj.exe", "IGNORE"),
    ("dist/server.exe", "IGNORE"),
    ("src/server/__pycache__/cli.cpython-312.pyc", "IGNORE"),
    ("src/__pycache__/__init__.cpython-312.pyc", "IGNORE"),
    ("proj.spec", "IGNORE"),
    ("build/something", "IGNORE"),
    (".vscode/settings.json", "IGNORE"),
    # 应该 KEEP
    ("src/server/cli.py", "KEEP"),
    ("main.py", "KEEP"),
    ("src/server/_config.py", "KEEP"),
    ("md/patch_q4_day2.py", "KEEP"),
]


def main():
    all_pass = True
    for p, expect in CASES:
        r = is_ignored(p)
        actual = "IGNORE" if r else "KEEP"
        ok = actual == expect
        if not ok:
            all_pass = False
        tag = "OK" if ok else "FAIL matched=" + str(r)
        line = "  [" + actual.ljust(7) + "] " + p.ljust(50) + " expect=" + expect + " " + tag
        print(line)
    print()
    print("ALL PASS" if all_pass else "SOME FAIL")


if __name__ == "__main__":
    main()