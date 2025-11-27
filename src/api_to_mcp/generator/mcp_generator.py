"""
MCP 服务器代码生成器
"""
from typing import Dict, Any, List, Optional
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template
import json

from ..models import APISpec, APIEndpoint, MCPServer, MCPTool


class MCPGenerator:
    """MCP 服务器生成器"""
    
    def __init__(self, output_dir: str = "generated_mcps", package_prefix: str = "bach", emcp_promotion: Optional[Dict[str, str]] = None, emcp_domain: str = "https://sit-emcp.kaleido.guru"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.package_prefix = package_prefix  # PyPI 包名前缀
        self.emcp_domain = emcp_domain  # EMCP 平台域名
        
        # EMCP 平台引流话术
        self.emcp_promotion = emcp_promotion or self._get_default_emcp_promotion()
        
        # 使用内置模板
        self.templates = self._load_builtin_templates()
    
    def _get_default_emcp_promotion(self) -> dict:
        """获取默认的 EMCP 平台引流话术（中英繁）"""
        return {
            'zh': f"""## 🚀 使用 EMCP 平台快速体验

**[EMCP]({self.emcp_domain})** 是一个强大的 MCP 服务器管理平台，让您无需手动配置即可快速使用各种 MCP 服务器！

### 快速开始：

1. 🌐 访问 **[EMCP 平台]({self.emcp_domain})**
2. 📝 注册并登录账号
3. 🎯 进入 **MCP 广场**，浏览所有可用的 MCP 服务器
4. 🔍 搜索或找到本服务器（`{{package_name}}`）
5. 🎉 点击 **"安装 MCP"** 按钮
6. ✅ 完成！即可在您的应用中使用

### EMCP 平台优势：

- ✨ **零配置**：无需手动编辑配置文件
- 🎨 **可视化管理**：图形界面轻松管理所有 MCP 服务器
- 🔐 **安全可靠**：统一管理 API 密钥和认证信息
- 🚀 **一键安装**：MCP 广场提供丰富的服务器选择
- 📊 **使用统计**：实时查看服务调用情况

立即访问 **[EMCP 平台]({self.emcp_domain})** 开始您的 MCP 之旅！
""",
            'en': f"""## 🚀 Quick Start with EMCP Platform

**[EMCP]({self.emcp_domain})** is a powerful MCP server management platform that allows you to quickly use various MCP servers without manual configuration!

### Quick Start:

1. 🌐 Visit **[EMCP Platform]({self.emcp_domain})**
2. 📝 Register and login
3. 🎯 Go to **MCP Marketplace** to browse all available MCP servers
4. 🔍 Search or find this server (`{{package_name}}`)
5. 🎉 Click the **"Install MCP"** button
6. ✅ Done! You can now use it in your applications

### EMCP Platform Advantages:

- ✨ **Zero Configuration**: No need to manually edit config files
- 🎨 **Visual Management**: Easy-to-use GUI for managing all MCP servers
- 🔐 **Secure & Reliable**: Centralized API key and authentication management
- 🚀 **One-Click Install**: Rich selection of servers in MCP Marketplace
- 📊 **Usage Statistics**: Real-time service call monitoring

Visit **[EMCP Platform]({self.emcp_domain})** now to start your MCP journey!
""",
            'zh_tw': f"""## 🚀 使用 EMCP 平台快速體驗

**[EMCP]({self.emcp_domain})** 是一個強大的 MCP 伺服器管理平台，讓您無需手動配置即可快速使用各種 MCP 伺服器！

### 快速開始：

1. 🌐 造訪 **[EMCP 平台]({self.emcp_domain})**
2. 📝 註冊並登入帳號
3. 🎯 進入 **MCP 廣場**，瀏覽所有可用的 MCP 伺服器
4. 🔍 搜尋或找到本伺服器（`{{package_name}}`）
5. 🎉 點擊 **「安裝 MCP」** 按鈕
6. ✅ 完成！即可在您的應用中使用

### EMCP 平台優勢：

- ✨ **零配置**：無需手動編輯配置檔案
- 🎨 **視覺化管理**：圖形介面輕鬆管理所有 MCP 伺服器
- 🔐 **安全可靠**：統一管理 API 金鑰和認證資訊
- 🚀 **一鍵安裝**：MCP 廣場提供豐富的伺服器選擇
- 📊 **使用統計**：即時查看服務調用情況

立即造訪 **[EMCP 平台]({self.emcp_domain})** 開始您的 MCP 之旅！
"""
        }
    
    def generate(self, api_spec: APISpec, transport: str = "stdio", custom_name: Optional[str] = None) -> MCPServer:
        """
        从 API 规范生成 MCP 服务器
        
        Args:
            api_spec: API 规范
            transport: 传输协议类型 (stdio, sse, streamable-http)
            custom_name: 自定义服务器名称（可选）
        
        Returns:
            生成的 MCP 服务器对象
        """
        # 将 API 端点转换为 MCP 工具
        mcp_tools = self._convert_endpoints_to_tools(api_spec.endpoints)
        
        # 使用自定义名称或从 API 标题生成
        server_name = self._sanitize_name(custom_name if custom_name else api_spec.title)
        
        # 生成 PyPI 包名（带前缀）
        package_name = f"{self.package_prefix}-{server_name}" if self.package_prefix else server_name
        
        # 创建 MCP 服务器对象
        mcp_server = MCPServer(
            name=server_name,
            version=api_spec.version,
            description=api_spec.description or f"MCP Server for {api_spec.title}",
            tools=mcp_tools,
            api_spec=api_spec
        )
        
        # 将包名存储到 MCP 服务器对象中
        mcp_server.package_name = package_name
        
        # 生成代码文件
        output_path = self._generate_server_code(mcp_server, transport)
        mcp_server.output_path = str(output_path)
        
        print(f"✅ MCP 服务器已生成: {output_path}")
        print(f"📦 PyPI 包名: {package_name}")
        
        return mcp_server
    
    def _convert_endpoints_to_tools(self, endpoints: List[APIEndpoint]) -> List[MCPTool]:
        """将 API 端点转换为 MCP 工具"""
        tools = []
        
        for endpoint in endpoints:
            tool = self._endpoint_to_tool(endpoint)
            tools.append(tool)
        
        return tools
    
    def _endpoint_to_tool(self, endpoint: APIEndpoint) -> MCPTool:
        """将单个端点转换为 MCP 工具"""
        # 生成工具名称
        tool_name = endpoint.operation_id or self._generate_tool_name(endpoint)
        tool_name = self._sanitize_name(tool_name)
        
        # 生成描述
        description = endpoint.enhanced_description or endpoint.description or endpoint.summary or f"{endpoint.method} {endpoint.path}"
        
        # 生成输入模式
        input_schema = self._generate_input_schema(endpoint)
        
        return MCPTool(
            name=tool_name,
            description=description,
            input_schema=input_schema,
            endpoint=endpoint
        )
    
    def _generate_tool_name(self, endpoint: APIEndpoint) -> str:
        """生成工具名称"""
        # 从路径生成名称
        path_parts = endpoint.path.strip('/').split('/')
        # 过滤掉参数部分
        name_parts = [part for part in path_parts if not part.startswith('{')]
        
        if not name_parts:
            name_parts = ['api']
        
        name = '_'.join(name_parts)
        name = f"{endpoint.method.lower()}_{name}"
        
        return name
    
    def _generate_input_schema(self, endpoint: APIEndpoint) -> Dict[str, Any]:
        """生成输入模式"""
        properties: Dict[str, Any] = {}
        required: List[str] = []
        
        for param in endpoint.parameters:
            param_schema: Dict[str, Any] = {
                "type": self._convert_type(param.type),
            }
            
            if param.description:
                param_schema["description"] = param.description
            
            if param.enum:
                param_schema["enum"] = param.enum
            
            if param.default is not None:
                param_schema["default"] = param.default
            
            properties[param.name] = param_schema
            
            if param.required:
                required.append(param.name)
        
        schema: Dict[str, Any] = {
            "type": "object",
            "properties": properties,
        }
        
        if required:
            schema["required"] = required
        
        return schema
    
    def _convert_type(self, api_type: str) -> str:
        """转换 API 类型到 JSON Schema 类型"""
        type_mapping = {
            'integer': 'number',
            'int': 'number',
            'long': 'number',
            'float': 'number',
            'double': 'number',
            'string': 'string',
            'boolean': 'boolean',
            'bool': 'boolean',
            'array': 'array',
            'object': 'object',
        }
        
        return type_mapping.get(api_type.lower(), 'string')
    
    def _sanitize_name(self, name: str) -> str:
        """清理名称，使其符合 Python 标识符规范"""
        # 替换非法字符
        name = name.replace(' ', '_').replace('-', '_')
        # 移除其他特殊字符
        name = ''.join(c for c in name if c.isalnum() or c == '_')
        # 确保不以数字开头
        if name and name[0].isdigit():
            name = 'api_' + name
        
        return name.lower()
    
    def _generate_server_code(self, mcp_server: MCPServer, transport: str = "stdio") -> Path:
        """生成服务器代码"""
        server_dir = self.output_dir / mcp_server.name
        server_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成 openapi.json 文件
        openapi_file = server_dir / "openapi.json"
        openapi_spec = self._api_spec_to_openapi(mcp_server.api_spec)
        openapi_file.write_text(json.dumps(openapi_spec, ensure_ascii=False, indent=2), encoding='utf-8')
        
        # 生成主服务器文件
        server_file = server_dir / "server.py"
        server_code = self._render_server_template(mcp_server, transport)
        server_file.write_text(server_code, encoding='utf-8')
        
        # 生成 pyproject.toml
        pyproject_file = server_dir / "pyproject.toml"
        pyproject_code = self._render_pyproject_template(mcp_server)
        pyproject_file.write_text(pyproject_code, encoding='utf-8')
        
        # 生成 LICENSE 文件
        license_file = server_dir / "LICENSE"
        license_code = self._generate_license()
        license_file.write_text(license_code, encoding='utf-8')
        
        # 生成 README（中文）
        readme_file = server_dir / "README.md"
        readme_code = self._render_readme_template(mcp_server, transport, lang='zh')
        readme_file.write_text(readme_code, encoding='utf-8')
        
        # 生成 README_EN.md（英文）
        readme_en_file = server_dir / "README_EN.md"
        readme_en_code = self._render_readme_template(mcp_server, transport, lang='en')
        readme_en_file.write_text(readme_en_code, encoding='utf-8')
        
        # 生成 README_ZH-TW.md（繁体中文）
        readme_tw_file = server_dir / "README_ZH-TW.md"
        readme_tw_code = self._render_readme_template(mcp_server, transport, lang='zh_tw')
        readme_tw_file.write_text(readme_tw_code, encoding='utf-8')
        
        # 生成 __init__.py
        init_file = server_dir / "__init__.py"
        init_file.write_text(f'"""MCP Server for {mcp_server.api_spec.title}"""\n', encoding='utf-8')
        
        # 生成 setup.py（兼容性）
        setup_file = server_dir / "setup.py"
        setup_code = self._generate_setup_py(mcp_server)
        setup_file.write_text(setup_code, encoding='utf-8')
        
        return server_dir
    
    def _generate_license(self) -> str:
        """生成 MIT 许可证"""
        from datetime import datetime
        year = datetime.now().year
        return f'''MIT License

Copyright (c) {year} bachstudio

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''
    
    def _generate_setup_py(self, mcp_server: MCPServer) -> str:
        """生成 setup.py 文件（兼容性）"""
        return f'''#!/usr/bin/env python3
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="{mcp_server.package_name}",
    version="{mcp_server.version}",
    description="MCP server for accessing {mcp_server.api_spec.title} API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="bachstudio",
    python_requires=">=3.10",
    install_requires=[
        "fastmcp>=2.0.0",
        "httpx>=0.25.0",
    ],
    py_modules=["server"],
    entry_points={{
        "console_scripts": [
            "{mcp_server.package_name.replace('-', '_')}=server:main",
        ],
    }},
    package_data={{
        "": ["openapi.json"],
    }},
    include_package_data=True,
)
'''
    
    def _render_server_template(self, mcp_server: MCPServer, transport: str) -> str:
        """渲染服务器模板"""
        template = self.templates['server.py']
        return template.render(
            server=mcp_server,
            api_spec=mcp_server.api_spec,
            tools=mcp_server.tools,
            transport=transport
        )
    
    def _render_pyproject_template(self, mcp_server: MCPServer) -> str:
        """渲染 pyproject.toml 模板"""
        template = self.templates['pyproject.toml']
        return template.render(
            server=mcp_server,
            api_spec=mcp_server.api_spec
        )
    
    def _render_readme_template(self, mcp_server: MCPServer, transport: str, lang: str = 'zh') -> str:
        """渲染 README 模板"""
        template = self.templates['README.md']
        
        # 获取 EMCP 引流话术
        emcp_promo = self.emcp_promotion.get(lang, self.emcp_promotion['zh'])
        emcp_promo = emcp_promo.format(package_name=mcp_server.package_name or mcp_server.name)
        
        return template.render(
            server=mcp_server,
            api_spec=mcp_server.api_spec,
            tools=mcp_server.tools,
            transport=transport,
            lang=lang,
            emcp_promotion=emcp_promo
        )
    
    def _load_builtin_templates(self) -> Dict[str, Template]:
        """加载内置模板"""
        templates = {}
        
        # 服务器模板
        templates['server.py'] = Template(SERVER_TEMPLATE)
        templates['pyproject.toml'] = Template(PYPROJECT_TEMPLATE)
        templates['README.md'] = Template(README_TEMPLATE)
        
        return templates
    
    def _api_spec_to_openapi(self, api_spec: APISpec) -> Dict[str, Any]:
        """将内部 API 规范转换回 OpenAPI 格式"""
        openapi = {
            "openapi": "3.0.0",
            "info": {
                "title": api_spec.title,
                "version": api_spec.version,
                "description": api_spec.description or ""
            },
            "servers": api_spec.servers if api_spec.servers else [
                {"url": api_spec.base_url or "https://api.example.com"}
            ],
            "paths": {}
        }
        
        # 转换端点
        for endpoint in api_spec.endpoints:
            path = endpoint.path
            if path not in openapi["paths"]:
                openapi["paths"][path] = {}
            
            # 处理响应定义，移除过于严格的 type 限制
            responses = endpoint.responses or {"200": {"description": "Success"}}
            # 修改响应 schema，移除 type 字段以支持灵活的返回类型
            if "200" in responses and "content" in responses["200"]:
                content = responses["200"]["content"]
                if "application/json" in content and "schema" in content["application/json"]:
                    schema = content["application/json"]["schema"]
                    # 如果 schema 只定义了 type: object，移除它以允许任意类型
                    if schema.get("type") == "object" and len(schema) == 1:
                        # 不指定 type，让 FastMCP 自动处理
                        content["application/json"]["schema"] = {}
            
            operation = {
                "summary": endpoint.enhanced_summary or endpoint.summary or "",
                "description": endpoint.enhanced_description or endpoint.description or "",
                "operationId": endpoint.operation_id or f"{endpoint.method.lower()}_{path.replace('/', '_')}",
                "parameters": [],
                "responses": responses
            }
            
            # 添加参数
            for param in endpoint.parameters:
                operation["parameters"].append({
                    "name": param.name,
                    "in": "query",  # 简化处理，实际应该根据参数位置判断
                    "required": param.required,
                    "description": param.description or "",
                    "schema": {
                        "type": param.type,
                        "default": param.default,
                        "enum": param.enum
                    }
                })
            
            openapi["paths"][path][endpoint.method.lower()] = operation
        
        # 添加安全定义
        if api_spec.auth_type:
            openapi["components"] = {
                "securitySchemes": {
                    "ApiAuth": api_spec.auth_config
                }
            }
            openapi["security"] = [{"ApiAuth": []}]
        
        return openapi


# 内置模板

SERVER_TEMPLATE = '''"""
{{ api_spec.title }} MCP Server

MCP server for accessing {{ api_spec.title }} API.

Version: {{ server.version }}
Transport: {{ transport }}
"""
import os
import json
import httpx
from pathlib import Path
from fastmcp import FastMCP

