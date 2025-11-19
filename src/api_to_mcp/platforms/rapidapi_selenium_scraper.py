"""
RapidAPI Selenium 爬虫 - 使用浏览器自动化完整提取参数和响应
"""
from typing import Dict, Any, List, Optional
import json
import time
import re


class RapidAPISeleniumScraper:
    """使用 Selenium 完整爬取 RapidAPI"""
    
    def __init__(self, headless: bool = True):
        """
        初始化 Selenium
        
        Args:
            headless: 是否无头模式（不显示浏览器窗口）
        """
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
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
                print("            ✅ ChromeDriver 初始化成功")
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
            time.sleep(3)  # 等待 JavaScript 加载
            
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
            
            # 2. 提取 Query Params
            print("            🔍 提取 Query Params...")
            query_params = self._extract_tab_params("Params")
            if query_params:
                all_params['query'] = query_params
                print(f"            ✅ 提取到 {len(query_params)} 个查询参数")
            
            # 3. 提取 Headers
            print("            🔍 提取 Headers...")
            headers = self._extract_tab_params("Headers")
            if headers:
                all_params['header'] = headers
                print(f"            ✅ 提取到 {len(headers)} 个 Header 参数")
            
            # 4. 提取 Body
            print("            🔍 提取 Body 参数...")
            body_data = self._extract_body_params()
            if body_data:
                all_params['body'] = body_data
                print(f"            ✅ 提取到 Body 参数")
            
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
    
    def _extract_tab_params(self, tab_name: str) -> List[Dict[str, Any]]:
        """通用的标签页参数提取方法"""
        try:
            # 点击指定标签页
            print(f"            📍 点击 {tab_name} 标签...")
            tab_xpath = f"//*[contains(text(), '{tab_name}') and @role='tab']"
            tabs = self.driver.find_elements(self.By.XPATH, tab_xpath)
            
            tab_clicked = False
            for tab in tabs:
                if tab.is_displayed():
                    try:
                        self.driver.execute_script("arguments[0].click();", tab)
                        time.sleep(2)
                        tab_clicked = True
                        print(f"            ✅ 点击了 {tab_name} 标签")
                        break
                    except:
                        continue
            
            if not tab_clicked:
                print(f"            ⚠️  未找到 {tab_name} 标签")
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
            body_tabs = self.driver.find_elements(self.By.XPATH, 
                "//*[text()='Body' and @role='tab']")
            
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
            # 等待页面加载完成
            print("            ⏳ 等待页面加载...")
            time.sleep(3)  # 增加等待时间
            
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
            
            print(f"            📦 找到 {len(param_labels)} 个参数标签")
            
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
                
                # 尝试更宽松的选择器
                print("            🔍 尝试更宽松的选择器...")
                param_labels = self.driver.find_elements(self.By.XPATH, 
                    "//label[@aria-label]")
                print(f"            📦 找到 {len(param_labels)} 个 label 元素")
            
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
                        'content-type', 'content type', 'accept', 'user-agent',  # HTTP 标准 headers
                        'authorization', 'cookie', 'referer', 'origin', 'host'   # 更多标准 headers
                    ]
                    if param_name.lower() in blacklist:
                        print(f"            ⊗ 过滤黑名单: {param_name}")
                        continue
                    
                    # 过滤太短或太长的参数名
                    if len(param_name) < 2 or len(param_name) > 50:
                        print(f"            ⊗ 过滤长度: {param_name}")
                        continue
                    
                    # 检查元素是否真的可见（排除 invisible 的元素）
                    try:
                        parent_classes = label_elem.find_element(self.By.XPATH, './ancestor::div[1]').get_attribute('class') or ''
                        if 'invisible' in parent_classes or '!invisible' in parent_classes:
                            print(f"            ⊗ 过滤不可见元素: {param_name}")
                            continue
                    except:
                        pass
                    
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
                    description = ''
                    try:
                        desc_divs = parent.find_elements(self.By.XPATH, 
                            './/div[contains(@class, "markdown")]')
                        if desc_divs:
                            description = desc_divs[0].text.strip()
                            # 限制描述长度
                            description = description[:500]
                    except:
                        pass
                    
                    # 7. 获取默认值
                    default_value = None
                    try:
                        default_divs = parent.find_elements(self.By.XPATH, 
                            './/div[contains(@class, "text-gray-500") and contains(text(), "Default:")]')
                        if default_divs:
                            default_text = default_divs[0].text
                            default_value = default_text.replace('Default:', '').strip()
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
    headless: bool = True
) -> List[Dict[str, Any]]:
    """
    使用 Selenium 爬取所有端点的完整信息
    
    Args:
        base_url: API 基础 URL
        endpoints: 端点列表
        headless: 是否无头模式
    
    Returns:
        更新后的端点列表（包含完整参数和响应）
    """
    try:
        with RapidAPISeleniumScraper(headless) as scraper:
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

