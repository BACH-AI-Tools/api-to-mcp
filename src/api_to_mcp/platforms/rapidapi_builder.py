"""
RapidAPI OpenAPI 构建器 - 手动构建 OpenAPI 规范
"""
from typing import Dict, Any, List, Optional
import json


class RapidAPIOpenAPIBuilder:
    """RapidAPI OpenAPI 规范构建器"""
    
    def __init__(self):
        self.openapi = {
            "openapi": "3.0.0",
            "info": {
                "title": "",
                "description": "",
                "version": "1.0.0"
            },
            "servers": [],
            "paths": {},
            "components": {
                "securitySchemes": {
                    "RapidAPIAuth": {
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
                {"RapidAPIAuth": []},
                {"RapidAPIHost": []}
            ]
        }
    
    def set_info(self, title: str, description: str = "", version: str = "1.0.0"):
        """设置 API 基本信息"""
        self.openapi["info"]["title"] = title
        self.openapi["info"]["description"] = description
        self.openapi["info"]["version"] = version
    
    def set_server(self, base_url: str):
        """设置服务器 URL"""
        self.openapi["servers"] = [{"url": base_url}]
    
    def add_endpoint_from_rapidapi(
        self,
        name: str,
        method: str,
        path: str,
        description: str = "",
        parameters: Optional[List[Dict[str, Any]]] = None
    ):
        """
        从 RapidAPI 端点信息添加端点
        
        Args:
            name: 端点名称（如 "Job Search"）
            method: HTTP 方法（GET, POST 等）
            path: 路径（如 "/search"）
            description: 描述
            parameters: 参数列表
        """
        if path not in self.openapi["paths"]:
            self.openapi["paths"][path] = {}
        
        operation = {
            "summary": name,
            "description": description,
            "operationId": name.lower().replace(' ', '_'),
            "parameters": parameters or [],
            "responses": {
                "200": {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object"
                            }
                        }
                    }
                }
            }
        }
        
        self.openapi["paths"][path][method.lower()] = operation
    
    def build_from_rapidapi_page_data(self, rapidapi_url: str, api_host: str) -> Dict[str, Any]:
        """
        根据 RapidAPI 页面数据快速构建
        
        Args:
            rapidapi_url: RapidAPI 页面 URL
            api_host: API Host (如 jsearch.p.rapidapi.com)
        """
        # 从 URL 提取信息
        import re
        pattern = r'rapidapi\.com/([^/]+)/api/([^/?]+)'
        match = re.search(pattern, rapidapi_url)
        
        if match:
            provider = match.group(1)
            api_name = match.group(2)
            
            self.set_info(
                title=api_name.replace('-', ' ').title(),
                description=f"API from RapidAPI: {provider}/{api_name}",
                version="1.0.0"
            )
            self.set_server(f"https://{api_host}")
        
        return self.openapi
    
    def get_openapi(self) -> Dict[str, Any]:
        """获取构建的 OpenAPI 规范"""
        return self.openapi
    
    def save_to_file(self, filename: str):
        """保存到文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.openapi, f, indent=2, ensure_ascii=False)


def create_rapidapi_template(api_name: str, api_host: str, endpoints: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    创建 RapidAPI OpenAPI 模板
    
    Args:
        api_name: API 名称
        api_host: API Host (如 jsearch.p.rapidapi.com)
        endpoints: 端点列表，格式:
            [
                {
                    "name": "Job Search",
                    "method": "GET",
                    "path": "/search",
                    "description": "Search for jobs",
                    "parameters": [
                        {"name": "query", "type": "string", "required": True, "description": "Search query"}
                    ]
                }
            ]
    """
    builder = RapidAPIOpenAPIBuilder()
    builder.set_info(
        title=api_name.replace('-', ' ').title(),
        description=f"RapidAPI: {api_name}",
        version="1.0.0"
    )
    builder.set_server(f"https://{api_host}")
    
    for endpoint in endpoints:
        params = []
        for p in endpoint.get('parameters', []):
            params.append({
                "name": p['name'],
                "in": "query",
                "required": p.get('required', False),
                "description": p.get('description', ''),
                "schema": {
                    "type": p.get('type', 'string')
                }
            })
        
        builder.add_endpoint_from_rapidapi(
            name=endpoint['name'],
            method=endpoint['method'],
            path=endpoint['path'],
            description=endpoint.get('description', ''),
            parameters=params
        )
    
    return builder.get_openapi()