# 服务器版本和配置
__version__ = "{{ server.version }}"
__tag__ = "{{ server.name }}/{{ server.version }}"

# API 配置
API_KEY = os.getenv("API_KEY", "")

# 传输协议配置
TRANSPORT = "{{ transport }}"
{% if transport in ['sse', 'streamable-http'] %}
PORT = int(os.getenv("PORT", "8000"))  # SSE/HTTP 服务器端口
HOST = os.getenv("HOST", "localhost")  # SSE/HTTP 服务器主机
{% endif %}


def load_openapi_spec():
    """从 openapi.json 文件加载 OpenAPI 规范"""
    openapi_path = Path(__file__).parent / "openapi.json"
    with open(openapi_path, "r", encoding="utf-8") as f:
        return json.load(f)


# 创建 HTTP 客户端
# 设置默认 headers
default_headers = {}

{% if api_spec.base_url and 'rapidapi.com' in api_spec.base_url %}
# RapidAPI 必需的 headers
if API_KEY:
    default_headers["X-RapidAPI-Key"] = API_KEY
    default_headers["X-RapidAPI-Host"] = "{{ api_spec.base_url.replace('https://', '').replace('http://', '') }}"
else:
    print("⚠️  警告: 未设置 API_KEY 环境变量")
    print("   RapidAPI 需要 API Key 才能正常工作")
    print("   请设置: export API_KEY=你的RapidAPI-Key")

