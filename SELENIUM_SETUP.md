# 🌐 Selenium 完全自动化设置指南

使用 Selenium 可以实现 **100% 自动提取** RapidAPI 的参数和响应！

## 📦 安装步骤

### 步骤1: 安装 Selenium

```bash
pip install selenium
```

### 步骤2: 安装 ChromeDriver

#### Windows:

**方法A: 使用 Chocolatey（推荐）**
```powershell
choco install chromedriver
```

**方法B: 手动安装**
1. 访问: https://chromedriver.chromium.org/downloads
2. 下载与你的 Chrome 版本匹配的 ChromeDriver
3. 解压并将 `chromedriver.exe` 放到 PATH 中（如 `C:\Windows\System32`）

#### 检查 Chrome 版本:
```powershell
# 打开 Chrome 浏览器
# 访问: chrome://version/
# 查看版本号（如 120.0.6099.109）
```

#### macOS:
```bash
brew install chromedriver
```

#### Linux:
```bash
sudo apt-get install chromium-chromedriver
```

### 步骤3: 验证安装

```bash
# 测试 Selenium
python -c "from selenium import webdriver; print('Selenium OK')"

# 测试 ChromeDriver
chromedriver --version
```

### 步骤4: 取消注释 requirements.txt

编辑 `requirements.txt`，取消最后一行的注释：

```txt
# 之前:
# selenium>=4.15.0

# 之后:
selenium>=4.15.0
```

然后重新安装：
```bash
pip install -r requirements.txt
```

## 🚀 使用 Selenium 自动提取

### 基本用法

```bash
# 设置编码
$env:PYTHONIOENCODING="utf-8"

# 使用 Selenium（自动提取参数和响应）
api-to-mcp rapidapi <RapidAPI-URL> -n <name> --use-selenium
```

### 示例：JSearch API

```bash
$env:PYTHONIOENCODING="utf-8"
api-to-mcp rapidapi https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch -n jsearch --use-selenium --no-enhance
```

**会自动：**
1. ✅ 访问主页面，提取端点列表
2. ✅ 逐个访问端点详情页
3. ✅ 等待 JavaScript 渲染完成
4. ✅ 提取所有参数（名称、类型、必需、枚举、默认值）
5. ✅ 切换到 Example Responses 标签
6. ✅ 提取响应 Schema 或从示例推断
7. ✅ 生成完整的 OpenAPI JSON
8. ✅ 生成 MCP 服务器

## 📊 Selenium vs 半自动

| 特性 | Selenium | 半自动工具 |
|------|----------|-----------|
| 端点提取 | ✅ 100% | ✅ 100% |
| 参数提取 | ✅ 100% | 📝 2分钟手动 |
| 响应提取 | ✅ 100% | ✅ 自动 |
| 速度 | 🐢 2-3分钟 | ⚡ 30秒+2分钟 |
| 依赖 | Chrome + ChromeDriver | 无 |
| 稳定性 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 维护 | 需要 | 不需要 |

## 🔧 故障排查

### 问题1: ChromeDriver 版本不匹配

**错误：**
```
SessionNotCreatedException: session not created: This version of ChromeDriver only supports Chrome version XX
```

**解决：**
1. 检查 Chrome 版本: `chrome://version/`
2. 下载匹配的 ChromeDriver
3. 或使用 webdriver-manager: `pip install webdriver-manager`

### 问题2: ChromeDriver 不在 PATH

**错误：**
```
WebDriverException: 'chromedriver' executable needs to be in PATH
```

**解决：**
```powershell
# 添加到 PATH 或指定路径
$env:PATH += ";C:\path\to\chromedriver"
```

### 问题3: 页面加载超时

**解决：**
增加等待时间或使用显式等待。

### 问题4: 找不到元素

这是最常见的问题。RapidAPI 可能更新了页面结构。

**解决：**
需要更新 DOM 选择器。

## 💡 优化建议

### 1. 使用 webdriver-manager（自动管理驱动）

```bash
pip install webdriver-manager
```

然后修改代码：
```python
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
```

### 2. 无头模式（不显示浏览器）

```bash
# 默认就是无头模式
api-to-mcp rapidapi <URL> --use-selenium
```

### 3. 显示浏览器（调试时）

修改代码中的 `headless=True` 为 `headless=False`

## 🎯 完整示例

### 从零开始使用 Selenium

```bash
# 1. 安装依赖
pip install selenium webdriver-manager

# 2. 测试
python -c "from selenium import webdriver; from webdriver_manager.chrome import ChromeDriverManager; from selenium.webdriver.chrome.service import Service; driver = webdriver.Chrome(service=Service(ChromeDriverManager().install())); driver.quit(); print('OK')"

# 3. 使用
$env:PYTHONIOENCODING="utf-8"
api-to-mcp rapidapi https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch -n jsearch --use-selenium

# 4. 查看结果
type rapidapi_jsearch_auto.json
# 应该包含完整的 parameters 和 responses

# 5. 生成 MCP
api-to-mcp convert rapidapi_jsearch_auto.json -n jsearch

# 6. 运行
cd generated_mcps/jsearch
python server.py
```

## 📝 注意事项

1. **速度**: Selenium 会慢一些（每个端点2-3秒）
2. **稳定性**: 依赖浏览器和网络
3. **维护**: RapidAPI 更新页面结构时需要调整
4. **隐私**: 使用真实浏览器，注意 cookies 等

## 🎉 预期效果

使用 Selenium 后，生成的 JSON 应该是：

```json
{
  "paths": {
    "/estimated-salary": {
      "get": {
        "parameters": [
          {
            "name": "job_title",
            "in": "query",
            "required": true,
            "description": "Job title for salary estimation",
            "schema": {"type": "string"}
          },
          {
            "name": "location",
            "in": "query",
            "required": true,
            "description": "Free-text location",
            "schema": {"type": "string"}
          },
          {
            "name": "location_type",
            "in": "query",
            "required": false,
            "description": "Location type",
            "schema": {
              "type": "string",
              "enum": ["ANY", "CITY", "STATE", "COUNTRY"],
              "default": "ANY"
            }
          }
        ],
        "responses": {
          "200": {
            "schema": {
              "type": "object",
              "properties": {
                "status": {"type": "string"},
                "request_id": {"type": "string"},
                "parameters": {"type": "object"},
                "data": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "location": {"type": "string"},
                      "job_title": {"type": "string"},
                      "min_salary": {"type": "number"},
                      "max_salary": {"type": "number"}
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

**完整、准确、可用！** 🎉

---

现在开始安装 Selenium，然后测试吧！
