"""
调试脚本：直接向 ciming.pages.dev 发送同步请求，输出详细响应
用法: python debug_sync.py
"""
import requests
import json

SYNC_URL = "https://ciming.pages.dev/api/sync-record"

payload = {
    "personId": "110101199001011234",
    "name":     "调试测试",
    "gender":   "男",
    "age":      "25",
    "department": "测试科室",
    "status":   "已完成",
    "number":   "TEST_DEBUG_001",
    "ossKey":   "reports/test/用户版测试.pdf",
    "ossKeyPro": "reports/test/专业版测试.pdf",
    "ossFolder": "reports/test",
}

print("=" * 60)
print("POST →", SYNC_URL)
print("Payload:", json.dumps(payload, ensure_ascii=False, indent=2))
print("=" * 60)

try:
    resp = requests.post(
        SYNC_URL,
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload, ensure_ascii=False),
        timeout=15
    )
    print(f"HTTP Status: {resp.status_code}")
    print(f"Response:   {resp.text}")
except Exception as e:
    print(f"请求失败: {type(e).__name__}: {e}")
