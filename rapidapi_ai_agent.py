#!/usr/bin/env python3
"""
RapidAPI AI Agent - 让 AI 控制浏览器

使用 GPT-4V 视觉能力来：
1. 看页面截图
2. 理解页面内容
3. 决定下一步操作（点击、输入、滚动等）
4. 判断是否有免费计划、是否可订阅

这是一个真正的 AI Agent，不依赖硬编码的选择器。

使用方法：
    python rapidapi_ai_agent.py --login  # 首次登录
    python rapidapi_ai_agent.py --target 100  # 自动处理 100 个 API
"""
import os
import sys
import json
import asyncio
import base64
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import click

try:
    from playwright.async_api import async_playwright, Page, Browser, BrowserContext
except ImportError:
    print("❌ 需要安装 Playwright: pip install playwright && playwright install chromium")
    sys.exit(1)

try:
    import openai
except ImportError:
    print("❌ 需要安装 openai: pip install openai")
    sys.exit(1)


class AIBrowserAgent:
    """AI 驱动的浏览器代理"""
    
    COOKIE_FILE = "rapidapi_cookies.json"
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # 初始化 AI 客户端
        self.ai_client = None
        self.ai_model = None
        self._init_ai_client()
        
        # 结果存储
        self.results = []
        self.subscribed_apis = []
    
    def _init_ai_client(self):
        """初始化 AI 客户端（支持 Azure OpenAI 和 OpenAI）"""
        # 优先 Azure OpenAI
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        azure_key = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_KEY")
        azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
        
        if azure_endpoint and azure_key:
            self.ai_client = openai.AzureOpenAI(
                azure_endpoint=azure_endpoint,
                api_key=azure_key,
                api_version="2024-02-15-preview"
            )
            self.ai_model = azure_deployment
            print(f"✅ AI 客户端: Azure OpenAI ({azure_deployment})")
            return
        
        # 回退到 OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.ai_client = openai.OpenAI(api_key=api_key)
            self.ai_model = "gpt-4o"
            print(f"✅ AI 客户端: OpenAI (gpt-4o)")
            return
        
        print("❌ 未配置 AI API Key")
        print("   Azure: AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_API_KEY")
        print("   OpenAI: OPENAI_API_KEY")
        sys.exit(1)
    
    async def start_browser(self):
        """启动浏览器"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        self.context = await self.browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        
        # 加载 Cookie
        if Path(self.COOKIE_FILE).exists():
            try:
                cookies = json.loads(Path(self.COOKIE_FILE).read_text())
                await self.context.add_cookies(cookies)
                print("🍪 已加载 Cookie")
            except:
                pass
        
        self.page = await self.context.new_page()
        print(f"🌐 浏览器已启动 (headless={self.headless})")
    
    async def close_browser(self):
        """关闭浏览器并保存 Cookie"""
        if self.context:
            try:
                cookies = await self.context.cookies()
                Path(self.COOKIE_FILE).write_text(json.dumps(cookies, indent=2))
                print("🍪 Cookie 已保存")
            except:
                pass
            await self.context.close()
        
        if self.browser:
            await self.browser.close()
    
    async def take_screenshot(self) -> str:
        """截图并返回 base64"""
        screenshot = await self.page.screenshot(type="png", full_page=False)
        return base64.b64encode(screenshot).decode()
    
    async def ask_ai(self, prompt: str, include_screenshot: bool = True) -> str:
        """询问 AI"""
        messages = [{"role": "user", "content": []}]
        
        if include_screenshot:
            screenshot_b64 = await self.take_screenshot()
            messages[0]["content"].append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"}
            })
        
        messages[0]["content"].append({"type": "text", "text": prompt})
        
        try:
            response = self.ai_client.chat.completions.create(
                model=self.ai_model,
                messages=messages,
                max_tokens=1500,
                temperature=0.1
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ AI 请求失败: {e}")
            return ""
    
    async def ai_analyze_page(self) -> Dict[str, Any]:
        """让 AI 分析当前页面"""
        prompt = """分析这个 RapidAPI 页面截图，返回 JSON 格式的信息：

{
    "page_type": "页面类型：home/api_detail/pricing/login/other",
    "api_name": "API 名称（如果是 API 页面）",
    "is_logged_in": true/false,
    "has_free_plan": true/false/unknown,
    "free_plan_needs_card": true/false/unknown,
    "is_subscribed": true/false/unknown,
    "can_subscribe": true/false,
    "subscribe_button_text": "订阅按钮的文字（如果有）",
    "subscribe_button_location": "订阅按钮的大概位置描述",
    "next_action": "建议的下一步操作",
    "notes": "其他重要信息"
}

