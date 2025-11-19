"""
批量爬取 RapidAPI 并生成 MCP 服务器

支持从文件读取多个 RapidAPI URL，自动爬取并生成 MCP 项目
适合晚上挂机批量处理

使用方法：
    python batch_rapidapi.py urls.txt
    python batch_rapidapi.py urls.txt --transport sse --use-selenium
"""
import sys
import time
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import click

from src.api_to_mcp.platforms.rapidapi_auto import RapidAPIAutoExtractor
from src.api_to_mcp.generator.mcp_generator import MCPGenerator
from src.api_to_mcp.models import APISpec


class BatchRapidAPIProcessor:
    """批量 RapidAPI 处理器"""
    
    def __init__(
        self, 
        output_dir: str = "generated_mcps",
        transport: str = "stdio",
        use_selenium: bool = False,
        delay_seconds: int = 5,
        retry_times: int = 3
    ):
        self.output_dir = output_dir
        self.transport = transport
        self.use_selenium = use_selenium
        self.delay_seconds = delay_seconds
        self.retry_times = retry_times
        
        # 统计信息
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'results': []
        }
        
        # 日志文件
        self.log_file = f"batch_rapidapi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    def log(self, message: str, level: str = "INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] [{level}] {message}"
        print(log_message)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + '\n')
    
    def process_url(self, url: str, api_name: str = None) -> Dict[str, Any]:
        """处理单个 RapidAPI URL"""
        result = {
            'url': url,
            'name': api_name,
            'status': 'pending',
            'error': None,
            'output_dir': None,
            'tools_count': 0
        }
        
        try:
            self.log(f"开始处理: {url}")
            
            # 创建提取器
            extractor = RapidAPIAutoExtractor()
            
            # 根据是否使用 Selenium 选择方法
            if self.use_selenium:
                self.log("使用 Selenium 深度爬取...")
                openapi_spec = extractor.auto_extract_with_selenium(url, verify_ssl=True)
            else:
                self.log("使用基础方法爬取...")
                openapi_spec = extractor.auto_extract(url, verify_ssl=True)
            
            if not openapi_spec:
                raise Exception("无法提取 API 规范")
            
            # 转换为 APISpec
            api_spec = self._openapi_to_api_spec(openapi_spec, url)
            
            # 生成 MCP 服务器
            generator = MCPGenerator(output_dir=self.output_dir)
            mcp_server = generator.generate(
                api_spec=api_spec,
                transport=self.transport,
                custom_name=api_name
            )
            
            result['status'] = 'success'
            result['output_dir'] = mcp_server.output_path
            result['tools_count'] = len(mcp_server.tools)
            
            self.log(f"✅ 成功: {url}")
            self.log(f"   输出目录: {mcp_server.output_path}")
            self.log(f"   工具数量: {len(mcp_server.tools)}")
            
            self.stats['success'] += 1
            
        except Exception as e:
            result['status'] = 'failed'
            result['error'] = str(e)
            self.log(f"❌ 失败: {url}", level="ERROR")
            self.log(f"   错误: {e}", level="ERROR")
            self.stats['failed'] += 1
        
        return result
    
    def process_urls(self, urls: List[Dict[str, str]]) -> Dict[str, Any]:
        """批量处理 URL 列表"""
        self.stats['total'] = len(urls)
        
        self.log("=" * 80)
        self.log(f"🚀 开始批量处理 RapidAPI")
        self.log(f"📊 总数: {len(urls)}")
        self.log(f"🔧 传输协议: {self.transport}")
        self.log(f"🌐 使用 Selenium: {'是' if self.use_selenium else '否'}")
        self.log(f"⏱️  延迟: {self.delay_seconds} 秒")
        self.log("=" * 80)
        self.log("")
        
        start_time = time.time()
        
        for i, url_info in enumerate(urls):
            url = url_info.get('url', url_info) if isinstance(url_info, dict) else url_info
            name = url_info.get('name') if isinstance(url_info, dict) else None
            
            self.log(f"\n📍 [{i+1}/{len(urls)}] 处理中...")
            self.log(f"   URL: {url}")
            if name:
                self.log(f"   名称: {name}")
            
            # 处理单个 URL（带重试）
            result = None
            for attempt in range(self.retry_times):
                try:
                    result = self.process_url(url, name)
                    if result['status'] == 'success':
                        break
                    
                    if attempt < self.retry_times - 1:
                        self.log(f"   ⚠️  重试 {attempt + 1}/{self.retry_times - 1}...", level="WARN")
                        time.sleep(self.delay_seconds)
                except Exception as e:
                    self.log(f"   ❌ 处理异常: {e}", level="ERROR")
                    if attempt < self.retry_times - 1:
                        time.sleep(self.delay_seconds)
            
            if result:
                self.stats['results'].append(result)
            
            # 延迟，避免被封
            if i < len(urls) - 1:
                self.log(f"   ⏱️  等待 {self.delay_seconds} 秒...")
                time.sleep(self.delay_seconds)
        
        # 统计
        elapsed_time = time.time() - start_time
        
        self.log("\n" + "=" * 80)
        self.log("🎉 批量处理完成！")
        self.log(f"📊 统计信息:")
        self.log(f"   总数: {self.stats['total']}")
        self.log(f"   成功: {self.stats['success']}")
        self.log(f"   失败: {self.stats['failed']}")
        self.log(f"   耗时: {elapsed_time:.2f} 秒 ({elapsed_time/60:.2f} 分钟)")
        self.log("=" * 80)
        
        # 保存结果
        self._save_report()
        
        return self.stats
    
    def _save_report(self):
        """保存处理报告"""
        report_file = f"batch_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)
        
        self.log(f"\n📄 详细报告已保存: {report_file}")
        
        # 生成成功列表
        success_list = [r for r in self.stats['results'] if r['status'] == 'success']
        if success_list:
            self.log("\n✅ 成功生成的 MCP 服务器:")
            for r in success_list:
                self.log(f"   • {r['name'] or 'Unknown'} ({r['tools_count']} 工具)")
                self.log(f"     路径: {r['output_dir']}")
        
        # 生成失败列表
        failed_list = [r for r in self.stats['results'] if r['status'] == 'failed']
        if failed_list:
            self.log("\n❌ 失败的 API:")
            for r in failed_list:
                self.log(f"   • {r['url']}")
                self.log(f"     错误: {r['error']}")
    
    def _openapi_to_api_spec(self, openapi: Dict[str, Any], source_url: str) -> APISpec:
        """将 OpenAPI 转换为 APISpec"""
        from src.api_to_mcp.models import APIEndpoint, APIParameter
        
        info = openapi.get('info', {})
        servers = openapi.get('servers', [])
        base_url = servers[0]['url'] if servers else None
        
        # 提取端点
        endpoints = []
        for path, methods in openapi.get('paths', {}).items():
            for method, operation in methods.items():
                # 提取参数
                parameters = []
                for param in operation.get('parameters', []):
                    parameters.append(APIParameter(
                        name=param['name'],
                        type=param.get('schema', {}).get('type', 'string'),
                        required=param.get('required', False),
                        description=param.get('description', ''),
                        default=param.get('schema', {}).get('default'),
                        enum=param.get('schema', {}).get('enum')
                    ))
                
                endpoint = APIEndpoint(
                    path=path,
                    method=method.upper(),
                    summary=operation.get('summary', ''),
                    description=operation.get('description', ''),
                    operation_id=operation.get('operationId'),
                    parameters=parameters,
                    responses=operation.get('responses', {})
                )
                endpoints.append(endpoint)
        
        # 提取认证配置
        auth_type = None
        auth_config = {}
        
        if 'components' in openapi and 'securitySchemes' in openapi['components']:
            schemes = openapi['components']['securitySchemes']
            if schemes:
                first_scheme = list(schemes.values())[0]
                auth_type = first_scheme.get('type')
                auth_config = first_scheme
        
        return APISpec(
            title=info.get('title', 'Unknown API'),
            version=info.get('version', '1.0.0'),
            description=info.get('description', ''),
            base_url=base_url,
            endpoints=endpoints,
            auth_type=auth_type,
            auth_config=auth_config,
            source_platform='rapidapi',
            source_url=source_url,
            servers=servers
        )


