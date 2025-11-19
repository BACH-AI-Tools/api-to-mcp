#!/usr/bin/env python3
"""
Selenium 一键安装脚本
"""
import subprocess
import sys
import os

def install_selenium():
    """安装 Selenium 和 webdriver-manager"""
    print("🚀 安装 Selenium 完全自动化支持...")
    print("=" * 60)
    print()
    
    # 安装 selenium
    print("📦 安装 selenium...")
    subprocess.run([sys.executable, "-m", "pip", "install", "selenium"], check=True)
    print("✅ selenium 已安装")
    print()
    
    # 安装 webdriver-manager
    print("📦 安装 webdriver-manager（自动管理 ChromeDriver）...")
    subprocess.run([sys.executable, "-m", "pip", "install", "webdriver-manager"], check=True)
    print("✅ webdriver-manager 已安装")
    print()
    
    # 验证
    print("🔍 验证安装...")
    try:
        import selenium
        print(f"✅ Selenium 版本: {selenium.__version__}")
        
        from webdriver_manager.chrome import ChromeDriverManager
        print("✅ webdriver-manager 可用")
        
        print()
        print("=" * 60)
        print("🎉 安装完成！")
        print()
        print("📝 现在可以使用 Selenium 模式:")
        print("   api-to-mcp rapidapi <URL> -n <name> --use-selenium")
        print()
        print("💡 webdriver-manager 会在首次使用时自动下载 ChromeDriver")
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        install_selenium()
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 安装失败: {e}")
        print("\n💡 请手动安装:")
        print("   pip install selenium webdriver-manager")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n❌ 已取消")
        sys.exit(1)

