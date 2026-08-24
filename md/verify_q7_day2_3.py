# Q7 Day2-3 验证:make_error_v2 完整 UUID 自动生成
import sys, re, json
sys.path.insert(0, 'src')
sys.path.insert(0, '.')
import proj

UUID4_RE = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$', re.I)

print('=== 默认:request_id/timestamp 都自动 ===')
err1 = proj.make_error_v2(proj.ERR_BAD_REQUEST, 'msg1')
print(json.dumps(err1, indent=2, ensure_ascii=False))
assert UUID4_RE.match(err1['error']['request_id']), f'UUID4 格式错: {err1["error"]["request_id"]}'
assert isinstance(err1['error']['timestamp'], int)
assert err1['error']['timestamp'] > 0

print()
print('=== 自动 UUID 多次调用不重复 ===')
ids = set()
for _ in range(5):
    err = proj.make_error_v2(400, 'x')
    ids.add(err['error']['request_id'])
assert len(ids) == 5, f'UUID 重复: {ids}'
print('  5 次调用 5 个不同 UUID ✅')

print()
print('=== 关掉 auto:request_id=None, auto_request_id=False ===')
err2 = proj.make_error_v2(
    proj.ERR_BAD_REQUEST, 'msg2',
    auto_request_id=False, auto_timestamp=False,
)
print(json.dumps(err2, indent=2, ensure_ascii=False))
assert 'request_id' not in err2['error']
assert 'timestamp' not in err2['error']

print()
print('=== 调用者传 request_id(覆盖自动) ===')
err3 = proj.make_error_v2(
    proj.ERR_BAD_REQUEST, 'msg3',
    request_id='my-custom-id-123',
)
print(json.dumps(err3, indent=2, ensure_ascii=False))
assert err3['error']['request_id'] == 'my-custom-id-123'

print()
print('=== 调用者传 timestamp(覆盖自动) ===')
err4 = proj.make_error_v2(
    proj.ERR_BAD_REQUEST, 'msg4',
    timestamp=1234567890,
)
print(json.dumps(err4, indent=2, ensure_ascii=False))
assert err4['error']['timestamp'] == 1234567890

print()
print('=== 兼容 v1:make_error() 不带 UUID/timestamp ===')
err5 = proj.make_error(proj.ERR_BAD_REQUEST, 'v1')
print(json.dumps(err5, indent=2, ensure_ascii=False))
assert 'request_id' not in err5['error']
assert 'timestamp' not in err5['error']

print()
print('✅ 全部通过 — UUID4 自动生成 + 可覆盖 + 可关闭')