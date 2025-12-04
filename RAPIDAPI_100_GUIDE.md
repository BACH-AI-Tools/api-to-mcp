# 🚀 RapidAPI 批量转 MCP 完整指南

自动将 100 个 RapidAPI 转换为 MCP 服务器的完整解决方案。

## 📋 方案概述

| 阶段 | 工具 | 功能 | 预计时间 |
|------|------|------|----------|
| 1️⃣ 发现 | `rapidapi_discovery.py` | 自动收集 500+ API 候选列表 | 1-2 小时 |
| 2️⃣ 订阅 | `rapidapi_subscriber.py` | 智能订阅 Free 计划 | 4-8 小时（挂机） |
| 3️⃣ 测试 | `rapidapi_tester.py` | 验证端点可用性 | 2-4 小时 |
| 4️⃣ 生成 | `batch_rapidapi.py` | 批量生成 MCP 项目 | 2-4 小时 |

**总计**：约 10-18 小时（大部分可挂机运行）

---

## 🛠️ 环境准备

### 1. 安装依赖

```bash
# 安装 Playwright（浏览器自动化）
pip install playwright
playwright install chromium

# 安装其他依赖
pip install httpx click beautifulsoup4

# 可选：AI 辅助（GPT-4 Vision 分析定价页）
pip install openai
```

### 2. 配置环境变量

```bash
# RapidAPI Key（必需，用于测试和调用 API）
export RAPIDAPI_KEY="your_rapidapi_key_here"

# 可选：AI 辅助分析定价页（二选一）

# 方式 A：Azure OpenAI（推荐）
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_API_KEY="your_azure_key_here"
export AZURE_OPENAI_DEPLOYMENT="gpt-4o"  # 你的部署名称

# 方式 B：OpenAI
export OPENAI_API_KEY="your_openai_key_here"
```

### 3. 获取 RapidAPI Key

1. 登录 https://rapidapi.com
2. 进入 **Dashboard** → **Developer Settings**
3. 找到或创建 **Application**
4. 复制 **API Key**

---

## 🚀 快速开始（一键运行）

```bash
# 完整流程（推荐晚上挂机）
python rapidapi_batch_100.py --target 100

# 首次运行需要先手动登录 RapidAPI
# 会提示你打开浏览器并登录
```

---

## 📖 详细步骤（分步运行）

### 阶段 1️⃣：API 发现

```bash
# 发现 500 个 API（考虑到筛选损耗，多发现一些）
python rapidapi_discovery.py --category all --limit 500

# 只发现特定分类
python rapidapi_discovery.py --category "AI,Data,Finance" --limit 200

# 显示浏览器（调试用）
python rapidapi_discovery.py --no-headless --limit 50
```

**输出文件**：
- `discovered_apis.json` - 完整 API 信息
- `discovered_apis.txt` - URL 列表

### 阶段 2️⃣：智能订阅

```bash
# 第一次运行（手动登录）
python rapidapi_subscriber.py discovered_apis.json --login --no-headless

# 后续运行（使用保存的 Cookie）
python rapidapi_subscriber.py discovered_apis.json

# 断点续传（从第 50 个开始）
python rapidapi_subscriber.py discovered_apis.json --start-from 50

# 使用 AI 辅助分析定价页（需要 OPENAI_API_KEY）
python rapidapi_subscriber.py discovered_apis.json --use-ai
```

**订阅逻辑**：

| 情况 | 处理方式 |
|------|----------|
| ✅ 有 Free 计划，无需信用卡 | 自动订阅 |
| ❌ 无 Free 计划 | 跳过 |
| ❌ Free 计划需要信用卡 | 跳过 |
| ❌ 需要申请/审批 | 跳过 |
| ✅ 已订阅 | 记录为成功 |

**输出文件**：
- `rapidapi_subscription_state.json` - 订阅状态
- `subscribed_apis.txt` - 成功订阅的 URL 列表
- `rapidapi_cookies.json` - 登录 Cookie（下次使用）

### 阶段 3️⃣：端点测试

```bash
# 测试订阅的 API
python rapidapi_tester.py subscribed_apis.txt

# 指定 API Key
python rapidapi_tester.py subscribed_apis.txt --api-key YOUR_KEY

# 限制测试数量
python rapidapi_tester.py subscribed_apis.txt --limit 50
```

**测试逻辑**：
- 自动提取 API 端点
- 发送测试请求
- 验证响应状态码

**输出文件**：
- `test_results_*.json` - 完整测试结果
- `tested_apis.txt` - 测试通过的 URL 列表

### 阶段 4️⃣：生成 MCP

```bash
# 批量生成 MCP（使用 Selenium 完整提取参数）
python batch_rapidapi.py tested_apis.txt --use-selenium --delay 20

# 快速生成（不使用 Selenium）
python batch_rapidapi.py tested_apis.txt --delay 5

# 指定传输协议
python batch_rapidapi.py tested_apis.txt --transport sse
```

**输出**：
```
generated_mcps/
├── api_name_1/
│   ├── server.py
│   ├── openapi.json
│   ├── pyproject.toml
│   ├── README.md
│   ├── README_EN.md
│   └── README_ZH-TW.md
├── api_name_2/
│   └── ...
└── ...（100 个 MCP 项目）
```

---

## ⚙️ 高级配置

### 使用 AI 辅助（推荐）

AI 可以帮助分析复杂的定价页面，支持 **Azure OpenAI** 和 **OpenAI**：

