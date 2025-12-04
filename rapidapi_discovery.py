#!/usr/bin/env python3
"""
RapidAPI API 发现工具

自动从 RapidAPI 分类页面收集 API 列表
适合作为批量订阅和转换的第一步

使用方法：
    python rapidapi_discovery.py --category all --limit 500
    python rapidapi_discovery.py --category "Data,AI,Finance" --limit 200
"""
import json
import time
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import click

try:
    from playwright.async_api import async_playwright, Page, Browser
except ImportError:
    print("❌ 需要安装 Playwright: pip install playwright && playwright install chromium")
    exit(1)


# RapidAPI 分类列表
RAPIDAPI_CATEGORIES = [
    "Data", "Sports", "Finance", "Weather", "Travel", "Entertainment",
    "Food", "Music", "News", "Social", "Business", "eCommerce",
    "Health", "Education", "Gaming", "Logistics", "Communication",
    "Translation", "Reward", "SMS", "Email", "Search", "Tools",
    "Video", "Mapping", "Events", "Monitoring", "Database", "AI",
    "Machine Learning", "Text Analysis", "Image", "Audio", "Crypto",
]


class RapidAPIDiscovery:
    """RapidAPI API 发现器"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.discovered_apis: List[Dict[str, Any]] = []
        
    async def start_browser(self):
        """启动浏览器"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        print(f"🌐 浏览器已启动 (headless={self.headless})")
    
    async def close_browser(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
            print("🌐 浏览器已关闭")
    
    async def discover_category(self, category: str, page: Page, limit: int = 50) -> List[Dict[str, Any]]:
        """从单个分类发现 API"""
        apis = []
        
        # 构建分类 URL
        category_slug = category.lower().replace(" ", "-")
        url = f"https://rapidapi.com/category/{category_slug}"
        
        print(f"\n📂 正在爬取分类: {category}")
        print(f"   URL: {url}")
        
        try:
            await page.goto(url, timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=15000)
            
            # 滚动加载更多
            scroll_count = 0
            max_scrolls = limit // 10  # 每次滚动大约加载 10 个
            
            while scroll_count < max_scrolls:
                # 获取当前 API 卡片数量
                cards = await page.query_selector_all('[data-testid="api-card"], .ApiCard, [class*="ApiCard"]')
                current_count = len(cards)
                
                if current_count >= limit:
                    break
                
                # 滚动到底部
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(1.5)
                
                # 检查是否还有新内容
                new_cards = await page.query_selector_all('[data-testid="api-card"], .ApiCard, [class*="ApiCard"]')
                if len(new_cards) == current_count:
                    # 没有新内容了
                    break
                
                scroll_count += 1
                print(f"   📜 滚动 {scroll_count}/{max_scrolls}, 已找到 {len(new_cards)} 个 API")
            
            # 提取 API 信息
            cards = await page.query_selector_all('[data-testid="api-card"], .ApiCard, [class*="ApiCard"], a[href*="/api/"]')
            
            for card in cards[:limit]:
                try:
                    # 尝试多种方式提取链接
                    href = await card.get_attribute("href")
                    if not href:
                        link = await card.query_selector("a[href*='/api/']")
                        if link:
                            href = await link.get_attribute("href")
                    
                    if href and "/api/" in href:
                        # 确保是完整 URL
                        if not href.startswith("http"):
                            href = f"https://rapidapi.com{href}"
                        
                        # 提取 API 名称
                        name_elem = await card.query_selector("h3, [class*='title'], [class*='name']")
                        name = await name_elem.inner_text() if name_elem else href.split("/api/")[-1].split("?")[0]
                        
                        # 提取描述
                        desc_elem = await card.query_selector("p, [class*='description']")
                        description = await desc_elem.inner_text() if desc_elem else ""
                        
                        # 检查是否有 Free 标签
                        has_free = False
                        free_elem = await card.query_selector("[class*='free'], [class*='Free'], :text('Free')")
                        if free_elem:
                            has_free = True
                        
                        api_info = {
                            "url": href,
                            "name": name.strip() if name else "",
                            "description": description.strip()[:200] if description else "",
                            "category": category,
                            "has_free_indicator": has_free,
                            "discovered_at": datetime.now().isoformat()
                        }
                        
                        # 去重
                        if not any(a["url"] == api_info["url"] for a in apis):
                            apis.append(api_info)
                            
                except Exception as e:
                    continue
            
            print(f"   ✅ 从 {category} 发现 {len(apis)} 个 API")
            
        except Exception as e:
            print(f"   ❌ 爬取 {category} 失败: {e}")
        
        return apis
    
    async def discover_search(self, query: str, page: Page, limit: int = 50) -> List[Dict[str, Any]]:
        """通过搜索发现 API"""
        apis = []
        
        url = f"https://rapidapi.com/search/{query}"
        print(f"\n🔍 搜索: {query}")
        print(f"   URL: {url}")
        
        try:
            await page.goto(url, timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=15000)
            
            # 类似的提取逻辑...
            cards = await page.query_selector_all('a[href*="/api/"]')
            
            for card in cards[:limit]:
                try:
                    href = await card.get_attribute("href")
                    if href and "/api/" in href and not href.endswith("/api/"):
                        if not href.startswith("http"):
                            href = f"https://rapidapi.com{href}"
                        
                        api_info = {
                            "url": href,
                            "name": href.split("/api/")[-1].split("?")[0].replace("-", " ").title(),
                            "description": "",
                            "category": f"search:{query}",
                            "has_free_indicator": False,
                            "discovered_at": datetime.now().isoformat()
                        }
                        
                        if not any(a["url"] == api_info["url"] for a in apis):
                            apis.append(api_info)
                            
                except Exception:
                    continue
            
            print(f"   ✅ 搜索 '{query}' 发现 {len(apis)} 个 API")
            
        except Exception as e:
            print(f"   ❌ 搜索失败: {e}")
        
        return apis
    
    async def discover_popular(self, page: Page, limit: int = 100) -> List[Dict[str, Any]]:
        """发现热门 API"""
        apis = []
        
        # 热门 API 页面
        urls = [
            "https://rapidapi.com/collection/recommended-apis",
            "https://rapidapi.com/collection/top-paid-apis",
            "https://rapidapi.com/collection/list-of-free-apis",
            "https://rapidapi.com/hub",
        ]
        
        for url in urls:
            print(f"\n⭐ 正在爬取: {url}")
            
            try:
                await page.goto(url, timeout=30000)
                await page.wait_for_load_state("networkidle", timeout=15000)
                
                # 滚动几次加载更多
                for _ in range(3):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await asyncio.sleep(1)
                
                cards = await page.query_selector_all('a[href*="/api/"]')
                
                for card in cards:
                    try:
                        href = await card.get_attribute("href")
                        if href and "/api/" in href and "/api/" != href[-5:]:
                            if not href.startswith("http"):
                                href = f"https://rapidapi.com{href}"
                            
                            api_info = {
                                "url": href,
                                "name": href.split("/api/")[-1].split("?")[0].replace("-", " ").title(),
                                "description": "",
                                "category": "popular",
                                "has_free_indicator": False,
                                "discovered_at": datetime.now().isoformat()
                            }
                            
                            if not any(a["url"] == api_info["url"] for a in apis):
                                apis.append(api_info)
                                
                    except Exception:
                        continue
                
                print(f"   ✅ 累计发现 {len(apis)} 个热门 API")
                
                if len(apis) >= limit:
                    break
                    
            except Exception as e:
                print(f"   ❌ 爬取失败: {e}")
        
        return apis[:limit]
    
    async def run_discovery(
        self, 
        categories: List[str] = None, 
        limit_per_category: int = 30,
        total_limit: int = 500,
        search_queries: List[str] = None
    ) -> List[Dict[str, Any]]:
        """运行 API 发现"""
        
        await self.start_browser()
        context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        try:
            # 1. 发现热门 API
            print("\n" + "=" * 60)
            print("📊 阶段 1: 发现热门 API")
            print("=" * 60)
            
            popular = await self.discover_popular(page, limit=100)
            self.discovered_apis.extend(popular)
            
            # 2. 按分类发现
            if categories:
                print("\n" + "=" * 60)
                print("📊 阶段 2: 按分类发现 API")
                print("=" * 60)
                
                for category in categories:
                    if len(self.discovered_apis) >= total_limit:
                        print(f"\n✅ 已达到目标数量 {total_limit}，停止发现")
                        break
                    
                    remaining = total_limit - len(self.discovered_apis)
                    apis = await self.discover_category(
                        category, 
                        page, 
                        limit=min(limit_per_category, remaining)
                    )
                    
                    # 去重添加
                    for api in apis:
                        if not any(a["url"] == api["url"] for a in self.discovered_apis):
                            self.discovered_apis.append(api)
                    
                    # 避免被封
                    await asyncio.sleep(2)
            
            # 3. 搜索发现
            if search_queries:
                print("\n" + "=" * 60)
                print("📊 阶段 3: 搜索发现 API")
                print("=" * 60)
                
                for query in search_queries:
                    if len(self.discovered_apis) >= total_limit:
                        break
                    
                    remaining = total_limit - len(self.discovered_apis)
                    apis = await self.discover_search(query, page, limit=min(30, remaining))
                    
                    for api in apis:
                        if not any(a["url"] == api["url"] for a in self.discovered_apis):
                            self.discovered_apis.append(api)
                    
                    await asyncio.sleep(2)
            
        finally:
            await context.close()
            await self.close_browser()
        
        return self.discovered_apis
    
    def save_results(self, output_file: str):
        """保存发现结果"""
        output_path = Path(output_file)
        
        results = {
            "discovered_at": datetime.now().isoformat(),
            "total_count": len(self.discovered_apis),
            "apis": self.discovered_apis
        }
        
        output_path.write_text(
            json.dumps(results, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        
        print(f"\n💾 结果已保存: {output_file}")
        print(f"   共 {len(self.discovered_apis)} 个 API")
        
        # 同时生成简单的 URL 列表
        url_list_file = output_path.with_suffix(".txt")
        with open(url_list_file, "w", encoding="utf-8") as f:
            f.write(f"# RapidAPI 发现列表 - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"# 共 {len(self.discovered_apis)} 个 API\n\n")
            for api in self.discovered_apis:
                f.write(f"{api['url']}\n")
        
        print(f"   URL 列表: {url_list_file}")


@click.command()
@click.option("--category", "-c", default="all", help="分类，逗号分隔，或 'all' 表示所有分类")
@click.option("--limit", "-l", default=500, type=int, help="总数限制")
@click.option("--limit-per-category", default=30, type=int, help="每个分类的限制")
@click.option("--search", "-s", default="", help="额外搜索词，逗号分隔")
@click.option("--output", "-o", default="discovered_apis.json", help="输出文件")
@click.option("--headless/--no-headless", default=True, help="是否无头模式")
def main(category: str, limit: int, limit_per_category: int, search: str, output: str, headless: bool):
    """
    RapidAPI API 发现工具
    
    自动从 RapidAPI 收集 API 列表，为批量订阅做准备
    
    示例：
    
    \b
    # 发现所有分类的 API（推荐）
    python rapidapi_discovery.py --category all --limit 500
    
    \b
    # 只发现特定分类
    python rapidapi_discovery.py --category "AI,Data,Finance" --limit 200
    
    \b
    # 加上搜索词
    python rapidapi_discovery.py --category all --search "translation,weather,stock" --limit 300
    """
    print("🚀 RapidAPI API 发现工具")
    print("=" * 60)
    
    # 解析分类
    if category.lower() == "all":
        categories = RAPIDAPI_CATEGORIES
    else:
        categories = [c.strip() for c in category.split(",")]
    
    # 解析搜索词
    search_queries = [s.strip() for s in search.split(",") if s.strip()] if search else []
    
    print(f"📂 分类: {len(categories)} 个")
    print(f"🔍 搜索词: {search_queries if search_queries else '无'}")
    print(f"📊 目标数量: {limit}")
    print(f"👁️ 无头模式: {headless}")
    print("=" * 60)
    
    async def run():
        discovery = RapidAPIDiscovery(headless=headless)
        await discovery.run_discovery(
            categories=categories,
            limit_per_category=limit_per_category,
            total_limit=limit,
            search_queries=search_queries
        )
        discovery.save_results(output)
        
        # 统计
        print("\n" + "=" * 60)
        print("📊 发现统计")
        print("=" * 60)
        
        by_category = {}
        for api in discovery.discovered_apis:
            cat = api.get("category", "unknown")
            by_category[cat] = by_category.get(cat, 0) + 1
        
        for cat, count in sorted(by_category.items(), key=lambda x: -x[1]):
            print(f"   {cat}: {count}")
        
        print("=" * 60)
        print(f"✅ 发现完成！共 {len(discovery.discovered_apis)} 个 API")
        print(f"📄 下一步：运行智能订阅脚本")
        print(f"   python rapidapi_subscriber.py {output}")
    
    asyncio.run(run())


if __name__ == "__main__":
    main()




