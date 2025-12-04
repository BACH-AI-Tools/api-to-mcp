#!/usr/bin/env python3
"""
RapidAPI 智能订阅工具

自动订阅 Free 计划的 API，跳过需要付费/信用卡的 API

核心功能：
1. 自动登录（保存 Cookie）
2. 智能判断是否有 Free 计划（无需信用卡）
3. 自动点击订阅
4. 记录订阅结果

使用方法：
    # 第一次运行（需要手动登录）
    python rapidapi_subscriber.py discovered_apis.json --login
    
    # 后续运行（使用保存的 Cookie）
    python rapidapi_subscriber.py discovered_apis.json
    
    # 显示浏览器（调试）
    python rapidapi_subscriber.py discovered_apis.json --no-headless
"""
import json
import asyncio
import os
import time
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import click

try:
    from playwright.async_api import async_playwright, Page, Browser, BrowserContext
except ImportError:
    print("❌ 需要安装 Playwright: pip install playwright && playwright install chromium")
    exit(1)


class SubscriptionStatus(Enum):
    """订阅状态"""
    PENDING = "pending"
    SUBSCRIBED = "subscribed"           # 成功订阅
    ALREADY_SUBSCRIBED = "already"      # 已订阅
    NO_FREE_PLAN = "no_free"            # 无免费计划
    REQUIRES_CARD = "requires_card"     # 需要信用卡
    REQUIRES_APPROVAL = "approval"      # 需要申请批准
    FAILED = "failed"                   # 失败
    SKIPPED = "skipped"                 # 跳过


@dataclass
class APISubscriptionResult:
    """API 订阅结果"""
    url: str
    name: str
    status: SubscriptionStatus
    message: str = ""
    free_plan_name: str = ""
    rate_limit: str = ""
    subscribed_at: str = ""
    error: str = ""
    
    def to_dict(self):
        result = asdict(self)
        result["status"] = self.status.value
        return result


