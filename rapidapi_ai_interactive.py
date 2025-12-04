#!/usr/bin/env python3
"""
RapidAPI AI 交互式代理

与用户实时对话，每一步都汇报并等待指令

使用方法：
    python rapidapi_ai_interactive.py
"""
import os
import sys
import json
import asyncio
import base64
import re
from pathlib import Path
from datetime import datetime
from typing import Optional
import click

try:
    from playwright.async_api import async_playwright, Page, Browser, BrowserContext
except ImportError:
    print("❌ pip install playwright && playwright install chromium")
    sys.exit(1)

try:
    import openai
except ImportError:
    print("❌ pip install openai")
    sys.exit(1)


class InteractiveAIAgent:
    """交互式 AI 代理 - 随时与用户对话"""
    
    COOKIE_FILE = "rapidapi_cookies.json"
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.subscribed_apis = []
        
        # 初始化 AI
        self._init_ai()
    
    def _init_ai(self):
        """初始化 AI 客户端"""
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
            print(f"✅ AI: Azure OpenAI ({azure_deployment})")
        else:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.ai_client = openai.OpenAI(api_key=api_key)
                self.ai_model = "gpt-4o"
                print(f"✅ AI: OpenAI (gpt-4o)")
            else:
                print("❌ 需要配置 AI API Key")
                sys.exit(1)
    
    def ask_user(self, question: str, options: list = None) -> str:
        """询问用户"""
        print(f"\n💬 {question}")
        if options:
            for i, opt in enumerate(options, 1):
                print(f"   {i}. {opt}")
            print(f"   0. 退出")
        
        response = input("👉 你的选择: ").strip()
        return response
    
    def tell_user(self, message: str):
        """告诉用户"""
        print(f"🤖 {message}")
    
    async def start_browser(self):
        """启动浏览器"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=False,
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
            except:
                pass
        
        self.page = await self.context.new_page()
        self.tell_user("浏览器已启动，你可以看到我的操作")
    
    async def save_and_close(self):
        """保存并关闭"""
        if self.context:
            try:
                cookies = await self.context.cookies()
                Path(self.COOKIE_FILE).write_text(json.dumps(cookies, indent=2))
            except:
                pass
            await self.context.close()
        if self.browser:
            await self.browser.close()
    
    async def screenshot_and_ask_ai(self, question: str) -> str:
        """截图并询问 AI"""
        screenshot = await self.page.screenshot(type="png")
        image_b64 = base64.b64encode(screenshot).decode()
        
        response = self.ai_client.chat.completions.create(
            model=self.ai_model,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
                    {"type": "text", "text": question}
                ]
            }],
            max_tokens=1000,
            temperature=0.1
        )
        return response.choices[0].message.content
    
    async def goto(self, url: str):
        """导航到 URL"""
        self.tell_user(f"正在打开: {url}")
        try:
            await self.page.goto(url, timeout=60000)
            await asyncio.sleep(2)
        except Exception as e:
            self.tell_user(f"页面加载超时，但我继续尝试...")
    
    async def click_at(self, x: int, y: int, description: str = ""):
        """点击指定位置"""
        self.tell_user(f"点击 ({x}, {y}): {description}")
        await self.page.mouse.click(x, y)
        await asyncio.sleep(2)
    
    async def main_loop(self):
        """主交互循环"""
        await self.start_browser()
        
        print("\n" + "=" * 60)
        print("🤖 RapidAPI AI 交互式代理")
        print("=" * 60)
        print("我会告诉你我在做什么，你可以随时给我指令。")
        print("=" * 60)
        
        # 检查登录
        await self.goto("https://rapidapi.com/hub")
        
        ai_response = await self.screenshot_and_ask_ai(
            "这个页面是否显示用户已登录？只回答 YES 或 NO"
        )
        
        if "NO" in ai_response.upper():
            choice = self.ask_user("你还没登录，需要我打开登录页面吗？", ["是，打开登录页面", "不，我已经登录了"])
            if choice == "1":
                await self.goto("https://rapidapi.com/auth/login")
                self.ask_user("请在浏览器中登录，完成后按 Enter 继续")
        
        self.tell_user("好的，已登录！")
        
        # 主菜单循环
        while True:
            choice = self.ask_user(
                "你想让我做什么？",
                [
                    "浏览 API 分类，帮我找免费的 API",
                    "打开指定的 API 页面",
                    "分析当前页面",
                    "帮我订阅当前页面的 API",
                    "查看已订阅的 API 列表",
                    "生成 MCP（用已订阅的 API）",
                    "自定义指令（输入你想让我做的事）"
                ]
            )
            
            if choice == "0":
                break
            elif choice == "1":
                await self.browse_categories()
            elif choice == "2":
                url = input("请输入 API URL: ").strip()
                if url:
                    await self.goto(url)
            elif choice == "3":
                await self.analyze_current_page()
            elif choice == "4":
                await self.subscribe_current_api()
            elif choice == "5":
                self.show_subscribed_list()
            elif choice == "6":
                await self.generate_mcps()
            elif choice == "7":
                instruction = input("请告诉我你想让我做什么: ").strip()
                if instruction:
                    await self.custom_instruction(instruction)
            else:
                self.tell_user("没理解你的选择，请输入数字 0-7")
        
        # 保存并退出
        self.tell_user("再见！正在保存...")
        self.save_subscribed_list()
        await self.save_and_close()
    
    async def browse_categories(self):
        """浏览分类"""
        self.tell_user("让我看看有哪些 API 分类...")
        
        await self.goto("https://rapidapi.com/hub")
        
        ai_response = await self.screenshot_and_ask_ai("""
