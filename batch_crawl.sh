#!/bin/bash
# 批量爬取 RapidAPI 脚本（Linux/Mac）

set -e

# 配置
URLS_FILE="${1:-rapidapi_urls_example.txt}"
DELAY="${2:-20}"

echo "🚀 开始批量爬取 RapidAPI"
echo "📝 URL 文件: $URLS_FILE"
echo "⏱️  延迟: $DELAY 秒"
echo ""

# 运行批量爬取
python batch_rapidapi.py "$URLS_FILE" \
  --use-selenium \
  --delay "$DELAY" \
  --retry 3 \
  --transport stdio

echo ""
echo "✅ 批量爬取完成！"
echo "📁 查看结果: generated_mcps/"

