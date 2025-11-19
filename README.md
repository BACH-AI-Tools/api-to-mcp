# API to MCP

**将任何 Web API 自动转换为 MCP (Model Context Protocol) 服务器**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastMCP](https://img.shields.io/badge/Powered%20by-FastMCP-purple)](https://fastmcp.wiki)

## 🌟 功能特性

- ✅ **FastMCP 驱动**: 使用 [FastMCP](https://fastmcp.wiki) 2.0 框架，享受快速、Pythonic 的 MCP 开发体验
- ✅ **多平台支持**: 支持 RapidAPI、OpenAPI 3.0+、Swagger 2.0
- ✅ **智能描述增强**: 使用 Azure OpenAI 自动优化 API 描述，让 AI Agent 更容易理解
- ✅ **多种传输协议**: 支持 stdio、SSE、Streamable HTTP 三种传输方式
- ✅ **自动代码生成**: 生成完整的 Python MCP 服务器代码，代码简洁优雅
- ✅ **开箱即用**: 生成的服务器可以直接用 `uvx` 命令启动
- ✅ **版本管理**: 自动为生成的 MCP 项目添加版本标签
- ✅ **规范验证**: 验证 OpenAPI/Swagger 规范文件的有效性

## 📦 安装

### 方式 1: 使用 pip (推荐)

```bash
# 克隆仓库
git clone https://github.com/yourusername/APItoMCP.git
cd APItoMCP

# 安装依赖
pip install -r requirements.txt

# 安装为可执行包
pip install -e .
```

### 方式 2: 使用 uv (更快)

```bash
git clone https://github.com/yourusername/APItoMCP.git
cd APItoMCP
uv pip install -e .
```

## 🚀 快速开始

### 1. 从 OpenAPI/Swagger 文件生成 MCP 服务器

```bash
# 基本用法（默认使用 stdio 协议）
api-to-mcp convert api-spec.json

# 自定义服务器名称
api-to-mcp convert api-spec.json -n my_awesome_api

# 使用 SSE 协议
api-to-mcp convert api-spec.json -t sse

# 使用 Streamable HTTP 协议
api-to-mcp convert api-spec.json -t streamable-http

# 指定输出目录
api-to-mcp convert api-spec.json -o ./my-mcps

# 不使用 LLM 增强描述
api-to-mcp convert api-spec.yaml --no-enhance
```

### 2. 从 URL 获取并转换

```bash
# 从 URL 获取 OpenAPI 规范
api-to-mcp from-url https://example.com/openapi.json

# RapidAPI 集成（需要先手动获取规范）
# 使用我们的辅助工具获取帮助
api-to-mcp rapidapi-help https://rapidapi.com/apidojo/api/yahoo-finance1
```

**RapidAPI 特别说明**: 
RapidAPI 不直接提供 OpenAPI 规范下载链接。请查看 [RAPIDAPI_GUIDE.md](RAPIDAPI_GUIDE.md) 了解如何获取。

### 3. 验证 API 规范

```bash
# 验证规范文件是否有效
api-to-mcp validate api-spec.json
```

### 4. 测试和发布

```bash
# 测试生成的服务器
api-to-mcp test generated_mcps/my_api

# 发布到 TestPyPI（推荐先测试）
api-to-mcp publish generated_mcps/my_api --target testpypi

# 发布到 PyPI
api-to-mcp publish generated_mcps/my_api --target pypi
```

详细发布指南请查看 [PUBLISH_GUIDE.md](PUBLISH_GUIDE.md)

### 5. 启动 GUI 界面

```bash
# 启动可视化界面
python gui_app.py

# 或使用 streamlit 直接运行
streamlit run src/api_to_mcp/gui.py
```

### 6. 查看配置

```bash
# 显示当前配置
api-to-mcp config
```

## ⚙️ 配置

### Azure OpenAI 配置

默认使用项目内置的 Azure OpenAI 配置，也可以通过环境变量自定义:

```bash
export AZURE_OPENAI_ENDPOINT="https://your-endpoint.openai.azure.com"
export AZURE_OPENAI_API_KEY="your-api-key"
export AZURE_OPENAI_DEPLOYMENT="gpt-4o"
```

### RapidAPI 配置

如果需要从 RapidAPI 获取 API 规范:

```bash
export RAPIDAPI_KEY="your-rapidapi-key"
```

## 📖 使用示例

### 示例 1: 转换天气 API

假设你有一个天气 API 的 OpenAPI 规范文件 `weather-api.json`:

```bash
api-to-mcp convert weather-api.json
```

输出:
```
🚀 开始转换: weather-api.json
📦 平台类型: openapi
📖 解析 API 规范...
✅ 解析成功: Weather API v1.0.0
   端点数量: 5
🤖 使用 LLM 增强描述...
  [1/5] 增强端点: GET /weather/current
  [2/5] 增强端点: GET /weather/forecast
  ...
✅ 描述增强完成
🔨 生成 MCP 服务器代码...
✅ MCP 服务器已生成: generated_mcps/weather_api
✅ 生成完成!
📁 输出目录: generated_mcps/weather_api
🎉 MCP 服务器: weather_api v1.0.0
🔧 工具数量: 5

📝 使用方法:
   uvx weather_api
```

### 示例 2: 在 Claude Desktop 中使用生成的 MCP 服务器

编辑 Claude Desktop 配置文件:

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`  
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "weather_api": {
      "command": "uvx",
      "args": ["weather_api"],
      "env": {
        "API_KEY": "your-api-key-here"
      }
    }
  }
}
```

重启 Claude Desktop，你就可以使用天气 API 的功能了！

### 示例 3: 批量转换多个 API

```bash
# 创建批处理脚本
for file in apis/*.json; do
    echo "Converting $file..."
    api-to-mcp convert "$file" -o generated_mcps
done
```

## 🏗️ 项目结构

```
APItoMCP/
├── src/
│   └── api_to_mcp/
│       ├── __init__.py          # 包初始化
│       ├── __main__.py          # 模块入口
│       ├── cli.py               # 命令行接口
│       ├── config.py            # 配置管理
│       ├── models.py            # 数据模型
│       ├── enhancer.py          # 描述增强器
│       ├── parsers/             # 解析器模块
│       │   ├── __init__.py
│       │   └── openapi_parser.py  # OpenAPI/Swagger 解析器
│       ├── platforms/           # 平台集成
│       │   ├── __init__.py
│       │   └── rapidapi.py      # RapidAPI 集成
│       └── generator/           # 代码生成器
│           ├── __init__.py
│           └── mcp_generator.py # MCP 服务器生成器
├── generated_mcps/              # 生成的 MCP 服务器（自动创建）
├── pyproject.toml               # 项目配置
├── requirements.txt             # 依赖列表
├── .gitignore                   # Git 忽略文件
└── README.md                    # 项目文档
```

## 🔧 生成的 MCP 服务器结构

每个生成的 MCP 服务器包含:

```
generated_mcps/your_api_name/
├── server.py              # MCP 服务器主文件
├── pyproject.toml         # 项目配置和依赖
├── README.md              # 使用文档
└── __init__.py            # 包初始化
```

## 🎯 支持的 API 规范

- **OpenAPI 3.0+** (JSON/YAML)
- **Swagger 2.0** (JSON/YAML)
- **RapidAPI** (通过 OpenAPI 规范)

## 💡 工作原理

1. **解析阶段**: 读取并解析 OpenAPI/Swagger 规范文件
2. **增强阶段**: 使用 Azure OpenAI (GPT-4) 分析并优化每个 API 端点的描述
3. **转换阶段**: 将 API 端点转换为 MCP 工具定义
4. **生成阶段**: 使用 FastMCP 框架和 Jinja2 模板生成优雅的 Python MCP 服务器代码
5. **打包阶段**: 创建 pyproject.toml，确保可以用 uvx 启动

## ⚡ 为什么选择 FastMCP？

本项目使用 [FastMCP 2.0](https://fastmcp.wiki) 作为底层框架，相比基础 MCP SDK，FastMCP 提供：

### 🚀 更简洁的代码
```python
# FastMCP 风格
from fastmcp import FastMCP

mcp = FastMCP("我的服务器")

@mcp.tool()
async def my_tool(arg: str) -> str:
    """工具描述"""
    return f"Result: {arg}"

mcp.run()
```

### 📡 多种传输协议
- **stdio**: 标准输入输出（默认，适合 Claude Desktop）
- **SSE**: 服务器发送事件（适合 Web 应用）
- **Streamable HTTP**: HTTP 流式传输（适合云部署）

### 🔧 企业级功能
- 高级认证支持（Google、GitHub、Azure、Auth0 等）
- 服务器组合和代理
- 内置测试框架
- 完整的客户端库

### 🎯 简单部署
```bash
# 本地运行
python server.py

# 使用 uvx
uvx my-mcp-server

# 指定协议
mcp.run(transport="sse")
```

了解更多关于 FastMCP 的信息：https://fastmcp.wiki

## 📝 命令行参考

### `convert` - 转换 API 规范文件

```bash
api-to-mcp convert [OPTIONS] INPUT_FILE
```

**参数:**
- `INPUT_FILE`: OpenAPI/Swagger 规范文件路径

**选项:**
- `-o, --output-dir TEXT`: 输出目录 (默认: generated_mcps)
- `--enhance / --no-enhance`: 是否使用 LLM 增强描述 (默认: True)
- `-p, --platform [openapi|swagger|rapidapi]`: API 平台类型 (默认: openapi)
- `-t, --transport [stdio|sse|streamable-http]`: MCP 传输协议 (默认: stdio)
- `-n, --name TEXT`: 自定义 MCP 服务器名称 (可选)

### `from-url` - 从 URL 获取并转换

```bash
api-to-mcp from-url [OPTIONS] SPEC_URL
```

**参数:**
- `SPEC_URL`: OpenAPI 规范的 URL

**选项:**
- `-o, --output-dir TEXT`: 输出目录
- `--enhance / --no-enhance`: 是否使用 LLM 增强描述
- `-k, --api-key TEXT`: RapidAPI Key
- `-t, --transport [stdio|sse|streamable-http]`: MCP 传输协议 (默认: stdio)
- `-n, --name TEXT`: 自定义 MCP 服务器名称 (可选)
- `--no-verify-ssl`: 跳过 SSL 证书验证 (不安全，仅测试用)

### `validate` - 验证规范文件

```bash
api-to-mcp validate INPUT_FILE
```

### `test` - 测试生成的 MCP 服务器

```bash
api-to-mcp test SERVER_PATH
```

**功能:**
- 检查项目结构完整性
- 验证 Python 语法
- 检查依赖安装
- 测试代码导入

### `publish` - 发布到 PyPI

```bash
api-to-mcp publish SERVER_PATH --target [testpypi|pypi]
```

**选项:**
- `-t, --target [testpypi|pypi]`: 发布目标 (默认: testpypi)

**流程:**
1. 检查前置条件
2. 构建包
3. 检查包完整性
4. 上传到 PyPI

### `rapidapi-help` - RapidAPI 辅助工具

```bash
api-to-mcp rapidapi-help RAPIDAPI_URL
```

**功能:**
- 显示如何从 RapidAPI 获取 OpenAPI 规范的详细说明
- 自动尝试获取规范（如果可能）
- 提供多种获取方法

**示例:**
```bash
api-to-mcp rapidapi-help https://rapidapi.com/apidojo/api/yahoo-finance1
```

详细说明请查看 [RAPIDAPI_GUIDE.md](RAPIDAPI_GUIDE.md)

### `config` - 显示配置

```bash
api-to-mcp config
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

- [FastMCP](https://fastmcp.wiki) - 快速、Pythonic 的 MCP 框架
- [MCP](https://github.com/modelcontextprotocol) - Model Context Protocol
- [OpenAPI](https://www.openapis.org/) - OpenAPI 规范
- [RapidAPI](https://rapidapi.com/) - API 市场平台
- [Azure OpenAI](https://azure.microsoft.com/products/ai-services/openai-service) - 描述增强

## 📮 联系方式

如有问题或建议，欢迎提交 Issue。

---

**Made with ❤️ by the API-to-MCP Team**

