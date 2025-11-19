#!/usr/bin/env python3
"""
快速创建 RapidAPI MCP 服务器的脚本

使用方法:
    python create_rapidapi_mcp.py
"""
import json
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from api_to_mcp.platforms.rapidapi_builder import RapidAPIOpenAPIBuilder
from api_to_mcp.parsers import OpenAPIParser
from api_to_mcp.generator import MCPGenerator


def create_rapidapi_mcp():
    """交互式创建 RapidAPI MCP 服务器"""
    print("🚀 RapidAPI MCP 快速创建工具")
    print("=" * 60)
    print()
    print("💡 从 RapidAPI 页面收集信息:")
    print("   1. 左侧端点列表 → 端点名称和路径")
    print("   2. 右侧代码示例 → Base URL 和参数")
    print()
    
    # 1. 收集基本信息
    print("📝 基本信息:")
    print()
    
    api_name = input("API 名称 (如: JSearch): ").strip()
    if not api_name:
        print("❌ API 名称不能为空")
        return
    
    print()
    print("💡 Base URL 示例: https://jsearch.p.rapidapi.com")
    print("   从右侧 curl 代码中的 --url 后面复制")
    base_url = input("Base URL: ").strip()
    if not base_url:
        print("❌ Base URL 不能为空")
        return
    
    description = input("API 描述 (可选): ").strip()
    
    # 2. 收集端点
    print()
    print("=" * 60)
    print("📍 添加端点 (从左侧端点列表)")
    print("=" * 60)
    print()
    
    endpoints = []
    endpoint_num = 1
    
    while True:
        print(f"\n🔹 端点 #{endpoint_num}:")
        print("-" * 40)
        
        endpoint_name = input("端点名称 (如: Job Search，留空结束): ").strip()
        if not endpoint_name:
            break
        
        method = input("HTTP 方法 (GET/POST，默认 GET): ").strip().upper() or "GET"
        path = input("路径 (如: /search): ").strip()
        
        if not path:
            print("⚠️  路径不能为空，跳过此端点")
            continue
        
        endpoint_desc = input("描述 (可选): ").strip()
        
        # 参数收集
        print("\n  📋 参数 (逐个添加，留空结束):")
        parameters = []
        param_num = 1
        
        while True:
            param_name = input(f"    参数 #{param_num} 名称 (留空结束): ").strip()
            if not param_name:
                break
            
            param_type = input(f"    └─ 类型 (string/integer, 默认 string): ").strip() or "string"
            param_required = input(f"    └─ 必需? (y/n, 默认 n): ").strip().lower() == 'y'
            param_desc = input(f"    └─ 描述: ").strip()
            
            parameters.append({
                "name": param_name,
                "type": param_type,
                "required": param_required,
                "description": param_desc
            })
            
            print(f"    ✅ 已添加参数: {param_name}")
            param_num += 1
        
        endpoints.append({
            "name": endpoint_name,
            "method": method,
            "path": path,
            "description": endpoint_desc,
            "parameters": parameters
        })
        
        print(f"✅ 已添加端点: {endpoint_name} ({method} {path})")
        endpoint_num += 1
    
    if not endpoints:
        print("\n❌ 至少需要添加一个端点")
        return
    
    # 3. 构建 OpenAPI
    print()
    print("=" * 60)
    print("🔨 构建 OpenAPI 规范...")
    
    builder = RapidAPIOpenAPIBuilder()
    builder.set_info(api_name, description or f"RapidAPI: {api_name}")
    builder.set_server(base_url)
    
    for endpoint in endpoints:
        params = []
        for p in endpoint['parameters']:
            params.append({
                "name": p['name'],
                "in": "query",
                "required": p['required'],
                "description": p['description'],
                "schema": {
                    "type": p['type']
                }
            })
        
        builder.add_endpoint_from_rapidapi(
            name=endpoint['name'],
            method=endpoint['method'],
            path=endpoint['path'],
            description=endpoint['description'],
            parameters=params
        )
    
    openapi_spec = builder.get_openapi()
    
    # 4. 保存 OpenAPI 文件
    filename = f"rapidapi_{api_name.lower().replace(' ', '_')}.json"
    builder.save_to_file(filename)
    print(f"✅ OpenAPI 规范已保存: {filename}")
    print(f"   包含 {len(endpoints)} 个端点")
    
    # 5. 生成 MCP 服务器
    print()
    mcp_name = input(f"MCP 服务器名称 (默认: {api_name.lower().replace(' ', '_')}): ").strip()
    if not mcp_name:
        mcp_name = api_name.lower().replace(' ', '_')
    
    print()
    print("🔨 生成 MCP 服务器...")
    
    parser = OpenAPIParser()
    api_spec = parser.parse_dict(openapi_spec)
    
    generator = MCPGenerator(output_dir="generated_mcps")
    mcp_server = generator.generate(api_spec, transport="stdio", custom_name=mcp_name)
    
    print()
    print("=" * 60)
    print("🎉 完成!")
    print("=" * 60)
    print()
    print(f"📁 MCP 服务器: {mcp_server.output_path}")
    print(f"📋 OpenAPI 文件: {filename}")
    print()
    print("📝 运行方法:")
    print(f"   cd {mcp_server.output_path}")
    print(f"   python server.py")
    print()
    print("🔑 设置 API Key:")
    print(f"   export API_KEY='你的 RapidAPI Key'")
    print()
    print("💡 在 Claude Desktop 中使用:")
    print(f'   "command": "python"')
    print(f'   "args": ["{mcp_server.output_path}\\\\server.py"]')
    print(f'   "env": {{"API_KEY": "your-rapidapi-key"}}')


if __name__ == "__main__":
    try:
        create_rapidapi_mcp()
    except KeyboardInterrupt:
        print("\n\n❌ 已取消")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


