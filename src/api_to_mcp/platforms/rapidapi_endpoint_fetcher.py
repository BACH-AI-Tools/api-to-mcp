"""
RapidAPI 端点详情获取器 - 访问端点详情页获取完整参数信息
"""
import requests
import re
import json
from typing import Dict, Any, List, Optional


class RapidAPIEndpointFetcher:
    """获取 RapidAPI 端点的详细信息"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch_endpoint_details(
        self,
        base_url: str,
        endpoint_id: str,
        verify_ssl: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        获取端点详情
        
        Args:
            base_url: RapidAPI 页面基础 URL（如 https://rapidapi.com/provider/api/api-name）
            endpoint_id: 端点 ID（如 endpoint_61dfc649-590b-47ec-82d8-07e6ae7d1d9a）
            verify_ssl: 是否验证 SSL
        
        Returns:
            包含参数信息的字典
        """
        # 构建端点详情页 URL
        endpoint_url = f"{base_url}/playground/{endpoint_id}"
        
        print(f"      📥 获取端点详情: {endpoint_url}")
        
        try:
            response = self.session.get(endpoint_url, verify=verify_ssl, timeout=10)
            response.raise_for_status()
            html = response.text
            
            # 从详情页提取参数
            parameters = self._parse_endpoint_page(html)
            
            if parameters:
                print(f"         ✓ 提取到 {len(parameters)} 个参数")
                return {'parameters': parameters}
            else:
                print(f"         ✗ 未找到参数")
                return None
                
        except Exception as e:
            print(f"         ✗ 获取失败: {e}")
            return None
    
    def _parse_endpoint_page(self, html: str) -> List[Dict[str, Any]]:
        """从端点详情页解析参数 - 通用方法"""
        parameters = []
        
        print(f"         🔍 分析端点详情页...")
        
        # 方法1: 从 Next.js 数据中查找 endpointData
        # RapidAPI 将端点详情存储在特定的数据块中
        push_pattern = r'self\.__next_f\.push\(\[.*?\]\)'
        matches = re.findall(push_pattern, html, re.DOTALL)
        
        print(f"            找到 {len(matches)} 个数据块")
        
        # 查找包含端点详情的块
        for i, match in enumerate(matches):
            # 寻找包含参数定义的块
            if 'endpointData' in match or 'queryParams' in match or ('required' in match and 'schema' in match):
                print(f"            块 #{i+1} 可能包含参数")
                params = self._extract_parameters_from_block(match)
                if params:
                    parameters.extend(params)
                    print(f"            ✓ 提取了 {len(params)} 个参数")
        
        # 方法2: 尝试从 React Query 缓存中提取
        # 查找 dehydratedState 或类似的缓存数据
        if not parameters:
            print(f"            尝试从 React Query 缓存提取...")
            params = self._extract_from_react_query(html)
            if params:
                parameters.extend(params)
        
        # 去重
        seen = set()
        unique_params = []
        for param in parameters:
            param_key = param['name']
            if param_key not in seen:
                seen.add(param_key)
                unique_params.append(param)
        
        return unique_params
    
    def _extract_parameters_from_block(self, block: str) -> List[Dict[str, Any]]:
        """从数据块中提取参数 - 改进的通用方法"""
        parameters = []
        
        # 提取字符串内容
        match = re.search(r'push\(\[[\d]+,"(.*)"\]\)', block, re.DOTALL)
        if not match:
            return parameters
        
        json_str = match.group(1)
        # 解码转义
        json_str_clean = json_str.replace('\\"', '"').replace('\\\\', '\\').replace('\\n', ' ')
        
        # 模式1: 标准 OpenAPI 格式的参数
        # {"name":"param_name","in":"query","required":true,"schema":{"type":"string"},"description":"..."}
        pattern1 = r'\{"name":"([^"]+)"[^{]*?"in":"([^"]+)"[^{]*?"required":(true|false)[^{]*?"schema":\{"type":"([^"]+)"[^}]*?\}[^{]*?"description":"([^"]*?)"'
        matches1 = re.findall(pattern1, json_str_clean, re.DOTALL)
        
        for name, param_in, required, param_type, description in matches1:
            if name and not any(p['name'] == name for p in parameters):
                parameters.append({
                    'name': name,
                    'in': param_in,
                    'required': required == 'true',
                    'type': param_type,
                    'description': description.strip()
                })
        
        # 模式2: 简化格式（没有 schema 嵌套）
        # {"name":"param_name","type":"string","required":true,"description":"..."}
        if not parameters:
            pattern2 = r'\{"name":"([^"]+)"[^{]*?"type":"([^"]+)"[^{]*?"required":(true|false)[^{]*?"description":"([^"]*?)"'
            matches2 = re.findall(pattern2, json_str_clean, re.DOTALL)
            
            for name, param_type, required, description in matches2:
                if name and not any(p['name'] == name for p in parameters):
                    parameters.append({
                        'name': name,
                        'in': 'query',  # 默认为 query
                        'required': required == 'true',
                        'type': param_type,
                        'description': description.strip()
                    })
        
        # 模式3: RapidAPI 特殊格式 - 从 endpointData 或 playground 数据中提取
        if not parameters:
            # 查找参数数组
            params_array_pattern = r'"(queryParams|headerParams|pathParams|bodyParams)"\s*:\s*\[([^\]]+)\]'
            array_matches = re.findall(params_array_pattern, json_str_clean)
            
            for param_type, params_content in array_matches:
                # 从数组内容中提取每个参数
                param_obj_pattern = r'\{"[^}]*?"name":"([^"]+)"[^}]*?\}'
                param_names = re.findall(param_obj_pattern, params_content)
                
                for name in param_names:
                    if name and not any(p['name'] == name for p in parameters):
                        # 提取该参数的详细信息
                        param_detail = self._extract_param_details(json_str_clean, name)
                        if param_detail:
                            parameters.append(param_detail)
        
        return parameters
    
    def _extract_param_details(self, json_str: str, param_name: str) -> Optional[Dict[str, Any]]:
        """提取单个参数的详细信息"""
        # 查找包含该参数名的完整对象
        param_obj_pattern = rf'\{{"[^}}]*?"name":"{re.escape(param_name)}"[^}}]*?\}}'
        match = re.search(param_obj_pattern, json_str)
        
        if not match:
            return None
        
        param_obj_str = match.group(0)
        
        # 提取字段
        result = {'name': param_name, 'in': 'query', 'required': False, 'type': 'string', 'description': ''}
        
        # 提取 type
        type_match = re.search(r'"type":"([^"]+)"', param_obj_str)
        if type_match:
            result['type'] = type_match.group(1)
        
        # 提取 required
        required_match = re.search(r'"required":(true|false)', param_obj_str)
        if required_match:
            result['required'] = required_match.group(1) == 'true'
        
        # 提取 description
        desc_match = re.search(r'"description":"([^"]*?)"', param_obj_str)
        if desc_match:
            result['description'] = desc_match.group(1)
        
        # 提取 in (位置)
        in_match = re.search(r'"in":"([^"]+)"', param_obj_str)
        if in_match:
            result['in'] = in_match.group(1)
        
        return result
    
    def _extract_from_react_query(self, html: str) -> List[Dict[str, Any]]:
        """从 React Query 缓存数据中提取参数"""
        parameters = []
        
        # 查找 dehydratedState 或 queries 数据
        # React Query 通常将数据缓存在这些结构中
        queries_pattern = r'"queries"\s*:\s*\[([^\]]+(?:\{[^\}]*\}[^\]]*)*)\]'
        match = re.search(queries_pattern, html, re.DOTALL)
        
        if match:
            queries_data = match.group(1)
            # 在 queries 数据中查找参数
            # ... 这里可以进一步解析
        
        return parameters


def fetch_complete_endpoint_info(
    api_url: str,
    endpoint_id: str,
    verify_ssl: bool = True
) -> Optional[Dict[str, Any]]:
    """获取端点的完整信息，包括参数"""
    fetcher = RapidAPIEndpointFetcher()
    return fetcher.fetch_endpoint_details(api_url, endpoint_id, verify_ssl)

