# 📘 RapidAPI 使用指南

RapidAPI 是全球最大的 API 市场，但它不直接提供 OpenAPI 规范下载链接。本指南说明如何从 RapidAPI 获取 API 规范。

## 🎯 快速开始

### 使用我们的辅助命令

```bash
# 获取帮助和自动尝试获取规范
api-to-mcp rapidapi-help https://rapidapi.com/apidojo/api/yahoo-finance1
```

这个命令会:
1. 显示详细的获取说明
2. 自动尝试获取 OpenAPI 规范
3. 如果成功，保存为 JSON 文件
4. 提供下一步转换命令

## 📋 手动方法（最可靠）

### 方法 1: 从浏览器网络请求获取 ⭐ 推荐

1. **访问 API 页面**
   - 打开你想要的 RapidAPI API 页面
   - 例如: https://rapidapi.com/apidojo/api/yahoo-finance1

2. **打开开发者工具**
   - Windows/Linux: 按 `F12` 或 `Ctrl + Shift + I`
   - macOS: 按 `Cmd + Option + I`

3. **查看网络请求**
   - 切换到 **Network** (网络) 标签
   - 刷新页面 (`F5` 或 `Ctrl + R`)

4. **查找 OpenAPI 规范**
   - 在请求列表中搜索 "spec" 或 "openapi"
   - 查找类似这些的请求:
     - `specs`
     - `openapi.json`
     - `swagger.json`
     - 包含 API 规范的 GraphQL 查询

5. **复制规范**
   - 点击找到的请求
   - 切换到 **Response** (响应) 标签
   - 复制 JSON 内容
   - 保存为 `api-spec.json`

6. **转换为 MCP**
   ```bash
   api-to-mcp convert api-spec.json -n your_api_name
   ```

### 方法 2: 查看页面源代码

1. **访问 Specs 页面**
   ```
   https://rapidapi.com/{provider}/api/{api-name}/specs
   ```

2. **查看源代码**
   - 右键点击页面 → "查看网页源代码"
   - 或按 `Ctrl + U` (Windows/Linux) / `Cmd + Option + U` (macOS)

3. **搜索规范**
   - 按 `Ctrl + F` 搜索 "openapi" 或 "swagger"
   - 查找 JavaScript 中嵌入的 JSON 数据
   - 常见位置:
     ```javascript
     window.__INITIAL_STATE__ = {...}
     ```

4. **提取并保存**
   - 复制 OpenAPI 规范的 JSON 部分
   - 保存为文件并转换

### 方法 3: 使用 RapidAPI Hub 的 API

某些 RapidAPI 提供了 API 来访问其规范:

```bash
# 如果 API 提供了规范端点
curl "https://rapidapi.com/api/v3/apis/{provider}/{api-name}/specs" \
  -H "X-RapidAPI-Key: YOUR_KEY" \
  > spec.json

# 转换
api-to-mcp convert spec.json -n your_api
```

### 方法 4: 联系 API 提供商

1. 查看 API 的 **About** 或 **Documentation** 部分
2. 检查是否有 GitHub 仓库链接
3. 在提供商的网站上查找 OpenAPI 规范
4. 直接联系提供商索取

## 💡 实用技巧

### 识别 OpenAPI 规范

有效的 OpenAPI 规范通常包含:

```json
{
  "openapi": "3.0.0",  // OpenAPI 3.x
  "info": {
    "title": "...",
    "version": "..."
  },
  "paths": {
    ...
  }
}
```

或 Swagger 2.0:

```json
{
  "swagger": "2.0",
  "info": {
    "title": "...",
    "version": "..."
  },
  "paths": {
    ...
  }
}
```

### 常见文件位置

RapidAPI 的 OpenAPI 规范可能在:

1. **页面嵌入数据**
   - `window.__INITIAL_STATE__`
   - `window.__NEXT_DATA__`
   - 内联 `<script>` 标签

2. **网络请求**
   - `/api/v3/apis/{id}/specs`
   - `/specs`
   - GraphQL 查询响应

3. **外部链接**
   - API 描述中的链接
   - GitHub 仓库
   - 提供商官网

## 🔧 使用我们的 Python 辅助工具

### 安装项目后

