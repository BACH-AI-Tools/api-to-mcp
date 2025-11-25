#!/usr/bin/env python3
"""
快速开始脚本 - 演示 API-to-MCP 的基本功能
"""
import sys
from pathlib import Path

def main():
    print("🚀 API-to-MCP 快速开始")
    print("=" * 60)
    print()
    
    # 检查 Python 版本
    if sys.version_info < (3, 10):
        print("❌ 错误: 需要 Python 3.10 或更高版本")
        print(f"   当前版本: Python {sys.version_info.major}.{sys.version_info.minor}")
        return 1
    
    print("✅ Python 版本检查通过")
    print()
    
    # 检查示例文件
    example_file = Path("examples/example_weather_api.json")
    if not example_file.exists():
        print(f"❌ 示例文件不存在: {example_file}")
        return 1
    
    print(f"✅ 找到示例文件: {example_file}")
    print()
    
    # 显示下一步操作
    print("📝 下一步操作:")
    print()
    print("1️⃣  安装依赖:")
    print("   pip install -r requirements.txt")
    print("   pip install -e .")
    print()
    print("2️⃣  验证示例 API:")
    print(f"   api-to-mcp validate {example_file}")
    print()
    print("3️⃣  转换为 MCP 服务器 (不使用 LLM):")
    print(f"   api-to-mcp convert {example_file} --no-enhance")
    print()
    print("4️⃣  转换为 MCP 服务器 (使用 LLM 增强):")
    print(f"   api-to-mcp convert {example_file}")
    print()
    print("5️⃣  查看配置:")
    print("   api-to-mcp config")
    print()
    print("=" * 60)
    print("📚 更多信息请查看:")
    print("   - README.md - 项目概述")
    print("   - USAGE.md - 详细使用指南")
    print("   - examples/README.md - 示例说明")
    print()
    print("🎉 祝你使用愉快!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())