分析这个页面，列出所有可见的 API 分类。
返回 JSON 格式：{"categories": ["分类1", "分类2", ...]}
""")
        
        try:
            match = re.search(r'\{[\s\S]*\}', ai_response)
            if match:
                data = json.loads(match.group())
                categories = data.get("categories", [])
                
                self.tell_user(f"我看到了 {len(categories)} 个分类:")
                for i, cat in enumerate(categories[:10], 1):
                    print(f"   {i}. {cat}")
                
                choice = self.ask_user("你想浏览哪个分类？输入数字或分类名")
                
                if choice.isdigit() and 1 <= int(choice) <= len(categories):
                    cat_name = categories[int(choice) - 1]
                else:
                    cat_name = choice
                
                # 导航到分类
                cat_slug = cat_name.lower().replace(" ", "-")
                await self.goto(f"https://rapidapi.com/category/{cat_slug}")
                
                # 分析分类页面的 API
                await self.analyze_api_list()
        except Exception as e:
            self.tell_user(f"分析失败: {e}")
    
    async def analyze_api_list(self):
        """分析 API 列表"""
        ai_response = await self.screenshot_and_ask_ai("""
分析这个页面，找出所有显示的 API。
对于每个 API，告诉我：名称、是否显示 FREE 标签、简介。
返回 JSON：{"apis": [{"name": "...", "has_free": true/false, "desc": "..."}]}
""")
        
        try:
            match = re.search(r'\{[\s\S]*\}', ai_response)
            if match:
                data = json.loads(match.group())
                apis = data.get("apis", [])
                
                self.tell_user(f"找到 {len(apis)} 个 API:")
                for i, api in enumerate(apis[:10], 1):
                    free_mark = "🆓" if api.get("has_free") else "💰"
                    print(f"   {i}. {free_mark} {api.get('name', 'Unknown')}")
                    print(f"      {api.get('desc', '')[:50]}...")
                
                choice = self.ask_user("想查看哪个 API？输入数字，或 'n' 跳过")
                
                if choice.isdigit() and 1 <= int(choice) <= len(apis):
                    api_name = apis[int(choice) - 1].get("name", "")
                    # 让 AI 帮忙点击这个 API
                    await self.click_api_by_name(api_name)
        except Exception as e:
            self.tell_user(f"分析失败: {e}")
    
    async def click_api_by_name(self, api_name: str):
        """点击指定名称的 API"""
        ai_response = await self.screenshot_and_ask_ai(f"""
