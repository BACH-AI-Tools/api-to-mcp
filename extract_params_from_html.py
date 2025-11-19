#!/usr/bin/env python3
"""
临时脚本：从端点详情HTML中提取参数
用于分析参数数据结构
"""
import re
import json

# 读取端点详情HTML
with open('debug_endpoint_details.html', 'r', encoding='utf-8') as f:
    html = f.read()

print("🔍 分析端点详情页面...")
print(f"页面大小: {len(html)} 字符")
print()

# 提取所有 push 调用
push_pattern = r'self\.__next_f\.push\(\[[\d]+,"([^"]*(?:[^"\\]|\\.)*)"\]\)'
matches = re.findall(push_pattern, html, re.DOTALL)

print(f"找到 {len(matches)} 个 push 调用")
print()

# 查找包含 job_id 的块
for i, match in enumerate(matches):
    if 'job_id' in match:
        print(f"=== 块 #{i+1} 包含 'job_id' ===")
        # 解码并清理
        decoded = match.replace('\\"', '"').replace('\\\\', '\\')
        
        # 查找参数相关的模式
        # 尝试提取 job_id 相关的 JSON 对象
        job_id_patterns = [
            r'\{"[^}]*?"name":"job_id"[^}]*?\}',
            r'"job_id"[^,]*?,',
            r'job_id[^,}]{0,100}',
        ]
        
        for pattern in job_id_patterns:
            param_matches = re.findall(pattern, decoded)
            if param_matches:
                print(f"  模式匹配到: {len(param_matches)} 个")
                for pm in param_matches[:3]:  # 只显示前3个
                    print(f"  {pm[:200]}")
                print()
                break
        
        # 显示上下文
        if 'job_id' in decoded:
            idx = decoded.find('job_id')
            context = decoded[max(0, idx-200):min(len(decoded), idx+300)]
            print(f"  上下文片段:")
            print(f"  {context}")
            print()
            print("=" * 60)
            break

print("\n💡 提示: 检查上面的输出，找到参数的数据结构模式")


