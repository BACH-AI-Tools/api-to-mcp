#!/usr/bin/env python3
"""
调试参数提取 - 分析端点详情页的参数数据结构
"""
import requests
import re
import json

# 获取一个端点详情页
url = "https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch/playground/apiendpoint_374e27ef-ac8b-4014-a801-29065a6f224b"

print(f"📥 获取端点详情页...")
response = requests.get(url)
html = response.text

# 保存
with open('debug_endpoint_params.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"   页面大小: {len(html)} 字符")
print(f"   已保存到: debug_endpoint_params.html")
print()

# 提取所有 push 调用
push_pattern = r'self\.__next_f\.push\(\[[\d]+,"([^"]*)"\]\)'
matches = re.findall(push_pattern, html, re.DOTALL)

print(f"找到 {len(matches)} 个 push 调用")
print()

# 查找包含参数名的块
param_keywords = ['job_title', 'location', 'years_of_experience']

for keyword in param_keywords:
    print(f"🔍 搜索 '{keyword}'...")
    for i, match in enumerate(matches):
        if keyword in match:
            print(f"   块 #{i+1} 包含 '{keyword}'")
            
            # 解码
            decoded = match.replace('\\"', '"').replace('\\\\', '\\')
            
            # 查找该参数前后的数据
            idx = decoded.find(keyword)
            if idx >= 0:
                # 提取前后各500字符
                start = max(0, idx - 500)
                end = min(len(decoded), idx + 500)
                context = decoded[start:end]
                
                print(f"   上下文:")
                print(f"   {context}")
                print()
                print("=" * 80)
            break
    print()

print("💾 完整数据已保存，请检查 debug_endpoint_params.html")