```python
from api_to_mcp.platforms.rapidapi_helper import RapidAPIHelper
import json

# 创建辅助工具
helper = RapidAPIHelper()

# 尝试自动获取
rapidapi_url = "https://rapidapi.com/apidojo/api/yahoo-finance1"
spec = helper.fetch_from_rapidapi_page(
    rapidapi_url,
    api_key="YOUR_RAPIDAPI_KEY"  # 可选
)

if spec:
    # 保存规范
    with open('spec.json', 'w', encoding='utf-8') as f:
        json.dump(spec, f, indent=2, ensure_ascii=False)
    
    print("✅ 成功获取规范!")
    print("下一步: api-to-mcp convert spec.json -n your_api")
else:
    print("❌ 无法自动获取，请使用手动方法")
    
    # 显示详细帮助
    print(helper.generate_instructions(rapidapi_url))
```

## 📝 完整示例

### 示例: Yahoo Finance API

```bash
# 1. 获取帮助
api-to-mcp rapidapi-help https://rapidapi.com/apidojo/api/yahoo-finance1

# 2. 如果自动获取成功
api-to-mcp convert rapidapi_yahoo-finance1_spec.json -n yahoo_finance

# 3. 如果需要手动:
# - 打开 https://rapidapi.com/apidojo/api/yahoo-finance1
# - F12 打开开发者工具
# - Network 标签 → 刷新页面
# - 搜索 "spec" 找到规范请求
# - 复制 JSON → 保存为 yahoo-finance-spec.json

# 4. 转换
api-to-mcp convert yahoo-finance-spec.json -n yahoo_finance

# 5. 测试
api-to-mcp test generated_mcps/yahoo_finance

# 6. 运行
cd generated_mcps/yahoo_finance
python server.py
```

## ❓ 常见问题

### Q: 为什么 RapidAPI 不提供直接下载？

**A**: RapidAPI 是一个 API 市场平台，主要功能是:
- 提供统一的 API 调用接口
- 处理认证和计费
- API 发现和文档

OpenAPI 规范主要用于内部文档展示，而不是供外部下载。

### Q: 有没有更简单的方法？

**A**: 最简单的方法依次是:
1. 使用我们的 `rapidapi-help` 命令自动获取
2. 从浏览器开发者工具的网络请求中复制
3. 联系 API 提供商索取规范

### Q: 自动获取为什么会失败？

**A**: 可能的原因:
- RapidAPI 更改了页面结构
- API 没有公开的规范端点
- 需要认证才能访问
- 规范嵌入在加密的数据中

这种情况下请使用手动方法。

### Q: 获取的规范不完整怎么办？

**A**: 
1. 检查是否获取了完整的 JSON
2. 尝试从不同的页面获取（Endpoints 页面 vs Specs 页面）
3. 手动补充缺失的端点信息
4. 联系 API 提供商

### Q: 可以批量获取多个 API 吗？

**A**: 可以，但建议逐个获取:

```bash
# 创建一个脚本
for url in \
    "https://rapidapi.com/provider1/api/api1" \
    "https://rapidapi.com/provider2/api/api2" \
    "https://rapidapi.com/provider3/api/api3"
do
    api-to-mcp rapidapi-help "$url"
    sleep 2  # 避免请求过快
done
```

## 🎯 最佳实践

1. **保存原始规范**: 总是保存从 RapidAPI 获取的原始规范，以便以后参考

2. **记录来源**: 在规范文件或 README 中记录:
   - RapidAPI URL
   - 获取日期
   - API 版本

3. **定期更新**: API 可能会更新，定期检查并重新生成 MCP 服务器

4. **测试所有端点**: 生成后测试所有关键端点确保正常工作

5. **遵守使用条款**: 确保你的使用符合 RapidAPI 和 API 提供商的条款

## 🔗 相关资源

- [RapidAPI 官网](https://rapidapi.com/)
- [OpenAPI 规范](https://spec.openapis.org/oas/latest.html)
- [本项目文档](README.md)
- [发布指南](PUBLISH_GUIDE.md)

## 🆘 需要帮助？

如果你在获取 RapidAPI 规范时遇到问题:

1. 运行 `api-to-mcp rapidapi-help <url>` 获取详细说明
2. 查看本指南的常见问题部分
3. 提交 Issue 到项目仓库，附上:
   - RapidAPI URL
   - 你尝试的方法
   - 遇到的具体错误

---

**祝你使用顺利！🚀**






