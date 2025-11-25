"""
RapidAPI Selenium 爬虫 - 使用浏览器自动化完整提取参数和响应
"""
from typing import Dict, Any, List, Optional
import json
import time
import re


class RapidAPISeleniumScraper:
    """使用 Selenium 完整爬取 RapidAPI"""
    
    def __init__(self, headless: bool = True, enable_screenshots: bool = True):
        """
        初始化 Selenium
        
        Args:
            headless: 是否无头模式（不显示浏览器窗口）
            enable_screenshots: 是否启用自动截图（记录每一步操作）
        """
        self.enable_screenshots = enable_screenshots
        self.screenshot_counter = 0
        
        # 创建截图目录
        if enable_screenshots:
            import os
            self.screenshot_dir = f"debug/screenshots_{int(time.time())}"
            os.makedirs(self.screenshot_dir, exist_ok=True)
            print(f"            📸 截图保存目录: {self.screenshot_dir}")
        
        try:
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.chrome.options import Options
            
            self.webdriver = webdriver
            self.By = By
            self.WebDriverWait = WebDriverWait
            self.EC = EC
            
            options = Options()
            if headless:
                options.add_argument('--headless')
                options.add_argument('--headless=new')  # 新版 Chrome 需要
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # 尝试使用 webdriver-manager 自动管理 ChromeDriver
            try:
                from selenium.webdriver.chrome.service import Service
                from webdriver_manager.chrome import ChromeDriverManager
                
                print("            📦 使用 webdriver-manager 自动管理 ChromeDriver...")
                print("            ⏳ 正在下载/检查 ChromeDriver（首次运行可能需要1-3分钟）...")
                print("            💡 提示：下载完成后会自动缓存，下次启动会很快")
                
                # 设置超时和日志级别
                import os
                os.environ['WDM_LOG'] = '1'  # 启用详细日志
                
                service = Service(ChromeDriverManager().install())
                print("            ✅ ChromeDriver 已准备好")
                
                print("            🚀 正在启动 Chrome 浏览器...")
                self.driver = webdriver.Chrome(service=service, options=options)
                print("            ✅ Chrome 浏览器启动成功！")
            except ImportError:
                # 如果没有 webdriver-manager，使用系统 PATH 中的 chromedriver
                print("            ⚠️  未安装 webdriver-manager，尝试使用系统 ChromeDriver...")
                print("            💡 建议安装: pip install webdriver-manager")
                print("            ⏳ 正在初始化浏览器（可能需要 10-30 秒）...")
                try:
                    self.driver = webdriver.Chrome(options=options)
                    print("            ✅ ChromeDriver 初始化成功")
                except Exception as e:
                    print(f"            ❌ ChromeDriver 初始化失败: {e}")
                    raise ImportError(
                        "\n❌ 无法初始化 ChromeDriver！\n\n"
                        "请选择以下方案之一：\n"
                        "1. 【推荐】安装 webdriver-manager（自动管理）:\n"
                        "   pip install webdriver-manager\n\n"
                        "2. 手动安装 ChromeDriver:\n"
                        "   - 下载地址: https://chromedriver.chromium.org/downloads\n"
                        "   - 确保版本匹配你的 Chrome 浏览器\n"
                        "   - 添加到系统 PATH\n\n"
                        "3. 不使用 Selenium（生成基础结构）:\n"
                        "   api-to-mcp rapidapi <url>  (去掉 --use-selenium)\n"
                    )
            
            self.wait = WebDriverWait(self.driver, 15)
            
        except ImportError as e:
            raise ImportError(
                "需要安装 Selenium:\n"
                "  pip install selenium webdriver-manager\n\n"
                "或查看安装指南: SELENIUM_SETUP.md"
            )
    
    def scrape_endpoint_full(self, endpoint_url: str) -> Dict[str, Any]:
        """
        完整爬取端点页面，包括参数和响应
        
        Args:
            endpoint_url: 端点详情页 URL
        
        Returns:
            包含 parameters 和 responses 的字典
        """
        print(f"      🌐 使用浏览器爬取: {endpoint_url}")
        
        try:
            self.driver.get(endpoint_url)
            
            # 等待页面主要内容加载完成
            try:
                # 等待标签页容器出现
                self.wait.until(self.EC.presence_of_element_located((self.By.XPATH, "//div[@role='tablist']")))
                time.sleep(2)  # 额外等待 JS 渲染
                print(f"            ✅ 页面加载完成")
            except:
                print(f"            ⚠️  页面加载超时，继续尝试...")
                time.sleep(3)
            
            # 截图：初始页面
            self._take_screenshot("01_page_loaded")
            
            result = {}
            
            # 步骤1: 提取所有类型的参数（Params, Headers, Body, App）
            all_params = self._click_and_extract_params()
            if all_params:
                result['parameters'] = all_params
                total = len(all_params.get('query', [])) + len(all_params.get('header', []))
                if all_params.get('body'):
                    total += 1
                print(f"         ✓ 提取参数: Query={len(all_params.get('query', []))}, Headers={len(all_params.get('header', []))}, Body={'是' if all_params.get('body') else '否'}")
            else:
                print(f"         ⚠️  未提取到参数")
            
            # 步骤2: 生成基础响应结构（简化，不深度提取）
            responses = self._click_and_extract_responses()
            result['responses'] = responses
            print(f"         ✓ 生成响应结构（object 类型）")
            
            return result
            
        except Exception as e:
            print(f"         ✗ Selenium 爬取失败: {e}")
            return {}
    
    def _take_screenshot(self, step_name: str):
        """截图记录当前步骤"""
        if not self.enable_screenshots:
            return
        
        try:
            self.screenshot_counter += 1
            filename = f"{self.screenshot_counter:02d}_{step_name}.png"
            filepath = f"{self.screenshot_dir}/{filename}"
            self.driver.save_screenshot(filepath)
            print(f"            📸 截图: {filename}")
        except Exception as e:
            print(f"            ⚠️  截图失败: {e}")
    
    def _close_cookie_dialog(self):
        """关闭 Cookie 对话框（如果存在）"""
        try:
            # 查找常见的 Cookie 对话框按钮
            button_texts = ['Accept All', 'Reject All', 'Accept', 'Close', '×', 'Got it']
            
            for text in button_texts:
                try:
                    buttons = self.driver.find_elements(self.By.XPATH, 
                        f"//button[contains(., '{text}')]")
                    for btn in buttons:
                        if btn.is_displayed():
                            btn.click()
                            print(f"            ✅ 已关闭 Cookie 对话框（点击了 '{text}'）")
                            time.sleep(1)
                            return
                except:
                    continue
            
            print(f"            ℹ️  未找到 Cookie 对话框")
        except Exception as e:
            print(f"            ⚠️  关闭 Cookie 对话框失败: {e}")
    
    def _click_and_extract_params(self) -> Dict[str, Any]:
        """点击各个标签页并提取所有类型的参数"""
        all_params = {
            'query': [],      # Query Params
            'header': [],     # Headers
            'body': None,     # Body (JSON)
            'app': {}         # App 配置
        }
        
        try:
            # 1. 提取 App 配置
            print("            🔍 提取 App 配置...")
            app_config = self._extract_app_config()
            if app_config:
                all_params['app'] = app_config
                print(f"            ✅ 提取到 App 配置")
            
            # 2. 首先关闭 Cookie 对话框（如果存在）
            self._close_cookie_dialog()
            
            # 3. 提取 Query Params（点击 Params 标签，然后提取）
            print("            🔍 提取 Query Params...")
            # 截图：点击Params前
            self._take_screenshot("02_before_click_params")
            
            # 先尝试点击 Params 标签（可能在主体区域顶部）
            self._click_params_tab()
            time.sleep(3)  # 增加等待时间，等待参数区域加载
            
            # 截图：点击Params后
            self._take_screenshot("03_after_click_params")
            
            # 使用统一的 DOM 结构提取方法（与 Headers 相同）
            query_params = self._extract_parameters()
            if query_params:
                all_params['query'] = query_params
                print(f"            ✅ 提取到 {len(query_params)} 个查询参数")
            
            # 3. 提取 Headers
            print("            🔍 提取 Headers...")
            self._take_screenshot("04_before_headers")
            headers = self._extract_tab_params("Headers")
            
            # 去重：如果 Headers 中的参数已经在 Query 中，则过滤掉
            if headers:
                query_param_names = {p['name'] for p in all_params['query']}
                headers_only = [h for h in headers if h['name'] not in query_param_names]
                
                # 同时过滤掉明显是 Query 参数但误识别为 Header 的
                # 真正的 Headers 通常是：X-RapidAPI-Host, Authorization, Content-Type 等
                real_headers = []
                for h in headers_only:
                    # 如果参数的 'in' 字段是 'query'，说明它本来就是 Query 参数
                    if h.get('in') == 'query':
                        # 移动到 query 数组
                        all_params['query'].append(h)
                        print(f"            📌 {h['name']} 从 Headers 移动到 Query Params")
                    else:
                        real_headers.append(h)
                
                if real_headers:
                    all_params['header'] = real_headers
                    print(f"            ✅ 提取到 {len(real_headers)} 个真正的 Header 参数")
                else:
                    print(f"            ℹ️  Headers 标签无额外参数（已去重）")
            self._take_screenshot("05_after_headers")
            
            # 4. 提取 Body
            print("            🔍 提取 Body 参数...")
            self._take_screenshot("06_before_body")
            body_data = self._extract_body_params()
            if body_data:
                all_params['body'] = body_data
                print(f"            ✅ 提取到 Body 参数")
            self._take_screenshot("07_after_body")
            
            return all_params
        
        except Exception as e:
            print(f"            ❌ 提取所有参数失败: {e}")
            # 返回空结构
            return {
                'query': [],
                'header': [],
                'body': None,
                'app': {}
            }
    
    def _extract_app_config(self) -> Dict[str, Any]:
        """提取 App 配置"""
        try:
            # 点击 App 标签
            app_tabs = self.driver.find_elements(self.By.XPATH, 
                "//*[text()='App' and @role='tab']")
            
            for tab in app_tabs:
                if tab.is_displayed():
                    try:
                        self.driver.execute_script("arguments[0].click();", tab)
                        time.sleep(1)
                        break
                    except:
                        continue
            
            # 提取 App 配置（通常是 select 下拉框）
            app_config = {}
            
            # 查找所有 label 和对应的值
            labels = self.driver.find_elements(self.By.XPATH, 
                "//label[@aria-label]")
            
            for label in labels:
                try:
                    aria_label = label.get_attribute('aria-label')
                    if aria_label and aria_label.lower() != 'app':
                        # 查找对应的输入值
                        parent = label.find_element(self.By.XPATH, './ancestor::div[contains(@class, "flex-col")][1]')
                        value_elem = parent.find_element(self.By.XPATH, './/input | .//select | .//*[contains(@class, "single-value")]')
                        value = value_elem.get_attribute('value') or value_elem.text
                        
                        if value:
                            app_config[aria_label] = value
                except:
                    continue
            
            return app_config
            
        except Exception as e:
            return {}
    
    def _debug_print_tabs(self):
        """调试：打印页面上所有的标签"""
        try:
            print("            🐛 调试：页面上的所有 tab 元素：")
            all_tabs = self.driver.find_elements(self.By.XPATH, "//*[@role='tab']")
            if all_tabs:
                for i, tab in enumerate(all_tabs):
                    try:
                        text = tab.text.strip()
                        visible = tab.is_displayed()
                        print(f"               Tab {i+1}: '{text}' (visible={visible})")
                    except:
                        pass
            else:
                print("               未找到任何 role='tab' 的元素")
            
            # 也检查一下是否有 button
            print("            🐛 调试：页面上的按钮文本：")
            buttons = self.driver.find_elements(self.By.TAG_NAME, "button")[:20]  # 只看前20个
            for i, btn in enumerate(buttons):
                try:
                    text = btn.text.strip()
                    if text:
                        print(f"               Button {i+1}: '{text}'")
                except:
                    pass
        except Exception as e:
            print(f"            🐛 调试失败: {e}")
    
    def _click_params_tab(self):
        """点击主体区域的 Params 标签"""
        try:
            print("            📍 点击 Params 标签...")
            
            # 多种定位策略查找 Params 标签
            selectors = [
                # 可能是按钮
                "//button[contains(text(), 'Params')]",
                "//button[contains(., 'Params')]",
                # 可能是 div
                "//div[contains(text(), 'Params') and contains(@class, 'tab')]",
                "//*[contains(text(), 'Params') and (self::button or self::div or self::a)]",
                # 可能有数字标记，如 "Params(4)"
                "//*[contains(text(), 'Params(')]",
            ]
            
            clicked = False
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(self.By.XPATH, selector)
                    for elem in elements:
                        if elem.is_displayed():
                            # 滚动到元素位置
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                            time.sleep(0.5)
                            # 尝试点击
                            try:
                                elem.click()
                            except:
                                # 如果直接点击失败，使用 JS 点击
                                self.driver.execute_script("arguments[0].click();", elem)
                            
                            clicked = True
                            print("            ✅ 成功点击 Params 标签")
                            break
                    if clicked:
                        break
                except:
                    continue
            
            if not clicked:
                print("            ⚠️  未找到 Params 标签（可能默认已展开）")
                
        except Exception as e:
            print(f"            ⚠️  点击 Params 标签失败: {e}")
    
    def _extract_query_params_from_page(self) -> List[Dict[str, Any]]:
        """从页面主体的 Query Params 区域提取参数"""
        try:
            print("            📍 提取参数内容...")
            time.sleep(1)  # 等待内容加载
            
            # 尝试多种方式定位参数区域
            params = []
            
            # 方法1: 查找参数列表（最常见的结构）
            try:
                # 查找所有可能包含参数的元素
                # 通常参数名会有特殊样式（蓝色标记等）
                param_names = self.driver.find_elements(self.By.XPATH,
                    "//div[contains(@class, 'param') or contains(@class, 'field')]//span[contains(@class, 'name') or contains(@class, 'key')]")
                
                if not param_names:
                    # 尝试查找所有带蓝色或高亮样式的参数名
                    param_names = self.driver.find_elements(self.By.XPATH,
                        "//*[contains(@class, 'parameter-name') or contains(@class, 'field-name')]")
                
                print(f"            📊 找到 {len(param_names)} 个候选参数元素")
                
                for param_elem in param_names:
                    try:
                        # 获取参数名
                        param_name = param_elem.text.strip()
                        if not param_name or len(param_name) > 50:  # 跳过空或过长的文本
                            continue
                        
                        # 查找该参数的父容器，获取完整信息
                        parent = param_elem.find_element(self.By.XPATH, "./ancestor::div[contains(@class, 'param') or contains(@class, 'field')][1]")
                        param_info = self._parse_param_from_container(param_name, parent)
                        
                        if param_info:
                            params.append(param_info)
                            print(f"               ✓ {param_name} ({param_info['schema']['type']})")
                    except:
                        continue
                        
            except Exception as e:
                print(f"            ⚠️  方法1失败: {e}")
            
            # 方法2: 从页面文本中解析参数（备用方案）
            if not params:
                print("            ⚠️  未能通过DOM提取参数，尝试文本解析...")
                try:
                    page_text = self.driver.find_element(self.By.TAG_NAME, "body").text
                    params = self._parse_params_from_text(page_text)
                    if params:
                        print(f"            ✅ 通过文本解析提取到 {len(params)} 个参数")
                except:
                    pass
            
            # 如果还是没有参数，保存HTML用于调试
            if not params:
                import os
                os.makedirs('debug', exist_ok=True)
                debug_file = f"debug/debug_no_params_{int(time.time())}.html"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                print(f"            💾 未提取到参数，页面已保存到: {debug_file}")
            
            return params
            
        except Exception as e:
            print(f"            ❌ 提取 Query Params 失败: {e}")
            return []
    
    def _parse_param_from_container(self, param_name: str, container) -> Optional[Dict[str, Any]]:
        """从参数容器元素中提取完整参数信息"""
        try:
            import re
            
            # 获取容器的完整文本
            text = container.text
            if not text:
                return None
            
            # 提取类型（String, Number, Boolean等）
            param_type = 'string'  # 默认
            type_keywords = ['String', 'Number', 'Integer', 'Boolean', 'Array', 'Object']
            for keyword in type_keywords:
                if keyword in text:
                    param_type = keyword
                    break
            
            # 判断是否必需（查找 "optional" 关键词）
            required = 'optional' not in text.lower() and '(optional)' not in text.lower()
            
            # 提取描述
            description = ''
            lines = text.split('\n')
            # 跳过第一行（通常是参数名和类型），后面的是描述
            if len(lines) > 1:
                desc_lines = []
                for line in lines[1:]:
                    line = line.strip()
                    # 跳过只包含类型关键字的行
                    if line and line not in type_keywords and not line.startswith('Default'):
                        desc_lines.append(line)
                description = ' '.join(desc_lines)
            
            # 提取默认值
            default_value = None
            default_match = re.search(r'[Dd]efault[:\s]+([^\s\n]+)', text)
            if default_match:
                default_str = default_match.group(1)
                # 尝试转换类型
                if param_type.lower() in ['number', 'integer']:
                    try:
                        default_value = int(default_str) if '.' not in default_str else float(default_str)
                    except:
                        default_value = default_str
                else:
                    default_value = default_str
            
            result = {
                'name': param_name,
                'in': 'query',
                'required': required,
                'description': description[:500] if description else '',  # 限制长度
                'schema': {
                    'type': self._convert_rapidapi_type(param_type)
                }
            }
            
            if default_value is not None:
                result['schema']['default'] = default_value
            
            return result
            
        except Exception as e:
            print(f"               ⚠️  解析参数 {param_name} 失败: {e}")
            return None
    
    def _parse_params_from_text(self, text: str) -> List[Dict[str, Any]]:
        """从页面文本中解析参数（备用方案）"""
        params = []
        import re
        
        # 查找参数模式：paramName String optional
        pattern = r'([a-zA-Z_][a-zA-Z0-9_]*)\s+(?:\()?([Ss]tring|[Nn]umber|[Bb]oolean|[Ii]nteger)(?:\))?\s*(optional|required)?'
        matches = re.findall(pattern, text)
        
        for match in matches:
            param_name, param_type, optional_flag = match
            
            # 过滤常见的非参数词
            if param_name.lower() in ['type', 'string', 'number', 'boolean', 'default', 'value']:
                continue
            
            params.append({
                'name': param_name,
                'in': 'query',
                'required': optional_flag.lower() != 'optional' if optional_flag else True,
                'description': '',
                'schema': {
                    'type': self._convert_rapidapi_type(param_type)
                }
            })
        
        return params
    
    def _convert_rapidapi_type(self, rapidapi_type: str) -> str:
        """转换 RapidAPI 类型到 OpenAPI 类型"""
        type_map = {
            'string': 'string',
            'number': 'number',
            'integer': 'integer',
            'boolean': 'boolean',
            'array': 'array',
            'object': 'object'
        }
        return type_map.get(rapidapi_type.lower(), 'string')
    
    def _extract_tab_params(self, tab_name: str) -> List[Dict[str, Any]]:
        """通用的标签页参数提取方法"""
        try:
            # 点击指定标签页
            print(f"            📍 点击 {tab_name} 标签...")
            
            # 尝试多种定位策略
            tab_xpaths = [
                f"//*[contains(text(), '{tab_name}') and @role='tab']",
                f"//button[contains(text(), '{tab_name}') and @role='tab']",
                f"//div[@role='tab' and contains(., '{tab_name}')]",
                f"//*[@role='tab']//*[contains(text(), '{tab_name}')]/ancestor::*[@role='tab']"
            ]
            
            tabs = []
            for xpath in tab_xpaths:
                tabs = self.driver.find_elements(self.By.XPATH, xpath)
                if tabs:
                    break
            
            if not tabs:
                # 调试：保存页面 HTML
                import os
                os.makedirs('debug', exist_ok=True)
                debug_file = f"debug/debug_tab_{tab_name}_{int(time.time())}.html"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                print(f"            ⚠️  未找到 {tab_name} 标签")
                print(f"            💾 页面已保存到: {debug_file}")
                return []
            
            tab_clicked = False
            for tab in tabs:
                try:
                    if tab.is_displayed():
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", tab)
                        time.sleep(0.5)
                        self.driver.execute_script("arguments[0].click();", tab)
                        time.sleep(3)  # 增加等待时间，确保标签页内容完全加载
                        tab_clicked = True
                        print(f"            ✅ 点击了 {tab_name} 标签")
                        break
                except Exception as e:
                    continue
            
            if not tab_clicked:
                print(f"            ⚠️  找到 {tab_name} 标签但无法点击")
                return []
            
            # 检查是否显示 "No additional params" 或 "No additional headers"
            try:
                no_params_text = self.driver.find_elements(self.By.XPATH,
                    "//div[@data-state='active']//*[contains(text(), 'No additional')]")
                if no_params_text:
                    print(f"            ℹ️  {tab_name}: No additional params")
                    return []
            except:
                pass
            
            # 提取参数（使用 DOM 结构方法）
            return self._extract_parameters()
            
        except Exception as e:
            print(f"            ❌ 提取 {tab_name} 失败: {e}")
            return []
    
    def _extract_body_params(self) -> Dict[str, Any]:
        """提取 Body 参数（JSON body）"""
        try:
            # 点击 Body 标签
            print("            📍 点击 Body 标签...")
            
            # 尝试多种定位策略
            body_xpaths = [
                "//*[text()='Body' and @role='tab']",
                "//button[contains(text(), 'Body') and @role='tab']",
                "//div[@role='tab' and contains(., 'Body')]",
                "//*[@role='tab']//*[contains(text(), 'Body')]/ancestor::*[@role='tab']"
            ]
            
            body_tabs = []
            for xpath in body_xpaths:
                body_tabs = self.driver.find_elements(self.By.XPATH, xpath)
                if body_tabs:
                    break
            
            tab_clicked = False
            for tab in body_tabs:
                # 检查是否被禁用
                is_disabled = tab.get_attribute('data-disabled') == 'true' or tab.get_attribute('disabled')
                if is_disabled:
                    print("            ⚠️  Body 标签被禁用（GET 请求）")
                    return None
                
                if tab.is_displayed():
                    try:
                        self.driver.execute_script("arguments[0].click();", tab)
                        time.sleep(2)
                        tab_clicked = True
                        print("            ✅ 点击了 Body 标签")
                        break
                    except:
                        continue
            
            if not tab_clicked:
                return None
            
            # 查找 Body 内容（通常在代码编辑器或 textarea 中）
            body_text = None
            
            # 方法1: 从 curl 命令提取 Body（最可靠）
            print("            🔍 从 curl 命令提取 Body...")
            try:
                # 查找 curl 命令中的 --data 参数
                code_elements = self.driver.find_elements(self.By.XPATH, "//code | //pre")
                
                for elem in code_elements:
                    text = elem.text
                    if text and 'curl' in text.lower() and '--data' in text:
                        # 提取 --data 后面的 JSON
                        data_match = re.search(r"--data\s+['\"](.+?)['\"]", text, re.DOTALL)
                        if data_match:
                            data_str = data_match.group(1)
                            # 处理转义
                            data_str = data_str.replace('\\"', '"').replace('\\n', '').replace('\\t', '')
                            
                            try:
                                import json
                                body_obj = json.loads(data_str)
                                print(f"            ✅ 从 curl 提取 Body: {list(body_obj.keys()) if isinstance(body_obj, dict) else 'array'}")
                                return body_obj
                            except:
                                continue
            except Exception as e:
                print(f"            ❌ curl 提取失败: {e}")
            
            # 方法2: 从 ace editor 提取
            print("            🔍 从 ace editor 提取 Body...")
            try:
                # ace editor 的内容在 textarea 中
                ace_textarea = self.driver.find_elements(self.By.XPATH,
                    "//div[@id='ace-editor']//textarea[@class='ace_text-input']")
                
                if ace_textarea:
                    # ace editor 把内容存在 textarea 的 value 属性或通过 JS 获取
                    ace_content = self.driver.execute_script("""
                        var editor = ace.edit("ace-editor");
                        return editor ? editor.getValue() : "";
                    """)
                    
                    if ace_content and ace_content.strip():
                        print(f"            📦 ace editor 内容长度: {len(ace_content)}")
                        try:
                            import json
                            body_obj = json.loads(ace_content)
                            print(f"            ✅ 从 ace editor 提取 Body: {list(body_obj.keys()) if isinstance(body_obj, dict) else 'array'}")
                            return body_obj
                        except:
                            print(f"            ❌ ace editor JSON 解析失败")
            except Exception as e:
                print(f"            ❌ ace editor 提取失败: {e}")
            
            # 方法3: 从可见的文本元素提取
            print("            🔍 从可见元素提取 Body...")
            try:
                # 只在当前激活的 Body 标签区域查找
                json_elements = self.driver.find_elements(self.By.XPATH,
                    "//div[@data-state='active']//pre | "
                    "//div[@data-state='active']//code")
                
                print(f"            📦 找到 {len(json_elements)} 个可能包含 JSON 的元素")
                
                for idx, elem in enumerate(json_elements):
                    text = elem.text or elem.get_attribute('value') or ''
                    text = text.strip()
                    
                    if text and len(text) > 5 and (text.startswith('{') or text.startswith('[')):
                        print(f"            🔍 尝试解析元素 #{idx+1}（长度: {len(text)}）")
                        try:
                            # 尝试解析 JSON
                            import json
                            body_obj = json.loads(text)
                            print(f"            ✅ 成功解析 Body JSON: {list(body_obj.keys()) if isinstance(body_obj, dict) else 'array'}")
                            return body_obj
                        except json.JSONDecodeError as e:
                            continue
            except Exception as e:
                print(f"            ❌ 查找 JSON 元素失败: {e}")
            
            # 方法2: 从输入框的默认值提取
            try:
                inputs = self.driver.find_elements(self.By.XPATH, "//input[@type='text' or @type='hidden']")
                for inp in inputs:
                    value = inp.get_attribute('value') or ''
                    if value and value.startswith('{'):
                        try:
                            import json
                            return json.loads(value)
                        except:
                            continue
            except:
                pass
            
            return None
            
        except Exception as e:
            print(f"            ❌ 提取 Body 失败: {e}")
            return None
    
    def _old_click_and_extract_params(self) -> List[Dict[str, Any]]:
        """旧方法：点击 Params 标签页并提取参数（优先从 curl 命令提取）"""
        try:
            # 方法1: 从 Code Snippets 的 curl 命令提取（最可靠）
            print("            🔍 尝试从 curl 命令提取参数...")
            params_from_curl = self._extract_params_from_curl()
            if params_from_curl:
                print(f"            ✅ 从 curl 命令提取到 {len(params_from_curl)} 个参数")
                return params_from_curl
            
            # 尝试多种可能的标签文本
            tab_texts = [
                "Params",
                "Parameters", 
                "Query Params",
                "Request Parameters"
            ]
            
            tab_clicked = False
            for tab_text in tab_texts:
                try:
                    # 使用更精确的 XPath，查找包含文本的可点击元素
                    xpath = f"//*[contains(text(), '{tab_text}') and (self::button or self::a or self::div[@role='tab'])]"
                    tabs = self.driver.find_elements(self.By.XPATH, xpath)
                    
                    for tab in tabs:
                        if tab.is_displayed():
                            try:
                                # 使用 JavaScript 点击，避免元素被遮挡
                                self.driver.execute_script("arguments[0].click();", tab)
                                print(f"            ✅ 点击了 '{tab_text}' 标签页")
                                time.sleep(2)  # 等待内容加载
                                tab_clicked = True
                                break
                            except Exception as e:
                                continue
                    
                    if tab_clicked:
                        break
                except Exception as e:
                    continue
            
            if not tab_clicked:
                print("            ⚠️  未找到 Params 标签页，使用当前页面")
            
            # 提取参数
            return self._extract_parameters()
            
        except Exception as e:
            print(f"            ❌ 点击标签页失败: {e}")
            return self._extract_parameters()
    
    def _extract_params_from_curl(self) -> List[Dict[str, Any]]:
        """从页面的 curl 命令中提取参数"""
        parameters = []
        
        try:
            # curl 命令通常在 Code Snippets 区域
            # 尝试找到包含 curl 的代码块
            
            # 查找所有 pre/code 元素
            code_elements = self.driver.find_elements(self.By.XPATH, 
                "//pre | //code | //*[contains(@class, 'code')] | //*[contains(@class, 'snippet')]")
            
            curl_command = None
            for elem in code_elements:
                try:
                    text = elem.text
                    if text and 'curl' in text.lower() and '--url' in text:
                        curl_command = text
                        print(f"            ✅ 找到 curl 命令（长度: {len(curl_command)}）")
                        break
                except:
                    continue
            
            if not curl_command:
                print("            ❌ 未找到 curl 命令")
                return []
            
            # 解析 curl 命令中的 URL
            # 格式：--url 'https://...?query=...&page=1&...'
            url_match = re.search(r"--url\s+['\"]([^'\"]+)['\"]", curl_command)
            if not url_match:
                print("            ❌ 无法从 curl 命令解析 URL")
                return []
            
            full_url = url_match.group(1)
            print(f"            📍 解析 URL: {full_url[:100]}...")
            
            # 解析查询参数
            from urllib.parse import urlparse, parse_qs
            
            parsed = urlparse(full_url)
            query_params = parse_qs(parsed.query)
            
            print(f"            📦 找到 {len(query_params)} 个查询参数")
            
            # 转换为 OpenAPI 参数格式
            for param_name, param_values in query_params.items():
                # parse_qs 返回的是列表，取第一个值
                example_value = param_values[0] if param_values else ''
                
                # 推断参数类型
                param_type = 'string'
                try:
                    # 尝试转换为数字
                    int_value = int(example_value)
                    param_type = 'integer'
                except:
                    try:
                        float_value = float(example_value)
                        param_type = 'number'
                    except:
                        # 检查布尔值
                        if example_value.lower() in ['true', 'false']:
                            param_type = 'boolean'
                
                parameter = {
                    'name': param_name,
                    'in': 'query',
                    'required': False,  # 从 curl 示例无法判断是否必需，默认为 False
                    'description': f'Example value: {example_value}',
                    'schema': {'type': param_type}
                }
                
                parameters.append(parameter)
                print(f"            ✓ {param_name} = {example_value} ({param_type})")
            
            return parameters
            
        except Exception as e:
            print(f"            ❌ 解析 curl 命令失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _extract_parameters(self) -> List[Dict[str, Any]]:
        """从渲染后的页面提取参数"""
        parameters = []
        
        try:
            # 等待页面加载完成（增加等待时间，确保标签页内容完全渲染）
            print("            ⏳ 等待页面加载...")
            time.sleep(6)  # 增加到6秒，确保所有动态内容都渲染完成
            
            # 方法1: 从 DOM 结构精确提取（最可靠，基于实际 HTML 结构）
            print("            🔍 方法1: 从 DOM 结构精确提取...")
            try:
                params = self._extract_params_from_dom_structure()
                if params and len(params) > 0:
                    print(f"            ✅ 从 DOM 结构提取到 {len(params)} 个参数")
                    return params
                print("            ❌ DOM 结构未找到参数")
            except Exception as e:
                print(f"            ❌ DOM 结构提取失败: {e}")
            
            # 方法2: 从页面的 React 状态中提取
            print("            🔍 方法2: 从 React 状态提取...")
            script = """
            // 尝试从各种可能的位置获取参数数据
            const data = window.__NEXT_DATA__ || 
                        window.__INITIAL_STATE__ || 
                        window.__REACT_QUERY_STATE__ ||
                        {};
            return JSON.stringify(data);
            """
            
            state_json = self.driver.execute_script(script)
            if state_json and state_json != '{}':
                state = json.loads(state_json)
                params = self._extract_params_from_state(state)
                if params:
                    print(f"            ✅ 从 React 状态提取到 {len(params)} 个参数")
                    return params
            print("            ❌ React 状态未找到参数")
            
            # 方法3: 从页面的输入框和表单元素直接提取
            print("            🔍 方法3: 从表单元素提取...")
            try:
                params = self._extract_params_from_form_elements()
                if params:
                    print(f"            ✅ 从表单元素提取到 {len(params)} 个参数")
                    return params
                print("            ❌ 表单元素未找到参数")
            except Exception as e:
                print(f"            ❌ 表单元素解析失败: {e}")
            
            # 禁用方法4：从页面文本提取（容易提取到垃圾数据）
            # print("            🔍 方法4: 从页面文本提取...")
            # params = self._extract_params_from_page_text()
            # if params:
            #     print(f"            ✅ 从页面文本提取到 {len(params)} 个参数")
            #     return params
            
            print("            ℹ️  未找到参数（可能该端点没有 Query Params）")
            
        except Exception as e:
            print(f"            ❌ 参数提取异常: {e}")
        
        return parameters
    
    def _extract_params_from_state(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从 React 状态中提取参数"""
        parameters = []
        
        # 递归查找参数数组
        def find_params(obj, path=""):
            if isinstance(obj, dict):
                # 查找 parameters, queryParams 等键
                for key in ['parameters', 'queryParams', 'params']:
                    if key in obj and isinstance(obj[key], list):
                        return obj[key]
                
                # 递归搜索
                for key, value in obj.items():
                    result = find_params(value, f"{path}.{key}")
                    if result:
                        return result
            
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    result = find_params(item, f"{path}[{i}]")
                    if result:
                        return result
            
            return None
        
        params_data = find_params(state)
        
        if params_data:
            for p in params_data:
                if isinstance(p, dict) and 'name' in p:
                    param = {
                        'name': p.get('name', ''),
                        'in': p.get('in', 'query'),
                        'required': p.get('required', False),
                        'description': p.get('description', ''),
                        'schema': p.get('schema', {'type': p.get('type', 'string')})
                    }
                    parameters.append(param)
        
        return parameters
    
    def _extract_params_from_html(self, html: str) -> List[Dict[str, Any]]:
        """从渲染后的 HTML 提取参数"""
        parameters = []
        
        try:
            # RapidAPI 的参数通常按以下模式显示：
            # 参数名 (类型, required/optional) - 描述
            # 例如: job_title (String, required) - Job title for which to get salary estimation
            
            # 模式1: 查找参数名称、类型和必需性
            # 匹配: job_title ... String ... required
            param_pattern = r'([a-z_][a-z0-9_]*)\s*[<>\"\']*\s*(String|Integer|Number|Boolean|Array|Object|Enum)\s*[<>\"\']*\s*,?\s*(required|optional)?'
            
            matches = re.findall(param_pattern, html, re.IGNORECASE)
            
            # 用于存储已找到的参数，避免重复
            found_params = set()
            
            for match in matches:
                param_name, param_type, required_flag = match
                
                # 过滤常见的非参数词
                if param_name.lower() in ['type', 'class', 'id', 'name', 'value', 'data', 'key', 'style', 'string', 'integer', 'number', 'boolean', 'object', 'array']:
                    continue
                
                # 避免重复
                if param_name in found_params:
                    continue
                
                found_params.add(param_name)
                
                # 转换类型
                type_map = {
                    'string': 'string',
                    'integer': 'integer',
                    'number': 'number',
                    'boolean': 'boolean',
                    'array': 'array',
                    'object': 'object',
                    'enum': 'string'  # Enum 通常是字符串类型
                }
                schema_type = type_map.get(param_type.lower(), 'string')
                
                # 尝试查找描述
                description = ''
                desc_pattern = rf'{param_name}[^<]*?[<>\"\']*\s*{param_type}[^<]*?[<>\"\']*\s*[^<]*?[-:]\s*([^<>{{}}]+)'
                desc_match = re.search(desc_pattern, html, re.IGNORECASE)
                if desc_match:
                    description = desc_match.group(1).strip()
                    # 清理描述
                    description = re.sub(r'\s+', ' ', description)
                    description = description[:200]  # 限制长度
                
                parameter = {
                    'name': param_name,
                    'in': 'query',
                    'required': required_flag.lower() == 'required' if required_flag else False,
                    'description': description,
                    'schema': {'type': schema_type}
                }
                
                parameters.append(parameter)
            
            # 如果找到参数，返回
            if parameters:
                return parameters
            
            # 备用方案：查找更宽松的模式
            param_sections = re.findall(
                r'<[^>]*?(?:data-testid|class|id)[^>]*?(?:param|query)[^>]*?>(.*?)</(?:div|section)>',
                html,
                re.DOTALL | re.IGNORECASE
            )
            
            for section in param_sections:
                # 尝试从 section 中提取参数信息
                name_match = re.search(r'<(?:label|span|div)[^>]*>([a-z_]+)</(?:label|span|div)>', section, re.IGNORECASE)
                if name_match:
                    param_name = name_match.group(1)
                    
                    # 检查是否是合理的参数名
                    if re.match(r'^[a-z_][a-z0-9_]*$', param_name, re.IGNORECASE):
                        # 查找类型
                        type_match = re.search(r'(String|Integer|Boolean|Number|Array|Object|Enum)', section, re.IGNORECASE)
                        param_type = type_match.group(1).lower() if type_match else 'string'
                        if param_type == 'enum':
                            param_type = 'string'
                        
                        # 查找是否必需
                        required = 'required' in section.lower() or '*' in section
                        
                        # 查找描述
                        desc_match = re.search(r'<p[^>]*>(.*?)</p>', section, re.DOTALL)
                        description = desc_match.group(1) if desc_match else ''
                        description = re.sub(r'<[^>]+>', '', description).strip()
                        
                        parameters.append({
                            'name': param_name,
                            'in': 'query',
                            'required': required,
                            'description': description,
                            'schema': {'type': param_type}
                        })
        
        except Exception as e:
            print(f"            HTML 解析异常: {e}")
        
        return parameters
    
    def _parse_param_element(self, element) -> Optional[Dict[str, Any]]:
        """解析单个参数元素"""
        try:
            # 尝试获取参数信息
            # 这需要根据实际的 DOM 结构调整
            
            # 方法1: 从 data 属性获取
            param_data = element.get_attribute('data-param')
            if param_data:
                return json.loads(param_data)
            
            # 方法2: 从文本内容提取
            text = element.text
            # 解析文本...
            
            return None
            
        except:
            return None
    
    def _extract_params_from_form_elements(self) -> List[Dict[str, Any]]:
        """从页面的表单元素（输入框、选择框等）直接提取参数"""
        parameters = []
        
        try:
            # 优先使用 DOM 结构提取（最精确）
            print("            🔍 优先使用 DOM 结构提取...")
            params_from_dom = self._extract_params_from_dom_structure()
            if params_from_dom and len(params_from_dom) > 0:
                return params_from_dom
            
            print("            ⚠️  DOM 结构提取失败，跳过表单元素提取（避免提取垃圾数据）")
            return []
            
            # 注释掉旧的表单元素提取逻辑（容易提取到垃圾数据）
            # 查找所有输入框、文本框等表单元素
            # RapidAPI 通常使用特定的 class 或 data 属性来标识参数输入框
            
            # 尝试多种可能的选择器
            selectors = [
                "input[name][type='text']",
                "input[placeholder]",
                "textarea[name]",
                "select[name]",
                "[data-param-name]",
                "[data-parameter]",
                ".parameter-input",
                ".param-input"
            ]
            
            found_inputs = []
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(self.By.CSS_SELECTOR, selector)
                    found_inputs.extend(elements)
                except:
                    continue
            
            # 去重（同一个元素可能被多个选择器找到）
            unique_inputs = list(set(found_inputs))
            
            for input_element in unique_inputs:
                try:
                    # 获取参数名称
                    param_name = (
                        input_element.get_attribute('name') or
                        input_element.get_attribute('data-param-name') or
                        input_element.get_attribute('placeholder') or
                        input_element.get_attribute('id')
                    )
                    
                    if not param_name or len(param_name) < 2:
                        continue
                    
                    # 过滤掉不相关的字段（更严格的过滤）
                    blacklist = [
                        'search', 'email', 'password', 'username', 
                        'g-recaptcha', 'recaptcha', 'captcha',
                        'search endpoints', 'filter', 'q', 'keyword',
                        'get', 'post', 'feat', 'custom', 'target', 'client',
                        'multitenancy', 'unique', 'and', 'or', 'card', 'phone',
                        'shared', 'security', 'maximum', 'the', 'this'
                    ]
                    if any(black in param_name.lower() for black in blacklist):
                        continue
                    
                    # 只接受合理的参数名格式（字母、数字、下划线、连字符）
                    import re
                    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', param_name):
                        continue
                    
                    # 获取参数类型
                    input_type = input_element.get_attribute('type') or 'string'
                    param_type = 'string'
                    if input_type in ['number', 'integer']:
                        param_type = 'integer'
                    elif input_type == 'checkbox':
                        param_type = 'boolean'
                    
                    # 获取是否必需
                    required = (
                        input_element.get_attribute('required') is not None or
                        input_element.get_attribute('aria-required') == 'true'
                    )
                    
                    # 获取描述或placeholder
                    description = (
                        input_element.get_attribute('placeholder') or
                        input_element.get_attribute('title') or
                        input_element.get_attribute('aria-label') or
                        ''
                    )
                    
                    # 查找相邻的 label
                    try:
                        label_text = self.driver.execute_script("""
                            var input = arguments[0];
                            var label = input.labels ? input.labels[0] : null;
                            if (!label && input.id) {
                                label = document.querySelector('label[for="' + input.id + '"]');
                            }
                            return label ? label.textContent.trim() : '';
                        """, input_element)
                        if label_text:
                            description = label_text + (': ' + description if description else '')
                    except:
                        pass
                    
                    parameter = {
                        'name': param_name,
                        'in': 'query',
                        'required': required,
                        'description': description,
                        'schema': {'type': param_type}
                    }
                    
                    # 避免重复
                    if not any(p['name'] == param_name for p in parameters):
                        parameters.append(parameter)
                        
                except Exception as e:
                    continue
            
            # 如果还是没找到参数，尝试从页面文本中提取
            if not parameters:
                parameters = self._extract_params_from_page_text()
                    
        except Exception as e:
            print(f"            表单元素提取异常: {e}")
        
        return parameters
    
    def _extract_params_from_dom_structure(self) -> List[Dict[str, Any]]:
        """从 DOM 结构精确提取参数（基于 RapidAPI 的实际 DOM 结构）"""
        parameters = []
        
        try:
            print("            🎯 从 DOM 结构提取参数...")
            
            # 更精确的选择器：查找参数区域内的 label 元素
            # 先找到参数容器（在当前激活的 tab 下）
            param_labels = self.driver.find_elements(self.By.XPATH, 
                "//div[@data-state='active']//label[@aria-label and not(contains(@aria-label, 'Request URL'))]")
            
            print(f"            📦 找到 {len(param_labels)} 个参数标签（方法1：激活标签页）")
            
            # 额外检查：尝试从所有可见的输入框获取参数（防止遗漏）
            # 查找所有 label + input 组合
            all_input_labels = self.driver.find_elements(self.By.XPATH, 
                "//label[@aria-label]//ancestor::div[1]//input/..//label[@aria-label]")
            if len(all_input_labels) > len(param_labels):
                print(f"            📦 找到额外 {len(all_input_labels) - len(param_labels)} 个可能的参数标签（方法2：所有输入框）")
                # 合并但去重
                existing_labels = set([l.get_attribute('aria-label') for l in param_labels if l.get_attribute('aria-label')])
                for label in all_input_labels:
                    label_text = label.get_attribute('aria-label')
                    if label_text and label_text not in existing_labels:
                        param_labels.append(label)
                        existing_labels.add(label_text)
                        print(f"            ➕ 添加遗漏的参数: {label_text}")
            
            print(f"            📦 总共 {len(param_labels)} 个参数标签待处理")
            
            # 如果找不到参数，保存页面用于调试
            if len(param_labels) == 0:
                try:
                    import os
                    os.makedirs('debug', exist_ok=True)
                    debug_html = f"debug/debug_params_{int(time.time())}.html"
                    with open(debug_html, 'w', encoding='utf-8') as f:
                        f.write(self.driver.page_source)
                    print(f"            💾 页面已保存到: {debug_html}（用于调试）")
                except:
                    pass
                
                # 尝试更宽松的选择器（但仍限制在激活的标签页内）
                print("            🔍 尝试更宽松的选择器...")
                # 关键修复：确保只查找当前激活标签页内的元素
                param_labels = self.driver.find_elements(self.By.XPATH, 
                    "//div[@data-state='active']//label[@aria-label]")
                print(f"            📦 找到 {len(param_labels)} 个 label 元素（仅激活标签页）")
                
                # 如果还是找不到，尝试所有label（包括不可见的，因为RapidAPI用invisible容器）
                if len(param_labels) == 0:
                    print("            🔍 尝试查找所有label（包括不可见容器中的）...")
                    # RapidAPI特殊处理：参数可能在invisible的容器中
                    all_labels = self.driver.find_elements(self.By.XPATH, "//label[@aria-label]")
                    print(f"            📦 找到 {len(all_labels)} 个 label 元素（包含不可见的）")
                    param_labels = all_labels
            
            for label_elem in param_labels:
                try:
                    # 1. 获取参数名
                    param_name = label_elem.get_attribute('aria-label')
                    if not param_name:
                        continue
                    
                    # 过滤黑名单（更严格）
                    blacklist = [
                        'app', 'x-rapidapi-key', 'x-rapidapi-host', 'request url',
                        'target', 'client', 'search endpoints', 'search',
                        'get', 'post', 'put', 'delete', 'feat', 'custom',
                        'g-recaptcha', 'recaptcha',
                        'rapid_do_not_include_in_request_key',  # RapidAPI 内部参数
                        'content-type', 'content type', 'accept', 'user-agent',  # HTTP 标准 headers
                        'authorization', 'cookie', 'referer', 'origin', 'host'   # 更多标准 headers
                    ]
                    if param_name.lower() in blacklist:
                        print(f"            ⊗ 过滤黑名单: {param_name}")
                        continue
                    
                    # 过滤太短或太长的参数名
                    # 但是保留常见的单字符参数（如 q, x, y, z 等）
                    common_single_char_params = ['q', 'x', 'y', 'z', 'n', 'k', 'v', 't', 's', 'p', 'i', 'id']
                    if len(param_name) < 1 or len(param_name) > 50:
                        print(f"            ⊗ 过滤长度: {param_name}")
                        continue
                    if len(param_name) == 1 and param_name.lower() not in common_single_char_params:
                        print(f"            ⊗ 过滤单字符（非白名单）: {param_name}")
                        continue
                    
                    # RapidAPI特殊处理：不检查可见性，因为参数可能在invisible容器中
                    # （RapidAPI使用invisible容器存储参数数据）
                    # 跳过可见性检查
                    
                    print(f"            🔍 解析参数: {param_name}")
                    
                    # 2. 获取父容器
                    parent = label_elem.find_element(self.By.XPATH, './ancestor::div[contains(@class, "flex-col")][1]')
                    
                    # 3. 检查是否必需（查找红色星号或 optional 标记）
                    required = False
                    try:
                        required_span = parent.find_elements(self.By.XPATH, './/span[contains(@class, "text-red-500")]')
                        required = len(required_span) > 0
                    except:
                        pass
                    
                    if not required:
                        try:
                            optional_span = parent.find_elements(self.By.XPATH, './/span[contains(text(), "optional")]')
                            required = len(optional_span) == 0
                        except:
                            pass
                    
                    # 4. 获取输入框和示例值
                    example_value = ''
                    input_type = 'string'
                    try:
                        input_elem = parent.find_element(self.By.TAG_NAME, 'input')
                        example_value = input_elem.get_attribute('value') or ''
                        input_html_type = input_elem.get_attribute('type')
                        
                        # 根据 input type 推断参数类型
                        if input_html_type == 'number':
                            input_type = 'integer' if '.' not in example_value else 'number'
                        elif input_html_type == 'checkbox':
                            input_type = 'boolean'
                    except:
                        pass
                    
                    # 5. 获取类型标签（String/Number 等）
                    param_type = input_type
                    try:
                        type_spans = parent.find_elements(self.By.XPATH, 
                            './/span[contains(@class, "text-[10px]") and contains(@class, "text-gray-900")]')
                        if type_spans:
                            type_text = type_spans[0].text.strip().lower()
                            type_map = {
                                'string': 'string',
                                'number': 'number',
                                'integer': 'integer',
                                'boolean': 'boolean',
                                'array': 'array',
                                'object': 'object'
                            }
                            param_type = type_map.get(type_text, 'string')
                    except:
                        pass
                    
                    # 6. 获取描述（markdown 区域）
                    # 使用 textContent 而不是 text，因为元素可能在invisible容器中
                    description = ''
                    try:
                        desc_divs = parent.find_elements(self.By.XPATH, 
                            './/div[contains(@class, "markdown")]')
                        if desc_divs:
                            # 优先使用textContent（不受可见性影响）
                            description = desc_divs[0].get_attribute('textContent') or desc_divs[0].text
                            description = description.strip()
                            # 清理换行和多余空格
                            description = ' '.join(description.split())
                            # 限制描述长度
                            description = description[:500]
                    except:
                        pass
                    
                    # 7. 获取默认值
                    default_value = None
                    try:
                        default_divs = parent.find_elements(self.By.XPATH, 
                            './/div[contains(@class, "text-gray-500")]')
                        for div in default_divs:
                            text = div.get_attribute('textContent') or div.text
                            if 'Default:' in text:
                                default_value = text.replace('Default:', '').strip()
                                break
                    except:
                        pass
                    
                    # 8. 构建参数对象
                    parameter = {
                        'name': param_name,
                        'in': 'query',
                        'required': required,
                        'description': description or f'Example value: {example_value}',
                        'schema': {
                            'type': param_type
                        }
                    }
                    
                    if default_value:
                        parameter['schema']['default'] = default_value
                    
                    if example_value:
                        parameter['schema']['example'] = example_value
                    
                    parameters.append(parameter)
                    print(f"            ✓ {param_name} ({param_type}, {'required' if required else 'optional'})")
                    if description:
                        print(f"              描述: {description[:80]}...")
                    
                except Exception as e:
                    print(f"            ⚠️  解析参数 {param_name} 失败: {e}")
                    continue
            
            # 最后检查：针对特定端点类型的智能补全
            # 如果是 auto-complete 或 search 端点但没有 q 参数，发出警告
            current_url = self.driver.current_url.lower()
            param_names = [p['name'] for p in parameters]
            
            if ('auto-complete' in current_url or 'search' in current_url) and 'q' not in param_names and 'query' not in param_names:
                print(f"            ⚠️  警告: {current_url}")
                print(f"               这是一个搜索/自动补全端点，但未找到 'q' 或 'query' 参数")
                print(f"               当前找到的参数: {param_names}")
                print(f"               这可能导致 API 调用失败！")
                
                # 尝试最后一次查找：搜索页面上任何名为 'q' 或 'query' 的输入框
                try:
                    q_inputs = self.driver.find_elements(self.By.XPATH, 
                        "//input[@name='q' or @name='query' or @placeholder='query' or @placeholder='search']")
                    if q_inputs:
                        print(f"            🔍 发现隐藏的查询输入框！尝试提取...")
                        for q_input in q_inputs:
                            try:
                                # 尝试找到对应的 label
                                label_elem = q_input.find_element(self.By.XPATH, 
                                    "./preceding-sibling::label[1] | ./ancestor::div[contains(@class, 'flex-col')][1]//label[1]")
                                param_name = label_elem.get_attribute('aria-label') or q_input.get_attribute('name') or 'q'
                                
                                if param_name not in param_names:
                                    print(f"            ✅ 找到遗漏的参数: {param_name}")
                                    parameters.append({
                                        'name': param_name,
                                        'in': 'query',
                                        'required': True,
                                        'description': 'Query for suggestions' if 'auto-complete' in current_url else 'Search query',
                                        'schema': {'type': 'string'}
                                    })
                            except:
                                continue
                except:
                    pass
            
            return parameters
            
        except Exception as e:
            print(f"            ❌ DOM 结构提取失败: {e}")
            return []
    
    def _extract_params_from_visible_text(self) -> List[Dict[str, Any]]:
        """从页面可见文本中提取参数信息（备用方法）"""
        parameters = []
        
        try:
            # 首先尝试定位到 "Query Params" 区域
            print("            🎯 定位 Query Params 区域...")
            params_section = None
            
            try:
                # 查找包含 "Query Params" 标题的区域
                sections = self.driver.find_elements(self.By.XPATH, 
                    "//*[contains(text(), 'Query Params') or contains(text(), 'Parameters')]/following-sibling::*[1] | "
                    "//*[contains(text(), 'Query Params') or contains(text(), 'Parameters')]/parent::*/following-sibling::*[1]")
                
                if sections:
                    params_section = sections[0]
                    page_text = params_section.text
                    print(f"            ✅ 找到参数区域（长度: {len(page_text)}）")
                else:
                    # 如果找不到特定区域，尝试找到包含参数的 div
                    # 通常参数在特定的 class 中
                    params_containers = self.driver.find_elements(self.By.XPATH,
                        "//*[contains(@class, 'param') or contains(@class, 'field')]")
                    
                    if params_containers:
                        # 获取所有参数容器的文本
                        page_text = '\n'.join([c.text for c in params_containers if c.text])
                        print(f"            ✅ 从参数容器提取（{len(params_containers)} 个容器）")
                    else:
                        # 最后的手段：从整个 body 获取，但这不太可靠
                        page_text = self.driver.find_element(self.By.TAG_NAME, "body").text
                        print("            ⚠️  使用整个页面文本（可能不准确）")
                        
            except Exception as e:
                page_text = self.driver.find_element(self.By.TAG_NAME, "body").text
                print(f"            ⚠️  定位失败，使用整个页面: {e}")
            
            # RapidAPI 参数格式：
            # query *
            # String
            # Free-form jobs search query...
            # page (optional)
            # Number
            # Page to return...
            
            # 提取参数名称行（通常是单独一行，后面跟着类型）
            lines = page_text.split('\n')
            
            # 先找到 "Query Params" 标记的位置
            start_idx = 0
            end_idx = len(lines)
            
            for idx, line in enumerate(lines):
                if 'Query Params' in line or 'Parameters' in line:
                    start_idx = idx + 1
                    break
            
            # 找到结束标记（通常是下一个大标题）
            for idx in range(start_idx, len(lines)):
                line = lines[idx].strip()
                # 如果遇到其他主要标题，停止
                if any(marker in line for marker in ['Headers', 'Body', 'Response', 'Authorization', 'Code Snippets']):
                    end_idx = idx
                    break
            
            print(f"            📍 解析行范围: {start_idx} 到 {end_idx}")
            
            i = start_idx
            while i < end_idx:
                line = lines[i].strip()
                
                # 跳过空行
                if not line:
                    i += 1
                    continue
                
                # 查找参数名称（可能带有 * 或 (optional)）
                # 参数名通常是 snake_case 或 camelCase
                param_match = re.match(r'^([a-z_][a-z0-9_]*)\s*(\*|\(optional\))?$', line, re.IGNORECASE)
                
                if param_match and i + 1 < end_idx:
                    param_name = param_match.group(1)
                    is_required_marker = param_match.group(2)
                    
                    # 下一行应该是类型
                    next_line = lines[i + 1].strip()
                    type_match = re.match(r'^(String|Integer|Number|Boolean|Array|Object|Enum)$', next_line, re.IGNORECASE)
                    
                    if type_match:
                        param_type = type_match.group(1).lower()
                        if param_type == 'enum':
                            param_type = 'string'
                        
                        # 判断是否必需
                        required = is_required_marker == '*'
                        
                        # 查找描述（通常在类型后面）
                        description = ''
                        if i + 2 < end_idx:
                            desc_line = lines[i + 2].strip()
                            # 描述通常不是参数名或类型
                            if desc_line and not re.match(r'^(String|Integer|Number|Boolean|Array|Object|Enum|[a-z_][a-z0-9_]*\s*[\*\(]?)$', desc_line, re.IGNORECASE):
                                description = desc_line[:200]  # 限制长度
                        
                        # 更严格的黑名单过滤
                        blacklist = [
                            'search endpoints', 'query params', 'headers', 'body', 'authorization',
                            'get', 'post', 'put', 'delete', 'feat', 'custom', 'multitena', 'unique',
                            'and', 'or', 'card', 'phone', 'shared', 'security', 'maximum', 'the', 'this'
                        ]
                        
                        # 检查参数名是否在黑名单中
                        if not any(black in param_name.lower() for black in blacklist):
                            parameter = {
                                'name': param_name,
                                'in': 'query',
                                'required': required,
                                'description': description,
                                'schema': {'type': param_type}
                            }
                            
                            # 避免重复
                            if not any(p['name'] == param_name for p in parameters):
                                parameters.append(parameter)
                                print(f"            ✓ 找到参数: {param_name} ({param_type}, {'required' if required else 'optional'})")
                        
                        # 跳过已处理的行
                        i += 2
                        continue
                
                i += 1
            
            if parameters:
                print(f"            ✅ 共提取到 {len(parameters)} 个有效参数")
                    
        except Exception as e:
            print(f"            ❌ 可见文本提取异常: {e}")
        
        return parameters
    
    def _extract_params_from_page_text(self) -> List[Dict[str, Any]]:
        """从页面源码中提取参数信息（备用方法）"""
        parameters = []
        
        try:
            # 获取页面源码
            page_source = self.driver.page_source
            
            # 查找"REQUIRED"或"OPTIONAL"标记附近的参数名称
            # 常见模式: query (string, required) - Search query
            param_pattern = r'([a-z_][a-z0-9_]*)\s*\(?\s*(string|integer|number|boolean|array|object)\s*,?\s*(required|optional)?\s*\)?'
            
            matches = re.findall(param_pattern, page_source, re.IGNORECASE)
            
            for match in matches:
                param_name, param_type, required_flag = match
                
                # 过滤常见的非参数词
                blacklist = ['type', 'class', 'id', 'name', 'value', 'data', 'key', 'style', 'search', 'filter']
                if param_name.lower() in blacklist:
                    continue
                
                parameter = {
                    'name': param_name,
                    'in': 'query',
                    'required': required_flag.lower() == 'required' if required_flag else False,
                    'description': '',
                    'schema': {'type': param_type.lower()}
                }
                
                # 避免重复
                if not any(p['name'] == param_name for p in parameters):
                    parameters.append(parameter)
                    
        except Exception as e:
            pass
        
        return parameters
    
    def _click_and_extract_responses(self) -> Dict[str, Any]:
        """返回基础响应结构（简化，不提取详细结构）"""
        try:
            print("            🔍 生成基础响应结构...")
            
            # 直接返回基础的 object 类型，不需要深度提取
            return {
                "200": {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object"
                            }
                        }
                    }
                }
            }
            
        except Exception as e:
            print(f"            ❌ 生成响应结构失败: {e}")
            return {
                "200": {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object"
                            }
                        }
                    }
                }
            }
    
    def _extract_responses(self) -> Dict[str, Any]:
        """从渲染后的页面提取响应结构"""
        try:
            print("            🔍 提取响应结构...")
            
            # 方法2: 从页面状态提取响应数据
            print("            🔍 从 React 状态查找响应示例...")
            script = """
            // 查找响应示例数据
            const data = window.__NEXT_DATA__ || window.__INITIAL_STATE__ || {};
            // 查找 example 或 response
            function findExample(obj) {
                if (obj && typeof obj === 'object') {
                    if (obj.example || obj.exampleResponse || obj.response) {
                        return obj.example || obj.exampleResponse || obj.response;
                    }
                    for (let key in obj) {
                        const result = findExample(obj[key]);
                        if (result) return result;
                    }
                }
                return null;
            }
            return JSON.stringify(findExample(data));
            """
            
            example_json = self.driver.execute_script(script)
            if example_json and example_json != 'null':
                try:
                    example = json.loads(example_json)
                    schema = self._infer_schema_from_example(example)
                    print(f"            ✅ 从 React 状态提取到响应结构（{len(schema.get('properties', {}))} 个属性）")
                    
                    return {
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {
                                    "schema": schema,
                                    "example": example
                                }
                            }
                        }
                    }
                except Exception as e:
                    print(f"            ❌ React 状态解析失败: {e}")
            
            # 方法3: 从页面的可见文本中提取 JSON
            print("            🔍 从页面可见文本提取响应...")
            try:
                # 方法3.1: 查找 Body/Schema 标签下的内容
                # 点击 Schema 标签（如果有的话）
                try:
                    schema_tabs = self.driver.find_elements(self.By.XPATH, "//*[text()='Schema' or text()='Body']")
                    for tab in schema_tabs:
                        if tab.is_displayed():
                            try:
                                self.driver.execute_script("arguments[0].click();", tab)
                                time.sleep(1)
                                print("            📍 点击了 Schema/Body 标签")
                                break
                            except:
                                continue
                except:
                    pass
                
                # 方法3.2: 尝试找到包含 JSON 的元素（更全面的选择器）
                json_elements = self.driver.find_elements(self.By.XPATH, 
                    "//pre | //code | //*[contains(@class, 'json')] | //*[contains(@class, 'response')] | //*[contains(@class, 'example')]")
                
                print(f"            📦 找到 {len(json_elements)} 个可能包含 JSON 的元素")
                
                for idx, elem in enumerate(json_elements):
                    try:
                        text = elem.text.strip()
                        
                        # 跳过太短的文本
                        if not text or len(text) < 30:
                            continue
                        
                        # 检查是否看起来像 JSON
                        if not (text.startswith('{') or text.startswith('[')):
                            continue
                        
                        print(f"            🔍 尝试解析元素 #{idx+1}（长度: {len(text)}）")
                        
                        # 清理可能的干扰字符
                        text = text.strip()
                        
                        # 尝试解析 JSON
                        response_obj = json.loads(text)
                        
                        # 验证是否是有效的 API 响应（至少有一些键）
                        if isinstance(response_obj, dict) and len(response_obj) > 0:
                            schema = self._infer_schema_from_example(response_obj)
                            prop_count = len(schema.get('properties', {}))
                            
                            # 只接受有合理数量属性的响应
                            if prop_count >= 2:
                                print(f"            ✅ 从可见元素 #{idx+1} 提取到响应结构（{prop_count} 个属性）")
                                return {
                                    "200": {
                                        "description": "Successful response",
                                        "content": {
                                            "application/json": {
                                                "schema": schema,
                                                "example": response_obj
                                            }
                                        }
                                    }
                                }
                        elif isinstance(response_obj, list) and len(response_obj) > 0:
                            schema = self._infer_schema_from_example(response_obj)
                            print(f"            ✅ 从可见元素 #{idx+1} 提取到数组响应结构")
                            return {
                                "200": {
                                    "description": "Successful response",
                                    "content": {
                                        "application/json": {
                                            "schema": schema,
                                            "example": response_obj
                                        }
                                    }
                                }
                            }
                    except json.JSONDecodeError as e:
                        # JSON 解析失败，继续下一个
                        continue
                    except Exception as e:
                        continue
                        
            except Exception as e:
                print(f"            ❌ 可见文本提取失败: {e}")
            
            # 方法4: 尝试从页面 HTML 提取
            print("            🔍 从页面 HTML 代码块提取响应...")
            page_source = self.driver.page_source
            
            # 查找 JSON 代码块（更宽松的匹配）
            json_blocks = re.findall(r'<(?:code|pre)[^>]*>(.*?)</(?:code|pre)>', page_source, re.DOTALL)
            print(f"            📦 找到 {len(json_blocks)} 个代码块")
            
            for i, block in enumerate(json_blocks):
                # 清理 HTML 标签和实体
                clean_text = re.sub(r'<[^>]+>', '', block)
                clean_text = clean_text.replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
                clean_text = clean_text.replace('&#x27;', "'").replace('&#39;', "'")
                clean_text = clean_text.strip()
                
                # 检查是否看起来像 JSON
                if not clean_text or len(clean_text) < 30:
                    continue
                    
                if not (clean_text.startswith('{') or clean_text.startswith('[')):
                    continue
                
                try:
                    response_obj = json.loads(clean_text)
                    
                    # 验证响应质量
                    if isinstance(response_obj, dict) and len(response_obj) >= 2:
                        schema = self._infer_schema_from_example(response_obj)
                        prop_count = len(schema.get('properties', {}))
                        
                        if prop_count >= 2:
                            print(f"            ✅ 从代码块 #{i+1} 提取到响应结构（{prop_count} 个属性）")
                            return {
                                "200": {
                                    "description": "Successful response",
                                    "content": {
                                        "application/json": {
                                            "schema": schema,
                                            "example": response_obj
                                        }
                                    }
                                }
                            }
                    elif isinstance(response_obj, list) and len(response_obj) > 0:
                        schema = self._infer_schema_from_example(response_obj)
                        print(f"            ✅ 从代码块 #{i+1} 提取到数组响应结构")
                        return {
                            "200": {
                                "description": "Successful response",
                                "content": {
                                    "application/json": {
                                        "schema": schema,
                                        "example": response_obj
                                    }
                                }
                            }
                        }
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    continue
            
            print("            ⚠️  未找到有效的响应示例")
            
        except Exception as e:
            print(f"            ❌ 响应提取异常: {e}")
        
        # 返回基本响应结构
        return {
            "200": {
                "description": "Successful response",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object"
                        }
                    }
                }
            }
        }
    
    def _infer_schema_from_example(self, example: Any, depth: int = 0, max_depth: int = 3) -> Dict[str, Any]:
        """从响应示例推断 Schema（递归，限制深度）"""
        if depth > max_depth:
            return {"type": "object"}
        
        if isinstance(example, dict):
            schema = {
                "type": "object",
                "properties": {}
            }
            # 限制属性数量，避免过大
            for i, (key, value) in enumerate(example.items()):
                if i >= 20:  # 最多处理20个属性
                    schema["properties"]["..."] = {"type": "object", "description": "更多属性..."}
                    break
                schema["properties"][key] = self._infer_schema_from_example(value, depth + 1, max_depth)
            return schema
        elif isinstance(example, list):
            if example and len(example) > 0:
                return {
                    "type": "array",
                    "items": self._infer_schema_from_example(example[0], depth + 1, max_depth)
                }
            else:
                return {"type": "array", "items": {"type": "object"}}
        elif isinstance(example, str):
            return {"type": "string", "example": example[:50] if len(example) < 100 else example[:50] + "..."}
        elif isinstance(example, bool):
            return {"type": "boolean"}
        elif isinstance(example, int):
            return {"type": "integer", "example": example}
        elif isinstance(example, float):
            return {"type": "number", "example": example}
        elif example is None:
            return {"type": "null"}
        else:
            return {"type": "object"}
    
    def close(self):
        """关闭浏览器"""
        if hasattr(self, 'driver'):
            self.driver.quit()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def scrape_with_selenium(
    base_url: str,
    endpoints: List[Dict[str, Any]],
    headless: bool = True,
    enable_screenshots: bool = True
) -> List[Dict[str, Any]]:
    """
    使用 Selenium 爬取所有端点的完整信息
    
    Args:
        base_url: API 基础 URL
        endpoints: 端点列表
        headless: 是否无头模式
        enable_screenshots: 是否启用自动截图（记录操作过程）
    
    Returns:
        更新后的端点列表（包含完整参数和响应）
    """
    try:
        with RapidAPISeleniumScraper(headless, enable_screenshots) as scraper:
            enriched = []
            
            for i, endpoint in enumerate(endpoints):
                print(f"   📍 端点 {i+1}/{len(endpoints)}: {endpoint.get('name', 'Unknown')}")
                
                if 'id' not in endpoint:
                    print(f"      ⚠️  缺少端点 ID，跳过")
                    enriched.append(endpoint)
                    continue
                
                endpoint_url = f"{base_url}/playground/{endpoint['id']}"
                details = scraper.scrape_endpoint_full(endpoint_url)
                
                # 合并信息
                updated = endpoint.copy()
                if details.get('parameters'):
                    updated['parameters'] = details['parameters']
                if details.get('responses'):
                    updated['responses'] = details['responses']
                
                enriched.append(updated)
                
                # 延迟
                if i < len(endpoints) - 1:
                    time.sleep(1)
            
            return enriched
            
    except ImportError as e:
        print(f"   ⚠️  Selenium 未安装: {e}")
        print(f"   💡 使用基础方法或安装: pip install selenium")
        return endpoints
    except Exception as e:
        print(f"   ⚠️  Selenium 爬取失败: {e}")
        return endpoints

