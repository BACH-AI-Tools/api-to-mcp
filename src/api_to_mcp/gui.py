"""
GUI 可视化界面 - 使用 Streamlit
"""
import streamlit as st
import os
import sys
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from api_to_mcp.parsers import OpenAPIParser
from api_to_mcp.platforms import RapidAPISpecFetcher
from api_to_mcp.platforms.rapidapi_helper import RapidAPIHelper
from api_to_mcp.platforms.rapidapi_auto import auto_extract_rapidapi
from api_to_mcp.enhancer import DescriptionEnhancer
from api_to_mcp.generator import MCPGenerator
from api_to_mcp.config import AzureOpenAIConfig


def main():
    st.set_page_config(
        page_title="API to MCP 转换器",
        page_icon="🚀",
        layout="wide",
        menu_items={
            'Get Help': None,
            'Report a bug': None,
            'About': "# API to MCP 转换器\n将 Web API 自动转换为 MCP 服务器"
        }
    )
    
    # 隐藏 Streamlit 的默认菜单和页脚
    hide_streamlit_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)
    
    st.title("🚀 API to MCP 转换器")
    st.markdown("将任何 Web API 自动转换为 MCP 服务器")
    
    # 侧边栏 - 配置
    with st.sidebar:
        st.header("⚙️ 配置")
        
        output_dir = st.text_input(
            "输出目录",
            value="generated_mcps",
            help="生成的 MCP 服务器保存目录"
        )
        
        transport = st.selectbox(
            "传输协议",
            options=["stdio", "sse", "streamable-http"],
            help="MCP 服务器的传输协议"
        )
        
        enhance = st.checkbox(
            "使用 LLM 增强描述",
            value=True,
            help="使用 Azure OpenAI 优化 API 描述"
        )
        
        verify_ssl = st.checkbox(
            "验证 SSL 证书",
            value=True,
            help="是否验证 HTTPS 证书"
        )
        
        st.divider()
        
        # EMCP 推广配置
        with st.expander("📣 EMCP 推广配置"):
            st.markdown("自定义生成的 README 中的 EMCP 引流话术")
            
            use_custom_promo = st.checkbox(
                "使用自定义推广语句",
                value=False,
                help="勾选后可以编辑自定义的推广内容"
            )
            
            if use_custom_promo:
                custom_promo_zh = st.text_area(
                    "简体中文推广语句",
                    height=150,
                    placeholder="输入中文推广内容...",
                    help="支持 Markdown 格式，使用 {package_name} 作为包名占位符"
                )
                
                custom_promo_en = st.text_area(
                    "English Promotion",
                    height=150,
                    placeholder="Enter English promotion content...",
                    help="Supports Markdown, use {package_name} as package name placeholder"
                )
                
                custom_promo_tw = st.text_area(
                    "繁體中文推廣語句",
                    height=150,
                    placeholder="輸入繁體中文推廣內容...",
                    help="支援 Markdown 格式，使用 {package_name} 作為套件名佔位符"
                )
                
                # 保存到 session state
                if custom_promo_zh or custom_promo_en or custom_promo_tw:
                    st.session_state['custom_emcp_promo'] = {
                        'zh': custom_promo_zh,
                        'en': custom_promo_en,
                        'zh_tw': custom_promo_tw
                    }
            else:
                # 显示默认推广语句预览
                st.info("使用默认推广语句：引导用户访问 https://sit-emcp.kaleido.guru")
                if st.button("预览默认推广语句"):
                    st.markdown("""
### 默认推广语句（简体中文）

**[EMCP](https://sit-emcp.kaleido.guru)** 是一个强大的 MCP 服务器管理平台，让您无需手动配置即可快速使用各种 MCP 服务器！

1. 🌐 访问 **[EMCP 平台](https://sit-emcp.kaleido.guru)**
2. 📝 注册并登录账号
3. 🎯 进入 **MCP 广场**
4. 🔍 搜索或找到本服务器
5. 🎉 点击 **"安装 MCP"** 按钮
6. ✅ 完成！即可使用
                    """)
        
        st.divider()
        
        # Azure OpenAI 配置
        with st.expander("🤖 Azure OpenAI 配置"):
            azure_config = AzureOpenAIConfig.from_env()
            st.info(f"**Endpoint**: {azure_config.endpoint}")
            st.info(f"**Model**: {azure_config.deployment_name}")
    
    # 主要内容
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📄 文件上传", "🌐 URL 导入", "🚀 RapidAPI", "🔥 批量爬取", "📊 历史记录"])
    
    # Tab 1: 文件上传
    with tab1:
        st.header("📄 从文件转换")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            uploaded_file = st.file_uploader(
                "选择 OpenAPI/Swagger 规范文件",
                type=["json", "yaml", "yml"],
                help="支持 OpenAPI 3.0+ 和 Swagger 2.0"
            )
        
        with col2:
            custom_name = st.text_input(
                "自定义服务器名称（可选）",
                help="留空则自动从 API 标题生成"
            )
        
        if uploaded_file is not None:
            st.success(f"✅ 已选择文件: {uploaded_file.name}")
            
            if st.button("🚀 开始转换", type="primary", use_container_width=True):
                with st.spinner("正在转换..."):
                    try:
                        # 保存上传的文件
                        temp_file = f"temp_{uploaded_file.name}"
                        with open(temp_file, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        # 解析
                        parser = OpenAPIParser()
                        api_spec = parser.parse_file(temp_file)
                        
                        st.success(f"✅ 解析成功: {api_spec.title} v{api_spec.version}")
                        st.info(f"📍 端点数量: {len(api_spec.endpoints)}")
                        
                        # 增强
                        if enhance:
                            with st.spinner("🤖 使用 LLM 增强描述..."):
                                enhancer = DescriptionEnhancer()
                                api_spec = enhancer.enhance_api_spec(api_spec)
                            st.success("✅ 描述增强完成")
                        
                        # 生成
                        with st.spinner("🔨 生成 MCP 服务器..."):
                            custom_promo = st.session_state.get('custom_emcp_promo', None)
                            generator = MCPGenerator(
                                output_dir=output_dir,
                                emcp_promotion=custom_promo
                            )
                            mcp_server = generator.generate(
                                api_spec,
                                transport=transport,
                                custom_name=custom_name if custom_name else None
                            )
                        
                        # 显示结果
                        st.success("🎉 生成完成!")
                        
                        result_col1, result_col2 = st.columns(2)
                        with result_col1:
                            st.metric("服务器名称", mcp_server.name)
                            st.metric("工具数量", len(mcp_server.tools))
                        with result_col2:
                            st.metric("版本", mcp_server.version)
                            st.metric("传输协议", transport)
                        
                        st.code(f"cd {mcp_server.output_path}\npython server.py", language="bash")
                        
                        # 显示生成的文件内容
                        with st.expander("查看生成的 server.py"):
                            server_file = Path(mcp_server.output_path) / "server.py"
                            if server_file.exists():
                                st.code(server_file.read_text(encoding='utf-8'), language="python")
                        
                        # 清理临时文件
                        os.remove(temp_file)
                        
                    except Exception as e:
                        st.error(f"❌ 错误: {str(e)}")
                        import traceback
                        with st.expander("查看详细错误"):
                            st.code(traceback.format_exc())
    
    # Tab 2: URL 导入
    with tab2:
        st.header("🌐 从 URL 转换")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            spec_url = st.text_input(
                "OpenAPI 规范 URL",
                placeholder="https://example.com/openapi.json",
                help="输入 OpenAPI/Swagger 规范的 URL"
            )
        
        with col2:
            custom_name_url = st.text_input(
                "自定义服务器名称（可选）",
                key="custom_name_url",
                help="留空则自动从 API 标题生成"
            )
        
        api_key = st.text_input(
            "API Key（可选）",
            type="password",
            help="如果 API 需要认证，请输入 API Key"
        )
        
        if spec_url:
            if st.button("🚀 开始转换", type="primary", use_container_width=True, key="url_convert"):
                with st.spinner("正在转换..."):
                    try:
                        # 获取规范
                        fetcher = RapidAPISpecFetcher()
                        api_spec = fetcher.fetch_from_url(
                            spec_url,
                            api_key=api_key if api_key else None,
                            verify_ssl=verify_ssl
                        )
                        
                        st.success(f"✅ 获取成功: {api_spec.title} v{api_spec.version}")
                        st.info(f"📍 端点数量: {len(api_spec.endpoints)}")
                        
                        # 增强
                        if enhance:
                            with st.spinner("🤖 使用 LLM 增强描述..."):
                                enhancer = DescriptionEnhancer()
                                api_spec = enhancer.enhance_api_spec(api_spec)
                            st.success("✅ 描述增强完成")
                        
                        # 生成
                        with st.spinner("🔨 生成 MCP 服务器..."):
                            custom_promo = st.session_state.get('custom_emcp_promo', None)
                            generator = MCPGenerator(
                                output_dir=output_dir,
                                emcp_promotion=custom_promo
                            )
                            mcp_server = generator.generate(
                                api_spec,
                                transport=transport,
                                custom_name=custom_name_url if custom_name_url else None
                            )
                        
                        # 显示结果
                        st.success("🎉 生成完成!")
                        
                        result_col1, result_col2 = st.columns(2)
                        with result_col1:
                            st.metric("服务器名称", mcp_server.name)
                            st.metric("工具数量", len(mcp_server.tools))
                        with result_col2:
                            st.metric("版本", mcp_server.version)
                            st.metric("传输协议", transport)
                        
                        st.code(f"cd {mcp_server.output_path}\npython server.py", language="bash")
                        
                        # 显示生成的文件内容
                        with st.expander("查看生成的 server.py"):
                            server_file = Path(mcp_server.output_path) / "server.py"
                            if server_file.exists():
                                st.code(server_file.read_text(encoding='utf-8'), language="python")
                        
                    except Exception as e:
                        st.error(f"❌ 错误: {str(e)}")
                        import traceback
                        with st.expander("查看详细错误"):
                            st.code(traceback.format_exc())
    
    # Tab 3: RapidAPI
    with tab3:
        st.header("🚀 RapidAPI 辅助工具")
        
        st.info("""
        💡 **RapidAPI 不直接提供 OpenAPI 规范下载**
        
        本工具会帮你：
        1. 自动尝试从 RapidAPI 获取规范
        2. 提供详细的手动获取方法
        3. 转换为 MCP 服务器
        """)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            rapidapi_url = st.text_input(
                "RapidAPI URL",
                placeholder="https://rapidapi.com/apidojo/api/yahoo-finance1",
                help="粘贴 RapidAPI 上的 API 页面 URL",
                key="rapidapi_url"
            )
        
        with col2:
            custom_name_rapid = st.text_input(
                "自定义服务器名称（可选）",
                key="custom_name_rapid",
                help="留空则自动从 API 名称生成"
            )
        
        if rapidapi_url:
            # 显示帮助信息
            with st.expander("📖 如何从 RapidAPI 获取规范"):
                st.markdown("""
                ### 方法 1: 浏览器开发者工具（最可靠）⭐
                
                1. 打开 RapidAPI 页面
                2. 按 **F12** 打开开发者工具
                3. 切换到 **Network** (网络) 标签
                4. **刷新页面** (F5)
                5. 在请求列表中搜索 "spec" 或 "openapi"
                6. 找到规范请求，复制 JSON 响应
                7. 保存为文件并在"文件上传"标签中使用
                
                ### 方法 2: 查看页面源代码
                
                1. 访问 API 的 Specs 页面
                2. 右键 → "查看网页源代码" (Ctrl+U)
                3. 搜索 "openapi" 或 "swagger"
                4. 复制 JSON 数据并保存
                
                ### 方法 3: 使用自动获取（成功率不保证）
                
                点击下方"自动获取规范"按钮，工具会尝试自动获取。
                """)
            
            # 解析 URL
            helper = RapidAPIHelper()
            api_info = helper.extract_api_info_from_url(rapidapi_url)
            
            if api_info:
                st.success(f"✅ 识别到 API: **{api_info['provider']}/{api_info['api']}**")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("🚀 一键自动转换", type="primary", use_container_width=True, key="auto_convert_rapid"):
                        with st.spinner("正在自动提取和转换..."):
                            try:
                                # 使用新的自动提取功能
                                spec = auto_extract_rapidapi(rapidapi_url, verify_ssl=verify_ssl)
                                
                                if spec and spec.get('paths'):
                                    st.success("🎉 成功提取规范！")
                                    
                                    # 保存 OpenAPI 文件
                                    import json
                                    # 使用正确的键名
                                    api_name = api_info.get('api') or api_info.get('api_name', 'api')
                                    openapi_file = f"rapidapi_{api_name}_auto.json"
                                    with open(openapi_file, 'w', encoding='utf-8') as f:
                                        json.dump(spec, f, indent=2, ensure_ascii=False)
                                    
                                    st.info(f"📁 已保存 OpenAPI: {openapi_file}")
                                    
                                    # 显示规范信息
                                    col_a, col_b = st.columns(2)
                                    with col_a:
                                        st.metric("API 标题", spec['info']['title'])
                                        st.metric("端点数量", len(spec.get('paths', {})))
                                    with col_b:
                                        st.metric("版本", spec['info']['version'])
                                        st.metric("Base URL", spec['servers'][0]['url'] if spec.get('servers') else 'N/A')
                                    
                                    # 显示规范预览
                                    with st.expander("查看完整 OpenAPI 规范"):
                                        st.json(spec)
                                    
                                    # 直接转换为 MCP
                                    with st.spinner("正在转换为 MCP..."):
                                        try:
                                            parser = OpenAPIParser()
                                            api_spec = parser.parse_dict(spec)
                                            
                                            # 增强描述
                                            if enhance:
                                                with st.spinner("🤖 使用 LLM 增强描述..."):
                                                    enhancer = DescriptionEnhancer()
                                                    api_spec = enhancer.enhance_api_spec(api_spec)
                                                st.success("✅ 描述增强完成")
                                            
                                            # 生成 MCP
                                            custom_promo = st.session_state.get('custom_emcp_promo', None)
                                            generator = MCPGenerator(
                                                output_dir=output_dir,
                                                emcp_promotion=custom_promo
                                            )
                                            # 使用正确的键名
                                            default_name = api_info.get('api') or api_info.get('api_name', 'api')
                                            mcp_server = generator.generate(
                                                api_spec,
                                                transport=transport,
                                                custom_name=custom_name_rapid if custom_name_rapid else default_name
                                            )
                                            
                                            st.success("🎉 MCP 服务器生成完成!")
                                            
                                            result_col1, result_col2 = st.columns(2)
                                            with result_col1:
                                                st.metric("服务器名称", mcp_server.name)
                                                st.metric("工具数量", len(mcp_server.tools))
                                            with result_col2:
                                                st.metric("版本", mcp_server.version)
                                                st.metric("传输协议", transport)
                                            
                                            st.code(f"cd {mcp_server.output_path}\npython server.py", language="bash")
                                            
                                            st.info("🔑 别忘了设置 RapidAPI Key: set API_KEY=你的Key")
                                            
                                            # 显示生成的服务器代码
                                            with st.expander("查看生成的 server.py"):
                                                server_file = Path(mcp_server.output_path) / "server.py"
                                                if server_file.exists():
                                                    st.code(server_file.read_text(encoding='utf-8'), language="python")
                                            
                                        except Exception as e:
                                            st.error(f"❌ 转换错误: {str(e)}")
                                            import traceback
                                            with st.expander("查看详细错误"):
                                                st.code(traceback.format_exc())
                                    
                                else:
                                    st.warning("❌ 无法自动获取规范")
                                    st.info("💡 请使用上方展开的手动方法获取规范，然后在【文件上传】标签中使用")
                                    
                            except Exception as e:
                                st.error(f"❌ 获取失败: {str(e)}")
                                st.info("💡 请使用手动方法")
                
                with col2:
                    st.markdown("**可能的规范位置：**")
                    possible_urls = helper.get_possible_spec_urls(rapidapi_url)
                    for url in possible_urls[:3]:
                        st.code(url, language="text")
                
            else:
                st.error("❌ 无法识别的 RapidAPI URL")
                st.info("请确保 URL 格式为: https://rapidapi.com/{provider}/api/{api-name}")
        
        # 帮助部分
        st.divider()
        st.markdown("""
        ### 💡 提示
        
        - **成功率**: 自动获取的成功率依赖于 RapidAPI 的页面结构，不保证 100% 成功
        - **最可靠**: 使用浏览器开发者工具手动获取是最可靠的方法
        - **保存规范**: 建议保存获取的规范文件，以便以后使用
        - **联系提供商**: 有些 API 提供商在 GitHub 或官网提供 OpenAPI 规范
        
        ### 📚 详细文档
        
        查看 [RAPIDAPI_GUIDE.md](https://github.com/yourusername/APItoMCP/blob/main/RAPIDAPI_GUIDE.md) 获取更多帮助。
        """)
    
    # Tab 4: 批量爬取
    with tab4:
        st.header("🔥 批量爬取 RapidAPI")
        st.markdown("一次性处理多个 RapidAPI，晚上挂机，第二天收获一堆 MCP 项目！")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📝 输入 URL 列表")
            
            # 输入方式选择
            input_mode = st.radio(
                "输入方式",
                options=["文本框输入", "上传文件"],
                horizontal=True
            )
            
            urls_data = []
            
            if input_mode == "文本框输入":
                urls_text = st.text_area(
                    "RapidAPI URLs（每行一个）",
                    height=300,
                    placeholder="https://rapidapi.com/provider/api/api-name-1\nhttps://rapidapi.com/provider/api/api-name-2\n...",
                    help="每行输入一个 RapidAPI URL，支持注释行（# 开头）"
                )
                
                if urls_text:
                    for line in urls_text.split('\n'):
                        line = line.strip()
                        if line and not line.startswith('#') and line.startswith('http'):
                            urls_data.append({'url': line})
            
            else:
                uploaded_urls_file = st.file_uploader(
                    "上传 URL 列表文件",
                    type=["txt", "json"],
                    help="支持纯文本（.txt）或 JSON 格式（.json）"
                )
                
                if uploaded_urls_file:
                    content = uploaded_urls_file.read().decode('utf-8')
                    
                    # 尝试解析
                    if uploaded_urls_file.name.endswith('.json'):
                        try:
                            import json
                            urls_data = json.loads(content)
                        except:
                            st.error("❌ JSON 格式错误")
                    else:
                        for line in content.split('\n'):
                            line = line.strip()
                            if line and not line.startswith('#') and line.startswith('http'):
                                urls_data.append({'url': line})
            
            if urls_data:
                st.success(f"✅ 找到 {len(urls_data)} 个 URL")
                
                # 显示前 5 个
                with st.expander(f"预览（前 5 个）"):
                    for i, url_info in enumerate(urls_data[:5]):
                        if isinstance(url_info, dict):
                            url = url_info.get('url', '')
                        else:
                            url = str(url_info)
                        st.text(f"{i+1}. {url}")
        
        with col2:
            st.subheader("⚙️ 批量配置")
            
            use_selenium_batch = st.checkbox(
                "使用 Selenium 深度爬取",
                value=True,
                help="提取完整的参数信息（速度较慢）",
                key="selenium_batch"
            )
            
            delay_seconds = st.slider(
                "延迟时间（秒）",
                min_value=5,
                max_value=60,
                value=20,
                help="每个 API 之间的延迟，避免被封 IP"
            )
            
            retry_times = st.number_input(
                "重试次数",
                min_value=1,
                max_value=10,
                value=3,
                help="失败后的重试次数"
            )
            
            start_from_idx = st.number_input(
                "从第 N 个开始",
                min_value=0,
                max_value=len(urls_data) if urls_data else 0,
                value=0,
                help="断点续传：从指定位置开始处理"
            )
            
            if start_from_idx > 0:
                st.info(f"⏭️ 将跳过前 {start_from_idx} 个 URL")
        
        st.divider()
        
        # 预计时间
        if urls_data:
            actual_count = len(urls_data) - start_from_idx
            estimated_time = actual_count * (delay_seconds + (25 if use_selenium_batch else 3))
            st.info(f"⏱️ 预计耗时: {estimated_time / 60:.1f} 分钟（约 {estimated_time / 3600:.1f} 小时）")
        
        # 开始按钮
        if st.button("🚀 开始批量爬取", type="primary", disabled=not urls_data):
            if urls_data:
                # 应用断点续传
                urls_to_process = urls_data[start_from_idx:] if start_from_idx > 0 else urls_data
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                success_count = 0
                failed_count = 0
                results_container = st.container()
                
                for i, url_info in enumerate(urls_to_process):
                    # 安全地提取 url 和 name
                    if isinstance(url_info, dict):
                        url = url_info.get('url', '')
                        name = url_info.get('name', None)
                    elif isinstance(url_info, str):
                        url = url_info
                        name = None
                    else:
                        continue
                    
                    status_text.text(f"处理中 [{i+1}/{len(urls_to_process)}]: {url}")
                    
                    try:
                        with st.spinner(f"爬取中..."):
                            # 调用处理函数
                            spec = auto_extract_rapidapi(
                                url,
                                verify_ssl=verify_ssl,
                                use_selenium=use_selenium_batch
                            )
                            
                            if spec:
                                # 生成 MCP
                                parser = OpenAPIParser()
                                api_spec = parser.parse_dict(spec)
                                
                                custom_promo = st.session_state.get('custom_emcp_promo', None)
                                generator = MCPGenerator(
                                    output_dir=output_dir,
                                    emcp_promotion=custom_promo
                                )
                                mcp_server = generator.generate(
                                    api_spec,
                                    transport=transport,
                                    custom_name=name
                                )
                                
                                success_count += 1
                                
                                with results_container:
                                    st.success(f"✅ [{i+1}] 成功: {url}")
                                    st.text(f"   输出: {mcp_server.output_path}")
                            else:
                                failed_count += 1
                                with results_container:
                                    st.error(f"❌ [{i+1}] 失败: {url}")
                    
                    except Exception as e:
                        failed_count += 1
                        with results_container:
                            st.error(f"❌ [{i+1}] 错误: {url}")
                            st.text(f"   原因: {str(e)}")
                    
                    # 更新进度
                    progress_bar.progress((i + 1) / len(urls_to_process))
                    
                    # 延迟
                    if i < len(urls_to_process) - 1:
                        import time
                        time.sleep(delay_seconds)
                
                # 完成提示
                status_text.empty()
                progress_bar.empty()
                
                st.balloons()
                st.success(f"🎉 批量处理完成！")
                st.metric("成功", success_count)
                st.metric("失败", failed_count)
                st.metric("总数", len(urls_to_process))
        
        # 使用说明
        st.divider()
        st.markdown("""
        ### 💡 使用提示
        
        **批量爬取适合场景：**
        - 🌙 晚上挂机处理大量 API（10-100+ 个）
        - 📚 批量收集某个分类的所有 API
        - 🔄 定期更新现有 API 的规范
        
        **速度对比：**
        - ⚡ 基础模式：~5 秒/个（快但可能不完整）
        - 🎯 Selenium 模式：~25 秒/个（慢但完整准确）
        
        **建议配置：**
        - 少量 API（< 10）：延迟 10 秒
        - 中等数量（10-50）：延迟 20 秒
        - 大量 API（> 50）：延迟 30-60 秒
        
        **断点续传：**
        如果中途中断，可以设置"从第 N 个开始"继续处理
        """)
        
        # 示例
        with st.expander("📝 URL 列表示例"):
            st.code("""# Job & Career APIs
https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
https://rapidapi.com/letscrape-6bRBa3QguO5/api/linkedin-data-api

# Weather APIs
https://rapidapi.com/weatherapi/api/weatherapi-com
https://rapidapi.com/visual-crossing-corporation-visual-crossing-corporation-default/api/visual-crossing-weather

# News APIs
https://rapidapi.com/newscatcher-api-newscatcher-api-default/api/newscatcher
https://rapidapi.com/contextualwebsearch/api/web-search
""", language="text")
    
    # Tab 5: 历史记录
    with tab5:
        st.header("📊 已生成的 MCP 服务器")
        
        output_path = Path(output_dir)
        if output_path.exists():
            servers = [d for d in output_path.iterdir() if d.is_dir()]
            
            if servers:
                st.info(f"找到 {len(servers)} 个已生成的服务器")
                
                for server_dir in servers:
                    with st.expander(f"📦 {server_dir.name}"):
                        readme_file = server_dir / "README.md"
                        server_file = server_dir / "server.py"
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("名称", server_dir.name)
                        with col2:
                            if server_file.exists():
                                st.metric("状态", "✅ 可用")
                            else:
                                st.metric("状态", "❌ 缺失文件")
                        with col3:
                            st.code(f"cd {server_dir}\npython server.py", language="bash")
                        
                        if readme_file.exists():
                            st.markdown(readme_file.read_text(encoding='utf-8'))
            else:
                st.warning("还没有生成任何 MCP 服务器")
        else:
            st.warning(f"输出目录不存在: {output_dir}")
    
    # 页脚
    st.divider()
    st.markdown("""
    ### 🎯 快速开始
    
    1. 选择 **文件上传** 或 **URL 导入** 标签
    2. 提供 OpenAPI/Swagger 规范
    3. （可选）自定义服务器名称和配置
    4. 点击 **开始转换**
    5. 在输出目录中找到生成的 MCP 服务器
    6. 运行 `python server.py` 启动服务器
    
    ### 📚 相关链接
    - [FastMCP 文档](https://fastmcp.wiki)
    - [MCP 协议](https://modelcontextprotocol.io/)
    - [项目仓库](https://github.com/yourusername/APItoMCP)
    """)


if __name__ == "__main__":
    main()