# 对于 POST/PUT/PATCH 请求，自动添加 Content-Type
default_headers["Content-Type"] = "application/json"

{% elif api_spec.auth_type %}
# 其他 API 的认证
if API_KEY:
    default_headers["{{ api_spec.auth_config.get('name', 'X-API-Key') if api_spec.auth_type == 'apikey' else 'Authorization' }}"] = API_KEY
{% endif %}

{% if api_spec.base_url %}
client = httpx.AsyncClient(
    base_url="{{ api_spec.base_url }}", 
    timeout=30.0
)
{% else %}
client = httpx.AsyncClient(
    timeout=30.0
)
{% endif %}

# 从 OpenAPI 规范创建 FastMCP 服务器
openapi_dict = load_openapi_spec()
mcp = FastMCP.from_openapi(
    openapi_spec=openapi_dict,
    client=client,
    name="{{ server.name }}",
    version=__version__
)

{% if api_spec.base_url and 'rapidapi.com' in api_spec.base_url %}
# 注册请求拦截器，为所有请求添加 RapidAPI headers
_original_request = client.request

async def _add_rapidapi_headers(method, url, **kwargs):
    """拦截所有请求，添加必需的 RapidAPI headers"""
    # 确保 headers 存在
    if 'headers' not in kwargs:
        kwargs['headers'] = {}
    
    # 添加 RapidAPI 必需的 headers
    if API_KEY:
        kwargs['headers']['X-RapidAPI-Key'] = API_KEY
        kwargs['headers']['X-RapidAPI-Host'] = "{{ api_spec.base_url.replace('https://', '').replace('http://', '') }}"
    else:
        print("⚠️  警告: API_KEY 未设置，请求可能失败")
    
    # 对于 POST/PUT/PATCH，添加 Content-Type
    if method.upper() in ['POST', 'PUT', 'PATCH']:
        if 'Content-Type' not in kwargs['headers']:
            kwargs['headers']['Content-Type'] = 'application/json'
    
    return await _original_request(method, url, **kwargs)

