"""
RapidAPI Next.js 数据解析器 - 从 Next.js App Router 页面提取 API 数据
"""
import re
import json
from typing import Dict, Any, List, Optional
from .rapidapi_endpoint_fetcher import fetch_complete_endpoint_info


class RapidAPINextParser:
    """解析 RapidAPI 的 Next.js 页面数据"""
    
    def parse_html(self, html: str) -> Optional[Dict[str, Any]]:
        """
        从 HTML 中解析 API 数据
        
        RapidAPI 使用 Next.js 13+ App Router，数据通过 self.__next_f.push() 加载
        """
        print("🔍 解析 Next.js 数据...")
        
        # 提取所有 self.__next_f.push() 调用
        push_pattern = r'self\.__next_f\.push\(\[.*?\]\)'
        matches = re.findall(push_pattern, html, re.DOTALL)
        
        print(f"   找到 {len(matches)} 个 __next_f.push 调用")
        
        # 查找包含 "endpoints" 关键词的数据块
        # 注意：Next.js 中是转义的 \"endpoints\"
        endpoints_blocks = []
        for i, match in enumerate(matches):
            if 'endpoints' in match and 'route' in match:
                endpoints_blocks.append(match)
                print(f"      块 #{i+1} 包含端点数据 (长度: {len(match)} 字符)")
        
        print(f"   其中 {len(endpoints_blocks)} 个可能包含端点数据")
        
        # 尝试从这些块中提取端点信息
        for block in endpoints_blocks:
            try:
                api_data = self._extract_from_block(block)
                if api_data and api_data.get('endpoints'):
                    print(f"   ✓ 成功提取 API 数据")
                    return api_data
            except Exception as e:
                print(f"   解析块时出错: {e}")
                continue
        
        print(f"   ✗ 未找到有效的 API 数据")
        return None
    
    def _extract_from_block(self, block: str) -> Optional[Dict[str, Any]]:
        """从单个 push 块中提取 API 数据"""
        
        # Next.js 数据格式: self.__next_f.push([1, "...json_string..."])
        # 提取字符串部分 - 更宽松的模式
        match = re.search(r'push\(\[[\d]+,"(.*)"\]\)', block, re.DOTALL)
        if not match:
            # 尝试另一种模式
            match = re.search(r'push\(\[[\d]+,(.*)[\]\)]+$', block, re.DOTALL)
            if not match:
                return None
        
        json_str = match.group(1)
        
        # 移除首尾引号（如果有）
        json_str = json_str.strip()
        if json_str.startswith('"') and json_str.endswith('"'):
            json_str = json_str[1:-1]
        
        print(f"      提取的字符串长度: {len(json_str)}")
        
        # 解码转义字符
        try:
            # 处理 JSON 转义（Next.js 使用反斜杠转义）
            # 不要全局替换，而是智能解析
            json_str_unescaped = json_str.replace('\\"', '"').replace('\\\\', '\\')
            
            # 直接尝试逐个提取端点（更可靠）
            endpoints = self._extract_endpoints_individually(json_str_unescaped)
            
            print(f"      提取到 {len(endpoints)} 个端点")
            
            if not endpoints:
                return None
            
            # 同时查找 API 基本信息
            api_info = self._extract_api_info(json_str)
            
            return {
                'api_info': api_info,
                'endpoints': endpoints
            }
            
        except Exception as e:
            print(f"      解析块时出错: {e}")
            return None
    
    def _extract_endpoints_individually(self, json_str: str) -> List[Dict[str, Any]]:
        """逐个提取端点对象，包括参数信息"""
        endpoints = []
        
        # 查找完整的端点对象，包括 id
        # 注意：id 可能是 "endpoint_" 或 "apiendpoint_" 开头
        # 格式: {"id":"endpoint_xxx","route":"/path","method":"GET","name":"...","description":"..."}
        endpoint_obj_pattern = r'\{"id":"((?:api)?endpoint_[a-f0-9\-]+)"[^{]*?"route":"([^"]+)"[^{]*?"method":"([^"]+)"[^{]*?"name":"([^"]+)"[^{]*?"description":"([^"]*?)"'
        
        matches = re.findall(endpoint_obj_pattern, json_str, re.DOTALL)
        
        if matches:
            print(f"         找到 {len(matches)} 个端点对象")
            for endpoint_id, route, method, name, description in matches:
                # 清理描述
                description = description.replace('\\n', ' ').replace('\\t', ' ').replace('\\"', '"').strip()
                # 截断过长的描述
                if len(description) > 500:
                    description = description[:497] + "..."
                
                endpoint = {
                    'id': endpoint_id,
                    'route': route,
                    'method': method,
                    'name': name,
                    'description': description,
                    'parameters': []  # 稍后填充
                }
                
                # 基于 ID 去重，而不是路径+方法
                # 这样同路径不同 body 的端点会被保留为不同的 tool
                if not any(e['id'] == endpoint_id for e in endpoints):
                    endpoints.append(endpoint)
                    print(f"            • {method} {route}: {name}")
        
        # 尝试为每个端点查找参数（从同一个数据块中）
        if endpoints:
            print(f"         🔍 在数据块中查找参数...")
            for endpoint in endpoints:
                params = self._extract_endpoint_parameters(json_str, endpoint['id'])
                if params:
                    endpoint['parameters'] = params
                    print(f"            • {endpoint['route']}: {len(params)} 个参数")
        
        return endpoints
    
    def _extract_endpoint_parameters(self, json_str: str, endpoint_id: str) -> List[Dict[str, Any]]:
        """为特定端点提取参数"""
        parameters = []
        
        # 在 JSON 字符串中查找与此端点相关的参数定义
        # RapidAPI 可能在端点对象附近或参数部分存储参数信息
        
        # 尝试查找参数模式（通用）
        # 参数通常有: name, type, required, description
        param_patterns = [
            # 模式1: 标准 OpenAPI 风格
            r'\{"name":"([^"]+)"[^}]*?"in":"([^"]+)"[^}]*?"required":(true|false)[^}]*?"description":"([^"]*?)"[^}]*?"schema":\{"type":"([^"]+)"',
            # 模式2: 简化格式
            r'\{"name":"([^"]+)"[^}]*?"type":"([^"]+)"[^}]*?"required":(true|false)[^}]*?"description":"([^"]*?)"',
        ]
        
        # 由于端点ID在 HTML 中，我们无法直接关联参数
        # 这里返回空，需要从端点详情页面获取
        # 或者我们可以提供一个占位符
        
        return parameters
    
    def _extract_api_info(self, json_str: str) -> Dict[str, Any]:
        """从 JSON 字符串中提取 API 基本信息"""
        api_info = {}
        
        # 查找 API 名称
        name_match = re.search(r'"name"\s*:\s*"([^"]+)"', json_str)
        if name_match:
            api_info['name'] = name_match.group(1)
        
        # 查找描述
        desc_match = re.search(r'"description"\s*:\s*"([^"]+)"', json_str)
        if desc_match:
            api_info['description'] = desc_match.group(1)
        
        # 查找 baseUrl (publicdns)
        dns_match = re.search(r'"address"\s*:\s*"([^"]+\.p\.rapidapi\.com)"', json_str)
        if dns_match:
            api_info['baseUrl'] = f"https://{dns_match.group(1)}"
        
        return api_info
    
    def _find_api_data(self, data_blocks: List[Any]) -> Optional[Dict[str, Any]]:
        """从数据块中查找 API 信息"""
        
        api_info = None
        endpoints = None
        
        # 查找包含 endpoints 的数据块
        for block in data_blocks:
            if not isinstance(block, dict):
                continue
            
            # 查找 endpoints 数组
            if 'endpoints' in block and isinstance(block['endpoints'], list):
                if len(block['endpoints']) > 0:
                    print(f"      ✓ 找到 {len(block['endpoints'])} 个端点")
                    endpoints = block['endpoints']
                    
                    # 同时提取 API 基本信息
                    if 'name' in block or 'title' in block:
                        api_info = {
                            'name': block.get('name') or block.get('title'),
                            'description': block.get('description') or block.get('longDescription'),
                            'version': block.get('version', {}).get('name', '1.0.0') if isinstance(block.get('version'), dict) else '1.0.0',
                        }
                    
                    # 提取 baseUrl
                    if 'version' in block and isinstance(block['version'], dict):
                        if 'publicdns' in block['version'] and block['version']['publicdns']:
                            dns = block['version']['publicdns'][0]
                            if 'address' in dns:
                                if api_info is None:
                                    api_info = {}
                                api_info['baseUrl'] = f"https://{dns['address']}"
                    
                    break
            
            # 查找嵌套的 API 数据
            if 'data' in block and isinstance(block['data'], dict):
                nested_result = self._find_api_data([block['data']])
                if nested_result:
                    return nested_result
        
        if endpoints:
            return {
                'api_info': api_info or {},
                'endpoints': endpoints
            }
        
        return None
    
    def build_openapi_from_data(self, parsed_data: Dict[str, Any], api_info_from_url: Dict[str, str]) -> Dict[str, Any]:
        """从解析的数据构建 OpenAPI 规范"""
        
        api_info = parsed_data.get('api_info', {})
        endpoints = parsed_data.get('endpoints', [])
        
        print(f"📝 构建 OpenAPI 规范...")
        print(f"   API: {api_info.get('name', 'Unknown')}")
        print(f"   端点数量: {len(endpoints)}")
        
        # 构建基础 OpenAPI 结构
        openapi = {
            "openapi": "3.0.0",
            "info": {
                "title": api_info.get('name') or api_info_from_url['api_name'].replace('-', ' ').title(),
                "description": api_info.get('description') or f"RapidAPI: {api_info_from_url['provider']}/{api_info_from_url['api_name']}",
                "version": str(api_info.get('version', '1.0.0'))
            },
            "servers": [
                {
                    "url": api_info.get('baseUrl') or f"https://{api_info_from_url['api_name']}.p.rapidapi.com"
                }
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
        
        # 添加每个端点
        for endpoint_data in endpoints:
            self._add_endpoint_to_openapi(openapi, endpoint_data)
        
        print(f"✅ OpenAPI 规范构建完成")
        print(f"   包含 {len(openapi['paths'])} 个路径")
        
        return openapi
    
    def _add_endpoint_to_openapi(self, openapi: Dict[str, Any], endpoint_data: Dict[str, Any]):
        """添加端点到 OpenAPI，包括参数和响应"""
        
        # 从 RapidAPI 数据提取
        route = endpoint_data.get('route', '/')
        method = endpoint_data.get('method', 'GET').lower()
        name = endpoint_data.get('name', f"{method}_{route}")
        description = endpoint_data.get('description', '')
        endpoint_id = endpoint_data.get('id', '')
        parameters = endpoint_data.get('parameters', [])
        responses = endpoint_data.get('responses', {})
        
        print(f"      添加: {method.upper()} {route} - {name}")
        
        # 打印参数信息（兼容新旧格式）
        if parameters:
            if isinstance(parameters, dict):
                # 新格式：{'query': [...], 'header': [...], 'body': {...}}
                total_params = len(parameters.get('query', [])) + len(parameters.get('header', []))
                print(f"         ├─ 参数: {total_params} 个")
                
                for p in parameters.get('query', []):
                    if isinstance(p, dict):
                        req_mark = "✓" if p.get('required') else "○"
                        enum_mark = f" (枚举)" if p.get('schema', {}).get('enum') else ""
                        print(f"         │  {req_mark} {p['name']} (query): {p.get('schema', {}).get('type', 'string')}{enum_mark}")
                
                for p in parameters.get('header', []):
                    if isinstance(p, dict):
                        req_mark = "✓" if p.get('required') else "○"
                        print(f"         │  {req_mark} {p['name']} (header): {p.get('schema', {}).get('type', 'string')}")
                
                if parameters.get('body'):
                    print(f"         │  ✓ Body: JSON")
            
            elif isinstance(parameters, list):
                # 旧格式：直接是参数列表
                print(f"         ├─ 参数: {len(parameters)} 个")
                for p in parameters:
                    if isinstance(p, dict):
                        req_mark = "✓" if p.get('required') else "○"
                        enum_mark = f" (枚举)" if p.get('schema', {}).get('enum') else ""
                        print(f"         │  {req_mark} {p['name']}: {p.get('schema', {}).get('type', 'string')}{enum_mark}")
        
        if responses:
            print(f"         └─ 响应: 已定义")
        
        # 确保路径存在
        if route not in openapi['paths']:
            openapi['paths'][route] = {}
        
        # 生成唯一的 operationId
        # 如果同路径已存在端点，添加后缀以区分
        base_operation_id = name.lower().replace(' ', '_').replace('-', '_')
        operation_id = base_operation_id
        
        # 检查是否已存在同名的 operationId
        suffix = 1
        while any(
            op.get('operationId') == operation_id 
            for path_ops in openapi['paths'].values() 
            for op in path_ops.values() if isinstance(op, dict)
        ):
            operation_id = f"{base_operation_id}_{suffix}"
            suffix += 1
        
        # 构建操作对象
        operation = {
            "summary": name,
            "description": description,
            "operationId": operation_id,
            "parameters": [],
            "responses": responses if responses else {
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
        
        # 处理所有类型的参数
        if isinstance(parameters, dict):
            # 新格式：{'query': [...], 'header': [...], 'body': {...}}
            # Query 参数
            for param in parameters.get('query', []):
                operation['parameters'].append(self._convert_param_to_openapi(param, 'query'))
            
            # Header 参数
            for param in parameters.get('header', []):
                operation['parameters'].append(self._convert_param_to_openapi(param, 'header'))
            
            # Body 参数
            if parameters.get('body'):
                operation['requestBody'] = {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "example": parameters['body']
                            }
                        }
                    }
                }
                print(f"         ├─ Body: 已定义")
        
        elif isinstance(parameters, list):
            # 旧格式：直接是参数列表
            for param in parameters:
                operation['parameters'].append(self._convert_param_to_openapi(param))
        
        # 如果同路径同方法已存在，使用不同的方法名（扩展）
        if method in openapi['paths'][route]:
            # 同路径同方法，使用 x-{method} 作为替代
            print(f"         ⚠️  {method} {route} 已存在，使用扩展方法名")
            method_key = f"x-{method}-{endpoint_id.split('_')[-1][:8]}" if endpoint_id else f"x-{method}-alt"
            openapi['paths'][route][method_key] = operation
        else:
            openapi['paths'][route][method] = operation
    
    def _convert_param_to_openapi(self, param: Dict[str, Any], param_in: str = None) -> Dict[str, Any]:
        """将参数转换为 OpenAPI 格式"""
        # 如果参数已经是标准格式，直接使用
        if 'schema' in param and param_in is None:
            return param
        
        # 否则转换格式
        openapi_param = {
            "name": param.get('name', ''),
            "in": param_in or param.get('in', 'query'),
            "required": param.get('required', False),
            "description": param.get('description', ''),
            "schema": param.get('schema', {
                "type": param.get('type', 'string')
            })
        }
        
        # 添加额外属性
        if 'default' in param and 'default' not in openapi_param['schema']:
            openapi_param['schema']['default'] = param['default']
        
        if 'enum' in param and 'enum' not in openapi_param['schema']:
            openapi_param['schema']['enum'] = param['enum']
        
        if 'example' in param and 'example' not in openapi_param['schema']:
            openapi_param['schema']['example'] = param['example']
        
        return openapi_param


def parse_rapidapi_html(
    html: str,
    api_info: Dict[str, str],
    fetch_params: bool = True,
    verify_ssl: bool = True
) -> Optional[Dict[str, Any]]:
    """
    从 RapidAPI HTML 解析并构建 OpenAPI 规范
    
    Args:
        html: HTML 内容
        api_info: 从 URL 提取的 API 信息
        fetch_params: 是否深度爬取参数和响应信息（需要额外请求）
        verify_ssl: 是否验证 SSL
    
    Returns:
        OpenAPI 规范字典
    """
    parser = RapidAPINextParser()
    
    # 解析 HTML
    parsed_data = parser.parse_html(html)
    
    if not parsed_data:
        return None
    
    # 如果需要深度爬取参数和响应
    if fetch_params and parsed_data.get('endpoints'):
        print("🚀 深度爬取端点详情（参数和响应）...")
        base_url = api_info['url'].rsplit('/playground', 1)[0] if '/playground' in api_info['url'] else api_info['url']
        
        # 尝试使用 Selenium（如果可用）
        try:
            from .rapidapi_selenium_scraper import scrape_with_selenium
            
            print("   🌐 使用 Selenium 浏览器自动化...")
            parsed_data['endpoints'] = scrape_with_selenium(
                base_url,
                parsed_data['endpoints'],
                headless=True
            )
            
        except ImportError:
            print("   ⚠️  Selenium 未安装，使用基础方法")
            print("   💡 安装 Selenium 以获取完整参数: pip install selenium")
            print("   📝 当前会生成基础结构，请使用工具补充参数：")
            print("      python add_rapidapi_params.py rapidapi_<name>_auto.json")
    
    # 构建 OpenAPI
    openapi = parser.build_openapi_from_data(parsed_data, api_info)
    
    return openapi