def read_urls_file(file_path: str) -> List[Dict[str, str]]:
    """
    从文件读取 URL 列表
    
    支持格式：
    1. 每行一个 URL
    2. JSON 格式: [{"url": "...", "name": "..."}, ...]
    3. JSON Lines 格式: {"url": "...", "name": "..."}
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    content = path.read_text(encoding='utf-8').strip()
    
    # 尝试解析为 JSON
    if content.startswith('['):
        try:
            urls = json.loads(content)
            return urls
        except:
            pass
    
    # 尝试解析为 JSON Lines
    if content.startswith('{'):
        try:
            urls = []
            for line in content.split('\n'):
                line = line.strip()
                if line:
                    urls.append(json.loads(line))
            return urls
        except:
            pass
    
    # 按行解析（纯文本）
    urls = []
    for line in content.split('\n'):
        line = line.strip()
        
        # 跳过注释和空行
        if not line or line.startswith('#'):
            continue
        
        # 如果是 URL，添加
        if line.startswith('http'):
            urls.append({'url': line})
    
    return urls


@click.command()
@click.argument('urls_file', type=click.Path(exists=True))
@click.option('--output-dir', '-o', default='generated_mcps', help='输出目录')
@click.option('--transport', '-t', default='stdio', type=click.Choice(['stdio', 'sse', 'streamable-http']), help='传输协议')
@click.option('--use-selenium', is_flag=True, help='使用 Selenium 完整提取参数和响应')
@click.option('--delay', '-d', default=5, type=int, help='每个 API 之间的延迟秒数（避免被封）')
@click.option('--retry', '-r', default=3, type=int, help='失败重试次数')
@click.option('--start-from', default=0, type=int, help='从第 N 个 URL 开始（断点续传）')
def main(urls_file: str, output_dir: str, transport: str, use_selenium: bool, delay: int, retry: int, start_from: int):
    """
    批量爬取 RapidAPI 并生成 MCP 服务器
    
    URLs_FILE: 包含 RapidAPI URL 的文件路径
    
    \b
    文件格式示例：
    
    1. 纯文本（每行一个 URL）:
       https://rapidapi.com/provider/api/api-name-1
       https://rapidapi.com/provider/api/api-name-2
       # 注释行会被忽略
    
    2. JSON 格式（可指定自定义名称）:
       [
         {"url": "https://...", "name": "custom-name-1"},
         {"url": "https://...", "name": "custom-name-2"}
       ]
    
    3. JSON Lines 格式:
       {"url": "https://...", "name": "custom-name-1"}
       {"url": "https://...", "name": "custom-name-2"}
    """
    try:
        # 读取 URL 列表
        click.echo("📖 读取 URL 列表...")
        urls = read_urls_file(urls_file)
        
        if not urls:
            click.echo("❌ 文件中没有找到有效的 URL", err=True)
            sys.exit(1)
        
        click.echo(f"✅ 找到 {len(urls)} 个 URL")
        
        # 应用断点续传
        if start_from > 0:
            click.echo(f"⏭️  跳过前 {start_from} 个 URL")
            urls = urls[start_from:]
            click.echo(f"📊 剩余 {len(urls)} 个 URL 待处理")
        
        # 确认开始
        if not click.confirm(f'\n是否开始批量处理？预计耗时: {len(urls) * delay / 60:.1f} 分钟'):
            click.echo("❌ 已取消")
            sys.exit(0)
        
        # 创建处理器
        processor = BatchRapidAPIProcessor(
            output_dir=output_dir,
            transport=transport,
            use_selenium=use_selenium,
            delay_seconds=delay,
            retry_times=retry
        )
        
        # 开始处理
        stats = processor.process_urls(urls)
        
        # 显示总结
        click.echo("\n" + "=" * 80)
        click.echo("🎉 批量处理完成！")
        click.echo("=" * 80)
        click.echo(f"✅ 成功: {stats['success']}/{stats['total']}")
        click.echo(f"❌ 失败: {stats['failed']}/{stats['total']}")
        click.echo(f"📁 输出目录: {output_dir}")
        click.echo(f"📄 日志文件: {processor.log_file}")
        click.echo("=" * 80)
        
        # 如果有失败的，显示失败列表
        failed_list = [r for r in stats['results'] if r['status'] == 'failed']
        if failed_list:
            click.echo("\n❌ 失败的 API:")
            for r in failed_list:
                click.echo(f"   • {r['url']}")
                click.echo(f"     原因: {r['error']}")
        
        sys.exit(0 if stats['failed'] == 0 else 1)
        
    except Exception as e:
        click.echo(f"\n❌ 批量处理失败: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