# 替换 request 方法
client.request = _add_rapidapi_headers
{% endif %}

def main():
    """主入口点"""
    print(f"🚀 启动 {{ api_spec.title }} MCP 服务器")
    print(f"📦 版本: {__tag__}")
    print(f"🔧 传输协议: {TRANSPORT}")
    {% if transport in ['sse', 'streamable-http'] %}
    print(f"🌐 监听地址: http://{HOST}:{PORT}")
    print(f"💡 提示: 可通过环境变量 PORT 和 HOST 修改监听地址")
    {% endif %}
    print()
    
    # 运行服务器
    {% if transport == 'sse' %}
    mcp.run(transport="sse", port=PORT, host=HOST)
    {% elif transport == 'streamable-http' %}
    mcp.run(transport="streamable-http", port=PORT, host=HOST)
    {% else %}
    mcp.run(transport="{{ transport }}")
    {% endif %}


if __name__ == "__main__":
    main()
'''

PYPROJECT_TEMPLATE = '''[project]
name = "{{ server.package_name }}"
version = "{{ server.version }}"
description = "MCP server for accessing {{ api_spec.title }} API"
readme = "README.md"
requires-python = ">=3.10"
license = {file = "LICENSE"}
authors = [
    {name = "bachstudio"}
]
keywords = ["mcp", "{{ server.name }}", "api", "model-context-protocol"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
dependencies = [
    "fastmcp>=2.0.0",
    "httpx>=0.25.0",
]

[project.scripts]
{{ server.package_name.replace('-', '_') }} = "server:main"

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "black>=23.0.0",
]

