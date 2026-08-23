# -*- coding: utf-8 -*-
import io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

target = None
for f in os.listdir(r"C:\Users\F\Desktop"):
    if f.startswith("14") and f.endswith(".md"):
        target = os.path.join(r"C:\Users\F\Desktop", f)
        break

with open(target, 'r', encoding='utf-8') as fp:
    lines = fp.readlines()

print(f"文件: {target}")
print(f"总行数: {len(lines)}")
print(f"总字符: {sum(len(l) for l in lines)}")
print()

# 找新章节起始
for i, line in enumerate(lines):
    if '2026-08-24 实操补遗' in line:
        print(f"新章节在第 {i+1} 行: {line.strip()}")
        break

# 打印新章节前 8 行
print()
print("=== 新章节内容预览 ===")
for i in range(len(lines)-1, max(len(lines)-15, 0), -1):
    print(f"  L{i+1}: {lines[i].rstrip()[:80]}")
print()
print("=== 倒数 14 行(原始顺序) ===")
for line in lines[-14:]:
    print(f"  {line.rstrip()[:80]}")