class RapidAPISubscriber:
    """RapidAPI 智能订阅器"""
    
    COOKIE_FILE = "rapidapi_cookies.json"
    STATE_FILE = "rapidapi_subscription_state.json"
    
    def __init__(self, headless: bool = True, use_ai: bool = False):
        self.headless = headless
        self.use_ai = use_ai  # 是否使用 AI 辅助判断
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.results: List[APISubscriptionResult] = []
        
        # AI 客户端（可选，支持 OpenAI 和 Azure OpenAI）
        self.ai_client = None
        self.ai_model = "gpt-4o"
        self.is_azure = False
        if use_ai:
            self._init_ai_client()
    
    def _init_ai_client(self):
        """初始化 AI 客户端（支持 OpenAI 和 Azure OpenAI）"""
        try:
            import openai
            
            # 优先检查 Azure OpenAI
            azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            azure_key = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_KEY")
            azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")  # 默认部署名
            
            if azure_endpoint and azure_key:
                self.ai_client = openai.AzureOpenAI(
                    azure_endpoint=azure_endpoint,
                    api_key=azure_key,
                    api_version="2024-02-15-preview"
                )
                self.ai_model = azure_deployment
                self.is_azure = True
                print(f"✅ AI 辅助已启用 (Azure OpenAI: {azure_deployment})")
                return
            
            # 回退到标准 OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.ai_client = openai.OpenAI(api_key=api_key)
                self.ai_model = "gpt-4o"
                self.is_azure = False
                print("✅ AI 辅助已启用 (OpenAI GPT-4)")
                return
            
            print("⚠️  未设置 AI API Key，AI 辅助已禁用")
            print("   Azure OpenAI: 设置 AZURE_OPENAI_ENDPOINT 和 AZURE_OPENAI_API_KEY")
            print("   OpenAI: 设置 OPENAI_API_KEY")
            
        except ImportError:
            print("⚠️  未安装 openai 库，AI 辅助已禁用")
            print("   安装方法: pip install openai")
    
    async def start_browser(self):
        """启动浏览器"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
            ]
        )
        
        # 创建上下文
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # 尝试加载已保存的 Cookie
        if Path(self.COOKIE_FILE).exists():
            try:
                cookies = json.loads(Path(self.COOKIE_FILE).read_text())
                await self.context.add_cookies(cookies)
                print("🍪 已加载保存的 Cookie")
            except Exception as e:
                print(f"⚠️  加载 Cookie 失败: {e}")
        
        self.page = await self.context.new_page()
        print(f"🌐 浏览器已启动 (headless={self.headless})")
    
    async def close_browser(self):
        """关闭浏览器"""
        if self.context:
            # 保存 Cookie
            try:
                cookies = await self.context.cookies()
                Path(self.COOKIE_FILE).write_text(json.dumps(cookies, indent=2))
                print("🍪 Cookie 已保存")
            except Exception as e:
                print(f"⚠️  保存 Cookie 失败: {e}")
            
            await self.context.close()
        
        if self.browser:
            await self.browser.close()
            print("🌐 浏览器已关闭")
    
    async def manual_login(self) -> bool:
        """手动登录（弹出浏览器让用户登录）"""
        print("\n" + "=" * 60)
        print("🔐 手动登录模式")
        print("=" * 60)
        print("1. 浏览器将打开 RapidAPI 登录页面")
        print("2. 请在浏览器中完成登录")
        print("3. 登录成功后，按 Enter 键继续...")
        print("=" * 60)
        
        # 导航到登录页
        await self.page.goto("https://rapidapi.com/auth/login", timeout=60000)
        
        # 等待用户登录
        input("\n⏳ 完成登录后按 Enter 键继续...")
        
        # 检查是否登录成功
        try:
            await self.page.goto("https://rapidapi.com/developer/dashboard", timeout=30000)
            await asyncio.sleep(2)
            
            # 检查是否在 dashboard 页面
            current_url = self.page.url
            if "dashboard" in current_url or "hub" in current_url:
                print("✅ 登录成功！")
                
                # 保存 Cookie
                cookies = await self.context.cookies()
                Path(self.COOKIE_FILE).write_text(json.dumps(cookies, indent=2))
                print("🍪 Cookie 已保存，下次运行无需重新登录")
                
                return True
            else:
                print("❌ 登录可能失败，当前 URL:", current_url)
                return False
                
        except Exception as e:
            print(f"❌ 检查登录状态失败: {e}")
            return False
    
    async def check_login_status(self) -> bool:
        """检查登录状态"""
        try:
            await self.page.goto("https://rapidapi.com/developer/dashboard", timeout=30000)
            await asyncio.sleep(2)
            
            current_url = self.page.url
            
            # 如果被重定向到登录页，说明未登录
            if "login" in current_url or "auth" in current_url:
                return False
            
            # 检查是否有用户菜单
            user_menu = await self.page.query_selector('[data-testid="user-menu"], [class*="UserMenu"], [class*="avatar"]')
            if user_menu:
                print("✅ 已登录")
                return True
            
            return "dashboard" in current_url or "hub" in current_url
            
        except Exception:
            return False
    
    async def analyze_pricing_page(self, api_url: str) -> Tuple[SubscriptionStatus, str, Dict[str, Any]]:
        """
        分析 API 的定价页面，判断是否有免费计划
        
        Returns:
            (status, message, plan_info)
        """
        pricing_url = api_url.rstrip("/") + "/pricing"
        
        try:
            await self.page.goto(pricing_url, timeout=30000)
            await self.page.wait_for_load_state("networkidle", timeout=15000)
            await asyncio.sleep(2)
            
            # 获取页面内容
            page_text = await self.page.inner_text("body")
            page_text_lower = page_text.lower()
            
            # 检查是否已订阅
            if any(text in page_text_lower for text in ["subscribed", "已订阅", "current plan", "当前计划"]):
                # 检查是否有 "unsubscribe" 按钮
                unsubscribe_btn = await self.page.query_selector('button:text("Unsubscribe"), button:text("取消订阅")')
                if unsubscribe_btn:
                    return SubscriptionStatus.ALREADY_SUBSCRIBED, "已订阅此 API", {}
            
            # 查找定价卡片
            plan_cards = await self.page.query_selector_all('[class*="PricingCard"], [class*="pricing-card"], [class*="PlanCard"], [data-testid*="pricing"]')
            
            if not plan_cards:
                # 尝试其他选择器
                plan_cards = await self.page.query_selector_all('[class*="plan"], [class*="Plan"]')
            
            # 分析每个计划
            free_plan = None
            
            for card in plan_cards:
                try:
                    card_text = await card.inner_text()
                    card_text_lower = card_text.lower()
                    
                    # 检查是否是免费计划
                    is_free = any(keyword in card_text_lower for keyword in [
                        "free", "$0", "0/mo", "免费", "basic", "starter"
                    ])
                    
                    if not is_free:
                        continue
                    
                    # 检查是否需要信用卡
                    requires_card = any(keyword in card_text_lower for keyword in [
                        "credit card", "信用卡", "payment method", "billing",
                        "card required", "需要付款"
                    ])
                    
                    if requires_card:
                        continue
                    
                    # 检查是否需要申请
                    requires_approval = any(keyword in card_text_lower for keyword in [
                        "request", "apply", "contact", "申请", "联系",
                        "approval", "审批"
                    ])
                    
                    if requires_approval:
                        return SubscriptionStatus.REQUIRES_APPROVAL, "Free 计划需要申请", {}
                    
                    # 提取计划信息
                    # 尝试提取 rate limit
                    rate_match = re.search(r'(\d+[\d,]*)\s*(?:requests?|calls?|/\s*(?:month|day|min))', card_text_lower)
                    rate_limit = rate_match.group(0) if rate_match else "unknown"
                    
                    # 提取计划名称
                    name_elem = await card.query_selector('h3, h4, [class*="title"], [class*="name"]')
                    plan_name = await name_elem.inner_text() if name_elem else "Free"
                    
                    free_plan = {
                        "name": plan_name.strip(),
                        "rate_limit": rate_limit,
                        "card": card
                    }
                    break
                    
                except Exception:
                    continue
            
            if free_plan:
                return SubscriptionStatus.PENDING, f"找到免费计划: {free_plan['name']}", free_plan
            
            # 没找到免费计划，检查页面是否有"免费"相关文字
            if "free" in page_text_lower or "免费" in page_text_lower:
                # 可能有免费计划但需要特殊处理
                
                # 检查是否需要信用卡
                if any(keyword in page_text_lower for keyword in ["credit card required", "add payment", "需要信用卡"]):
                    return SubscriptionStatus.REQUIRES_CARD, "Free 计划需要信用卡", {}
                
                # 使用 AI 辅助判断（如果启用）
                if self.use_ai and self.ai_client:
                    result = await self._ai_analyze_pricing(api_url)
                    if result:
                        return result
                
                return SubscriptionStatus.NO_FREE_PLAN, "无法识别免费计划", {}
            
            return SubscriptionStatus.NO_FREE_PLAN, "没有免费计划", {}
            
        except Exception as e:
            return SubscriptionStatus.FAILED, f"分析定价页失败: {e}", {}
    
    async def _ai_analyze_pricing(self, api_url: str) -> Optional[Tuple[SubscriptionStatus, str, Dict]]:
        """使用 AI 分析定价页面（支持 OpenAI 和 Azure OpenAI）"""
        if not self.ai_client:
            return None
        
        try:
            # 截图
            screenshot = await self.page.screenshot(type="png")
            
            import base64
            image_base64 = base64.b64encode(screenshot).decode()
            
            # 使用配置的模型名称
            model_name = getattr(self, 'ai_model', 'gpt-4o')
            
            response = self.ai_client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """分析这个 RapidAPI 定价页面截图，回答：
