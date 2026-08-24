# Q7 Day2-2 验证:make_error v1 + make_error_v2(独立函数)
import sys
sys.path.insert(0, 'src')
sys.path.insert(0, '.')
import proj
import json

print('=== make_error()(v1 固定,Q6 Day4 完全兼容) ===')
err1 = proj.make_error(proj.ERR_BAD_REQUEST, 'msg1')
print(json.dumps(err1, indent=2, ensure_ascii=False))
assert err1 == {"error": {"code": 400, "message": "msg1"}}, 'v1 应跟 Q6 Day4 完全一致'

print()
print('=== make_error_v2() 全字段 ===')
err2 = proj.make_error_v2(
    proj.ERR_BAD_REQUEST, 'msg2',
    request_id='r-test-001',
    timestamp=1787538629185,
    details={'field': 'action', 'expected': 'str', 'got': 'int'},
)
print(json.dumps(err2, indent=2, ensure_ascii=False))
assert err2['error']['request_id'] == 'r-test-001'
assert err2['error']['timestamp'] == 1787538629185
assert err2['error']['details']['field'] == 'action'

print()
print('=== make_error_v2() 部分字段(auto_xxx=False 不输出) ===')
# Q8 Day2 修复:timestamp 默认自动输出,要用 auto_timestamp=False 才关
err3 = proj.make_error_v2(
    proj.ERR_BAD_REQUEST, 'msg3',
    request_id='r-only',
    auto_timestamp=False,
)
print(json.dumps(err3, indent=2, ensure_ascii=False))
assert 'request_id' in err3['error']
assert 'timestamp' not in err3['error']
assert 'details' not in err3['error']

print()
print('=== make_error_v2() 全 auto=False 字段(只剩 code/message) ===')
# Q8 Day2 修复:默认 auto_request_id/auto_timestamp 都是 True,全关才能只剩 code/message
err4 = proj.make_error_v2(
    proj.ERR_BAD_REQUEST, 'msg4',
    auto_request_id=False,
    auto_timestamp=False,
)
print(json.dumps(err4, indent=2, ensure_ascii=False))
assert set(err4['error'].keys()) == {'code', 'message'}

print()
print('=== ERR_FORMAT_V2 常量值 ===')
print('  V2 =', proj.ERR_FORMAT_V2, '(期望 2)')
# 注意:没有 ERR_FORMAT_V1,因为 v1 是默认,不需要常量

print()
print('=== v1 老调用方式仍 OK ===')
err5 = proj.make_error(400, 'legacy way')
print(json.dumps(err5, indent=2, ensure_ascii=False))
assert err5 == {'error': {'code': 400, 'message': 'legacy way'}}

print()
print('=== __all__ 包含两个函数 + ERR_FORMAT_V2 ===')
print('  __all__:', proj.__all__)

print()
print('✅ 全部通过 — make_error 不破 + make_error_v2 独立')