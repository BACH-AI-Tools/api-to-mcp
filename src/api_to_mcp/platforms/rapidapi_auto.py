"""
RapidAPI 自动提取工具 - 自动从 RapidAPI 页面提取 API 信息
"""
import requests
import json
import re
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from .rapidapi_next_parser import parse_rapidapi_html


class RapidAPIAutoExtractor:
    """RapidAPI 自动信息提取器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def auto_extract_with_selenium(self, rapidapi_url: str, verify_ssl: bool = True, headless: bool = True) -> Dict[str, Any]:
        """
        使用 Selenium 完整提取（包括参数和响应）
        
        Args:
            rapidapi_url: RapidAPI URL
            verify_ssl: 是否验证 SSL
            headless: 是否无头模式（True=不显示浏览器，False=显示浏览器）
        
        Returns:
            完整的 OpenAPI 规范
        """
        print(f"🔍 自动分析 RapidAPI (Selenium 模式): {rapidapi_url}")
        
        # 1. 提取 API 基本信息
        api_info = self._extract_api_info_from_url(rapidapi_url)
        print(f"✅ API: {api_info['provider']}/{api_info['api_name']}")
        
        # 2. 先获取端点列表（使用静态方法）
        print("📥 获取端点列表...")
        response = self.session.get(rapidapi_url, verify=verify_ssl)
        response.raise_for_status()
        html = response.text
        
        # 使用 Next.js 解析器提取端点
        from .rapidapi_next_parser import RapidAPINextParser
        parser = RapidAPINextParser()
        parsed_data = parser.parse_html(html)
        
        if not parsed_data or not parsed_data.get('endpoints'):
            print("❌ 无法提取端点")
            return self._create_basic_template(api_info)
        
        endpoints = parsed_data['endpoints']
        print(f"✅ 提取到 {len(endpoints)} 个端点")
        
        # 3. 使用 Selenium 爬取每个端点的参数和响应
        print("🌐 使用 Selenium 爬取参数和响应...")
        
        from .rapidapi_selenium_scraper import scrape_with_selenium
        
        base_url = rapidapi_url
        enriched_endpoints = scrape_with_selenium(
            base_url,
            endpoints,
            headless=headless
        )
        
        # 4. 构建完整 OpenAPI
        parsed_data['endpoints'] = enriched_endpoints
        openapi = parser.build_openapi_from_data(parsed_data, api_info)
        
        return openapi
    
    def auto_extract(self, rapidapi_url: str, verify_ssl: bool = True) -> Dict[str, Any]:
        """
        自动从 RapidAPI URL 提取并构建 OpenAPI 规范
        
        Args:
            rapidapi_url: RapidAPI 页面 URL
            verify_ssl: 是否验证 SSL
        
        Returns:
            OpenAPI 3.0 规范
        """
        print(f"🔍 自动分析 RapidAPI: {rapidapi_url}")
        
        # 1. 提取 API 基本信息
        api_info = self._extract_api_info_from_url(rapidapi_url)
        print(f"✅ API: {api_info['provider']}/{api_info['api_name']}")
        
        # 2. 获取页面内容
        print("📥 获取页面内容...")
        response = self.session.get(rapidapi_url, verify=verify_ssl)
        response.raise_for_status()
        html = response.text
        print(f"   ✓ 页面大小: {len(html)} 字符")
        
        # 保存 HTML 用于调试
        import os
        os.makedirs('debug', exist_ok=True)
        debug_file = f"debug/debug_rapidapi_{api_info['api_name']}.html"
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"   💾 页面已保存到: {debug_file} (用于调试)")
        
        # 3. 尝试使用 Next.js 解析器（新方法）
        print("🔎 尝试 Next.js 数据解析器...")
        openapi = parse_rapidapi_html(
            html,
            api_info,
            fetch_params=True,  # 启用深度爬取，获取参数和响应
            verify_ssl=verify_ssl
        )
        
        if openapi:
            print("✅ 使用 Next.js 解析器成功提取数据!")
            print(f"   📍 完整端点数: {len(openapi.get('paths', {}))}")
            return openapi
        
        print("   Next.js 解析器未找到数据，尝试传统方法...")
        
        # 4. 提取 JSON 数据（传统方法）
        print("🔎 分析页面数据（传统方法）...")
        page_data = self._extract_page_data(html)
        
        if not page_data:
            print("⚠️  无法从页面提取数据")
            print("💡 建议:")
            print("   1. 查看保存的 HTML 文件: " + debug_file)
            print("   2. 使用交互式工具: python create_rapidapi_mcp.py")
            print("   3. 联系我们提供支持")
            print()
            print("⚠️  生成基本模板...")
            return self._create_basic_template(api_info)
        
        # 5. 构建 OpenAPI（传统方法）
        print("🔨 构建 OpenAPI 规范...")
        openapi = self._build_openapi_from_page_data(page_data, api_info)
        
        print(f"✅ 提取成功: {openapi['info']['title']}")
        print(f"   📍 端点数量: {len(openapi.get('paths', {}))}")
        
        # 保存提取的数据用于调试
        os.makedirs('debug', exist_ok=True)
        debug_data_file = f"debug/debug_rapidapi_{api_info['api_name']}_data.json"
        with open(debug_data_file, 'w', encoding='utf-8') as f:
            json.dump(page_data, f, indent=2, ensure_ascii=False)
        print(f"   💾 提取的数据已保存到: {debug_data_file} (用于调试)")
        
        return openapi
    
    def _extract_api_info_from_url(self, url: str) -> Dict[str, str]:
        """从 URL 提取 API 信息"""
        pattern = r'rapidapi\.com/([^/]+)/api/([^/?]+)'
        match = re.search(pattern, url)
        
        if not match:
            raise ValueError(f"无法识别的 RapidAPI URL: {url}")
        
        provider = match.group(1)
        api_name = match.group(2)
        
        return {
            "provider": provider,
            "api_name": api_name,
            "url": url,
            "host": f"{api_name}.p.rapidapi.com",
            "base_url": f"https://{api_name}.p.rapidapi.com"
        }
    
    def _extract_page_data(self, html: str) -> Optional[Dict[str, Any]]:
        """从页面提取 JSON 数据"""
        
        print("   🔎 搜索 __NEXT_DATA__...")
        # 方法 1: __NEXT_DATA__
        pattern = r'<script[^>]*id="__NEXT_DATA__"[^>]*type="application/json"[^>]*>(.*?)</script>'
        match = re.search(pattern, html, re.DOTALL)
        if match:
            try:
                json_text = match.group(1)
                print(f"   ✓ 找到 __NEXT_DATA__ (长度: {len(json_text)} 字符)")
                data = json.loads(json_text)
                print(f"   ✓ 成功解析 __NEXT_DATA__")
                print(f"   📊 数据结构键: {list(data.keys())}")
                return data
            except Exception as e:
                print(f"   ❌ 解析 __NEXT_DATA__ 失败: {e}")
        else:
            print("   ✗ 未找到 __NEXT_DATA__")
        
        print("   🔎 搜索 __INITIAL_STATE__...")
        # 方法 2: __INITIAL_STATE__
        pattern = r'window\.__INITIAL_STATE__\s*=\s*({.*?});'
        match = re.search(pattern, html, re.DOTALL)
        if match:
            try:
                json_text = match.group(1)
                print(f"   ✓ 找到 __INITIAL_STATE__ (长度: {len(json_text)} 字符)")
                data = json.loads(json_text)
                print(f"   ✓ 成功解析 __INITIAL_STATE__")
                print(f"   📊 数据结构键: {list(data.keys())}")
                return data
            except Exception as e:
                print(f"   ❌ 解析 __INITIAL_STATE__ 失败: {e}")
        else:
            print("   ✗ 未找到 __INITIAL_STATE__")
        
        print("   🔎 搜索其他 JSON 数据模式...")
        # 方法 3: 其他 JSON 数据
        patterns = [
            (r'window\.apiData\s*=\s*({.*?});', 'window.apiData'),
            (r'var\s+apiSpec\s*=\s*({.*?});', 'var apiSpec'),
            (r'const\s+spec\s*=\s*({.*?});', 'const spec'),
            (r'window\.__REDUX_STATE__\s*=\s*({.*?});', 'window.__REDUX_STATE__'),
        ]
        
        for pattern, name in patterns:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                try:
                    json_text = match.group(1)
                    print(f"   ✓ 找到 {name} (长度: {len(json_text)} 字符)")
                    data = json.loads(json_text)
                    print(f"   ✓ 成功解析 {name}")
                    print(f"   📊 数据结构键: {list(data.keys())}")
                    return data
                except Exception as e:
                    print(f"   ❌ 解析 {name} 失败: {e}")
                    continue
        
        print("   ✗ 未找到任何可识别的 JSON 数据")
        
        # 方法 4: 搜索页面中所有的大型 JSON 块
        print("   🔎 搜索页面中的所有 JSON 块...")
        json_blocks = re.findall(r'({[^{}]*(?:{[^{}]*}[^{}]*)*})', html, re.DOTALL)
        print(f"   📊 找到 {len(json_blocks)} 个潜在 JSON 块")
        
        for i, block in enumerate(json_blocks[:5]):  # 只检查前5个
            if len(block) > 1000:  # 只检查大块
                try:
                    data = json.loads(block)
                    if isinstance(data, dict) and len(data) > 3:
                        print(f"   ✓ 成功解析 JSON 块 #{i+1}")
                        print(f"   📊 数据结构键: {list(data.keys())[:10]}")
                        # 检查是否包含 API 相关信息
                        if any(key in str(data).lower() for key in ['api', 'endpoint', 'path', 'operation']):
                            print(f"   ✓ JSON 块 #{i+1} 可能包含 API 数据")
                            return data
                except:
                    continue
        
        return None
    
    def _build_openapi_from_page_data(
        self, page_data: Dict[str, Any], api_info: Dict[str, str]
    ) -> Dict[str, Any]:
        """从页面数据构建 OpenAPI"""
        
        print("   🔍 分析数据结构...")
        print(f"   📊 顶层键: {list(page_data.keys())}")
        
        # 尝试从 __NEXT_DATA__ 提取
        props = page_data.get('props', {})
        print(f"   📊 props 键: {list(props.keys()) if props else 'None'}")
        
        page_props = props.get('pageProps', {})
        print(f"   📊 pageProps 键: {list(page_props.keys()) if page_props else 'None'}")
        
        # 提取 API 数据
        api_data = (
            page_props.get('api') or
            page_props.get('data') or
            page_props.get('apiData') or
            page_data.get('api') or
            page_data.get('data') or
            {}
        )
        
        if api_data:
            print(f"   ✓ 找到 API 数据")
            print(f"   📊 API 数据键: {list(api_data.keys()) if isinstance(api_data, dict) else 'Not a dict'}")
        else:
            print(f"   ✗ 未找到 API 数据")
        
        # 基本信息
        title = api_data.get('name') or api_data.get('title') or api_info['api_name'].replace('-', ' ').title()
        description = api_data.get('description') or api_data.get('summary') or f"RapidAPI: {api_info['provider']}/{api_info['api_name']}"
        version = str(api_data.get('version', '1.0.0'))
        
        # 构建基础 OpenAPI
        openapi = {
            "openapi": "3.0.0",
            "info": {
                "title": title,
                "description": description,
                "version": version
            },
            "servers": [
                {"url": api_info['base_url']}
            ],
            "paths": {},
            "components": {
                "securitySchemes": {
                    "RapidAPIKey": {
                        "type": "apiKey",
                        "in": "header",
                        "name": "X-RapidAPI-Key"
                    },
                    "RapidAPIHost": {
                        "type": "apiKey",
                        "in": "header",
                        "name": "X-RapidAPI-Host"
                    }
                }
            },
            "security": [
                {"RapidAPIKey": []},
                {"RapidAPIHost": []}
            ]
        }
        
        # 提取端点 - 尝试多种可能的键名
        print("   🔍 搜索端点数据...")
        endpoints = None
        
        possible_endpoint_keys = ['endpoints', 'paths', 'operations', 'routes', 'apis']
        for key in possible_endpoint_keys:
            if key in api_data:
                endpoints = api_data[key]
                print(f"   ✓ 在 api_data['{key}'] 找到端点数据")
                break
        
        # 如果 api_data 本身就是端点列表
        if not endpoints and isinstance(api_data, list):
            endpoints = api_data
            print(f"   ✓ api_data 本身就是端点列表")
        
        if endpoints and len(endpoints) > 0:
            print(f"   ✓ 找到 {len(endpoints)} 个端点")
            print(f"   📊 第一个端点的键: {list(endpoints[0].keys()) if isinstance(endpoints[0], dict) else 'Not a dict'}")
            
            for i, endpoint in enumerate(endpoints):
                print(f"   处理端点 #{i+1}...")
                self._add_endpoint(openapi, endpoint)
        else:
            print("   ⚠️  未找到端点数据")
            print(f"   💡 api_data 类型: {type(api_data)}")
            print(f"   💡 api_data 内容预览: {str(api_data)[:200]}...")
            print("   ⚠️  创建基本模板")
            
            # 创建一个示例端点
            openapi["paths"]["/endpoint"] = {
                "get": {
                    "summary": "API Endpoint",
                    "description": "请手动修改此端点或使用交互式工具",
                    "operationId": "api_endpoint",
                    "parameters": [],
                    "responses": {
                        "200": {"description": "Success"}
                    }
                }
            }
        
        return openapi
    
    def _add_endpoint(self, openapi: Dict[str, Any], endpoint: Dict[str, Any]):
        """添加端点到 OpenAPI"""
        print(f"      - 端点数据键: {list(endpoint.keys())}")
        
        # 提取端点信息（适配不同的数据结构）
        path = endpoint.get('path') or endpoint.get('url') or endpoint.get('route') or endpoint.get('endpoint') or '/'
        method = (endpoint.get('method') or endpoint.get('verb') or endpoint.get('httpMethod') or 'GET').lower()
        name = endpoint.get('name') or endpoint.get('summary') or endpoint.get('operationId') or endpoint.get('title') or f"{method}_{path}"
        description = endpoint.get('description') or endpoint.get('summary') or endpoint.get('details') or ''
        
        print(f"      ✓ 路径: {path}, 方法: {method}, 名称: {name}")
        
        if path not in openapi["paths"]:
            openapi["paths"][path] = {}
        
        # 构建操作
        operation = {
            "summary": name,
            "description": description,
            "operationId": name.lower().replace(' ', '_').replace('-', '_'),
            "parameters": [],
            "responses": {
                "200": {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "schema": {"type": "object"}
                        }
                    }
                }
            }
        }
        
        # 添加参数
        params = endpoint.get('parameters') or endpoint.get('params') or []
        for param in params:
            param_schema = {
                "name": param.get('name', ''),
                "in": param.get('in', 'query'),
                "required": param.get('required', False),
                "description": param.get('description', ''),
                "schema": {
                    "type": param.get('type', 'string')
                }
            }
            
            # 添加默认值和枚举
            if 'default' in param:
                param_schema['schema']['default'] = param['default']
            if 'enum' in param:
                param_schema['schema']['enum'] = param['enum']
            
            operation["parameters"].append(param_schema)
        
        openapi["paths"][path][method] = operation
    
    def _create_basic_template(self, api_info: Dict[str, str]) -> Dict[str, Any]:
        """创建基本模板（当无法提取数据时）"""
        return {
            "openapi": "3.0.0",
            "info": {
                "title": api_info['api_name'].replace('-', ' ').title(),
                "description": f"RapidAPI: {api_info['provider']}/{api_info['api_name']}",
                "version": "1.0.0"
            },
            "servers": [
                {"url": api_info['base_url']}
            ],
            "paths": {
                "/endpoint": {
                    "get": {
                        "summary": "API Endpoint",
                        "description": "请根据 RapidAPI 页面手动添加端点信息",
                        "operationId": "api_endpoint",
                        "parameters": [
                            {
                                "name": "param",
                                "in": "query",
                                "required": False,
                                "description": "参数",
                                "schema": {"type": "string"}
                            }
                        ],
                        "responses": {
                            "200": {"description": "Success"}
                        }
                    }
                }
            },
            "components": {
                "securitySchemes": {
                    "RapidAPIKey": {
                        "type": "apiKey",
                        "in": "header",
                        "name": "X-RapidAPI-Key"
                    },
                    "RapidAPIHost": {
                        "type": "apiKey",
                        "in": "header",
                        "name": "X-RapidAPI-Host"
                    }
                }
            },
            "security": [
                {"RapidAPIKey": []},
                {"RapidAPIHost": []}
            ]
        }


def auto_extract_rapidapi(rapidapi_url: str, verify_ssl: bool = True) -> Dict[str, Any]:
    """自动从 RapidAPI 提取并构建 OpenAPI 规范"""
    extractor = RapidAPIAutoExtractor()
    return extractor.auto_extract(rapidapi_url, verify_ssl)