1. 是否有免费(Free)计划？
2. 免费计划是否需要信用卡？
3. 免费计划是否需要申请/审批？

请用 JSON 格式回答：
{
  "has_free": true/false,
  "requires_card": true/false,
  "requires_approval": true/false,
  "free_plan_name": "计划名称",
  "rate_limit": "请求限制"
}"""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )
            
            result_text = response.choices[0].message.content
            
            # 解析 JSON
            json_match = re.search(r'\{[^}]+\}', result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                
                if not result.get("has_free"):
                    return SubscriptionStatus.NO_FREE_PLAN, "AI: 没有免费计划", {}
                if result.get("requires_card"):
                    return SubscriptionStatus.REQUIRES_CARD, "AI: 需要信用卡", {}
                if result.get("requires_approval"):
                    return SubscriptionStatus.REQUIRES_APPROVAL, "AI: 需要申请", {}
                
                return SubscriptionStatus.PENDING, f"AI: 找到免费计划 {result.get('free_plan_name', 'Free')}", {
                    "name": result.get("free_plan_name", "Free"),
                    "rate_limit": result.get("rate_limit", "unknown")
                }
                
        except Exception as e:
            print(f"   ⚠️  AI 分析失败: {e}")
        
        return None
    
    async def subscribe_to_free_plan(self, api_url: str, plan_info: Dict[str, Any]) -> Tuple[bool, str]:
        """订阅免费计划"""
        try:
            pricing_url = api_url.rstrip("/") + "/pricing"
            
            # 确保在定价页面
            if self.page.url != pricing_url:
                await self.page.goto(pricing_url, timeout=30000)
                await asyncio.sleep(2)
            
            # 查找订阅按钮
            subscribe_selectors = [
                'button:text("Subscribe")',
                'button:text("订阅")',
                'button:text("Start Free")',
                'button:text("Get Started")',
                'button:text("Select Plan")',
                '[data-testid="subscribe-button"]',
                '[class*="subscribe"] button',
            ]
            
            subscribe_btn = None
            
            # 如果有计划卡片信息，在卡片内查找按钮
            if "card" in plan_info and plan_info["card"]:
                card = plan_info["card"]
                for selector in subscribe_selectors:
                    try:
                        btn = await card.query_selector(selector)
                        if btn:
                            subscribe_btn = btn
                            break
                    except:
                        continue
            
            # 如果没找到，在整个页面查找
            if not subscribe_btn:
                for selector in subscribe_selectors:
                    try:
                        btns = await self.page.query_selector_all(selector)
                        for btn in btns:
                            btn_text = await btn.inner_text()
                            btn_text_lower = btn_text.lower()
                            
                            # 跳过已订阅的按钮
                            if "unsubscribe" in btn_text_lower or "subscribed" in btn_text_lower:
                                continue
                            
                            subscribe_btn = btn
                            break
                        
                        if subscribe_btn:
                            break
                    except:
                        continue
            
            if not subscribe_btn:
                return False, "找不到订阅按钮"
            
            # 点击订阅
            await subscribe_btn.click()
            await asyncio.sleep(3)
            
            # 检查是否出现确认对话框或信用卡要求
            page_text = await self.page.inner_text("body")
            page_text_lower = page_text.lower()
            
            # 检查是否需要信用卡
            if any(keyword in page_text_lower for keyword in [
                "add payment", "credit card", "billing information",
                "payment method", "信用卡", "付款方式"
            ]):
                return False, "需要添加信用卡"
            
            # 检查是否有确认按钮
            confirm_selectors = [
                'button:text("Confirm")',
                'button:text("确认")',
                'button:text("Subscribe")',
                'button:text("Yes")',
                '[data-testid="confirm"]',
            ]
            
            for selector in confirm_selectors:
                try:
                    confirm_btn = await self.page.query_selector(selector)
                    if confirm_btn:
                        await confirm_btn.click()
                        await asyncio.sleep(2)
                        break
                except:
                    continue
            
            # 验证订阅成功
            await asyncio.sleep(2)
            page_text = await self.page.inner_text("body")
            page_text_lower = page_text.lower()
            
            success_indicators = [
                "subscribed", "successfully", "成功", "已订阅",
                "thank you", "welcome", "congratulations"
            ]
            
            if any(indicator in page_text_lower for indicator in success_indicators):
                return True, "订阅成功"
            
            # 检查是否显示 Unsubscribe 按钮（表示已订阅）
            unsubscribe_btn = await self.page.query_selector('button:text("Unsubscribe")')
            if unsubscribe_btn:
                return True, "订阅成功"
            
            return True, "可能已订阅（请验证）"
            
        except Exception as e:
            return False, f"订阅过程出错: {e}"
    
    async def process_api(self, api_info: Dict[str, Any]) -> APISubscriptionResult:
        """处理单个 API"""
        url = api_info["url"]
        name = api_info.get("name", url.split("/api/")[-1])
        
        result = APISubscriptionResult(
            url=url,
            name=name,
            status=SubscriptionStatus.PENDING
        )
        
        print(f"\n📍 处理: {name}")
        print(f"   URL: {url}")
        
        try:
            # 1. 分析定价页面
            status, message, plan_info = await self.analyze_pricing_page(url)
            
            print(f"   💰 定价分析: {message}")
            
            if status != SubscriptionStatus.PENDING:
                result.status = status
                result.message = message
                return result
            
            # 2. 尝试订阅
            result.free_plan_name = plan_info.get("name", "Free")
            result.rate_limit = plan_info.get("rate_limit", "unknown")
            
            print(f"   🔄 尝试订阅: {result.free_plan_name}")
            
            success, sub_message = await self.subscribe_to_free_plan(url, plan_info)
            
            if success:
                result.status = SubscriptionStatus.SUBSCRIBED
                result.message = sub_message
                result.subscribed_at = datetime.now().isoformat()
                print(f"   ✅ {sub_message}")
            else:
                if "信用卡" in sub_message or "credit card" in sub_message.lower():
                    result.status = SubscriptionStatus.REQUIRES_CARD
                else:
                    result.status = SubscriptionStatus.FAILED
                result.message = sub_message
                print(f"   ❌ {sub_message}")
            
        except Exception as e:
            result.status = SubscriptionStatus.FAILED
            result.error = str(e)
            print(f"   ❌ 错误: {e}")
        
        return result
    
    def save_state(self, output_file: str):
        """保存处理状态"""
        state = {
            "updated_at": datetime.now().isoformat(),
            "total": len(self.results),
            "stats": {
                status.value: sum(1 for r in self.results if r.status == status)
                for status in SubscriptionStatus
            },
            "results": [r.to_dict() for r in self.results]
        }
        
        Path(output_file).write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    
    async def run(
        self, 
        apis: List[Dict[str, Any]], 
        need_login: bool = False,
        delay: int = 5,
        start_from: int = 0
    ):
        """运行订阅流程"""
        
        await self.start_browser()
        
        try:
            # 1. 检查/执行登录
            if need_login:
                # 需要显示浏览器进行登录
                if self.headless:
                    print("⚠️  登录模式需要显示浏览器，请使用 --no-headless")
                    return
                
                success = await self.manual_login()
                if not success:
                    print("❌ 登录失败，退出")
                    return
            else:
                # 检查登录状态
                logged_in = await self.check_login_status()
                if not logged_in:
                    print("❌ 未登录，请先使用 --login 参数登录")
                    print("   python rapidapi_subscriber.py apis.json --login --no-headless")
                    return
            
            # 2. 处理 API 列表
            print("\n" + "=" * 60)
            print(f"📊 开始处理 {len(apis)} 个 API")
            print(f"⏭️  从第 {start_from} 个开始")
            print("=" * 60)
            
            apis_to_process = apis[start_from:]
            
            for i, api in enumerate(apis_to_process):
                actual_index = start_from + i
                print(f"\n{'='*40}")
                print(f"📍 [{actual_index + 1}/{len(apis)}] 处理中...")
                
                result = await self.process_api(api)
                self.results.append(result)
                
                # 定期保存状态
                if (i + 1) % 10 == 0:
                    self.save_state(self.STATE_FILE)
                    print(f"\n💾 状态已保存 ({i + 1} 个已处理)")
                
                # 延迟
                if i < len(apis_to_process) - 1:
                    print(f"   ⏳ 等待 {delay} 秒...")
                    await asyncio.sleep(delay)
            
            # 3. 保存最终状态
            self.save_state(self.STATE_FILE)
            
            # 4. 统计
            print("\n" + "=" * 60)
            print("📊 订阅统计")
            print("=" * 60)
            
            stats = {}
            for result in self.results:
                status = result.status.value
                stats[status] = stats.get(status, 0) + 1
            
            for status, count in sorted(stats.items()):
                emoji = {
                    "subscribed": "✅",
                    "already": "📌",
                    "no_free": "💰",
                    "requires_card": "💳",
                    "approval": "📝",
                    "failed": "❌",
                    "skipped": "⏭️",
                    "pending": "⏳"
                }.get(status, "❓")
                print(f"   {emoji} {status}: {count}")
            
            print("=" * 60)
            
            # 5. 生成成功订阅的 URL 列表（供下一步使用）
            subscribed = [r for r in self.results if r.status in [
                SubscriptionStatus.SUBSCRIBED, 
                SubscriptionStatus.ALREADY_SUBSCRIBED
            ]]
            
            if subscribed:
                subscribed_file = "subscribed_apis.txt"
                with open(subscribed_file, "w", encoding="utf-8") as f:
                    f.write(f"# 已订阅的 API 列表 - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
                    f.write(f"# 共 {len(subscribed)} 个\n\n")
                    for r in subscribed:
                        f.write(f"{r.url}\n")
                
                print(f"\n✅ 已订阅 API 列表已保存: {subscribed_file}")
                print(f"   共 {len(subscribed)} 个，可用于下一步生成 MCP")
                print(f"\n📌 下一步：测试端点")
                print(f"   python rapidapi_tester.py {subscribed_file}")
            
        finally:
            await self.close_browser()


@click.command()
@click.argument("apis_file", type=click.Path(exists=True))
@click.option("--login", is_flag=True, help="手动登录模式（首次使用）")
@click.option("--headless/--no-headless", default=True, help="是否无头模式")
@click.option("--delay", "-d", default=5, type=int, help="每个 API 之间的延迟")
@click.option("--start-from", default=0, type=int, help="从第 N 个开始（断点续传）")
@click.option("--use-ai", is_flag=True, help="使用 AI 辅助分析定价页（需要 OPENAI_API_KEY）")
@click.option("--limit", "-l", default=0, type=int, help="处理数量限制（0=全部）")
def main(apis_file: str, login: bool, headless: bool, delay: int, start_from: int, use_ai: bool, limit: int):
    """
    RapidAPI 智能订阅工具
    
    自动订阅 Free 计划的 API
    
    \b
    第一次使用（需要登录）：
        python rapidapi_subscriber.py discovered_apis.json --login --no-headless
    
    \b
    后续使用（使用保存的 Cookie）：
        python rapidapi_subscriber.py discovered_apis.json
    
    \b
    断点续传：
        python rapidapi_subscriber.py discovered_apis.json --start-from 50
    """
    print("🚀 RapidAPI 智能订阅工具")
    print("=" * 60)
    
    # 加载 API 列表
    content = Path(apis_file).read_text(encoding="utf-8")
    
    # 支持多种格式
    if apis_file.endswith(".json"):
        data = json.loads(content)
        if isinstance(data, dict) and "apis" in data:
            apis = data["apis"]
        elif isinstance(data, list):
            apis = data
        else:
            apis = [data]
    else:
        # 文本格式，每行一个 URL
        apis = []
        for line in content.split("\n"):
            line = line.strip()
            if line and not line.startswith("#") and line.startswith("http"):
                apis.append({"url": line, "name": line.split("/api/")[-1].split("?")[0]})
    
    # 应用限制
    if limit > 0:
        apis = apis[:limit]
    
    print(f"📄 加载 {len(apis)} 个 API")
    print(f"🔐 登录模式: {'是' if login else '否'}")
    print(f"👁️ 无头模式: {headless}")
    print(f"🤖 AI 辅助: {use_ai}")
    print(f"⏱️ 延迟: {delay} 秒")
    print("=" * 60)
    
    if login and headless:
        print("\n⚠️  登录模式需要显示浏览器")
        print("   请使用: --login --no-headless")
        return
    
    async def run():
        subscriber = RapidAPISubscriber(headless=headless, use_ai=use_ai)
        await subscriber.run(
            apis=apis,
            need_login=login,
            delay=delay,
            start_from=start_from
        )
    
    asyncio.run(run())


if __name__ == "__main__":
    main()