在这个页面中找到名为 "{api_name}" 的 API 卡片。
返回它的中心坐标 (页面宽度 1280，高度 900)。
格式：x,y
如果找不到，返回 NOT_FOUND
""")
        
        if "NOT_FOUND" in ai_response.upper():
            self.tell_user(f"找不到 {api_name}")
            return
        
        try:
            coords = ai_response.strip().replace(" ", "").split(",")
            x, y = int(coords[0]), int(coords[1])
            await self.click_at(x, y, f"点击 {api_name}")
            await asyncio.sleep(2)
        except:
            self.tell_user("点击失败")
    
    async def analyze_current_page(self):
        """分析当前页面"""
        self.tell_user("让我分析一下当前页面...")
        
        ai_response = await self.screenshot_and_ask_ai("""
详细分析这个 RapidAPI 页面：
1. 这是什么页面？（首页/API详情/定价页/其他）
2. 如果是 API 页面：
   - API 名称是什么？
   - 有免费计划吗？
   - 我是否已经订阅？
   - 订阅按钮在哪里？
3. 页面上有哪些重要元素？
4. 你建议我下一步做什么？

用中文回答，要详细。
""")
        
        print(f"\n📊 AI 分析结果:\n{ai_response}\n")
        
        self.ask_user("分析完毕，按 Enter 继续")
    
    async def subscribe_current_api(self):
        """订阅当前页面的 API"""
        self.tell_user("让我看看能否订阅这个 API...")
        
        # 先分析页面
        ai_response = await self.screenshot_and_ask_ai("""
分析这个页面，回答：
1. 这是 API 的哪个页面？（详情页/定价页）
2. 有没有 "Subscribe" 或 "订阅" 按钮？
3. 如果有，它在页面的什么位置（坐标 x,y，页面 1280x900）？
4. 是否显示已订阅？
5. 是否需要信用卡？

返回 JSON：
{
    "page_type": "detail/pricing",
    "has_subscribe_btn": true/false,
    "btn_position": "x,y" 或 null,
    "is_subscribed": true/false,
    "needs_card": true/false,
    "api_name": "API名称"
}
""")
        
        try:
            match = re.search(r'\{[\s\S]*\}', ai_response)
            if match:
                data = json.loads(match.group())
                
                api_name = data.get("api_name", "Unknown")
                
                if data.get("is_subscribed"):
                    self.tell_user(f"✅ {api_name} 已经订阅过了！")
                    if api_name not in [a.get("name") for a in self.subscribed_apis]:
                        self.subscribed_apis.append({"name": api_name, "url": self.page.url})
                    return
                
                if data.get("needs_card"):
                    self.tell_user(f"❌ {api_name} 需要信用卡，跳过")
                    return
                
                if not data.get("has_subscribe_btn"):
                    # 尝试去 pricing 页面
                    choice = self.ask_user("没看到订阅按钮，要去 Pricing 页面看看吗？", ["是", "否"])
                    if choice == "1":
                        current_url = self.page.url.rstrip("/")
                        await self.goto(f"{current_url}/pricing")
                        await self.subscribe_current_api()  # 递归
                    return
                
                # 有订阅按钮，尝试点击
                btn_pos = data.get("btn_position")
                if btn_pos:
                    coords = btn_pos.replace(" ", "").split(",")
                    x, y = int(coords[0]), int(coords[1])
                    
                    choice = self.ask_user(f"找到订阅按钮在 ({x}, {y})，要点击吗？", ["是，订阅", "否，跳过"])
                    if choice == "1":
                        await self.click_at(x, y, "Subscribe 按钮")
                        
                        # 检查结果
                        await asyncio.sleep(2)
                        self.tell_user("让我检查订阅结果...")
                        
                        check_response = await self.screenshot_and_ask_ai("""
订阅操作后，检查：
1. 是否订阅成功？
2. 是否出现需要信用卡的提示？
3. 是否需要点击确认按钮？

