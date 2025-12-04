#!/usr/bin/env python3
"""
RapidAPI 端点测试工具

测试已订阅的 API 端点是否可用

使用方法：
    python rapidapi_tester.py subscribed_apis.txt
    python rapidapi_tester.py subscribed_apis.txt --api-key YOUR_KEY
"""
import json
import asyncio
import os
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import click
import httpx

try:
    from playwright.async_api import async_playwright, Page
except ImportError:
    print("⚠️  Playwright 未安装，将只使用 HTTP 测试")


class TestStatus(Enum):
    """测试状态"""
    PENDING = "pending"
    SUCCESS = "success"           # 测试成功
    PARTIAL = "partial"           # 部分端点成功
    AUTH_ERROR = "auth_error"     # 认证错误
    RATE_LIMITED = "rate_limited" # 被限流
    NOT_FOUND = "not_found"       # API 不存在
    TIMEOUT = "timeout"           # 超时
    ERROR = "error"               # 其他错误


@dataclass
class EndpointTestResult:
    """端点测试结果"""
    path: str
    method: str
    status_code: int = 0
    success: bool = False
    response_time_ms: float = 0
    error: str = ""


@dataclass
class APITestResult:
    """API 测试结果"""
    url: str
    name: str
    status: TestStatus
    base_url: str = ""
    total_endpoints: int = 0
    successful_endpoints: int = 0
    api_key_works: bool = False
    endpoints: List[EndpointTestResult] = None
    error: str = ""
    tested_at: str = ""
    
    def __post_init__(self):
        if self.endpoints is None:
            self.endpoints = []
    
    def to_dict(self):
        result = asdict(self)
        result["status"] = self.status.value
        result["endpoints"] = [asdict(e) for e in self.endpoints]
        return result


