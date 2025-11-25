# 🎯 RapidAPI 完整转换指南

## 通用流程：任何 RapidAPI → 完整 MCP

### 第1步：自动提取端点 ✅

```powershell
# 设置编码（避免emoji显示问题）
$env:PYTHONIOENCODING="utf-8"

# 自动提取（适用于任何RapidAPI）
api-to-mcp rapidapi <RapidAPI-URL> -n <自定义名称> --no-enhance

# 示例：
api-to-mcp rapidapi https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch -n jsearch --no-enhance
```

**自动提取内容：**
- ✅ API 名称和描述
- ✅ 端点列表（路径、方法、名称、描述）
- ✅ Base URL
- ✅ 生成基础 OpenAPI 文件：`rapidapi_<name>_auto.json`

### 第2步：补充参数信息 📝

#### 方法A：使用交互式工具（推荐）⭐⭐⭐

```powershell
# 使用我们的参数补充工具
python add_rapidapi_params.py rapidapi_jsearch_auto.json

# 按提示操作：
# 1. 选择要添加参数的端点
# 2. 从 RapidAPI 页面复制参数信息
# 3. 逐个输入参数
# 4. 自动保存为 rapidapi_jsearch_auto_with_params.json
```

**从 RapidAPI 获取参数信息：**
1. 在 RapidAPI 页面点击端点（如 "Job Search"）
2. 查看 **Params(4)** 标签
3. 复制每个参数的信息：
   - 名称（如 `query`, `page`）
   - 类型（String, Integer, Boolean）
   - 是否必需（required）
   - 描述
   - 默认值（如果有）

#### 方法B：直接编辑 JSON 文件

```powershell
# 用编辑器打开
code rapidapi_jsearch_auto.json

# 或
notepad rapidapi_jsearch_auto.json
```

**添加参数示例：**

```json
{
  "paths": {
    "/search": {
      "get": {
        "summary": "Job Search",
        "parameters": [
          {
            "name": "query",
            "in": "query",
            "required": true,
            "description": "Search query (e.g. 'Python developer in NYC')",
            "schema": {
              "type": "string"
            }
          },
          {
            "name": "page",
            "in": "query",
            "required": false,
            "description": "Page number",
            "schema": {
              "type": "integer",
              "default": 1
            }
          },
          {
            "name": "num_pages",
            "in": "query",
            "required": false,
            "description": "Number of pages to return (1-20)",
            "schema": {
              "type": "integer",
              "default": 1,
              "minimum": 1,
              "maximum": 20
            }
          }
        ]
      }
    },
    "/job-details": {
      "get": {
        "summary": "Job Details",
        "parameters": [
          {
            "name": "job_id",
            "in": "query",
            "required": true,
            "description": "Job ID from search results",
            "schema": {
              "type": "string"
            }
          },
          {
            "name": "country",
            "in": "query",
            "required": false,
            "description": "Country code (e.g. 'us')",
            "schema": {
              "type": "string",
              "default": "us"
            }
          }
        ]
      }
    }
  }
}
```

### 第3步：重新生成 MCP 🔨

```powershell
# 使用补充了参数的 OpenAPI 文件
api-to-mcp convert rapidapi_jsearch_auto_with_params.json -n jsearch

# 或直接使用编辑后的原文件
api-to-mcp convert rapidapi_jsearch_auto.json -n jsearch
```

### 第4步：测试和运行 🚀

```powershell
# 测试
api-to-mcp test generated_mcps/jsearch

# 运行
cd generated_mcps/jsearch
$env:API_KEY="你的RapidAPI-Key"
python server.py
```

## 📋 完整示例：JSearch API

### 1. 自动提取

```powershell
$env:PYTHONIOENCODING="utf-8"
api-to-mcp rapidapi https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch -n jsearch --no-enhance
```

**输出：**
```
✅ 提取到 4 个端点:
   • GET /search: Job Search
   • GET /job-details: Job Details
   • GET /estimated-salary: Job Salary
   • GET /company-job-salary: Company Job Salary
   
📁 保存到: rapidapi_jsearch_auto.json
```

