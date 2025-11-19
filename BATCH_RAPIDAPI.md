# 批量爬取 RapidAPI 工具

## 📝 简介

这个工具可以自动批量爬取多个 RapidAPI，生成对应的 MCP 服务器。非常适合晚上挂机批量处理！

## 🚀 快速开始

### 1. 准备 URL 列表文件

#### 方式 A: 纯文本格式（推荐，简单）

创建 `my_apis.txt`:

```txt
# 我要爬取的 RapidAPI 列表
https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
https://rapidapi.com/weatherapi/api/weatherapi-com
https://rapidapi.com/newscatcher-api-newscatcher-api-default/api/newscatcher

# 添加更多 API...
```

#### 方式 B: JSON 格式（可自定义名称）

创建 `my_apis.json`:

```json
[
  {
    "url": "https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch",
    "name": "job-search"
  },
  {
    "url": "https://rapidapi.com/weatherapi/api/weatherapi-com",
    "name": "weather"
  }
]
```

### 2. 运行批量爬取

```bash
# 基础爬取（快速，但参数可能不完整）
python batch_rapidapi.py my_apis.txt

# 使用 Selenium 深度爬取（慢，但完整）
python batch_rapidapi.py my_apis.txt --use-selenium

# 指定传输协议
python batch_rapidapi.py my_apis.txt --transport sse

# 自定义延迟（避免被封）
python batch_rapidapi.py my_apis.txt --delay 10

# 完整示例
python batch_rapidapi.py my_apis.txt \
  --use-selenium \
  --transport sse \
  --delay 10 \
  --retry 3
```

## 📊 参数说明

| 参数 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| `--output-dir` | `-o` | `generated_mcps` | 输出目录 |
| `--transport` | `-t` | `stdio` | 传输协议（stdio/sse/streamable-http） |
| `--use-selenium` | - | `False` | 使用 Selenium 深度爬取（提取完整参数） |
| `--delay` | `-d` | `5` | 每个 API 之间的延迟秒数 |
| `--retry` | `-r` | `3` | 失败重试次数 |
| `--start-from` | - | `0` | 从第 N 个 URL 开始（断点续传） |

## 💡 使用场景

### 场景 1: 晚上挂机批量爬取（推荐）

1. 准备好 URL 列表（50-100 个）
2. 使用 Selenium 深度爬取，延迟设置长一点：

```bash
# 预计耗时：100 个 API × 30 秒 = 50 分钟
python batch_rapidapi.py my_100_apis.txt \
  --use-selenium \
  --delay 30 \
  --retry 3
```

3. 第二天早上查看结果：
   - ✅ 成功生成的项目在 `generated_mcps/` 目录
   - 📄 详细日志在 `batch_rapidapi_YYYYMMDD_HHMMSS.log`
   - 📊 汇总报告在 `batch_report_YYYYMMDD_HHMMSS.json`

### 场景 2: 快速批量提取（测试）

只提取基础结构，不使用 Selenium：

```bash
# 预计耗时：100 个 API × 5 秒 = 8 分钟
python batch_rapidapi.py my_100_apis.txt --delay 5
```

### 场景 3: 断点续传

如果中途失败，可以从某个位置继续：

```bash
# 从第 50 个 URL 开始继续处理
python batch_rapidapi.py my_apis.txt --start-from 50 --use-selenium
```

## 📈 输出内容

### 1. 生成的 MCP 项目

```
generated_mcps/
├── jsearch/
│   ├── server.py
│   ├── pyproject.toml
│   ├── README.md (简体中文)
│   ├── README_EN.md (英文)
│   └── README_ZH-TW.md (繁体中文)
├── weather-api/
│   ├── server.py
│   └── ...
└── news-api/
    ├── server.py
    └── ...
```

### 2. 日志文件

`batch_rapidapi_20241119_220000.log`:

```
[2024-11-19 22:00:00] [INFO] ================================================================================
[2024-11-19 22:00:00] [INFO] 🚀 开始批量处理 RapidAPI
[2024-11-19 22:00:00] [INFO] 📊 总数: 10
[2024-11-19 22:00:00] [INFO] 🔧 传输协议: stdio
[2024-11-19 22:00:00] [INFO] 🌐 使用 Selenium: 是
[2024-11-19 22:00:00] [INFO] ================================================================================
[2024-11-19 22:00:05] [INFO] 📍 [1/10] 处理中...
[2024-11-19 22:00:05] [INFO]    URL: https://rapidapi.com/...
[2024-11-19 22:00:35] [INFO] ✅ 成功: https://rapidapi.com/...
...
```

### 3. 汇总报告

`batch_report_20241119_220000.json`:

