"""
RapidAPI 深度爬虫 - 访问每个端点页面提取完整参数和响应信息
"""
import requests
import re
import json
import time
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin


class RapidAPIDeepScraper:
    """深度爬取 RapidAPI 端点详情"""
    
    def __init__(self, verify_ssl: bool = True):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.verify_ssl = verify_ssl
    
    def scrape_endpoint_details(self, base_url: str, endpoint_id: str) -> Dict[str, Any]:
        """
        深度爬取单个端点的完整信息
        
        Args:
            base_url: API 基础 URL (如 https://rapidapi.com/provider/api/api-name)
            endpoint_id: 端点 ID
        
        Returns:
            包含 parameters 和 responses 的字典
        """
        endpoint_url = f"{base_url}/playground/{endpoint_id}"
        
        print(f"      🔍 深度爬取: {endpoint_url}")
        
        try:
            response = self.session.get(endpoint_url, verify=self.verify_ssl, timeout=15)
            response.raise_for_status()
            html = response.text
            
            # 提取参数和响应
            params = self._extract_params_from_page(html)
            responses = self._extract_responses_from_page(html)
            
            result = {}
            if params:
                result['parameters'] = params
                print(f"         ✓ 提取 {len(params)} 个参数")
            
            if responses:
                result['responses'] = responses
                print(f"         ✓ 提取响应结构")
            
            return result
            
        except Exception as e:
            print(f"         ✗ 爬取失败: {e}")
            return {}
    
    def _extract_params_from_page(self, html: str) -> List[Dict[str, Any]]:
        """从页面提取参数 - 查找 Params 标签的数据"""
        parameters = []
        
        # 在 Next.js 数据中查找参数
        # 方法1: 查找 endpointData 或 playground 相关数据
        push_pattern = r'self\.__next_f\.push\(\[[\d]+,"([^"]*)"\]\)'
        matches = re.findall(push_pattern, html, re.DOTALL)
        
        for match in matches:
            # 解码
            decoded = match.replace('\\"', '"').replace('\\\\', '\\')
            
            # 查找参数定义模式
            # RapidAPI 的参数格式可能包含：name, type, required, description, enum, default
            if '"parameters"' in decoded or '"queryParams"' in decoded:
                params = self._parse_params_from_json(decoded)
                if params:
                    parameters.extend(params)
        
        # 去重
        seen = set()
        unique = []
        for p in parameters:
            key = p['name']
            if key not in seen:
                seen.add(key)
                unique.append(p)
        
        return unique
    
    def _parse_params_from_json(self, json_str: str) -> List[Dict[str, Any]]:
        """从 JSON 字符串解析参数"""
        parameters = []
        
        # 模式1: 查找完整的参数对象
        # {"name":"param_name","type":"string","required":true,"description":"..."}
        param_patterns = [
            # 完整格式（带 schema）
            r'\{"name":"([^"]+)"[^{]*?"in":"([^"]+)"[^{]*?"required":(true|false)[^{]*?"description":"([^"]*?)"[^{]*?"schema":\{"type":"([^"]+)"(?:[^}]*?"enum":\[([^\]]+)\])?(?:[^}]*?"default":"([^"]*?)")?',
            # 简化格式
            r'\{"name":"([^"]+)"[^{]*?"type":"([^"]+)"[^{]*?"required":(true|false)[^{]*?"description":"([^"]*?)"(?:[^}]*?"enum":\[([^\]]+)\])?(?:[^}]*?"default":"([^"]*?)")?',
        ]
        
        for pattern in param_patterns:
            matches = re.findall(pattern, json_str, re.DOTALL)
            if matches:
                for match in matches:
                    if len(match) >= 4:
                        param = self._build_param_from_match(match, pattern)
                        if param and param not in parameters:
                            parameters.append(param)
        
        return parameters
    
    def _build_param_from_match(self, match: tuple, pattern: str) -> Optional[Dict[str, Any]]:
        """从正则匹配构建参数对象"""
        try:
            if 'schema' in pattern:
                # 格式1: name, in, required, description, type, enum, default
                name, param_in, required, description, param_type = match[:5]
                enum_str = match[5] if len(match) > 5 else None
                default = match[6] if len(match) > 6 else None
            else:
                # 格式2: name, type, required, description, enum, default
                name, param_type, required, description = match[:4]
                param_in = 'query'
                enum_str = match[4] if len(match) > 4 else None
                default = match[5] if len(match) > 5 else None
            
            param = {
                'name': name,
                'in': param_in,
                'required': required == 'true',
                'description': description.strip(),
                'schema': {
                    'type': param_type
                }
            }
            
            # 添加枚举值
            if enum_str:
                # 解析枚举: "val1","val2","val3"
                enum_values = re.findall(r'"([^"]+)"', enum_str)
                if enum_values:
                    param['schema']['enum'] = enum_values
            
            # 添加默认值
            if default and default != 'null':
                param['schema']['default'] = default
            
            return param
            
        except Exception as e:
            return None
    
    def _extract_responses_from_page(self, html: str) -> Dict[str, Any]:
        """从页面提取响应结构 - 查找 Example Responses 和 Schema"""
        
        # 查找响应示例
        # RapidAPI 通常在 "Example Responses" 标签中显示响应
        
        # 方法1: 查找 response schema
        push_pattern = r'self\.__next_f\.push\(\[[\d]+,"([^"]*)"\]\)'
        matches = re.findall(push_pattern, html, re.DOTALL)
        
        for match in matches:
            decoded = match.replace('\\"', '"').replace('\\\\', '\\')
            
            # 查找响应相关的数据
            if '"response"' in decoded or '"responses"' in decoded or '"schema"' in decoded:
                # 尝试提取响应 schema
                schema = self._parse_response_schema(decoded)
                if schema:
                    return {
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {
                                    "schema": schema
                                }
                            }
                        }
                    }
        
        # 默认响应
        return {
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
    
    def _parse_response_schema(self, json_str: str) -> Optional[Dict[str, Any]]:
        """解析响应 schema"""
        
        # 尝试查找完整的 schema 对象
        # 通常包含 type, properties 等
        schema_pattern = r'\{"type":"([^"]+)"[^{]*?"properties":\{([^}]+)\}'
        match = re.search(schema_pattern, json_str)
        
        if match:
            schema_type = match.group(1)
            properties_str = match.group(2)
            
            # 构建基本 schema
            schema = {
                "type": schema_type,
                "properties": {}
            }
            
            # 解析 properties（简化处理）
            # 实际的 properties 可能很复杂，这里提供基本结构
            
            return schema
        
        # 返回基本类型
        return {"type": "object"}


def scrape_complete_api(
    base_url: str,
    endpoints: List[Dict[str, Any]],
    verify_ssl: bool = True,
    delay: float = 0.5
) -> List[Dict[str, Any]]:
    """
    深度爬取所有端点的完整信息
    
    Args:
        base_url: API 基础 URL
        endpoints: 端点列表（必须包含 'id' 字段）
        verify_ssl: 是否验证 SSL
        delay: 请求间隔（秒）
    
    Returns:
        更新后的端点列表（包含参数和响应）
    """
    scraper = RapidAPIDeepScraper(verify_ssl)
    
    enriched_endpoints = []
    
    for i, endpoint in enumerate(endpoints):
        print(f"   📍 端点 {i+1}/{len(endpoints)}: {endpoint.get('name', 'Unknown')}")
        
        if 'id' not in endpoint:
            print(f"      ⚠️  缺少端点 ID，跳过")
            enriched_endpoints.append(endpoint)
            continue
        
        # 爬取详情
        details = scraper.scrape_endpoint_details(base_url, endpoint['id'])
        
        # 合并信息
        enriched = endpoint.copy()
        if details.get('parameters'):
            enriched['parameters'] = details['parameters']
        if details.get('responses'):
            enriched['responses'] = details['responses']
        
        enriched_endpoints.append(enriched)
        
        # 延迟，避免请求过快
        if i < len(endpoints) - 1:
            time.sleep(delay)
    
    return enriched_endpoints


