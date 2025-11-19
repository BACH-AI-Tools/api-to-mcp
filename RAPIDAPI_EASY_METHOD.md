# 🎯 RapidAPI 最简单的方法

看了你的截图，我明白了 RapidAPI 的实际情况。这里提供**最实用的方法**。

## 🚀 推荐方法：使用交互式脚本

我创建了一个交互式脚本，你只需要从 RapidAPI 页面复制信息填入即可！

### 步骤 1: 运行交互式脚本

```bash
python create_rapidapi_mcp.py
```

### 步骤 2: 按提示填写信息

```
🚀 RapidAPI MCP 快速创建工具
============================================================

💡 从 RapidAPI 页面收集信息:
   1. 左侧端点列表 → 端点名称和路径
   2. 右侧代码示例 → Base URL 和参数

📝 基本信息:

API 名称 (如: JSearch): JSearch

💡 Base URL 示例: https://jsearch.p.rapidapi.com
   从右侧 curl 代码中的 --url 后面复制
Base URL: https://jsearch.p.rapidapi.com

API 描述 (可选): Fast job search API

============================================================
📍 添加端点 (从左侧端点列表)
============================================================

🔹 端点 #1:
----------------------------------------
端点名称 (如: Job Search，留空结束): Job Search
HTTP 方法 (GET/POST/etc, 默认 GET): GET
路径 (如: /search): /search
描述 (可选): Search for jobs
  📋 参数 (逐个添加，留空结束):
    参数 #1 名称 (留空结束): query
    └─ 类型 (string/integer, 默认 string): string
    └─ 必需? (y/n, 默认 n): y
    └─ 描述: Search query
    ✅ 已添加参数: query
    参数 #2 名称 (留空结束): page
    └─ 类型: integer
    └─ 必需? (y/n): n
    └─ 描述: Page number
    ✅ 已添加参数: page
    参数 #3 名称 (留空结束): [按回车结束]
✅ 已添加端点: Job Search (GET /search)

🔹 端点 #2:
----------------------------------------
端点名称 (留空结束): [按回车结束添加更多端点]

🔨 构建 OpenAPI 规范...
✅ OpenAPI 规范已保存: rapidapi_jsearch.json

MCP 服务器名称 (默认: jsearch): jsearch

🔨 生成 MCP 服务器...

🎉 完成!
```

## 📋 从你的截图获取信息

### JSearch API 示例

根据你的截图，JSearch API 的信息是：

**基本信息:**
- API 名称: `JSearch`
- Base URL: `https://jsearch.p.rapidapi.com` (从 curl 代码中获取)
- 描述: Fast, reliable, and comprehensive jobs API

**端点列表** (从左侧获取):
1. **Job Search** - `GET /search`
2. **Job Details** - `GET /job-details`
3. **Job Salary** - `GET /job-salary`
4. **Company Job Salary** - `GET /company-job-salary`

**参数** (从右侧代码示例或点击端点查看):
- 从 curl 命令中的 `query=` 部分获取

## 🎯 快速方法：使用现成模板

我已经为你创建了 JSearch 的模板！

```bash
# 1. 使用模板
api-to-mcp convert rapidapi_template_jsearch.json -n jsearch

# 2. 测试
api-to-mcp test generated_mcps/jsearch

# 3. 运行
cd generated_mcps/jsearch
python server.py
```

## 📝 为其他 RapidAPI 创建规范

### 快速方法：复制模板并修改

```bash
# 1. 复制 JSearch 模板
cp rapidapi_template_jsearch.json my_api.json

# 2. 编辑文件，修改:
#    - title (API 名称)
#    - servers[0].url (Base URL)
#    - paths (端点和参数)

# 3. 转换
api-to-mcp convert my_api.json -n my_api
```

### 模板结构

```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "你的 API 名称",
    "description": "描述",
    "version": "1.0.0"
  },
  "servers": [
    {
      "url": "https://your-api.p.rapidapi.com"
    }
  ],
  "paths": {
    "/endpoint1": {
      "get": {
        "summary": "端点名称",
        "operationId": "endpoint1",
        "parameters": [
          {
            "name": "param1",
            "in": "query",
            "required": true,
            "schema": {"type": "string"}
          }
        ]
      }
    }
  },
  "components": {
    "securitySchemes": {
      "RapidAPIAuth": {
        "type": "apiKey",
        "in": "header",
        "name": "X-RapidAPI-Key"
      }
    }
  },
  "security": [{"RapidAPIAuth": []}]
}
```

## 🎬 实战演示 - JSearch API

### 从截图收集信息

**从 curl 示例中获取:**
```bash
curl --request GET \
  --url 'https://jsearch.p.rapidapi.com/search?query=...' \
  --header 'x-rapidapi-host: jsearch.p.rapidapi.com' \
  --header 'x-rapidapi-key: ...'
```

提取信息:
- ✅ Base URL: `https://jsearch.p.rapidapi.com`
- ✅ 端点路径: `/search`
- ✅ 方法: `GET`
- ✅ 参数: `query`

### 快速创建

```bash
# 使用我提供的模板
api-to-mcp convert rapidapi_template_jsearch.json -n jsearch

# 生成完成后
cd generated_mcps/jsearch
python server.py
```

## 💡 终极简单方法

如果觉得手动创建太麻烦，使用通用的 RapidAPI 包装器：

```bash
# 使用交互式脚本
python create_rapidapi_mcp.py

# 按提示输入:
# - API 名称: JSearch
# - Base URL: https://jsearch.p.rapidapi.com
# - 端点信息...

# 一次性完成！
```

## 🔑 重要提示

**RapidAPI 的所有 API 都需要两个特殊头:**
1. `X-RapidAPI-Key`: 你的 API Key
2. `X-RapidAPI-Host`: API 的 Host (如 `jsearch.p.rapidapi.com`)

生成的 MCP 服务器会自动处理这些！

## 🎉 总结

三种方法，从简单到复杂：

1. **最简单**: 使用我提供的 `rapidapi_template_jsearch.json` 模板
2. **中等**: 运行 `python create_rapidapi_mcp.py` 交互式创建
3. **灵活**: 手动创建 JSON，然后 `api-to-mcp convert`

现在试试吧！GUI 也已经修复好了！🚀