### 2. 补充参数

```powershell
python add_rapidapi_params.py rapidapi_jsearch_auto.json
```

**交互示例：**
```
📍 现有端点:
   1. GET /search - Job Search
      当前参数数量: 0
   2. GET /job-details - Job Details
      当前参数数量: 0
   ...

选择要添加参数的端点编号: 1

📝 为 GET /search 添加参数
------------------------------------------------------------

  参数名称: query
  query 类型: string
  query 必需？ (y/n): y
  query 描述: Search query for jobs
  query 默认值: 
  query 位置: query
  ✅ 已添加参数: query

  参数名称: page
  page 类型: integer
  page 必需？ (y/n): n
  page 描述: Page number
  page 默认值: 1
  page 位置: query
  ✅ 已添加参数: page

  参数名称: [按回车结束]

✅ 端点 /search 现在有 2 个参数

选择要添加参数的端点编号: [按回车退出]

✅ 已保存到: rapidapi_jsearch_auto_with_params.json
```

### 3. 生成完整 MCP

```powershell
api-to-mcp convert rapidapi_jsearch_auto_with_params.json -n jsearch
```

### 4. 测试和使用

```powershell
cd generated_mcps/jsearch
$env:API_KEY="你的Key"
python server.py
```

## 🎯 响应参数

**注意**: 响应参数通常不需要手动定义！

FastMCP 的 `from_openapi()` 方法会：
- ✅ 自动处理 JSON 响应
- ✅ 返回完整的响应数据
- ✅ AI Agent 可以直接使用

如果需要定义响应格式（可选）：

```json
{
  "paths": {
    "/search": {
      "get": {
        "responses": {
          "200": {
            "description": "Successful response",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "status": {"type": "string"},
                    "request_id": {"type": "string"},
                    "data": {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "properties": {
                          "job_id": {"type": "string"},
                          "job_title": {"type": "string"},
                          "employer_name": {"type": "string"}
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

## 🔧 快速参考

### 参数类型映射

| RapidAPI 显示 | OpenAPI type |
|--------------|--------------|
| String | string |
| Integer | integer |
| Boolean | boolean |
| Number | number |
| Array | array |
| Object | object |

### 参数位置

| 位置 | 说明 | OpenAPI "in" |
|------|------|--------------|
| Query Params | URL查询参数 | query |
| Path Params | URL路径参数 | path |
| Header Params | HTTP头 | header |
| Body | 请求体 | body (需要用 requestBody) |

### 完整参数模板

```json
{
  "name": "参数名",
  "in": "query",
  "required": true,
  "description": "参数描述",
  "schema": {
    "type": "string",
    "default": "默认值",
    "enum": ["选项1", "选项2"],
    "minimum": 1,
    "maximum": 100
  }
}
```

## 💡 实用技巧

### 技巧1：批量从 curl 提取参数

从 RapidAPI 的 curl 示例中：
```bash
curl --url 'https://api.com/search?query=test&page=1&limit=10'
```

提取参数：
- query (string, required)
- page (integer, optional)  
- limit (integer, optional)

### 技巧2：使用浏览器开发者工具

1. F12 打开开发者工具
2. 点击 "Test Endpoint" 按钮
3. 查看 Network 标签中的请求
4. 复制实际使用的参数

### 技巧3：参考 API 文档

大多数 RapidAPI 的 API 都有文档链接，查找：
- API 文档
- GitHub 仓库
- 官方网站

## 🎉 总结

### 完全自动化
- ✅ 端点提取：100% 自动
- ✅ 基础结构：100% 自动
- ✅ MCP 生成：100% 自动

### 需要2-5分钟手动操作
- 📝 参数补充：从 RapidAPI 页面复制即可

### 最终结果
- 🎯 完整功能的 MCP 服务器
- 🚀 可直接在 Claude Desktop 使用
- ✅ 支持所有 API 功能

---

**这就是最实用的通用方案！** 给我任何 RapidAPI URL，2-5 分钟内完成转换！🚀






