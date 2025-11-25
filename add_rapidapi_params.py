#!/usr/bin/env python3
"""
RapidAPI 参数补充工具 - 交互式添加参数到已生成的 OpenAPI 规范
"""
import json
import sys
from pathlib import Path

def add_parameters_to_openapi(openapi_file: str):
    """交互式添加参数"""
    
    # 读取 OpenAPI 文件
    with open(openapi_file, 'r', encoding='utf-8') as f:
        openapi = json.load(f)
    
    print("🔧 RapidAPI 参数补充工具")
    print("=" * 60)
    print()
    print(f"📂 OpenAPI 文件: {openapi_file}")
    print(f"📝 API: {openapi['info']['title']}")
    print()
    
    # 列出所有端点
    print("📍 现有端点:")
    endpoints = []
    for path, methods in openapi.get('paths', {}).items():
        for method, operation in methods.items():
            endpoints.append((path, method, operation.get('summary', path)))
            param_count = len(operation.get('parameters', []))
            print(f"   {len(endpoints)}. {method.upper()} {path} - {operation.get('summary', path)}")
            print(f"      当前参数数量: {param_count}")
    
    print()
    print("💡 提示: 从 RapidAPI 页面点击端点，查看 Params 标签获取参数信息")
    print()
    
    # 选择端点
    while True:
        choice = input("选择要添加参数的端点编号（留空退出）: ").strip()
        if not choice:
            break
        
        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(endpoints):
                print("❌ 无效的编号")
                continue
        except ValueError:
            print("❌ 请输入数字")
            continue
        
        path, method, summary = endpoints[idx]
        print()
        print(f"📝 为 {method.upper()} {path} 添加参数")
        print("-" * 60)
        
        # 获取或创建 parameters 数组
        if 'parameters' not in openapi['paths'][path][method]:
            openapi['paths'][path][method]['parameters'] = []
        
        params_list = openapi['paths'][path][method]['parameters']
        
        # 添加参数
        while True:
            print()
            param_name = input("  参数名称（留空结束）: ").strip()
            if not param_name:
                break
            
            param_type = input(f"  {param_name} 类型 (string/integer/boolean/number, 默认string): ").strip() or "string"
            param_required = input(f"  {param_name} 必需？ (y/n, 默认n): ").strip().lower() == 'y'
            param_desc = input(f"  {param_name} 描述: ").strip()
            param_default = input(f"  {param_name} 默认值（可选，按回车跳过）: ").strip()
            param_in = input(f"  {param_name} 位置 (query/path/header, 默认query): ").strip() or "query"
            
            # 构建参数对象
            param_obj = {
                "name": param_name,
                "in": param_in,
                "required": param_required,
                "description": param_desc,
                "schema": {
                    "type": param_type
                }
            }
            
            # 添加默认值
            if param_default:
                param_obj['schema']['default'] = param_default
            
            # 检查是否已存在
            existing = next((p for p in params_list if p['name'] == param_name), None)
            if existing:
                print(f"  ⚠️  参数 '{param_name}' 已存在，更新中...")
                params_list.remove(existing)
            
            params_list.append(param_obj)
            print(f"  ✅ 已添加参数: {param_name}")
        
        print()
        print(f"✅ 端点 {path} 现在有 {len(params_list)} 个参数")
    
    # 保存更新后的文件
    output_file = openapi_file.replace('.json', '_with_params.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(openapi, f, indent=2, ensure_ascii=False)
    
    print()
    print("=" * 60)
    print(f"✅ 已保存到: {output_file}")
    print()
    print("📝 下一步:")
    print(f"   api-to-mcp convert {output_file} -n <name>")
    print()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        openapi_file = sys.argv[1]
    else:
        print("用法: python add_rapidapi_params.py <openapi_file.json>")
        print()
        print("示例: python add_rapidapi_params.py rapidapi_jsearch_auto.json")
        sys.exit(1)
    
    if not Path(openapi_file).exists():
        print(f"❌ 文件不存在: {openapi_file}")
        sys.exit(1)
    
    add_parameters_to_openapi(openapi_file)






