"""
配置管理模块
"""
from dataclasses import dataclass
from typing import Optional
import os


@dataclass
class AzureOpenAIConfig:
    """Azure OpenAI 配置
    
    ⚠️ 重要：请通过环境变量设置敏感信息，不要在代码中硬编码！
    
    环境变量：
    - AZURE_OPENAI_ENDPOINT: Azure OpenAI 端点
    - AZURE_OPENAI_API_KEY: Azure OpenAI API 密钥
    - AZURE_OPENAI_DEPLOYMENT: 部署名称（默认：gpt-4o）
    - AZURE_OPENAI_API_VERSION: API 版本（默认：2024-02-15-preview）
    """
    endpoint: Optional[str] = None
    api_key: Optional[str] = None
    deployment_name: str = "gpt-4o"
    api_version: str = "2024-02-15-preview"
    
    @classmethod
    def from_env(cls) -> "AzureOpenAIConfig":
        """从环境变量加载配置"""
        return cls(
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT", cls.deployment_name),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", cls.api_version),
        )


@dataclass
class RapidAPIConfig:
    """RapidAPI 配置"""
    api_key: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> "RapidAPIConfig":
        """从环境变量加载配置"""
        return cls(
            api_key=os.getenv("RAPIDAPI_KEY")
        )


@dataclass
class MCPGeneratorConfig:
    """MCP 生成器配置"""
    output_dir: str = "generated_mcps"
    template_dir: str = "templates"
    include_version: bool = True
    default_version: str = "1.0.0"
    # 协议类型：stdio, sse, streamable-http
    default_transport: str = "stdio"

