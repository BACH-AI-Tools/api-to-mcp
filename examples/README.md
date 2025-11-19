# 示例

这个目录包含了一些示例 API 规范文件，用于测试和演示 API-to-MCP 工具。

## 文件说明

### `example_weather_api.json`

一个简单的天气 API 示例，包含：
- 获取当前天气 (`GET /weather/current`)
- 获取天气预报 (`GET /weather/forecast`)

## 使用方法

### 1. 验证规范

```bash
api-to-mcp validate examples/example_weather_api.json
```

### 2. 转换为 MCP 服务器

```bash
# 使用 LLM 增强描述
api-to-mcp convert examples/example_weather_api.json -o test_output

# 不使用 LLM 增强
api-to-mcp convert examples/example_weather_api.json -o test_output --no-enhance
```

### 3. 测试生成的 MCP 服务器

```bash
cd test_output/weather_api
uvx weather_api
```

## 添加你自己的示例

你可以将任何 OpenAPI/Swagger 规范文件放在这个目录中进行测试。支持的格式：

- OpenAPI 3.0+ (`.json`, `.yaml`)
- Swagger 2.0 (`.json`, `.yaml`)

### 从 RapidAPI 导出规范

1. 访问 [RapidAPI](https://rapidapi.com/)
2. 选择你想要的 API
3. 找到 "API Specification" 或 "OpenAPI" 链接
4. 下载 JSON/YAML 文件
5. 保存到这个目录
6. 使用 `api-to-mcp convert` 转换