返回 JSON：{"success": true/false, "needs_card": true/false, "needs_confirm": true/false, "confirm_position": "x,y" 或 null}
""")
                        
                        check_match = re.search(r'\{[\s\S]*\}', check_response)
                        if check_match:
                            check_data = json.loads(check_match.group())
                            
                            if check_data.get("needs_confirm"):
                                confirm_pos = check_data.get("confirm_position")
                                if confirm_pos:
                                    coords = confirm_pos.replace(" ", "").split(",")
                                    cx, cy = int(coords[0]), int(coords[1])
                                    await self.click_at(cx, cy, "确认按钮")
                                    self.tell_user(f"✅ {api_name} 订阅成功！")
                                    self.subscribed_apis.append({"name": api_name, "url": self.page.url})
                            elif check_data.get("success"):
                                self.tell_user(f"✅ {api_name} 订阅成功！")
                                self.subscribed_apis.append({"name": api_name, "url": self.page.url})
                            elif check_data.get("needs_card"):
                                self.tell_user(f"❌ {api_name} 需要信用卡")
                            else:
                                self.tell_user("⚠️ 订阅结果不确定，请检查页面")
                
        except Exception as e:
            self.tell_user(f"操作失败: {e}")
    
    def show_subscribed_list(self):
        """显示已订阅列表"""
        if not self.subscribed_apis:
            self.tell_user("还没有订阅任何 API")
            return
        
        self.tell_user(f"已订阅 {len(self.subscribed_apis)} 个 API:")
        for i, api in enumerate(self.subscribed_apis, 1):
            print(f"   {i}. {api.get('name', 'Unknown')}")
            print(f"      {api.get('url', '')}")
    
    def save_subscribed_list(self):
        """保存订阅列表"""
        if self.subscribed_apis:
            with open("interactive_subscribed.txt", "w", encoding="utf-8") as f:
                f.write(f"# 交互式订阅的 API - {datetime.now()}\n")
                for api in self.subscribed_apis:
                    f.write(f"{api.get('url', '')}\n")
            self.tell_user(f"已保存 {len(self.subscribed_apis)} 个 API 到 interactive_subscribed.txt")
    
    async def generate_mcps(self):
        """生成 MCP"""
        if not self.subscribed_apis:
            self.tell_user("还没有订阅任何 API，先去订阅一些吧！")
            return
        
        self.save_subscribed_list()
        
        choice = self.ask_user(
            f"准备用 {len(self.subscribed_apis)} 个 API 生成 MCP，确认吗？",
            ["是，开始生成", "否，稍后再说"]
        )
        
        if choice == "1":
            self.tell_user("开始生成 MCP...")
            import subprocess
            subprocess.run([
                sys.executable, "batch_rapidapi.py",
                "interactive_subscribed.txt",
                "--use-selenium",
                "--delay", "20"
            ])
    
    async def custom_instruction(self, instruction: str):
        """执行自定义指令"""
        self.tell_user(f"你说: {instruction}")
        self.tell_user("让我想想怎么做...")
        
        ai_response = await self.screenshot_and_ask_ai(f"""
用户给了我这个指令："{instruction}"

基于当前页面，我应该怎么做？
请给出具体的操作步骤，包括：
1. 需要点击什么位置（给出坐标 x,y）
2. 需要输入什么内容
3. 预期会发生什么

用中文详细回答。
""")
        
        print(f"\n🤖 AI 建议:\n{ai_response}\n")
        
        choice = self.ask_user("要按照 AI 的建议执行吗？", ["是", "否"])
        if choice == "1":
            # 尝试解析并执行
            # 这里可以进一步解析 AI 的回复来自动执行
            self.tell_user("正在执行...")
            # TODO: 解析 AI 回复中的坐标和操作


@click.command()
def main():
    """RapidAPI AI 交互式代理 - 随时与你对话"""
    print("=" * 60)
    print("🤖 RapidAPI AI 交互式代理")
    print("=" * 60)
    print("我会打开浏览器，你可以看到我的每一步操作。")
    print("随时告诉我你想做什么！")
    print("=" * 60)
    
    agent = InteractiveAIAgent()
    
    async def run():
        try:
            await agent.main_loop()
        except KeyboardInterrupt:
            print("\n\n👋 再见！")
            agent.save_subscribed_list()
            await agent.save_and_close()
    
    asyncio.run(run())


if __name__ == "__main__":
    main()