[project.urls]
Homepage = "https://github.com/bachstudio/{{ server.package_name }}"
Repository = "https://github.com/bachstudio/{{ server.package_name }}"
Documentation = "https://github.com/bachstudio/{{ server.package_name }}#readme"
"Bug Tracker" = "https://github.com/bachstudio/{{ server.package_name }}/issues"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["."]
artifacts = ["openapi.json"]

[tool.hatch.build.targets.sdist]
include = [
    "server.py",
    "openapi.json",
    "README.md",
    "LICENSE",
    "__init__.py",
]

[tool.hatch.version]
path = "server.py"
pattern = '__version__ = "(?P<version>[^"]+)"'
'''

README_TEMPLATE = '''# {{ api_spec.title }} MCP Server

{% if lang == 'zh' %}[English](./README_EN.md) | 简体中文 | [繁體中文](./README_ZH-TW.md){% elif lang == 'en' %}English | [简体中文](./README.md) | [繁體中文](./README_ZH-TW.md){% elif lang == 'zh_tw' %}[English](./README_EN.md) | [简体中文](./README.md) | 繁體中文{% endif %}

{% if lang == 'zh' %}用于访问 {{ api_spec.title }} API 的 MCP 服务器。{% elif lang == 'en' %}An MCP server for accessing {{ api_spec.title }} API.{% elif lang == 'zh_tw' %}用於存取 {{ api_spec.title }} API 的 MCP 伺服器。{% endif %}

