"""
数据模型定义
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class APIParameter(BaseModel):
    """API 参数"""
    name: str
    type: str
    description: Optional[str] = None
    required: bool = False
    default: Optional[Any] = None
    enum: Optional[List[str]] = None


class APIEndpoint(BaseModel):
    """API 端点"""
    path: str
    method: str
    summary: Optional[str] = None
    description: Optional[str] = None
    operation_id: Optional[str] = None
    parameters: List[APIParameter] = Field(default_factory=list)
    request_body: Optional[Dict[str, Any]] = None
    responses: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    
    # 优化后的描述
    enhanced_description: Optional[str] = None
    enhanced_summary: Optional[str] = None


class APISpec(BaseModel):
    """API 规范"""
    title: str
    version: str
    description: Optional[str] = None
    base_url: Optional[str] = None
    servers: List[Dict[str, Any]] = Field(default_factory=list)
    endpoints: List[APIEndpoint] = Field(default_factory=list)
    
    # 来源信息
    source_platform: str = "unknown"  # rapidapi, swagger, openapi
    source_url: Optional[str] = None
    
    # 认证信息
    auth_type: Optional[str] = None  # apikey, bearer, oauth2, etc.
    auth_config: Dict[str, Any] = Field(default_factory=dict)


class MCPTool(BaseModel):
    """MCP 工具定义"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    
    # 关联的 API 端点
    endpoint: APIEndpoint


class MCPServer(BaseModel):
    """MCP 服务器定义"""
    name: str
    version: str
    description: str
    tools: List[MCPTool] = Field(default_factory=list)
    
    # PyPI 包名（带前缀）
    package_name: Optional[str] = None
    
    # API 规范引用
    api_spec: APISpec
    
    # 生成的代码路径
    output_path: Optional[str] = None

