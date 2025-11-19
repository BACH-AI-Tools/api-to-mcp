"""
RapidAPI 辅助工具 - 帮助从 RapidAPI 获取 OpenAPI 规范
"""
import requests
import json
import re
from typing import Optional, Dict, Any
from urllib.parse import urlparse


class RapidAPIHelper:
    """RapidAPI 辅助工具"""
    
    @staticmethod
    def extract_api_info_from_url(rapidapi_url: str) -> Optional[Dict[str, str]]:
        """
        从 RapidAPI URL 提取 API 信息
        
        例如: https://rapidapi.com/apidojo/api/yahoo-finance1
        返回: {"provider": "apidojo", "api": "yahoo-finance1"}
        """
        # RapidAPI URL 格式: https://rapidapi.com/{provider}/api/{api-name}
        pattern = r'rapidapi\.com/([^/]+)/api/([^/?]+)'
        match = re.search(pattern, rapidapi_url)
        
        if match:
            return {
                "provider": match.group(1),
                "api": match.group(2)
            }
        return None
    
    @staticmethod
    def get_possible_spec_urls(rapidapi_url: str) -> list[str]:
        """
        获取可能的 OpenAPI 规范 URL
        
        RapidAPI 的 OpenAPI 规范通常在以下位置之一:
        1. https://rapidapi.com/apidojo/api/yahoo-finance1/specs (官方规范页面)
        2. API 端点页面的网络请求中
        3. 某些 API 提供商的直接链接
        """
        api_info = RapidAPIHelper.extract_api_info_from_url(rapidapi_url)
        if not api_info:
            return []
        
        provider = api_info["provider"]
        api_name = api_info["api"]
        
        possible_urls = [
            # 规范页面
            f"https://rapidapi.com/{provider}/api/{api_name}/specs",
            # 可能的直接 API 规范链接
            f"https://rapidapi.com/api/{provider}/{api_name}/openapi.json",
            f"https://rapidapi.com/api/{provider}/{api_name}/swagger.json",
            # V3 API 端点
            f"https://rapidapi.com/api/v3/apis/{provider}/{api_name}/specs",
        ]
        
        return possible_urls
    
    @staticmethod
    def fetch_from_rapidapi_page(rapidapi_url: str, api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        尝试从 RapidAPI 页面获取 OpenAPI 规范
        
        方法:
        1. 访问 specs 页面
        2. 尝试从页面 HTML 中提取 OpenAPI 数据
        3. 尝试可能的 API 端点
        """
        api_info = RapidAPIHelper.extract_api_info_from_url(rapidapi_url)
        if not api_info:
            return None
        
        headers = {}
        if api_key:
            headers['X-RapidAPI-Key'] = api_key
        
        # 尝试 specs 页面
        specs_url = f"https://rapidapi.com/{api_info['provider']}/api/{api_info['api']}/specs"
        
        try:
            response = requests.get(specs_url, headers=headers, timeout=10)
            
            # 尝试从 HTML 中提取 OpenAPI 数据
            # RapidAPI 通常在页面的 JavaScript 中嵌入 OpenAPI 规范
            html = response.text
            
            # 查找可能的 JSON 数据
            # 方法1: 查找 window.__INITIAL_STATE__ 或类似的全局变量
            patterns = [
                r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
                r'openapi["\']?\s*:\s*({.*?})',
                r'swagger["\']?\s*:\s*({.*?})',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, html, re.DOTALL)
                if match:
                    try:
                        data = json.loads(match.group(1))
                        return data
                    except:
                        continue
            
        except Exception as e:
            print(f"尝试从 specs 页面获取失败: {e}")
        
        # 尝试其他可能的 URL
        for url in RapidAPIHelper.get_possible_spec_urls(rapidapi_url):
            try:
                response = requests.get(url, headers=headers, timeout=10, verify=False)
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if 'openapi' in data or 'swagger' in data:
                            return data
                    except:
                        continue
            except:
                continue
        
        return None
    
    @staticmethod
    def generate_instructions(rapidapi_url: str) -> str:
        """
        生成获取 OpenAPI 规范的说明
        """
        api_info = RapidAPIHelper.extract_api_info_from_url(rapidapi_url)
        if not api_info:
            return "❌ 无法解析 RapidAPI URL"
        
        provider = api_info["provider"]
        api_name = api_info["api"]
        
        instructions = f"""
# 📋 从 RapidAPI 获取 OpenAPI 规范

**API**: {provider}/{api_name}

## 🔍 方法 1: 手动下载（推荐）

1. 访问 API 页面的 **Endpoints** 标签
2. 打开浏览器开发者工具 (F12)
3. 切换到 **Network** (网络) 标签
4. 刷新页面
5. 在网络请求中查找包含 "spec" 或 "openapi" 的请求
6. 找到 OpenAPI 规范的 JSON 响应
7. 复制 JSON 内容并保存为文件
8. 使用命令转换:
   ```bash
   api-to-mcp convert downloaded-spec.json -n {api_name}
   ```

## 🌐 方法 2: 检查规范页面

访问: https://rapidapi.com/{provider}/api/{api_name}/specs

查看页面源代码 (Ctrl+U)，搜索 "openapi" 或 "swagger"

## 🔧 方法 3: 联系 API 提供商

有些 RapidAPI 的 API 提供商会在:
- API 描述中提供 OpenAPI 规范链接
- GitHub 仓库中提供
- 官方文档中提供

## 💡 方法 4: 使用我们的辅助工具

```python
from api_to_mcp.platforms.rapidapi_helper import RapidAPIHelper

# 尝试自动获取
spec = RapidAPIHelper.fetch_from_rapidapi_page(
    "{rapidapi_url}",
    api_key="your-rapidapi-key"  # 可选
)

if spec:
    # 保存并转换
    import json
    with open('spec.json', 'w') as f:
        json.dump(spec, f)
```

## 📝 常见问题

**Q: 为什么 RapidAPI 不直接提供下载链接？**
A: RapidAPI 主要是一个 API 市场平台，专注于 API 调用而不是规范下载。OpenAPI 规范通常嵌入在页面的 JavaScript 数据中。

**Q: 有没有更简单的方法？**
A: 最简单的方法是询问 API 提供商是否有公开的 OpenAPI 规范链接。

## 🎯 测试示例

如果您有 RapidAPI Key，可以尝试:

```bash
# 使用我们的工具尝试自动获取
python -c "
from api_to_mcp.platforms.rapidapi_helper import RapidAPIHelper
import json

spec = RapidAPIHelper.fetch_from_rapidapi_page(
    '{rapidapi_url}',
    api_key='YOUR_KEY'
)

if spec:
    with open('rapidapi_spec.json', 'w') as f:
        json.dump(spec, f, indent=2)
    print('✅ 成功获取规范！')
else:
    print('❌ 无法自动获取，请使用手动方法')
"

# 然后转换
api-to-mcp convert rapidapi_spec.json -n {api_name}
```
"""
        
        return instructions


def get_rapidapi_help(rapidapi_url: str):
    """获取 RapidAPI 帮助信息"""
    helper = RapidAPIHelper()
    print(helper.generate_instructions(rapidapi_url))