{{ emcp_promotion }}

---

{% if lang == 'zh' %}## 简介{% elif lang == 'en' %}## Introduction{% elif lang == 'zh_tw' %}## 簡介{% endif %}

{% if lang == 'zh' %}这是一个 MCP 服务器，用于访问 {{ api_spec.title }} API。{% elif lang == 'en' %}This is an MCP server for accessing the {{ api_spec.title }} API.{% elif lang == 'zh_tw' %}這是一個 MCP 伺服器，用於存取 {{ api_spec.title }} API。{% endif %}

{% if lang == 'zh' %}- **PyPI 包名**: `{{ server.package_name }}`
- **版本**: {{ server.version }}
- **传输协议**: {{ transport }}
{% elif lang == 'en' %}- **PyPI Package**: `{{ server.package_name }}`
- **Version**: {{ server.version }}
- **Transport Protocol**: {{ transport }}
{% elif lang == 'zh_tw' %}- **PyPI 套件名**: `{{ server.package_name }}`
- **版本**: {{ server.version }}
- **傳輸協定**: {{ transport }}
{% endif %}

## 安装

### 从 PyPI 安装:

```bash
pip install {{ server.package_name }}
```

### 从源码安装:

```bash
pip install -e .
```

## 运行

### 方式 1: 使用 uvx（推荐，无需安装）

