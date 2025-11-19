# 🎉 欢迎使用 API to MCP！

## 🆕 批量爬取 RapidAPI（新功能！）

支持批量爬取多个 RapidAPI，晚上挂机，第二天收获一堆 MCP 项目！

```bash
# 快速开始 - 批量爬取
python batch_rapidapi.py rapidapi_top_50.txt --use-selenium --delay 20
```

👉 **详细文档**: [BATCH_RAPIDAPI.md](./BATCH_RAPIDAPI.md)

---

## 🚀 快速开始（5 分钟）

### 步骤 1: 安装依赖

```bash
pip install -r requirements.txt
pip install -e .
```

### 步骤 2: 测试示例

```bash
# 验证示例 API
api-to-mcp validate examples/example_weather_api.json

# 转换示例（不使用 LLM，更快）
api-to-mcp convert examples/example_weather_api.json --no-enhance
```

### 步骤 3: 查看生成的服务器

```bash
cd generated_mcps/weather_api
cat server.py  # 查看生成的 FastMCP 服务器代码
```

### 步骤 4: 测试服务器

```bash
# 测试服务器可用性
api-to-mcp test generated_mcps/weather_api
```

### 步骤 5: 运行服务器

```bash
# 方式 1: 直接运行
cd generated_mcps/weather_api
python server.py

# 方式 2: 发布后使用 uvx
api-to-mcp publish generated_mcps/weather_api --target testpypi
pip install -i https://test.pypi.org/simple/ weather_api
```

## 📖 下一步

### 使用自己的 API

```bash
# 从本地文件（自定义名称）
api-to-mcp convert your-api.json -n my_api

# 从 URL
api-to-mcp from-url https://example.com/openapi.json -n my_api

# 使用不同的传输协议
api-to-mcp convert your-api.json -t sse
api-to-mcp convert your-api.json -t streamable-http
```

### 测试和发布

```bash
# 1. 测试服务器
api-to-mcp test generated_mcps/my_api

# 2. 发布到 TestPyPI
api-to-mcp publish generated_mcps/my_api --target testpypi

# 3. 测试安装
pip install -i https://test.pypi.org/simple/ my-api

# 4. 发布到正式 PyPI
api-to-mcp publish generated_mcps/my_api --target pypi
```

详细说明请查看 [PUBLISH_GUIDE.md](PUBLISH_GUIDE.md)

### 使用 GUI 界面

```bash
# 启动可视化界面
python gui_app.py
```

然后在浏览器中访问 http://localhost:8501

### 启用 AI 增强

```bash
# 使用 Azure OpenAI 增强描述（项目已内置配置）
api-to-mcp convert your-api.json --enhance
```

### 在 Claude Desktop 中使用

1. 找到生成的服务器目录（例如 `generated_mcps/your_api`）
2. 编辑 Claude Desktop 配置文件：
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

3. 添加配置：
```json
{
  "mcpServers": {
    "your_api": {
      "command": "python",
      "args": ["E:\\code\\APItoMCP\\generated_mcps\\your_api\\server.py"]
    }
  }
}
```

4. 重启 Claude Desktop

## 🎯 项目特色

### ✨ 使用 FastMCP 2.0
- 更简洁的代码（相比传统 MCP SDK 减少 70% 代码）
- 更好的开发体验
- 企业级功能支持

### 📡 多种传输协议
- **stdio**: 适合 Claude Desktop（默认）
- **SSE**: 适合 Web 应用
- **Streamable HTTP**: 适合云部署

### 🤖 AI 驱动
- Azure OpenAI GPT-4 优化 API 描述
- 让 AI Agent 更容易理解和使用你的 API

## 📚 完整文档

- **README.md**: 完整功能和使用说明
- **USAGE.md**: 详细教程和示例
- **PROJECT_SUMMARY.md**: 项目技术总结
- **CHANGELOG.md**: 版本更新记录

## 🆘 需要帮助？

### 常见问题

**Q: 生成的服务器无法启动？**
- 确保已安装 `fastmcp>=2.0.0` 和 `httpx>=0.25.0`
- 检查 Python 版本（需要 3.10+）

**Q: 如何使用自己的 Azure OpenAI？**
```bash
export AZURE_OPENAI_ENDPOINT="your-endpoint"
export AZURE_OPENAI_API_KEY="your-key"
```

**Q: 支持哪些 API 格式？**
- OpenAPI 3.0+（JSON/YAML）
- Swagger 2.0（JSON/YAML）
- RapidAPI（OpenAPI 格式）

### 获取更多帮助

- 查看完整文档: `README.md`
- 运行快速开始脚本: `python quickstart.py`
- 查看示例: `examples/README.md`

## 🎓 学习资源

### FastMCP 文档
https://fastmcp.wiki

### MCP 协议
https://modelcontextprotocol.io/

### OpenAPI 规范
https://www.openapis.org/

## 🌟 开始构建

```bash
# 尝试转换一个真实的 API
api-to-mcp from-url https://petstore3.swagger.io/api/v3/openapi.json

# 查看生成的服务器
cd generated_mcps/swagger_petstore___openapi_3.0
cat README.md
```

## 🔧 RapidAPI 特别说明

RapidAPI 不直接提供 OpenAPI 规范下载。使用我们的辅助工具:

```bash
# 获取帮助和自动尝试获取规范
api-to-mcp rapidapi-help https://rapidapi.com/apidojo/api/yahoo-finance1

# 如果自动获取成功，会保存为 JSON 文件
# 然后转换
api-to-mcp convert rapidapi_yahoo-finance1_spec.json -n yahoo_finance
```

详细方法请查看 [RAPIDAPI_GUIDE.md](RAPIDAPI_GUIDE.md)

## 💡 提示

1. **快速测试**: 使用 `--no-enhance` 跳过 AI 增强，转换更快
2. **选择协议**: stdio 用于本地开发，SSE/HTTP 用于生产部署
3. **批量转换**: 可以编写脚本批量转换多个 API
4. **自定义代码**: 生成的代码可以自由修改和扩展
5. **RapidAPI**: 使用 `rapidapi-help` 命令获取获取规范的帮助

## 🎉 祝你使用愉快！

如有问题或建议，欢迎提交 Issue 或 PR。

---

**Made with ❤️ using FastMCP**

