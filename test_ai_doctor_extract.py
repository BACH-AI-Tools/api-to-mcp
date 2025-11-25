#!/usr/bin/env python3
"""测试 AI Doctor API 提取"""
import json
from src.api_to_mcp.platforms.rapidapi_auto import auto_extract_rapidapi

# 目标 URL
url = "https://rapidapi.com/bilgisamapi-api2/api/ai-doctor-api-ai-medical-chatbot-healthcare-ai-assistant"

print("=" * 80)
print("测试 AI Doctor API 端点提取")
print("=" * 80)
print()

# 使用 Selenium 模式
print("🔍 使用 Selenium 模式爬取...")
print()

spec = auto_extract_rapidapi(url, verify_ssl=True, use_selenium=True, headless=True)

if spec:
    print()
    print("=" * 80)
    print("提取结果:")
    print("=" * 80)
    print(f"标题: {spec['info']['title']}")
    print(f"端点数量: {len(spec.get('paths', {}))}")
    print()
    print("端点列表:")
    for path, methods in spec.get('paths', {}).items():
        for method, operation in methods.items():
            if isinstance(operation, dict):
                print(f"  - {method.upper()} {path}: {operation.get('summary', 'N/A')}")
    
    print()
    print("保存到: test_ai_doctor_output.json")
    with open("test_ai_doctor_output.json", "w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2, ensure_ascii=False)
    
    print()
    print("=" * 80)
    print("完整 OpenAPI 规范预览:")
    print("=" * 80)
    print(json.dumps(spec, indent=2, ensure_ascii=False))
else:
    print()
    print("❌ 提取失败")