class RapidAPITester:
    """RapidAPI 端点测试器"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("RAPIDAPI_KEY") or os.getenv("API_KEY")
        self.results: List[APITestResult] = []
        
        if not self.api_key:
            print("⚠️  未设置 API Key，测试可能失败")
            print("   设置方法: export RAPIDAPI_KEY=your_key")
            print("   或使用: --api-key YOUR_KEY")
    
    async def extract_api_info(self, api_url: str) -> Tuple[str, str, List[Dict]]:
        """从 RapidAPI 页面提取 API 信息"""
        # 从 URL 提取 host
        pattern = r'rapidapi\.com/[^/]+/api/([^/?]+)'
        match = re.search(pattern, api_url)
        
        if not match:
            return "", "", []
        
        api_slug = match.group(1)
        base_url = f"https://{api_slug}.p.rapidapi.com"
        host = f"{api_slug}.p.rapidapi.com"
        
        # 获取端点列表
        endpoints = []
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    api_url,
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=30.0,
                    follow_redirects=True
                )
                
                html = response.text
                
                # 尝试从 __NEXT_DATA__ 提取端点
                next_data_match = re.search(
                    r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',
                    html, re.DOTALL
                )
                
                if next_data_match:
                    try:
                        data = json.loads(next_data_match.group(1))
                        # 深度搜索端点数据
                        endpoints = self._find_endpoints_in_data(data)
                    except:
                        pass
                
                # 如果没找到端点，创建默认测试端点
                if not endpoints:
                    # 从 HTML 中提取路径
                    path_matches = re.findall(r'["\'](/[a-z0-9/_-]+)["\']', html.lower())
                    unique_paths = list(set(p for p in path_matches if len(p) > 1 and len(p) < 50))[:5]
                    
                    for path in unique_paths:
                        endpoints.append({
                            "path": path,
                            "method": "GET"
                        })
                    
                    # 添加根路径
                    if not any(e["path"] == "/" for e in endpoints):
                        endpoints.insert(0, {"path": "/", "method": "GET"})
                
        except Exception as e:
            print(f"   ⚠️  提取端点失败: {e}")
            endpoints = [{"path": "/", "method": "GET"}]
        
        return base_url, host, endpoints
    
    def _find_endpoints_in_data(self, data: Any, depth: int = 0) -> List[Dict]:
        """在数据中递归查找端点"""
        if depth > 10:
            return []
        
        endpoints = []
        
        if isinstance(data, dict):
            # 检查是否是端点数据
            if "path" in data or "route" in data or "endpoint" in data:
                path = data.get("path") or data.get("route") or data.get("endpoint")
                method = data.get("method", "GET").upper()
                if path and isinstance(path, str):
                    endpoints.append({
                        "path": path,
                        "method": method,
                        "name": data.get("name", ""),
                        "parameters": data.get("parameters", [])
                    })
            
            # 检查端点列表
            for key in ["endpoints", "paths", "operations", "routes"]:
                if key in data and isinstance(data[key], (list, dict)):
                    if isinstance(data[key], list):
                        for item in data[key]:
                            endpoints.extend(self._find_endpoints_in_data(item, depth + 1))
                    else:
                        endpoints.extend(self._find_endpoints_in_data(data[key], depth + 1))
            
            # 递归搜索
            for value in data.values():
                if isinstance(value, (dict, list)):
                    endpoints.extend(self._find_endpoints_in_data(value, depth + 1))
                    
        elif isinstance(data, list):
            for item in data:
                endpoints.extend(self._find_endpoints_in_data(item, depth + 1))
        
        # 去重
        seen = set()
        unique = []
        for ep in endpoints:
            key = f"{ep.get('method', 'GET')}:{ep.get('path', '/')}"
            if key not in seen:
                seen.add(key)
                unique.append(ep)
        
        return unique
    
    async def test_endpoint(
        self, 
        base_url: str, 
        host: str, 
        endpoint: Dict,
        timeout: float = 10.0
    ) -> EndpointTestResult:
        """测试单个端点"""
        path = endpoint.get("path", "/")
        method = endpoint.get("method", "GET").upper()
        
        result = EndpointTestResult(
            path=path,
            method=method
        )
        
        url = f"{base_url}{path}"
        
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": host,
            "User-Agent": "Mozilla/5.0"
        }
        
        try:
            start_time = datetime.now()
            
            async with httpx.AsyncClient() as client:
                if method == "GET":
                    response = await client.get(url, headers=headers, timeout=timeout)
                elif method == "POST":
                    response = await client.post(url, headers=headers, json={}, timeout=timeout)
                else:
                    response = await client.request(method, url, headers=headers, timeout=timeout)
                
                elapsed = (datetime.now() - start_time).total_seconds() * 1000
                
                result.status_code = response.status_code
                result.response_time_ms = round(elapsed, 2)
                
                # 判断成功
                if response.status_code in [200, 201, 204]:
                    result.success = True
                elif response.status_code == 401:
                    result.error = "认证失败"
                elif response.status_code == 403:
                    result.error = "无权限"
                elif response.status_code == 429:
                    result.error = "请求过多"
                elif response.status_code == 404:
                    result.error = "端点不存在"
                else:
                    result.error = f"HTTP {response.status_code}"
                    
        except httpx.TimeoutException:
            result.error = "超时"
        except Exception as e:
            result.error = str(e)
        
        return result
    
    async def test_api(self, api_url: str, name: str = None) -> APITestResult:
        """测试单个 API"""
        if not name:
            name = api_url.split("/api/")[-1].split("?")[0]
        
        result = APITestResult(
            url=api_url,
            name=name,
            status=TestStatus.PENDING,
            tested_at=datetime.now().isoformat()
        )
        
        print(f"\n📍 测试: {name}")
        print(f"   URL: {api_url}")
        
        try:
            # 1. 提取 API 信息
            base_url, host, endpoints = await self.extract_api_info(api_url)
            
            if not base_url:
                result.status = TestStatus.NOT_FOUND
                result.error = "无法解析 API URL"
                print(f"   ❌ {result.error}")
                return result
            
            result.base_url = base_url
            result.total_endpoints = len(endpoints)
            
            print(f"   🌐 Base URL: {base_url}")
            print(f"   📍 端点数量: {len(endpoints)}")
            
            # 2. 测试端点
            for i, endpoint in enumerate(endpoints[:5]):  # 最多测试 5 个端点
                path = endpoint.get("path", "/")
                method = endpoint.get("method", "GET")
                
                print(f"   🔄 测试 [{i+1}/{min(len(endpoints), 5)}]: {method} {path}")
                
                ep_result = await self.test_endpoint(base_url, host, endpoint)
                result.endpoints.append(ep_result)
                
                if ep_result.success:
                    result.successful_endpoints += 1
                    print(f"      ✅ {ep_result.status_code} ({ep_result.response_time_ms}ms)")
                else:
                    print(f"      ❌ {ep_result.error}")
                
                # 短暂延迟避免限流
                await asyncio.sleep(0.5)
            
            # 3. 判断整体状态
            if result.successful_endpoints == result.total_endpoints:
                result.status = TestStatus.SUCCESS
                result.api_key_works = True
            elif result.successful_endpoints > 0:
                result.status = TestStatus.PARTIAL
                result.api_key_works = True
            elif any(e.status_code == 401 for e in result.endpoints):
                result.status = TestStatus.AUTH_ERROR
            elif any(e.status_code == 429 for e in result.endpoints):
                result.status = TestStatus.RATE_LIMITED
            elif any("超时" in (e.error or "") for e in result.endpoints):
                result.status = TestStatus.TIMEOUT
            else:
                result.status = TestStatus.ERROR
            
            print(f"   📊 结果: {result.successful_endpoints}/{len(result.endpoints)} 端点成功")
            
        except Exception as e:
            result.status = TestStatus.ERROR
            result.error = str(e)
            print(f"   ❌ 错误: {e}")
        
        return result
    
    async def run(
        self, 
        apis: List[Dict[str, Any]], 
        delay: int = 3,
        start_from: int = 0
    ):
        """运行测试"""
        print("\n" + "=" * 60)
        print(f"📊 开始测试 {len(apis)} 个 API")
        print("=" * 60)
        
        apis_to_test = apis[start_from:]
        
        for i, api in enumerate(apis_to_test):
            actual_index = start_from + i
            
            url = api.get("url", api) if isinstance(api, dict) else api
            name = api.get("name") if isinstance(api, dict) else None
            
            print(f"\n{'='*40}")
            print(f"📍 [{actual_index + 1}/{len(apis)}]")
            
            result = await self.test_api(url, name)
            self.results.append(result)
            
            # 延迟
            if i < len(apis_to_test) - 1:
                await asyncio.sleep(delay)
        
        # 保存结果
        self.save_results()
    
    def save_results(self):
        """保存测试结果"""
        # 完整结果
        full_results = {
            "tested_at": datetime.now().isoformat(),
            "total": len(self.results),
            "stats": {
                status.value: sum(1 for r in self.results if r.status == status)
                for status in TestStatus
            },
            "results": [r.to_dict() for r in self.results]
        }
        
        results_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        Path(results_file).write_text(
            json.dumps(full_results, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"\n💾 完整结果: {results_file}")
        
        # 成功的 API 列表（供 MCP 生成使用）
        successful = [
            r for r in self.results 
            if r.status in [TestStatus.SUCCESS, TestStatus.PARTIAL]
        ]
        
        if successful:
            success_file = "tested_apis.txt"
            with open(success_file, "w", encoding="utf-8") as f:
                f.write(f"# 测试通过的 API 列表 - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
                f.write(f"# 共 {len(successful)} 个\n\n")
                for r in successful:
                    f.write(f"{r.url}\n")
            
            print(f"✅ 测试通过列表: {success_file}")
            print(f"   共 {len(successful)} 个 API")
        
        # 统计
        print("\n" + "=" * 60)
        print("📊 测试统计")
        print("=" * 60)
        
        for status in TestStatus:
            count = sum(1 for r in self.results if r.status == status)
            if count > 0:
                emoji = {
                    "success": "✅",
                    "partial": "⚠️",
                    "auth_error": "🔐",
                    "rate_limited": "🚫",
                    "not_found": "❓",
                    "timeout": "⏱️",
                    "error": "❌",
                    "pending": "⏳"
                }.get(status.value, "❓")
                print(f"   {emoji} {status.value}: {count}")
        
        print("=" * 60)
        
        if successful:
            print(f"\n✅ 下一步：生成 MCP")
            print(f"   python batch_rapidapi.py tested_apis.txt --use-selenium")


@click.command()
@click.argument("apis_file", type=click.Path(exists=True))
@click.option("--api-key", "-k", default=None, help="RapidAPI Key")
@click.option("--delay", "-d", default=3, type=int, help="每个 API 之间的延迟")
@click.option("--start-from", default=0, type=int, help="从第 N 个开始")
@click.option("--limit", "-l", default=0, type=int, help="测试数量限制（0=全部）")
def main(apis_file: str, api_key: str, delay: int, start_from: int, limit: int):
    """
    RapidAPI 端点测试工具
    
    测试已订阅的 API 是否可用
    
    \b
    使用方法：
        python rapidapi_tester.py subscribed_apis.txt
        python rapidapi_tester.py subscribed_apis.txt --api-key YOUR_KEY
    """
    print("🚀 RapidAPI 端点测试工具")
    print("=" * 60)
    
    # 加载 API 列表
    content = Path(apis_file).read_text(encoding="utf-8")
    
    if apis_file.endswith(".json"):
        data = json.loads(content)
        if isinstance(data, dict) and "apis" in data:
            apis = data["apis"]
        elif isinstance(data, dict) and "results" in data:
            apis = [r["url"] for r in data["results"] if r.get("status") in ["subscribed", "already"]]
        elif isinstance(data, list):
            apis = data
        else:
            apis = [data]
    else:
        apis = []
        for line in content.split("\n"):
            line = line.strip()
            if line and not line.startswith("#") and line.startswith("http"):
                apis.append({"url": line})
    
    if limit > 0:
        apis = apis[:limit]
    
    print(f"📄 加载 {len(apis)} 个 API")
    print(f"🔑 API Key: {'已设置' if api_key or os.getenv('RAPIDAPI_KEY') else '未设置'}")
    print("=" * 60)
    
    async def run():
        tester = RapidAPITester(api_key=api_key)
        await tester.run(apis, delay=delay, start_from=start_from)
    
    asyncio.run(run())


if __name__ == "__main__":
    main()




