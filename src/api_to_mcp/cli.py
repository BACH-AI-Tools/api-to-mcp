"""
命令行接口
"""
import click
import json
import sys
from pathlib import Path
from typing import Optional

from .config import AzureOpenAIConfig, RapidAPIConfig, MCPGeneratorConfig
from .parsers import OpenAPIParser
from .platforms import RapidAPISpecFetcher
from .enhancer import DescriptionEnhancer
from .generator import MCPGenerator
from .tester import test_mcp_server
from .publisher import publish_mcp_server
from .platforms.rapidapi_helper import RapidAPIHelper
from .platforms.rapidapi_auto import auto_extract_rapidapi


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """API to MCP - 将 Web API 转换为 MCP 服务器"""
    pass


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output-dir', '-o', default='generated_mcps', help='输出目录')
@click.option('--enhance/--no-enhance', default=True, help='是否使用 LLM 增强描述')
@click.option('--platform', '-p', default='openapi', type=click.Choice(['openapi', 'swagger', 'rapidapi']), help='API 平台类型')
@click.option('--transport', '-t', default='stdio', type=click.Choice(['stdio', 'sse', 'streamable-http']), help='MCP 传输协议')
@click.option('--name', '-n', help='自定义 MCP 服务器名称（默认从 API 标题生成）')
def convert(input_file: str, output_dir: str, enhance: bool, platform: str, transport: str, name: Optional[str]):
    """
    从文件转换 API 到 MCP 服务器
    
    支持的文件格式:
    - OpenAPI 3.0+ (JSON/YAML)
    - Swagger 2.0 (JSON/YAML)
    """
    click.echo(f"🚀 开始转换: {input_file}")
    click.echo(f"📦 平台类型: {platform}")
    
    try:
        # 解析 API 规范
        click.echo("📖 解析 API 规范...")
        if platform == 'rapidapi':
            fetcher = RapidAPISpecFetcher()
            api_spec = fetcher.fetch_from_file(input_file)
        else:
            parser = OpenAPIParser()
            api_spec = parser.parse_file(input_file)
        
        click.echo(f"✅ 解析成功: {api_spec.title} v{api_spec.version}")
        click.echo(f"   端点数量: {len(api_spec.endpoints)}")
        
        # 增强描述
        if enhance:
            click.echo("🤖 使用 LLM 增强描述...")
            enhancer = DescriptionEnhancer()
            api_spec = enhancer.enhance_api_spec(api_spec)
            click.echo("✅ 描述增强完成")
        
        # 生成 MCP 服务器
        click.echo("🔨 生成 MCP 服务器代码...")
        click.echo(f"📡 传输协议: {transport}")
        if name:
            click.echo(f"📝 自定义名称: {name}")
        generator = MCPGenerator(output_dir=output_dir)
        mcp_server = generator.generate(api_spec, transport=transport, custom_name=name)
        
        click.echo(f"✅ 生成完成!")
        click.echo(f"📁 输出目录: {mcp_server.output_path}")
        click.echo(f"🎉 MCP 服务器: {mcp_server.name} v{mcp_server.version}")
        click.echo(f"🔧 工具数量: {len(mcp_server.tools)}")
        click.echo(f"📡 协议: {transport}")
        click.echo()
        click.echo("📝 运行方法:")
        click.echo(f"   cd {mcp_server.output_path}")
        click.echo(f"   python server.py")
        
    except Exception as e:
        click.echo(f"❌ 错误: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument('spec_url')
@click.option('--output-dir', '-o', default='generated_mcps', help='输出目录')
@click.option('--enhance/--no-enhance', default=True, help='是否使用 LLM 增强描述')
@click.option('--api-key', '-k', help='RapidAPI Key')
@click.option('--transport', '-t', default='stdio', type=click.Choice(['stdio', 'sse', 'streamable-http']), help='MCP 传输协议')
@click.option('--no-verify-ssl', is_flag=True, help='跳过 SSL 证书验证（不安全，仅用于测试）')
@click.option('--name', '-n', help='自定义 MCP 服务器名称（默认从 API 标题生成）')
def from_url(spec_url: str, output_dir: str, enhance: bool, api_key: Optional[str], transport: str, no_verify_ssl: bool, name: Optional[str]):
    """
    从 URL 获取 OpenAPI 规范并转换为 MCP 服务器
    """
    click.echo(f"🚀 从 URL 获取 API 规范: {spec_url}")
    
    try:
        # 获取 API 规范
        click.echo("📥 下载 API 规范...")
        if no_verify_ssl:
            click.echo("⚠️  警告: 已禁用 SSL 证书验证（不安全）")
        fetcher = RapidAPISpecFetcher()
        api_spec = fetcher.fetch_from_url(spec_url, api_key, verify_ssl=not no_verify_ssl)
        
        click.echo(f"✅ 获取成功: {api_spec.title} v{api_spec.version}")
        click.echo(f"   端点数量: {len(api_spec.endpoints)}")
        
        # 增强描述
        if enhance:
            click.echo("🤖 使用 LLM 增强描述...")
            enhancer = DescriptionEnhancer()
            api_spec = enhancer.enhance_api_spec(api_spec)
            click.echo("✅ 描述增强完成")
        
        # 生成 MCP 服务器
        click.echo("🔨 生成 MCP 服务器代码...")
        click.echo(f"📡 传输协议: {transport}")
        if name:
            click.echo(f"📝 自定义名称: {name}")
        generator = MCPGenerator(output_dir=output_dir)
        mcp_server = generator.generate(api_spec, transport=transport, custom_name=name)
        
        click.echo(f"✅ 生成完成!")
        click.echo(f"📁 输出目录: {mcp_server.output_path}")
        click.echo(f"🎉 MCP 服务器: {mcp_server.name} v{mcp_server.version}")
        click.echo(f"🔧 工具数量: {len(mcp_server.tools)}")
        click.echo(f"📡 协议: {transport}")
        click.echo()
        click.echo("📝 运行方法:")
        click.echo(f"   cd {mcp_server.output_path}")
        click.echo(f"   python server.py")
        
    except Exception as e:
        click.echo(f"❌ 错误: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
def validate(input_file: str):
    """
    验证 OpenAPI/Swagger 规范文件
    """
    click.echo(f"🔍 验证 API 规范: {input_file}")
    
    try:
        parser = OpenAPIParser()
        api_spec = parser.parse_file(input_file)
        
        click.echo(f"✅ 验证成功!")
        click.echo()
        click.echo(f"📋 API 信息:")
        click.echo(f"   名称: {api_spec.title}")
        click.echo(f"   版本: {api_spec.version}")
        if api_spec.description:
            click.echo(f"   描述: {api_spec.description[:100]}...")
        click.echo(f"   基础 URL: {api_spec.base_url or 'N/A'}")
        click.echo(f"   端点数量: {len(api_spec.endpoints)}")
        
        if api_spec.auth_type:
            click.echo(f"   认证类型: {api_spec.auth_type}")
        
        click.echo()
        click.echo("📍 端点列表:")
        for endpoint in api_spec.endpoints[:10]:  # 只显示前 10 个
            click.echo(f"   {endpoint.method:6} {endpoint.path}")
            if endpoint.summary:
                click.echo(f"          {endpoint.summary[:70]}")
        
        if len(api_spec.endpoints) > 10:
            click.echo(f"   ... 还有 {len(api_spec.endpoints) - 10} 个端点")
        
    except Exception as e:
        click.echo(f"❌ 验证失败: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument('server_path', type=click.Path(exists=True))
def test(server_path: str):
    """
    测试生成的 MCP 服务器
    """
    try:
        result = test_mcp_server(server_path)
        
        if result["all_passed"]:
            click.echo()
            click.echo("🎉 所有测试通过! MCP 服务器可以发布")
            sys.exit(0)
        else:
            click.echo()
            click.echo("❌ 部分测试失败，请修复后再发布")
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ 测试异常: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('server_path', type=click.Path(exists=True))
@click.option('--target', '-t', default='testpypi', type=click.Choice(['testpypi', 'pypi']), help='发布目标')
def publish(server_path: str, target: str):
    """
    发布 MCP 服务器到 PyPI
    
    需要先配置 PyPI/TestPyPI API Token:
    https://pypi.org/manage/account/token/
    """
    try:
        result = publish_mcp_server(server_path, target)
        
        if result["success"]:
            click.echo()
            click.echo(f"🎉 成功发布到 {target.upper()}!")
            if target == "testpypi":
                click.echo()
                click.echo("📝 测试安装:")
                server_name = Path(server_path).name
                click.echo(f"   pip install -i https://test.pypi.org/simple/ {server_name}")
            sys.exit(0)
        else:
            click.echo()
            click.echo(f"❌ 发布失败在 {result.get('stage', 'unknown')} 阶段")
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ 发布异常: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('rapidapi_url')
@click.option('--output-dir', '-o', default='generated_mcps', help='输出目录')
@click.option('--name', '-n', help='自定义 MCP 服务器名称')
@click.option('--no-verify-ssl', is_flag=True, help='跳过 SSL 验证')
@click.option('--enhance/--no-enhance', default=False, help='是否使用 LLM 增强描述')
@click.option('--transport', '-t', default='stdio', type=click.Choice(['stdio', 'sse', 'streamable-http']), help='传输协议')
@click.option('--use-selenium', is_flag=True, help='使用 Selenium 完整提取参数和响应（需要 selenium 和 ChromeDriver）')
@click.option('--show-browser', is_flag=True, help='显示浏览器窗口（用于调试，默认无头模式）')
def rapidapi(rapidapi_url: str, output_dir: str, name: Optional[str], no_verify_ssl: bool, enhance: bool, transport: str, use_selenium: bool, show_browser: bool):
    """
    自动从 RapidAPI 提取并转换为 MCP 服务器 🚀
    
    这是最简单的方法！只需提供 RapidAPI URL，工具会自动：
    1. 提取 API 信息
    2. 构建 OpenAPI 规范
    3. 生成 MCP 服务器
    
    示例: 
        api-to-mcp rapidapi https://rapidapi.com/openweb-ninja/api/jsearch -n jsearch
    """
    click.echo(f"🚀 自动处理 RapidAPI: {rapidapi_url}")
    click.echo()
    
    try:
        # 自动提取
        click.echo("🔍 自动提取 API 信息...")
        if no_verify_ssl:
            click.echo("⚠️  警告: 已禁用 SSL 验证")
        
        if use_selenium:
            if show_browser:
                click.echo("🌐 使用 Selenium 浏览器自动化（显示浏览器窗口）...")
            else:
                click.echo("🌐 使用 Selenium 浏览器自动化（无头模式）...")
            try:
                from .platforms.rapidapi_auto import RapidAPIAutoExtractor
                
                extractor = RapidAPIAutoExtractor()
                # 使用 Selenium 模式
                openapi_spec = extractor.auto_extract_with_selenium(
                    rapidapi_url, 
                    verify_ssl=not no_verify_ssl,
                    headless=not show_browser  # show_browser=True 时使用有头模式
                )
                
            except ImportError as e:
                click.echo(f"❌ Selenium 未安装: {e}")
                click.echo("💡 安装方法:")
                click.echo("   pip install selenium")
                click.echo("   下载 ChromeDriver: https://chromedriver.chromium.org/")
                raise click.Abort()
        else:
            openapi_spec = auto_extract_rapidapi(rapidapi_url, verify_ssl=not no_verify_ssl)
        
        # 保存 OpenAPI 文件
        import re
        match = re.search(r'/api/([^/?]+)', rapidapi_url)
        api_name = match.group(1) if match else 'api'
        openapi_file = f"rapidapi_{api_name}_auto.json"
        
        with open(openapi_file, 'w', encoding='utf-8') as f:
            json.dump(openapi_spec, f, indent=2, ensure_ascii=False)
        
        click.echo(f"✅ OpenAPI 规范已保存: {openapi_file}")
        
        # 解析并生成
        parser = OpenAPIParser()
        api_spec = parser.parse_dict(openapi_spec)
        
        click.echo(f"✅ 解析成功: {api_spec.title}")
        click.echo(f"   端点数量: {len(api_spec.endpoints)}")
        
        # 增强描述
        if enhance:
            click.echo("🤖 使用 LLM 增强描述...")
            enhancer = DescriptionEnhancer()
            api_spec = enhancer.enhance_api_spec(api_spec)
            click.echo("✅ 描述增强完成")
        
        # 生成 MCP
        click.echo("🔨 生成 MCP 服务器...")
        generator = MCPGenerator(output_dir=output_dir)
        mcp_server = generator.generate(api_spec, transport=transport, custom_name=name)
        
        click.echo()
        click.echo("🎉 完成!")
        click.echo(f"📁 输出目录: {mcp_server.output_path}")
        click.echo(f"🎉 MCP 服务器: {mcp_server.name}")
        click.echo(f"🔧 工具数量: {len(mcp_server.tools)}")
        click.echo()
        click.echo("📝 运行方法:")
        click.echo(f"   cd {mcp_server.output_path}")
        click.echo(f"   python server.py")
        click.echo()
        click.echo("🔑 记得设置 RapidAPI Key:")
        click.echo(f"   set API_KEY=你的RapidAPI-Key")
        
    except Exception as e:
        click.echo(f"❌ 错误: {e}", err=True)
        import traceback
        click.echo("\n详细错误:")
        click.echo(traceback.format_exc())
        raise click.Abort()


@cli.command()
@click.argument('rapidapi_url')
def rapidapi_help(rapidapi_url: str):
    """
    获取从 RapidAPI 获取 OpenAPI 规范的帮助（旧方法）
    
    ⚠️  建议使用新命令: api-to-mcp rapidapi <url>
    
    示例: api-to-mcp rapidapi-help https://rapidapi.com/apidojo/api/yahoo-finance1
    """
    click.echo("⚠️  建议使用新命令: api-to-mcp rapidapi <url> -n <name>")
    click.echo("   这个命令会自动完成所有步骤！")
    click.echo()
    
    helper = RapidAPIHelper()
    instructions = helper.generate_instructions(rapidapi_url)
    click.echo(instructions)
    
    # 尝试自动获取
    click.echo("\n🔍 尝试自动获取规范...")
    try:
        spec = helper.fetch_from_rapidapi_page(rapidapi_url)
        if spec:
            # 保存到文件
            api_info = helper.extract_api_info_from_url(rapidapi_url)
            if api_info:
                filename = f"rapidapi_{api_info['api']}_spec.json"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(spec, f, indent=2, ensure_ascii=False)
                
                click.echo(f"✅ 成功获取并保存规范到: {filename}")
                click.echo()
                click.echo("📝 下一步:")
                click.echo(f"   api-to-mcp convert {filename} -n {api_info['api']}")
        else:
            click.echo("❌ 无法自动获取，请使用上述手动方法")
    except Exception as e:
        click.echo(f"⚠️  自动获取失败: {e}")
        click.echo("请使用上述手动方法")


@cli.command()
def config():
    """
    显示当前配置
    """
    click.echo("⚙️  当前配置:")
    click.echo()
    
    # Azure OpenAI 配置
    azure_config = AzureOpenAIConfig.from_env()
    click.echo("🤖 Azure OpenAI:")
    click.echo(f"   Endpoint: {azure_config.endpoint}")
    click.echo(f"   Deployment: {azure_config.deployment_name}")
    click.echo(f"   API Key: {'***' + azure_config.api_key[-4:] if azure_config.api_key else '未设置'}")
    click.echo()
    
    # RapidAPI 配置
    rapidapi_config = RapidAPIConfig.from_env()
    click.echo("🚀 RapidAPI:")
    if rapidapi_config.api_key:
        click.echo(f"   API Key: ***{rapidapi_config.api_key[-4:]}")
    else:
        click.echo("   API Key: 未设置")
    click.echo()
    
    # MCP 生成器配置
    mcp_config = MCPGeneratorConfig()
    click.echo("📦 MCP 生成器:")
    click.echo(f"   输出目录: {mcp_config.output_dir}")
    click.echo(f"   默认版本: {mcp_config.default_version}")


def main():
    """主入口"""
    cli()


if __name__ == '__main__':
    main()

