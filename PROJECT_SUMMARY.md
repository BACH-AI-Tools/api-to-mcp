# API to MCP - 项目总结

## 项目概述

**API to MCP** 是一个强大的工具，可以自动将任何 Web API（OpenAPI/Swagger 规范）转换为功能完整的 MCP (Model Context Protocol) 服务器。

## ✨ 核心优势

### 1. FastMCP 2.0 驱动
- 使用业界领先的 [FastMCP](https://fastmcp.wiki) 框架
- 生成的代码简洁、优雅、易于维护
- 享受 FastMCP 的全部高级功能

### 2. 多种传输协议
- **stdio**: 标准输入输出（Claude Desktop 默认）
- **SSE**: 服务器发送事件（Web 应用友好）
- **Streamable HTTP**: HTTP 流式传输（云部署优化）

### 3. AI 驱动的描述增强
- 使用 Azure OpenAI GPT-4
- 自动优化 API 描述
- 让 AI Agent 更容易理解和使用

### 4. 多平台支持
- RapidAPI
- OpenAPI 3.0+
- Swagger 2.0

## 🏗️ 项目结构

```
APItoMCP/
├── src/api_to_mcp/
│   ├── __init__.py           # 包初始化
│   ├── __main__.py           # 模块入口
│   ├── cli.py                # 命令行接口
│   ├── config.py             # 配置管理
│   ├── models.py             # 数据模型
│   ├── enhancer.py           # AI 描述增强器
│   ├── parsers/              # OpenAPI/Swagger 解析器
│   ├── platforms/            # 平台集成（RapidAPI 等）
│   └── generator/            # FastMCP 代码生成器
├── examples/                 # 示例文件
├── generated_mcps/           # 生成的服务器（运行时创建）
├── pyproject.toml            # 项目配置
├── requirements.txt          # 依赖列表
├── README.md                 # 主文档
├── USAGE.md                  # 使用指南
├── CHANGELOG.md              # 更新日志
└── CONTRIBUTING.md           # 贡献指南
```

## 🚀 快速开始

### 安装

```bash
# 克隆项目
git clone https://github.com/yourusername/APItoMCP.git
cd APItoMCP

# 安装依赖
pip install -r requirements.txt
pip install -e .
```

### 基本使用

```bash
# 转换 API 规范（stdio 协议）
api-to-mcp convert api-spec.json

# 使用 SSE 协议
api-to-mcp convert api-spec.json -t sse

# 使用 LLM 增强描述
api-to-mcp convert api-spec.json --enhance

# 从 URL 获取
api-to-mcp from-url https://example.com/openapi.json

# 验证规范
api-to-mcp validate api-spec.json
```

## 📊 生成的代码示例

使用 FastMCP 生成的服务器代码非常简洁：

```python
"""Weather API MCP Server"""
import os
from typing import Any
import httpx
from fastmcp import FastMCP

# 配置
API_BASE_URL = "https://api.weather.example.com/v1"
API_KEY = os.getenv("API_KEY", "")

# 创建客户端
client = httpx.AsyncClient(base_url=API_BASE_URL, timeout=30.0)

# 创建服务器
mcp = FastMCP(
    name="weather_api",
    version="1.0.0",
    description="Weather API MCP Server"
)

# 定义工具
@mcp.tool()
async def get_current_weather(location: str, units: str = "metric") -> Any:
    """获取当前天气"""
    headers = {}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    
    response = await client.get(
        "/weather/current",
        headers=headers,
        params={"location": location, "units": units}
    )
    return response.json()

# 运行服务器
if __name__ == "__main__":
    mcp.run(transport="stdio")
```

## 🎯 使用场景

### 1. 快速集成 RapidAPI
从 RapidAPI 下载 OpenAPI 规范，一键转换为 MCP 服务器

### 2. 为现有 API 创建 AI 接口
将公司内部 API 转换为 MCP，让 AI Agent 可以调用

### 3. API 市场
批量转换多个 API，构建 MCP 服务器市场

### 4. 教学和原型
快速创建 MCP 服务器，用于学习和原型验证

## 🔧 主要功能

### 命令行工具

- `convert`: 转换 API 规范文件
- `from-url`: 从 URL 获取并转换
- `validate`: 验证 API 规范
- `config`: 显示配置信息

### 协议支持

- **stdio**: `api-to-mcp convert api.json -t stdio`
- **SSE**: `api-to-mcp convert api.json -t sse`
- **HTTP**: `api-to-mcp convert api.json -t streamable-http`

### AI 增强

- 自动检测不清晰的描述
- 使用 GPT-4 生成清晰的说明
- 提高 AI Agent 的理解能力

## 📝 配置

### Azure OpenAI

项目内置了 Azure OpenAI 配置，也可以通过环境变量自定义：

```bash
export AZURE_OPENAI_ENDPOINT="https://your-endpoint.openai.azure.com"
export AZURE_OPENAI_API_KEY="your-key"
export AZURE_OPENAI_DEPLOYMENT="gpt-4o"
```

### RapidAPI

```bash
export RAPIDAPI_KEY="your-rapidapi-key"
```

## 🌟 核心优势对比

### 传统 MCP SDK vs FastMCP

| 特性 | 传统 MCP SDK | FastMCP (本项目) |
|------|-------------|-----------------|
| 代码行数 | ~100 行 | ~30 行 |
| 装饰器语法 | ❌ | ✅ |
| 协议支持 | stdio only | stdio/SSE/HTTP |
| 类型提示 | 部分 | 完整 |
| 异步支持 | 基础 | 完整 |
| 企业功能 | ❌ | ✅ |

## 📦 生成的 MCP 服务器

每个生成的服务器包含：

- `server.py`: FastMCP 服务器主文件
- `pyproject.toml`: 项目配置
- `README.md`: 使用文档
- `__init__.py`: 包初始化

### 特点

- 开箱即用
- 支持 `uvx` 启动
- 完整的类型注解
- 错误处理
- 异步支持

## 🔮 未来计划

- [ ] 支持更多认证方式（OAuth2、JWT）
- [ ] 批量转换 UI 界面
- [ ] 支持 GraphQL API
- [ ] MCP 服务器测试工具
- [ ] Docker 部署支持
- [ ] 插件系统
- [ ] 在线转换服务

## 📚 文档

- **README.md**: 项目概述和快速开始
- **USAGE.md**: 详细使用指南和教程
- **CHANGELOG.md**: 版本更新记录
- **CONTRIBUTING.md**: 贡献指南
- **PROJECT_SUMMARY.md**: 本文档

## 🙏 致谢

- **FastMCP**: 提供了强大的 MCP 框架
- **Azure OpenAI**: 驱动 AI 描述增强
- **MCP Protocol**: 定义了标准协议
- **OpenAPI**: 提供了 API 规范标准

## 📮 联系和支持

- GitHub Issues: 报告 bug 和请求功能
- GitHub Discussions: 讨论和交流
- Email: your.email@example.com

## 📄 许可证

MIT License - 自由使用、修改和分发

---

**Made with ❤️ using FastMCP**

项目地址: https://github.com/yourusername/APItoMCP
FastMCP 文档: https://fastmcp.wiki