```bash
# 方式 A：Azure OpenAI（推荐）
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
export AZURE_OPENAI_API_KEY="your_key"
export AZURE_OPENAI_DEPLOYMENT="gpt-4o"  # 你的模型部署名

# 方式 B：OpenAI
export OPENAI_API_KEY="your_key"

# 启用 AI 辅助
python rapidapi_subscriber.py apis.json --use-ai
```

**AI 功能**：
- 分析定价页面截图（使用 GPT-4 Vision）
- 识别隐藏的免费计划
- 判断是否需要信用卡
- 自动处理复杂的定价结构

### 断点续传

如果中途失败或中断：

```bash
# 从第 N 个 API 继续
python rapidapi_subscriber.py apis.json --start-from 50
python rapidapi_tester.py apis.txt --start-from 30
python batch_rapidapi.py apis.txt --start-from 20
```

### 分批处理

建议分批处理以避免问题：

```bash
# 每批 30 个
python rapidapi_subscriber.py apis.json --limit 30 --start-from 0
python rapidapi_subscriber.py apis.json --limit 30 --start-from 30
python rapidapi_subscriber.py apis.json --limit 30 --start-from 60
```

---

## 🎯 最佳实践

### 1. 时间安排

```
第一天晚上：
1. 运行 API 发现（1-2 小时）
2. 手动登录 RapidAPI
3. 启动订阅流程，挂机过夜

第二天早上：
4. 查看订阅结果
5. 运行端点测试（2-4 小时）

第二天下午/晚上：
6. 启动 MCP 生成，挂机过夜

第三天早上：
7. 收获 100 个 MCP 项目！
```

### 2. 延迟设置

| 阶段 | 推荐延迟 | 原因 |
|------|----------|------|
| 发现 | 2-3 秒 | 避免被封 |
| 订阅 | 5-10 秒 | 页面交互需要时间 |
| 测试 | 3-5 秒 | 避免触发限流 |
| 生成 | 15-30 秒 | Selenium 需要加载完整页面 |

### 3. 监控进度

```bash
# 查看订阅状态
cat rapidapi_subscription_state.json | jq '.stats'

# 查看测试结果
cat test_results_*.json | jq '.stats'

# 统计已生成的 MCP
ls generated_mcps/ | wc -l
```

---

## 🔧 故障排查

### 问题 1: 登录失败

```bash
# 清除 Cookie 重新登录
rm rapidapi_cookies.json
python rapidapi_subscriber.py apis.json --login --no-headless
```

### 问题 2: 订阅被限流

```bash
# 增加延迟
python rapidapi_subscriber.py apis.json --delay 15

# 分批处理
python rapidapi_subscriber.py apis.json --limit 20
```

### 问题 3: 端点测试全部失败

检查 API Key 是否正确：
```bash
# 测试 API Key
curl --request GET \
  --url "https://jsearch.p.rapidapi.com/search?query=python" \
  --header "X-RapidAPI-Key: YOUR_KEY" \
  --header "X-RapidAPI-Host: jsearch.p.rapidapi.com"
```

### 问题 4: Selenium 崩溃

```bash
# 更新 Playwright
playwright install chromium

# 不使用 Selenium（参数可能不完整）
python batch_rapidapi.py apis.txt --delay 5
```

---

## 📊 预期结果

从 500 个发现的 API 中：

| 阶段 | 预期数量 | 比例 |
|------|----------|------|
| 发现 | 500 | 100% |
| 有 Free 计划 | ~200 | ~40% |
| 无需信用卡 | ~150 | ~30% |
| 测试通过 | ~120 | ~24% |
| 最终生成 | 100+ | ~20% |

---

## 🎉 完成后

### 验证生成的 MCP

```bash
# 进入某个 MCP 项目
cd generated_mcps/some_api

# 测试运行
export API_KEY="your_rapidapi_key"
python server.py
```

### 批量发布到 PyPI

```bash
# 发布脚本
for dir in generated_mcps/*/; do
  cd "$dir"
  python -m build
  twine upload dist/*
  cd ../..
  sleep 5
done
```

### 集成到 EMCP 平台

生成的 MCP 已包含 EMCP 平台引流内容，可直接用于：
- Claude Desktop
- Cursor
- 其他 MCP 客户端

---

## 🔷 使用 Azure OpenAI

如果你有 Azure OpenAI 资源，可以这样配置：

```bash
# 设置 Azure OpenAI 环境变量
export AZURE_OPENAI_ENDPOINT="https://你的资源名.openai.azure.com/"
export AZURE_OPENAI_API_KEY="你的Azure密钥"
export AZURE_OPENAI_DEPLOYMENT="gpt-4o"  # 或你部署的模型名称（如 gpt-4-vision）

# 启用 AI 辅助运行订阅
python rapidapi_subscriber.py discovered_apis.json --use-ai
```

**Azure OpenAI 优势**：
- 企业级稳定性和 SLA
- 更好的数据隐私保护
- 可能有更高的 API 配额
- 支持私有网络部署

**注意**：确保你的 Azure OpenAI 部署支持 Vision 功能（如 gpt-4o、gpt-4-vision-preview）。

---

## 📞 需要帮助？

如果遇到问题：

1. 查看日志文件：`batch_rapidapi_*.log`
2. 检查状态文件：`rapidapi_subscription_state.json`
3. 保存的 HTML 调试：`debug/` 目录

---

**祝你批量转换成功！** 🚀


