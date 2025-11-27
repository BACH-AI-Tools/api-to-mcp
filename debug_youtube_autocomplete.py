"""
调试脚本：重新爬取 YouTube138 的 Auto Complete 端点
检查为什么会漏掉 q 参数
"""

import sys
from src.api_to_mcp.platforms.rapidapi_selenium_scraper import RapidAPISeleniumScraper

# YouTube138 Auto Complete 端点
ENDPOINT_URL = "https://rapidapi.com/Glavier/api/youtube138/playground/apiendpoint_fdb7488e-19e0-4e4e-a3d4-e99f5b29f88e"

def debug_scrape():
    print("=" * 80)
    print("🔍 调试 YouTube138 Auto Complete 端点参数提取")
    print("=" * 80)
    print()
    
    # 使用 headless=False 以便可以看到浏览器操作
    with RapidAPISeleniumScraper(headless=False, enable_screenshots=True) as scraper:
        print(f"📍 正在爬取: {ENDPOINT_URL}")
        print()
        
        # 爬取端点
        result = scraper.scrape_endpoint_full(ENDPOINT_URL)
        
        print()
        print("=" * 80)
        print("📊 爬取结果:")
        print("=" * 80)
        
        if result.get('parameters'):
            print(f"\n✅ 提取到 {len(result['parameters'])} 个参数:\n")
            for param in result['parameters']:
                print(f"  • {param['name']}")
                print(f"    - 类型: {param.get('schema', {}).get('type', 'unknown')}")
                print(f"    - 必需: {'是' if param.get('required') else '否'}")
                print(f"    - 描述: {param.get('description', '无')[:80]}")
                print()
        else:
            print("\n❌ 未提取到任何参数!")
        
        print()
        print("=" * 80)
        print("🔍 检查是否缺少 'q' 参数")
        print("=" * 80)
        
        param_names = [p['name'] for p in result.get('parameters', [])]
        if 'q' in param_names:
            print("\n✅ 找到了 'q' 参数!")
        else:
            print("\n❌ 缺少 'q' 参数!")
            print("\n   提示: 检查以下可能原因:")
            print("   1. 参数被黑名单过滤")
            print("   2. XPath 选择器未找到该参数")
            print("   3. 页面加载时机问题")
            print("   4. DOM 结构变化")
            
            print("\n   当前提取到的参数:", param_names)

if __name__ == "__main__":
    try:
        debug_scrape()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)