```bash
# 运行（uvx 会自动安装并运行）
uvx --from {{ server.package_name }} {{ server.package_name.replace('-', '_') }}

# 或指定版本
uvx --from {{ server.package_name }}@latest {{ server.package_name.replace('-', '_') }}
```

### 方式 2: 直接运行（开发模式）

```bash
python server.py
```

### 方式 3: 安装后作为命令运行

```bash
# 安装
pip install {{ server.package_name }}

# 运行（命令名使用下划线）
{{ server.package_name.replace('-', '_') }}
```

{% if lang == 'zh' %}## 配置

### API 认证

此 API 需要认证。请设置环境变量:

```bash
export API_KEY="your_api_key_here"
```

### 环境变量

| 变量名 | 说明 | 必需 |
|--------|------|------|
| `API_KEY` | API 密钥 | 是 |
| `PORT` | {% if transport in ['sse', 'streamable-http'] %}服务器端口（默认 8000）{% else %}不适用{% endif %} | 否 |
| `HOST` | {% if transport in ['sse', 'streamable-http'] %}服务器主机（默认 localhost）{% else %}不适用{% endif %} | 否 |

{% elif lang == 'en' %}## Configuration

### API Authentication

This API requires authentication. Please set environment variable:

```bash
export API_KEY="your_api_key_here"
```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `API_KEY` | API Key | Yes |
| `PORT` | {% if transport in ['sse', 'streamable-http'] %}Server port (default 8000){% else %}N/A{% endif %} | No |
| `HOST` | {% if transport in ['sse', 'streamable-http'] %}Server host (default localhost){% else %}N/A{% endif %} | No |

{% elif lang == 'zh_tw' %}## 配置

### API 認證

此 API 需要認證。請設定環境變數:

```bash
export API_KEY="your_api_key_here"
```

### 環境變數

| 變數名 | 說明 | 必需 |
|--------|------|------|
| `API_KEY` | API 金鑰 | 是 |
| `PORT` | {% if transport in ['sse', 'streamable-http'] %}伺服器埠號（預設 8000）{% else %}不適用{% endif %} | 否 |
| `HOST` | {% if transport in ['sse', 'streamable-http'] %}伺服器主機（預設 localhost）{% else %}不適用{% endif %} | 否 |

{% endif %}

{% if lang == 'zh' %}### 在 Cursor 中使用{% elif lang == 'en' %}### Using with Cursor{% elif lang == 'zh_tw' %}### 在 Cursor 中使用{% endif %}

{% if lang == 'zh' %}编辑 Cursor MCP 配置文件 `~/.cursor/mcp.json`:{% elif lang == 'en' %}Edit Cursor MCP config file `~/.cursor/mcp.json`:{% elif lang == 'zh_tw' %}編輯 Cursor MCP 配置檔案 `~/.cursor/mcp.json`:{% endif %}

{% if transport == 'stdio' %}
```json
{
  "mcpServers": {
    "{{ server.package_name }}": {
      "command": "uvx",
      "args": ["--from", "{{ server.package_name }}", "{{ server.package_name.replace('-', '_') }}"]{% if api_spec.auth_type %},
      "env": {
        "API_KEY": "your_api_key_here"
      }{% endif %}
    }
  }
}
```

{% if lang == 'zh' %}### 在 Claude Desktop 中使用{% elif lang == 'en' %}### Using with Claude Desktop{% elif lang == 'zh_tw' %}### 在 Claude Desktop 中使用{% endif %}

{% if lang == 'zh' %}编辑 Claude Desktop 配置文件 `claude_desktop_config.json`:{% elif lang == 'en' %}Edit Claude Desktop config file `claude_desktop_config.json`:{% elif lang == 'zh_tw' %}編輯 Claude Desktop 配置檔案 `claude_desktop_config.json`:{% endif %}

