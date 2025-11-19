"""
RapidAPI 页面抓取器 - 从 RapidAPI 网页提取端点信息
"""
import requests
import json
import re
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup


class RapidAPIScraper:
    """从 RapidAPI 页面抓取 API 信息并构建 OpenAPI 规范"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def scrape_api(self, rapidapi_url: str, api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        从 RapidAPI URL 抓取 API 信息并构建 OpenAPI 规范
        
        Args:
            rapidapi_url: RapidAPI 页面 URL
            api_key: RapidAPI Key (可选)
        
        Returns:
            OpenAPI 3.0 规范字典
        """
        # 提取 API 信息
        api_info = self._extract_api_info(rapidapi_url)
        if not api_info:
            raise ValueError("无法从 URL 提取 API 信息")
        
        # 获取页面内容
        response = self.session.get(rapidapi_url)
        response.raise_for_status()
        html_content = response.text
        
        # 尝试从页面中提取数据
        # 方法 1: 从 __NEXT_DATA__ 中提取
        next_data = self._extract_next_data(html_content)
        if next_data:
            return self._build_openapi_from_next_data(next_data, api_info, api_key)
        
        # 方法 2: 从 __INITIAL_STATE__ 中提取
        initial_state = self._extract_initial_state(html_content)
        if initial_state:
            return self._build_openapi_from_initial_state(initial_state, api_info, api_key)
        
        # 方法 3: 解析 HTML 结构
        return self._build_openapi_from_html(html_content, api_info, api_key)
    
    def _extract_api_info(self, url: str) -> Optional[Dict[str, str]]:
        """从 URL 提取 API 信息"""
        # https://rapidapi.com/openweb-ninja/api/jsearch
        pattern = r'rapidapi\.com/([^/]+)/api/([^/?]+)'
        match = re.search(pattern, url)
        
        if match:
            return {
                "provider": match.group(1),
                "api_name": match.group(2),
                "base_url": url
            }
        return None
    
    def _extract_next_data(self, html: str) -> Optional[Dict[str, Any]]:
        """从 __NEXT_DATA__ 提取数据"""
        pattern = r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>'
        match = re.search(pattern, html, re.DOTALL)
        
        if match:
            try:
                return json.loads(match.group(1))
            except:
                pass
        return None
    
    def _extract_initial_state(self, html: str) -> Optional[Dict[str, Any]]:
        """从 __INITIAL_STATE__ 提取数据"""
        pattern = r'window\.__INITIAL_STATE__\s*=\s*({.*?});'
        match = re.search(pattern, html, re.DOTALL)
        
        if match:
            try:
                return json.loads(match.group(1))
            except:
                pass
        return None
    
    def _build_openapi_from_next_data(
        self, next_data: Dict[str, Any], api_info: Dict[str, str], api_key: Optional[str]
    ) -> Dict[str, Any]:
        """从 __NEXT_DATA__ 构建 OpenAPI 规范"""
        
        # 尝试找到 API 数据
        props = next_data.get('props', {})
        page_props = props.get('pageProps', {})
        
        # 提取 API 元数据
        api_data = page_props.get('api', {}) or page_props.get('data', {})
        
        title = api_data.get('name', api_info['api_name'])
        description = api_data.get('description', '')
        version = api_data.get('version', '1.0.0')
        
        # 提取端点
        endpoints = api_data.get('endpoints', []) or []
        
        # 构建 OpenAPI
        openapi = {
            "openapi": "3.0.0",
            "info": {
                "title": title,
                "description": description,
                "version": str(version)
            },
            "servers": [
                {
                    "url": f"https://{api_info['api_name']}.p.rapidapi.com"
                }
            ],
            "paths": {},
            "components": {
                "securitySchemes": {
                    "RapidAPIAuth": {
                        "type": "apiKey",
                        "in": "header",
                        "name": "X-RapidAPI-Key"
                    }
                }
            },
            "security": [{"RapidAPIAuth": []}]
        }
        
        # 添加端点
        for endpoint in endpoints:
            self._add_endpoint_to_openapi(openapi, endpoint)
        
        return openapi
    
    def _build_openapi_from_initial_state(
        self, initial_state: Dict[str, Any], api_info: Dict[str, str], api_key: Optional[str]
    ) -> Dict[str, Any]:
        """从 __INITIAL_STATE__ 构建 OpenAPI 规范"""
        # 类似的逻辑
        return self._build_openapi_from_next_data(initial_state, api_info, api_key)
    
    def _build_openapi_from_html(
        self, html: str, api_info: Dict[str, str], api_key: Optional[str]
    ) -> Dict[str, Any]:
        """从 HTML 构建基本的 OpenAPI 规范（最后手段）"""
        
        # 构建基本的 OpenAPI 结构
        openapi = {
            "openapi": "3.0.0",
            "info": {
                "title": api_info['api_name'].replace('-', ' ').title(),
                "description": f"API from RapidAPI: {api_info['provider']}/{api_info['api_name']}",
                "version": "1.0.0"
            },
            "servers": [
                {
                    "url": f"https://{api_info['api_name']}.p.rapidapi.com"
                }
            ],
            "paths": {},
            "components": {
                "securitySchemes": {
                    "RapidAPIAuth": {
                        "type": "apiKey",
                        "in": "header",
                        "name": "X-RapidAPI-Key"
                    }
                }
            },
            "security": [{"RapidAPIAuth": []}]
        }
        
        # 尝试从 HTML 中提取端点信息
        # 这是一个基本实现，可能需要根据实际页面结构调整
        soup = BeautifulSoup(html, 'html.parser')
        
        # 查找端点相关的脚本或数据
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and ('endpoint' in script.string.lower() or 'path' in script.string.lower()):
                # 尝试提取端点信息
                try:
                    # 这里需要根据实际页面结构来解析
                    pass
                except:
                    continue
        
        return openapi
    
    def _add_endpoint_to_openapi(self, openapi: Dict[str, Any], endpoint: Dict[str, Any]):
        """添加端点到 OpenAPI 规范"""
        path = endpoint.get('path', endpoint.get('url', '/'))
        method = endpoint.get('method', 'GET').lower()
        
        if path not in openapi['paths']:
            openapi['paths'][path] = {}
        
        operation = {
            "summary": endpoint.get('name', endpoint.get('summary', '')),
            "description": endpoint.get('description', ''),
            "operationId": endpoint.get('id', f"{method}_{path.replace('/', '_')}"),
            "parameters": [],
            "responses": {
                "200": {
                    "description": "Successful response"
                }
            }
        }
        
        # 添加参数
        params = endpoint.get('parameters', []) or endpoint.get('params', [])
        for param in params:
            operation['parameters'].append({
                "name": param.get('name', ''),
                "in": param.get('in', 'query'),
                "required": param.get('required', False),
                "description": param.get('description', ''),
                "schema": {
                    "type": param.get('type', 'string')
                }
            })
        
        openapi['paths'][path][method] = operation


def scrape_rapidapi(rapidapi_url: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """抓取 RapidAPI 并生成 OpenAPI 规范"""
    scraper = RapidAPIScraper()
    return scraper.scrape_api(rapidapi_url, api_key)