```json
{
  "total": 10,
  "success": 8,
  "failed": 2,
  "results": [
    {
      "url": "https://...",
      "name": "jsearch",
      "status": "success",
      "output_dir": "generated_mcps/jsearch",
      "tools_count": 4
    },
    {
      "url": "https://...",
      "name": null,
      "status": "failed",
      "error": "Connection timeout"
    }
  ]
}
```

## ⚠️ 注意事项

### 1. 爬取速度建议

- **基础爬取**：5-10 秒延迟（每小时可处理 360-720 个）
- **Selenium 爬取**：20-30 秒延迟（每小时可处理 120-180 个）
- **建议**：晚上挂机时设置较长延迟，避免被 RapidAPI 封 IP

### 2. Selenium 依赖

如果使用 `--use-selenium`，需要先安装：

```bash
pip install selenium webdriver-manager
```

### 3. 内存占用

- 基础爬取：内存占用小（~100MB）
- Selenium 爬取：每个浏览器实例约 200-300MB
- 建议：处理大量 API 时，分批进行

### 4. 断点续传

如果中途失败或中断：

```bash
# 从第 50 个 URL 继续
python batch_rapidapi.py my_apis.txt --start-from 50
```

## 🎯 实战示例

### 示例 1: 爬取 Top 100 RapidAPI

```bash
# 1. 准备 URL 列表（手动或爬虫获取）
cat > top_100_apis.txt << EOF
https://rapidapi.com/api-1
https://rapidapi.com/api-2
...（共 100 个）
EOF

# 2. 晚上 10 点开始爬取
python batch_rapidapi.py top_100_apis.txt \
  --use-selenium \
  --delay 20 \
  --retry 3 \
  --output-dir my_mcp_collection

# 3. 预计第二天早上 6 点完成（8 小时）
# 100 个 API × 30 秒/个 = 50 分钟 + 重试时间
```

### 示例 2: 分类批量爬取

```bash
# 爬取所有 Jobs 相关的 API
python batch_rapidapi.py jobs_apis.txt --use-selenium --delay 15

# 爬取所有 Finance 相关的 API
python batch_rapidapi.py finance_apis.txt --use-selenium --delay 15

# 爬取所有 AI 相关的 API
python batch_rapidapi.py ai_apis.txt --use-selenium --delay 15
```

## 📦 批量发布到 PyPI

爬取完成后，可以批量发布：

```bash
#!/bin/bash
# publish_all.sh

cd generated_mcps

for dir in */; do
  cd "$dir"
  echo "🚀 发布: $dir"
  
  # 清理
  rm -rf dist build *.egg-info
  
  # 构建
  python -m build
  
  # 上传
  twine upload dist/*
  
  cd ..
  
  # 延迟避免 PyPI 限流
  sleep 5
done
```

## 🔍 查看处理结果

```bash
# 查看日志
cat batch_rapidapi_*.log

# 查看报告
cat batch_report_*.json | jq .

# 统计成功数量
grep "✅ 成功" batch_rapidapi_*.log | wc -l

# 查看失败的 API
grep "❌ 失败" batch_rapidapi_*.log
```

## 🛠️ 故障排查

### 问题 1: 大量失败

**可能原因**：
- 延迟太短，被 RapidAPI 限流
- 网络不稳定

**解决方案**：
```bash
# 增加延迟到 30-60 秒
python batch_rapidapi.py urls.txt --delay 60
```

### 问题 2: Selenium 崩溃

**可能原因**：
- ChromeDriver 版本不匹配
- 内存不足

**解决方案**：
```bash
# 不使用 Selenium（生成基础结构）
python batch_rapidapi.py urls.txt --delay 5

# 或分批处理（每批 20 个）
python batch_rapidapi.py urls.txt --start-from 0 --use-selenium
python batch_rapidapi.py urls.txt --start-from 20 --use-selenium
python batch_rapidapi.py urls.txt --start-from 40 --use-selenium
```

### 问题 3: 部分 API 爬取失败

查看失败原因：

```bash
# 查看日志中的错误
grep "ERROR" batch_rapidapi_*.log

# 手动重试失败的 API
python batch_rapidapi.py failed_urls.txt --retry 5
```

## 📚 高级用法

### 自定义包名前缀

编辑 `src/api_to_mcp/generator/mcp_generator.py` 第 15 行：

```python
def __init__(self, output_dir: str = "generated_mcps", package_prefix: str = "your-prefix"):
```

### 自定义 EMCP 引流话术

编辑 `src/api_to_mcp/generator/mcp_generator.py` 的 `_get_default_emcp_promotion()` 方法。

---

## 💪 开始批量爬取！

```bash
# 1. 准备 URL 列表
nano my_apis.txt

# 2. 开始爬取
python batch_rapidapi.py my_apis.txt --use-selenium --delay 20

# 3. 晚上挂机，第二天早上收获一堆 MCP 项目！
```

🎉 祝你批量爬取成功！