只返回 JSON，不要其他文字。"""
        
        response = await self.ask_ai(prompt)
        
        # 解析 JSON
        try:
            # 提取 JSON
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {"error": "无法解析", "raw": response}
    
    async def ai_find_element(self, description: str) -> Optional[str]:
        """让 AI 帮忙找到页面元素的选择器"""
        prompt = f"""在这个页面截图中，找到以下元素：
"{description}"

返回一个 CSS 选择器或 XPath 来定位这个元素。
如果找不到，返回 "NOT_FOUND"。

只返回选择器字符串，不要其他文字。例如：
button.subscribe-btn
或
//button[contains(text(), 'Subscribe')]"""
        
        response = await self.ask_ai(prompt)
        response = response.strip().strip('"').strip("'").strip('`')
        
        if "NOT_FOUND" in response.upper():
            return None
        
        return response
    
    async def ai_click(self, description: str) -> bool:
        """让 AI 帮忙点击元素"""
        prompt = f"""我需要点击页面上的这个元素："{description}"

请告诉我这个元素在页面上的大概坐标位置（x, y），其中：
- x 是从左边开始的像素位置（页面宽度 1280）
- y 是从上边开始的像素位置（页面高度 900）

只返回坐标，格式：x,y
例如：640,450

如果找不到这个元素，返回：NOT_FOUND"""
        
        response = await self.ask_ai(prompt)
        response = response.strip()
        
        if "NOT_FOUND" in response.upper():
            print(f"   ❌ 找不到元素: {description}")
            return False
        
        try:
            # 解析坐标
            coords = response.replace(" ", "").split(",")
            x, y = int(coords[0]), int(coords[1])
            
            print(f"   🖱️ 点击 ({x}, {y}): {description}")
            await self.page.mouse.click(x, y)
            await asyncio.sleep(2)
            return True
        except Exception as e:
            print(f"   ❌ 点击失败: {e}")
            return False
    
    async def manual_login(self):
        """手动登录"""
        print("\n" + "=" * 60)
        print("🔐 手动登录 RapidAPI")
        print("=" * 60)
        print("1. 浏览器将打开 RapidAPI 登录页面")
        print("2. 请在浏览器中完成登录")
        print("3. 登录成功后按 Enter 继续...")
        print("=" * 60)
        
        try:
            await self.page.goto("https://rapidapi.com/auth/login", timeout=60000)
        except Exception as e:
            print(f"⚠️ 页面加载慢，但继续等待... ({e})")
        
        await asyncio.sleep(2)
        
        input("\n⏳ 完成登录后按 Enter...")
        
        # 保存 Cookie
        cookies = await self.context.cookies()
        Path(self.COOKIE_FILE).write_text(json.dumps(cookies, indent=2))
        print("✅ 登录成功，Cookie 已保存")
    
    async def discover_apis_with_ai(self, target: int = 100) -> List[str]:
        """使用 AI 发现 API"""
        print("\n" + "=" * 60)
        print(f"🔍 AI 辅助发现 API (目标: {target} 个)")
        print("=" * 60)
        
        discovered = []
        
        # 访问 RapidAPI Hub
        try:
            await self.page.goto("https://rapidapi.com/hub", timeout=60000)
        except Exception as e:
            print(f"⚠️ 页面加载超时: {e}")
        await asyncio.sleep(3)
        
        page_num = 0
        while len(discovered) < target:
            page_num += 1
            print(f"\n📄 第 {page_num} 页，已发现 {len(discovered)} 个")
            
            # 让 AI 分析页面，提取 API 链接
            prompt = """分析这个 RapidAPI 页面，找出所有 API 的链接。

返回 JSON 格式：
{
    "api_links": [
        {"name": "API名称", "url": "完整URL"},
        ...
    ],
    "has_more": true/false,
    "scroll_needed": true/false
}

只返回 JSON。"""
            
            response = await self.ask_ai(prompt)
            
            try:
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    data = json.loads(json_match.group())
                    
                    for api in data.get("api_links", []):
                        url = api.get("url", "")
                        if url and "/api/" in url and url not in discovered:
                            if not url.startswith("http"):
                                url = f"https://rapidapi.com{url}"
                            discovered.append(url)
                            print(f"   ✅ {api.get('name', 'Unknown')}")
                    
                    # 滚动或翻页
                    if data.get("scroll_needed") and len(discovered) < target:
                        await self.page.evaluate("window.scrollBy(0, 800)")
                        await asyncio.sleep(2)
                    elif not data.get("has_more"):
                        break
                        
            except Exception as e:
                print(f"   ⚠️ 解析失败: {e}")
            
            if page_num > 20:  # 防止无限循环
                break
        
        print(f"\n✅ 共发现 {len(discovered)} 个 API")
        return discovered[:target]
    
    async def process_api_with_ai(self, api_url: str) -> Dict[str, Any]:
        """使用 AI 处理单个 API（分析、订阅）"""
        result = {
            "url": api_url,
            "name": "",
            "status": "pending",
            "has_free": False,
            "subscribed": False,
            "error": ""
        }
        
        print(f"\n📍 处理: {api_url}")
        
        try:
            # 1. 访问 API 页面
            try:
                await self.page.goto(api_url, timeout=60000)
            except Exception as e:
                print(f"   ⚠️ 页面加载超时，继续尝试...")
            await asyncio.sleep(3)
            
            # 2. AI 分析页面
            analysis = await self.ai_analyze_page()
            print(f"   📊 AI 分析: {json.dumps(analysis, ensure_ascii=False)[:200]}")
            
            result["name"] = analysis.get("api_name", "Unknown")
            
            # 3. 检查是否已订阅
            if analysis.get("is_subscribed"):
                result["status"] = "already_subscribed"
                result["subscribed"] = True
                print(f"   ✅ 已订阅")
                return result
            
            # 4. 检查是否有免费计划
            if not analysis.get("has_free_plan"):
                # 尝试去 pricing 页面看看
                pricing_url = api_url.rstrip("/") + "/pricing"
                try:
                    await self.page.goto(pricing_url, timeout=60000)
                except:
                    pass
                await asyncio.sleep(2)
                
                analysis = await self.ai_analyze_page()
                print(f"   📊 Pricing 分析: {json.dumps(analysis, ensure_ascii=False)[:200]}")
            
            if analysis.get("has_free_plan") == False:
                result["status"] = "no_free_plan"
                print(f"   ❌ 无免费计划")
                return result
            
            if analysis.get("free_plan_needs_card"):
                result["status"] = "needs_card"
                print(f"   ❌ 需要信用卡")
                return result
            
            result["has_free"] = True
            
            # 5. 尝试订阅
            if analysis.get("can_subscribe"):
                btn_text = analysis.get("subscribe_button_text", "Subscribe")
                btn_location = analysis.get("subscribe_button_location", "")
                
                print(f"   🔄 尝试点击: {btn_text} ({btn_location})")
                
                # 让 AI 帮忙点击订阅按钮
                clicked = await self.ai_click(f"订阅按钮，文字是 '{btn_text}'，位置在 {btn_location}")
                
                if clicked:
                    await asyncio.sleep(3)
                    
                    # 检查结果
                    post_analysis = await self.ai_analyze_page()
                    
                    if post_analysis.get("is_subscribed"):
                        result["status"] = "subscribed"
                        result["subscribed"] = True
                        print(f"   ✅ 订阅成功!")
                    elif "card" in str(post_analysis).lower():
                        result["status"] = "needs_card"
                        print(f"   ❌ 需要信用卡")
                    else:
                        # 可能需要确认
                        confirm_clicked = await self.ai_click("确认按钮或 Confirm 按钮")
                        if confirm_clicked:
                            await asyncio.sleep(2)
                            final_analysis = await self.ai_analyze_page()
                            if final_analysis.get("is_subscribed"):
                                result["status"] = "subscribed"
                                result["subscribed"] = True
                                print(f"   ✅ 订阅成功!")
                            else:
                                result["status"] = "unknown"
                                print(f"   ⚠️ 状态未知")
                else:
                    result["status"] = "click_failed"
                    print(f"   ❌ 点击失败")
            else:
                result["status"] = "cannot_subscribe"
                print(f"   ⚠️ 无法订阅")
                
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            print(f"   ❌ 错误: {e}")
        
        return result
    
    async def run(self, target: int = 100, api_list: List[str] = None, login_first: bool = False):
        """运行 AI Agent"""
        await self.start_browser()
        
        try:
            # 登录
            if login_first:
                await self.manual_login()
                return
            
            # 检查登录状态 - 尝试访问需要登录的页面
            print("🔍 检查登录状态...")
            try:
                await self.page.goto("https://rapidapi.com/hub", timeout=60000)
                await asyncio.sleep(3)
            except Exception as e:
                print(f"⚠️ 页面加载超时: {e}")
                print("   继续尝试...")
            
            # 让 AI 判断是否已登录
            analysis = await self.ai_analyze_page()
            print(f"   AI 分析: is_logged_in={analysis.get('is_logged_in')}")
            
            if analysis.get("is_logged_in") == False:
                print("❌ 未登录，请先使用 --login 登录")
                return
            
            print("✅ 已登录")
            
            # 获取 API 列表
            if api_list:
                apis_to_process = api_list
            else:
                apis_to_process = await self.discover_apis_with_ai(target * 3)  # 多发现一些
            
            print(f"\n📊 准备处理 {len(apis_to_process)} 个 API")
            
            # 处理每个 API
            for i, api_url in enumerate(apis_to_process):
                if len(self.subscribed_apis) >= target:
                    print(f"\n✅ 已达到目标 {target} 个!")
                    break
                
                print(f"\n{'='*50}")
                print(f"[{i+1}/{len(apis_to_process)}] 已订阅: {len(self.subscribed_apis)}/{target}")
                
                result = await self.process_api_with_ai(api_url)
                self.results.append(result)
                
                if result.get("subscribed"):
                    self.subscribed_apis.append(api_url)
                
                # 保存进度
                if (i + 1) % 5 == 0:
                    self._save_progress()
                
                # 延迟
                await asyncio.sleep(3)
            
            # 保存最终结果
            self._save_progress()
            self._print_summary()
            
        finally:
            await self.close_browser()
    
    def _save_progress(self):
        """保存进度"""
        # 保存详细结果
        Path("ai_agent_results.json").write_text(
            json.dumps({
                "timestamp": datetime.now().isoformat(),
                "total": len(self.results),
                "subscribed": len(self.subscribed_apis),
                "results": self.results
            }, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        
        # 保存已订阅列表
        if self.subscribed_apis:
            with open("ai_subscribed_apis.txt", "w", encoding="utf-8") as f:
                f.write(f"# AI Agent 订阅的 API - {datetime.now()}\n")
                for url in self.subscribed_apis:
                    f.write(f"{url}\n")
    
    def _print_summary(self):
        """打印总结"""
        print("\n" + "=" * 60)
        print("📊 AI Agent 运行总结")
        print("=" * 60)
        
        stats = {}
        for r in self.results:
            status = r.get("status", "unknown")
            stats[status] = stats.get(status, 0) + 1
        
        for status, count in sorted(stats.items()):
            emoji = {
                "subscribed": "✅",
                "already_subscribed": "📌",
                "no_free_plan": "💰",
                "needs_card": "💳",
                "error": "❌"
            }.get(status, "❓")
            print(f"   {emoji} {status}: {count}")
        
        print(f"\n✅ 成功订阅: {len(self.subscribed_apis)} 个")
        print(f"📄 结果文件: ai_agent_results.json")
        print(f"📄 订阅列表: ai_subscribed_apis.txt")
        print("=" * 60)


@click.command()
@click.option("--login", is_flag=True, help="手动登录模式")
@click.option("--target", "-t", default=100, help="目标订阅数量")
@click.option("--headless/--no-headless", default=False, help="是否无头模式（默认显示浏览器）")
@click.option("--input", "-i", "input_file", default=None, help="API URL 列表文件")
def main(login: bool, target: int, headless: bool, input_file: str):
    """
    RapidAPI AI Agent - 让 AI 控制浏览器自动订阅 API
    
    \b
    首次使用（登录）:
        python rapidapi_ai_agent.py --login
    
    \b
    自动发现并订阅:
        python rapidapi_ai_agent.py --target 100
    
    \b
    使用已有列表:
        python rapidapi_ai_agent.py --input apis.txt --target 50
    """
    print("🤖 RapidAPI AI Agent")
    print("=" * 60)
    
    # 加载 API 列表
    api_list = None
    if input_file and Path(input_file).exists():
        with open(input_file, "r", encoding="utf-8") as f:
            api_list = [
                line.strip() for line in f 
                if line.strip() and not line.startswith("#") and line.startswith("http")
            ]
        print(f"📄 加载 {len(api_list)} 个 API")
    
    async def run():
        agent = AIBrowserAgent(headless=headless)
        await agent.run(target=target, api_list=api_list, login_first=login)
    
    asyncio.run(run())


if __name__ == "__main__":
    main()

