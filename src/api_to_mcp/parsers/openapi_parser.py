"""
OpenAPI/Swagger 解析器
"""
from typing import Dict, Any, List, Optional
import json
import yaml
from pathlib import Path

from ..models import APISpec, APIEndpoint, APIParameter


class OpenAPIParser:
    """OpenAPI/Swagger 规范解析器"""
    
    def parse_file(self, file_path: str) -> APISpec:
        """解析 OpenAPI/Swagger 文件"""
        file_path = Path(file_path)
        
        if file_path.suffix in ['.json']:
            with open(file_path, 'r', encoding='utf-8') as f:
                spec_data = json.load(f)
        elif file_path.suffix in ['.yaml', '.yml']:
            with open(file_path, 'r', encoding='utf-8') as f:
                spec_data = yaml.safe_load(f)
        else:
            raise ValueError(f"不支持的文件格式: {file_path.suffix}")
        
        return self.parse_dict(spec_data)
    
    def parse_dict(self, spec_data: Dict[str, Any]) -> APISpec:
        """解析 OpenAPI/Swagger 字典数据"""
        # 检测版本
        if 'swagger' in spec_data:
            return self._parse_swagger_2(spec_data)
        elif 'openapi' in spec_data:
            return self._parse_openapi_3(spec_data)
        else:
            raise ValueError("无法识别的 API 规范格式")
    
    def _parse_swagger_2(self, spec_data: Dict[str, Any]) -> APISpec:
        """解析 Swagger 2.0 规范"""
        info = spec_data.get('info', {})
        
        # 构建 base_url
        base_url = None
        if 'host' in spec_data:
            scheme = spec_data.get('schemes', ['https'])[0]
            base_path = spec_data.get('basePath', '')
            base_url = f"{scheme}://{spec_data['host']}{base_path}"
        
        # 解析端点
        endpoints = []
        paths = spec_data.get('paths', {})
        for path, path_item in paths.items():
            for method, operation in path_item.items():
                if method in ['get', 'post', 'put', 'delete', 'patch', 'options', 'head']:
                    endpoint = self._parse_swagger_operation(path, method, operation)
                    endpoints.append(endpoint)
        
        # 解析认证
        auth_type = None
        auth_config = {}
        if 'securityDefinitions' in spec_data:
            security_defs = spec_data['securityDefinitions']
            if security_defs:
                first_auth = list(security_defs.values())[0]
                auth_type = first_auth.get('type')
                auth_config = first_auth
        
        return APISpec(
            title=info.get('title', 'Untitled API'),
            version=info.get('version', '1.0.0'),
            description=info.get('description'),
            base_url=base_url,
            endpoints=endpoints,
            source_platform='swagger',
            auth_type=auth_type,
            auth_config=auth_config,
        )
    
    def _parse_swagger_operation(
        self, path: str, method: str, operation: Dict[str, Any]
    ) -> APIEndpoint:
        """解析 Swagger 操作"""
        parameters = []
        for param in operation.get('parameters', []):
            parameters.append(APIParameter(
                name=param.get('name', ''),
                type=param.get('type', 'string'),
                description=param.get('description'),
                required=param.get('required', False),
                default=param.get('default'),
                enum=param.get('enum'),
            ))
        
        return APIEndpoint(
            path=path,
            method=method.upper(),
            summary=operation.get('summary'),
            description=operation.get('description'),
            operation_id=operation.get('operationId'),
            parameters=parameters,
            responses=operation.get('responses', {}),
            tags=operation.get('tags', []),
        )
    
    def _parse_openapi_3(self, spec_data: Dict[str, Any]) -> APISpec:
        """解析 OpenAPI 3.0+ 规范"""
        info = spec_data.get('info', {})
        
        # 解析服务器
        servers = spec_data.get('servers', [])
        base_url = servers[0]['url'] if servers else None
        
        # 解析端点
        endpoints = []
        paths = spec_data.get('paths', {})
        for path, path_item in paths.items():
            for method, operation in path_item.items():
                if method in ['get', 'post', 'put', 'delete', 'patch', 'options', 'head']:
                    endpoint = self._parse_openapi_operation(
                        path, method, operation, spec_data
                    )
                    endpoints.append(endpoint)
        
        # 解析认证
        auth_type = None
        auth_config = {}
        components = spec_data.get('components', {})
        security_schemes = components.get('securitySchemes', {})
        if security_schemes:
            first_scheme = list(security_schemes.values())[0]
            auth_type = first_scheme.get('type')
            auth_config = first_scheme
        
        return APISpec(
            title=info.get('title', 'Untitled API'),
            version=info.get('version', '1.0.0'),
            description=info.get('description'),
            base_url=base_url,
            servers=servers,
            endpoints=endpoints,
            source_platform='openapi',
            auth_type=auth_type,
            auth_config=auth_config,
        )
    
    def _parse_openapi_operation(
        self, path: str, method: str, operation: Dict[str, Any], spec_data: Dict[str, Any]
    ) -> APIEndpoint:
        """解析 OpenAPI 操作"""
        parameters = []
        
        # 解析路径/查询/头部参数
        for param in operation.get('parameters', []):
            param_schema = param.get('schema', {})
            parameters.append(APIParameter(
                name=param.get('name', ''),
                type=param_schema.get('type', 'string'),
                description=param.get('description'),
                required=param.get('required', False),
                default=param_schema.get('default'),
                enum=param_schema.get('enum'),
            ))
        
        # 解析请求体
        request_body = operation.get('requestBody')
        
        return APIEndpoint(
            path=path,
            method=method.upper(),
            summary=operation.get('summary'),
            description=operation.get('description'),
            operation_id=operation.get('operationId'),
            parameters=parameters,
            request_body=request_body,
            responses=operation.get('responses', {}),
            tags=operation.get('tags', []),
        )


