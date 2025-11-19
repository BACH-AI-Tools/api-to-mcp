# API to MCP 使用指南

这份文档详细说明了如何使用 API-to-MCP 工具将各种 Web API 转换为 MCP 服务器。

## 目录

1. [安装](#安装)
2. [基本概念](#基本概念)
3. [使用场景](#使用场景)
4. [详细教程](#详细教程)
5. [高级用法](#高级用法)
6. [常见问题](#常见问题)

## 安装

### 前置要求

- Python 3.10 或更高版本
- pip 或 uv 包管理器

### 安装步骤

```bash
# 克隆项目
git clone https://github.com/yourusername/APItoMCP.git
cd APItoMCP

# 安装依赖
pip install -r requirements.txt

# 以可编辑模式安装
pip install -e .
```

### 验证安装

```bash
api-to-mcp --version
```

## 基本概念

### 什么是 MCP？

MCP (Model Context Protocol) 是一个协议，允许 AI 应用（如 Claude Desktop）通过标准化的接口访问外部工具和数据源。

### 工作流程

```
OpenAPI/Swagger 规范 
    ↓
[解析] → [LLM 增强] → [生成 MCP 代码]
    ↓
可运行的 MCP 服务器
```

## 使用场景

### 场景 1: 转换 RapidAPI 上的 API

1. 在 RapidAPI 上找到你需要的 API
2. 下载其 OpenAPI 规范文件
3. 使用本工具转换

```bash
api-to-mcp convert rapidapi-spec.json
```

### 场景 2: 转换自己的 API

如果你有自己的 API 并且有 OpenAPI/Swagger 文档：

```bash
api-to-mcp convert my-api.yaml --enhance
```

### 场景 3: 批量转换多个 API

```bash
for file in specs/*.json; do
    api-to-mcp convert "$file"
done
```

## 详细教程

### 教程 1: 转换天气 API

#### 步骤 1: 准备 API 规范

使用项目提供的示例文件：

```bash
api-to-mcp validate examples/example_weather_api.json
```

#### 步骤 2: 转换为 MCP 服务器

```bash
api-to-mcp convert examples/example_weather_api.json -o my_mcps
```

你会看到类似的输出：

```
🚀 开始转换: examples/example_weather_api.json
📦 平台类型: openapi
📖 解析 API 规范...
✅ 解析成功: Weather API v1.0.0
   端点数量: 2
🤖 使用 LLM 增强描述...
  [1/2] 增强端点: GET /weather/current
  [2/2] 增强端点: GET /weather/forecast
✅ 描述增强完成
🔨 生成 MCP 服务器代码...
✅ MCP 服务器已生成: my_mcps/weather_api
✅ 生成完成!
```

#### 步骤 3: 检查生成的代码

```bash
cd my_mcps/weather_api
cat server.py  # 查看服务器代码
cat README.md  # 查看使用文档
```

#### 步骤 4: 在 Claude Desktop 中使用

编辑 Claude Desktop 配置文件：

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "weather_api": {
      "command": "python",
      "args": ["E:\\code\\APItoMCP\\my_mcps\\weather_api\\server.py"],
      "env": {
        "API_KEY": "your-weather-api-key"
      }
    }
  }
}
```

重启 Claude Desktop，然后你可以问 Claude：

> "帮我查询北京的当前天气"

### 教程 2: 从 RapidAPI 转换真实 API

#### 步骤 1: 在 RapidAPI 上找到 API

访问 https://rapidapi.com/ 并搜索你需要的 API。

#### 步骤 2: 获取 OpenAPI 规范

大多数 RapidAPI 上的 API 都提供 OpenAPI 规范：

1. 进入 API 页面
2. 查找 "Endpoints" 或 "API Specification" 标签
3. 找到 OpenAPI/Swagger 规范的链接
4. 下载 JSON 或 YAML 文件

#### 步骤 3: 转换

```bash
# 如果你下载了文件
api-to-mcp convert rapidapi-geocoding.json

# 如果有直接的 URL
api-to-mcp from-url https://example.com/api/spec.json
```

#### 步骤 4: 配置认证

生成的 MCP 服务器会自动检测 API 的认证方式。通常 RapidAPI 使用 `X-RapidAPI-Key` 头：

```json
{
  "mcpServers": {
    "geocoding_api": {
      "command": "uvx",
      "args": ["geocoding_api"],
      "env": {
        "API_KEY": "your-rapidapi-key"
      }
    }
  }
}
```

### 教程 3: 不使用 LLM 增强

如果你的 API 描述已经很清晰，或者想要快速转换：

```bash
api-to-mcp convert api-spec.json --no-enhance
```

这样会跳过 Azure OpenAI 调用，直接使用原始描述。

## 高级用法

### 自定义输出目录

```bash
api-to-mcp convert api-spec.json -o ./custom/output/path
```

### 批量处理脚本

创建一个批处理脚本 `batch_convert.sh`:

```bash
#!/bin/bash

# 批量转换目录中的所有规范文件
for spec in specs/*.{json,yaml,yml}; do
    if [ -f "$spec" ]; then
        echo "Converting $spec..."
        api-to-mcp convert "$spec" --enhance
        echo "✅ Done: $spec"
        echo "---"
    fi
done

echo "🎉 All conversions completed!"
```

运行：

```bash
chmod +x batch_convert.sh
./batch_convert.sh
```

### 使用环境变量配置

创建 `.env` 文件：

```env
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_DEPLOYMENT=gpt-4o
RAPIDAPI_KEY=your-rapidapi-key
```

然后加载环境变量：

```bash
source .env  # Linux/Mac
# 或者在 PowerShell:
# Get-Content .env | ForEach-Object { $var = $_.Split('='); [Environment]::SetEnvironmentVariable($var[0], $var[1]) }

api-to-mcp convert api-spec.json
```

### 验证和调试

使用 `validate` 命令检查 API 规范：

```bash
api-to-mcp validate api-spec.json
```

这会显示：
- API 基本信息
- 端点列表
- 认证方式
- 参数详情

### 查看当前配置

```bash
api-to-mcp config
```

显示：
- Azure OpenAI 配置
- RapidAPI 配置
- 输出目录等设置

## 常见问题

### Q1: 生成的 MCP 服务器无法启动

**A**: 检查以下几点：

1. 确保已安装所有依赖：
```bash
cd generated_mcps/your_api
pip install -r requirements.txt  # 如果有
```

2. 检查 Python 版本（需要 3.10+）：
```bash
python --version
```

3. 查看错误日志，通常与 API Key 或网络配置有关

### Q2: LLM 增强失败

**A**: 可能的原因：

1. Azure OpenAI 配置不正确
   - 检查 endpoint、API key、deployment name
   
2. 网络问题
   - 确保可以访问 Azure OpenAI 服务
   
3. 配额限制
   - 检查 Azure OpenAI 的配额和限制

**临时方案**：使用 `--no-enhance` 跳过增强

```bash
api-to-mcp convert api-spec.json --no-enhance
```

### Q3: 如何更新生成的 MCP 服务器？

**A**: 重新运行转换命令即可覆盖：

```bash
api-to-mcp convert api-spec.json -o generated_mcps
```

如果想保留旧版本：

```bash
# 备份
mv generated_mcps/your_api generated_mcps/your_api.backup

# 重新生成
api-to-mcp convert api-spec.json
```

### Q4: 支持哪些 OpenAPI/Swagger 版本？

**A**: 
- ✅ OpenAPI 3.0.x
- ✅ OpenAPI 3.1.x
- ✅ Swagger 2.0

### Q5: 生成的代码可以自定义吗？

**A**: 可以！生成的代码是标准的 Python 代码，你可以：

1. 直接编辑生成的 `server.py`
2. 添加自定义逻辑
3. 修改错误处理
4. 添加缓存、限流等功能

修改后重新启动即可。

### Q6: 如何处理需要复杂认证的 API？

**A**: 对于 OAuth2 等复杂认证：

1. 生成基础 MCP 服务器
2. 手动修改 `server.py` 中的认证逻辑
3. 添加必要的 OAuth2 库

示例：

```python
# 在 server.py 中添加
from authlib.integrations.httpx_client import OAuth2Client

async def get_authenticated_client():
    client = OAuth2Client(
        client_id=os.getenv("CLIENT_ID"),
        client_secret=os.getenv("CLIENT_SECRET")
    )
    # ... OAuth2 流程
    return client
```

### Q7: 生成的 MCP 服务器性能如何？

**A**: 
- 每个请求都是异步的（使用 `httpx.AsyncClient`）
- 支持并发请求
- 建议在生产环境中添加：
  - 请求缓存
  - 速率限制
  - 错误重试

### Q8: 可以将生成的 MCP 服务器部署到服务器吗？

**A**: 当然可以！生成的是标准 Python 包：

```bash
# 打包
cd generated_mcps/your_api
pip install build
python -m build

# 部署到 PyPI 或私有仓库
twine upload dist/*

# 或使用 Docker
docker build -t your-api-mcp .
docker run your-api-mcp
```

## 最佳实践

### 1. 描述质量

- 尽量使用原生描述清晰的 API
- 如果描述不清晰，使用 `--enhance` 选项
- 检查生成的描述是否准确

### 2. 版本管理

- 为生成的 MCP 服务器创建 Git 仓库
- 使用语义化版本号
- 记录 API 规范的版本

### 3. 安全性

- 不要将 API Key 硬编码在代码中
- 使用环境变量管理敏感信息
- 定期轮换 API Key

### 4. 测试

在部署到生产前，先在 Claude Desktop 中测试：

1. 测试所有端点
2. 验证参数处理
3. 检查错误处理
4. 确认返回格式

### 5. 监控

在生产环境中添加监控：

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@server.call_tool()
async def call_tool(arguments):
    logger.info(f"Tool called with: {arguments}")
    # ... 工具逻辑
```

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目！

## 获取帮助

- 查看 [README.md](README.md)
- 提交 Issue: https://github.com/yourusername/APItoMCP/issues
- 查看示例: [examples/](examples/)

---

祝你使用愉快！🎉


