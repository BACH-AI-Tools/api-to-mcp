"""
RapidAPI 平台集成
"""
from typing import Dict, Any, Optional, List
import requests
import urllib3
from ..models import APISpec
from ..parsers import OpenAPIParser


class RapidAPIClient:
    """RapidAPI 客户端"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://rapidapi.com/api"
        self.parser = OpenAPIParser()
    
    def fetch_api_spec(self, api_name: str) -> APISpec:
        """
        从 RapidAPI 获取 API 规范
        
        Args:
            api_name: API 名称，例如 "weatherapi/weatherapi-com"
        """
        # RapidAPI 通常提供 OpenAPI 规范的 URL
        # 这里需要根据实际的 RapidAPI API 来实现
        
        # 方法1: 如果有直接的 OpenAPI 规范 URL
        spec_url = self._get_openapi_spec_url(api_name)
        if spec_url:
            response = requests.get(spec_url)
            response.raise_for_status()
            spec_data = response.json()
            
            api_spec = self.parser.parse_dict(spec_data)
            api_spec.source_platform = "rapidapi"
            api_spec.source_url = spec_url
            
            return api_spec
        
        raise NotImplementedError("需要 RapidAPI API Key 和具体的 API 获取实现")
    
    def _get_openapi_spec_url(self, api_name: str) -> Optional[str]:
        """
        获取 API 的 OpenAPI 规范 URL
        
        注意: 这个方法需要根据 RapidAPI 的实际 API 来实现
        通常每个 API 都有自己的 OpenAPI 规范链接
        """
        # 示例: 某些 RapidAPI 的 API 会提供类似的 URL
        # https://rapidapi.com/api/{provider}/{api-name}/spec
        return None
    
    def search_apis(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        搜索 RapidAPI 上的 API
        
        Args:
            query: 搜索关键词
            limit: 返回结果数量
        """
        # 这需要 RapidAPI 的搜索 API
        # 目前作为占位符
        raise NotImplementedError("需要 RapidAPI 搜索 API 实现")
    
    def get_api_info(self, api_name: str) -> Dict[str, Any]:
        """
        获取 API 的基本信息
        
        Args:
            api_name: API 名称
        """
        # 这需要 RapidAPI 的 API 详情接口
        raise NotImplementedError("需要 RapidAPI API 详情接口实现")


class RapidAPISpecFetcher:
    """
    RapidAPI 规范获取器（从文件或 URL）
    
    由于 RapidAPI 的 API 访问可能需要特定的凭据和权限，
    这个类提供了从已导出的 OpenAPI 文件中读取的功能
    """
    
    def __init__(self):
        self.parser = OpenAPIParser()
    
    def fetch_from_url(self, spec_url: str, api_key: Optional[str] = None, verify_ssl: bool = True) -> APISpec:
        """
        从 URL 获取 OpenAPI 规范
        
        Args:
            spec_url: OpenAPI 规范的 URL
            api_key: RapidAPI Key（如果需要认证）
            verify_ssl: 是否验证 SSL 证书（默认 True）
        """
        headers = {}
        if api_key:
            headers['X-RapidAPI-Key'] = api_key
        
        # 如果禁用 SSL 验证，抑制警告信息
        if not verify_ssl:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # 添加 verify 参数来控制 SSL 验证
        response = requests.get(spec_url, headers=headers, verify=verify_ssl)
        response.raise_for_status()
        
        spec_data = response.json()
        api_spec = self.parser.parse_dict(spec_data)
        api_spec.source_platform = "rapidapi"
        api_spec.source_url = spec_url
        
        # 如果规范中包含 RapidAPI 特定的认证配置
        if api_key:
            api_spec.auth_type = "apikey"
            api_spec.auth_config = {
                "type": "apiKey",
                "in": "header",
                "name": "X-RapidAPI-Key"
            }
        
        return api_spec
    
    def fetch_from_file(self, file_path: str) -> APISpec:
        """
        从本地文件获取 OpenAPI 规范
        
        Args:
            file_path: OpenAPI 规范文件路径
        """
        api_spec = self.parser.parse_file(file_path)
        api_spec.source_platform = "rapidapi"
        
        return api_spec