```json
{
  "mcpServers": {
    "{{ server.package_name }}": {
      "command": "uvx",
      "args": ["--from", "{{ server.package_name }}", "{{ server.package_name.replace('-', '_') }}"]{% if api_spec.auth_type %},
      "env": {
        "API_KEY": "your_api_key_here"
      }{% endif %}
    }
  }
}
```
{% elif transport == 'sse' %}
```json
{
  "mcpServers": {
    "{{ server.name }}": {
      "url": "http://localhost:8000/sse"{% if api_spec.auth_type %},
      "env": {
        "API_KEY": "your_api_key_here"
      }{% endif %}
    }
  }
}
```

启动 SSE 服务器:
```bash
# 使用默认端口 8000
python server.py

# 或指定自定义端口
PORT=9000 python server.py

# 指定主机和端口
HOST=0.0.0.0 PORT=9000 python server.py
```

**端口配置**:
- 默认端口: `8000`
- 通过环境变量 `PORT` 修改端口
- 通过环境变量 `HOST` 修改监听地址（默认 `localhost`）
{% elif transport == 'streamable-http' %}
```json
{
  "mcpServers": {
    "{{ server.name }}": {
      "url": "http://localhost:8000"{% if api_spec.auth_type %},
      "env": {
        "API_KEY": "your_api_key_here"
      }{% endif %}
    }
  }
}
```

启动 HTTP 服务器:
```bash
# 使用默认端口 8000
python server.py

# 或指定自定义端口
PORT=9000 python server.py

# 指定主机和端口
HOST=0.0.0.0 PORT=9000 python server.py
```

**端口配置**:
- 默认端口: `8000`
- 通过环境变量 `PORT` 修改端口
- 通过环境变量 `HOST` 修改监听地址（默认 `localhost`）
{% endif %}

## 可用工具

此服务器提供以下工具:

{% for tool in tools %}
### `{{ tool.name }}`

{{ tool.description }}

**端点**: `{{ tool.endpoint.method }} {{ tool.endpoint.path }}`

{% if tool.endpoint.parameters %}
**参数**:
{% for param in tool.endpoint.parameters %}
- `{{ param.name }}` ({{ param.type }}){% if param.required %} *必需*{% endif %}: {{ param.description or '无描述' }}
{% endfor %}
{% endif %}

---

{% endfor %}

{% if lang == 'zh' %}## 技术栈{% elif lang == 'en' %}## Tech Stack{% elif lang == 'zh_tw' %}## 技術棧{% endif %}

{% if lang == 'zh' %}- **传输协议**: {{ transport }}
- **HTTP 客户端**: httpx
{% elif lang == 'en' %}- **Transport Protocol**: {{ transport }}
- **HTTP Client**: httpx
{% elif lang == 'zh_tw' %}- **傳輸協定**: {{ transport }}
- **HTTP 客戶端**: httpx
{% endif %}

{% if lang == 'zh' %}## 许可证{% elif lang == 'en' %}## License{% elif lang == 'zh_tw' %}## 授權{% endif %}

{% if lang == 'zh' %}MIT License - 详见 [LICENSE](./LICENSE) 文件。{% elif lang == 'en' %}MIT License - See [LICENSE](./LICENSE) file for details.{% elif lang == 'zh_tw' %}MIT License - 詳見 [LICENSE](./LICENSE) 檔案。{% endif %}

{% if lang == 'zh' %}## 开发{% elif lang == 'en' %}## Development{% elif lang == 'zh_tw' %}## 開發{% endif %}

{% if lang == 'zh' %}此服务器由 [API-to-MCP](https://github.com/BACH-AI-Tools/api-to-mcp) 工具生成。

版本: {{ server.version }}
{% elif lang == 'en' %}This server is generated by [API-to-MCP](https://github.com/BACH-AI-Tools/api-to-mcp) tool.

Version: {{ server.version }}
{% elif lang == 'zh_tw' %}此伺服器由 [API-to-MCP](https://github.com/BACH-AI-Tools/api-to-mcp) 工具生成。

版本: {{ server.version }}
{% endif %}
'''

