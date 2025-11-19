"""
API 描述增强模块 - 使用 Azure OpenAI 优化描述
"""
from typing import Optional, List
from openai import AzureOpenAI

from .config import AzureOpenAIConfig
from .models import APIEndpoint, APISpec


class DescriptionEnhancer:
    """API 描述增强器"""
    
    def __init__(self, config: Optional[AzureOpenAIConfig] = None):
        self.config = config or AzureOpenAIConfig.from_env()
        self.client = AzureOpenAI(
            api_key=self.config.api_key,
            api_version=self.config.api_version,
            azure_endpoint=self.config.endpoint
        )
    
    def enhance_endpoint(self, endpoint: APIEndpoint, context: str = "") -> APIEndpoint:
        """
        增强单个端点的描述
        
        Args:
            endpoint: API 端点
            context: 额外的上下文信息（如 API 整体描述）
        """
        # 检查描述是否需要增强
        if not self._needs_enhancement(endpoint):
            return endpoint
        
        # 构建提示词
        prompt = self._build_enhancement_prompt(endpoint, context)
        
        try:
            # 调用 Azure OpenAI
            response = self.client.chat.completions.create(
                model=self.config.deployment_name,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个 API 文档专家。你的任务是为 API 端点生成清晰、准确、对 AI Agent 友好的描述。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            enhanced_text = response.choices[0].message.content.strip()
            
            # 解析增强后的描述
            enhanced_summary, enhanced_description = self._parse_enhanced_text(enhanced_text)
            
            endpoint.enhanced_summary = enhanced_summary
            endpoint.enhanced_description = enhanced_description
            
        except Exception as e:
            print(f"警告: 无法增强端点 {endpoint.operation_id} 的描述: {e}")
            # 使用原始描述
            endpoint.enhanced_summary = endpoint.summary
            endpoint.enhanced_description = endpoint.description
        
        return endpoint
    
    def enhance_api_spec(self, api_spec: APISpec) -> APISpec:
        """
        增强整个 API 规范的描述
        
        Args:
            api_spec: API 规范
        """
        context = f"API 名称: {api_spec.title}\n"
        if api_spec.description:
            context += f"API 描述: {api_spec.description}\n"
        
        print(f"正在增强 API 规范: {api_spec.title}")
        print(f"端点数量: {len(api_spec.endpoints)}")
        
        for i, endpoint in enumerate(api_spec.endpoints, 1):
            print(f"  [{i}/{len(api_spec.endpoints)}] 增强端点: {endpoint.method} {endpoint.path}")
            self.enhance_endpoint(endpoint, context)
        
        return api_spec
    
    def _needs_enhancement(self, endpoint: APIEndpoint) -> bool:
        """
        判断端点描述是否需要增强
        
        标准:
        - 没有描述
        - 描述太短（少于 20 个字符）
        - 描述不清晰（包含 TODO, TBD 等）
        """
        if not endpoint.description and not endpoint.summary:
            return True
        
        desc = (endpoint.description or "") + (endpoint.summary or "")
        
        if len(desc) < 20:
            return True
        
        unclear_markers = ['todo', 'tbd', 'fixme', 'xxx', 'pending']
        if any(marker in desc.lower() for marker in unclear_markers):
            return True
        
        return False
    
    def _build_enhancement_prompt(self, endpoint: APIEndpoint, context: str) -> str:
        """构建增强提示词"""
        prompt = f"""请为以下 API 端点生成清晰的描述。描述应该让 AI Agent 能够准确理解这个端点的功能和使用方法。

{context}

端点信息:
- 路径: {endpoint.path}
- 方法: {endpoint.method}
- 操作 ID: {endpoint.operation_id or 'N/A'}
"""
        
        if endpoint.summary:
            prompt += f"- 当前摘要: {endpoint.summary}\n"
        
        if endpoint.description:
            prompt += f"- 当前描述: {endpoint.description}\n"
        
        if endpoint.parameters:
            prompt += f"\n参数:\n"
            for param in endpoint.parameters:
                prompt += f"  - {param.name} ({param.type}): {param.description or '无描述'}\n"
        
        if endpoint.tags:
            prompt += f"\n标签: {', '.join(endpoint.tags)}\n"
        
        prompt += """
请生成:
1. 一行简洁的摘要（summary）
2. 详细的描述（description），包括：
   - 这个端点的主要功能
   - 适用场景
   - 关键参数说明
   - 返回数据说明

格式:
SUMMARY: [一行摘要]
DESCRIPTION: [详细描述]
"""
        
        return prompt
    
    def _parse_enhanced_text(self, text: str) -> tuple[str, str]:
        """解析增强后的文本"""
        lines = text.split('\n')
        summary = ""
        description = ""
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('SUMMARY:'):
                summary = line.replace('SUMMARY:', '').strip()
                current_section = 'summary'
            elif line.startswith('DESCRIPTION:'):
                description = line.replace('DESCRIPTION:', '').strip()
                current_section = 'description'
            elif current_section == 'description' and line:
                description += ' ' + line
        
        return summary, description.strip()
    
    def batch_enhance_endpoints(
        self, endpoints: List[APIEndpoint], context: str = "", batch_size: int = 5
    ) -> List[APIEndpoint]:
        """
        批量增强端点描述
        
        Args:
            endpoints: 端点列表
            context: 上下文信息
            batch_size: 每批处理的数量
        """
        enhanced_endpoints = []
        
        for i in range(0, len(endpoints), batch_size):
            batch = endpoints[i:i + batch_size]
            for endpoint in batch:
                enhanced_endpoint = self.enhance_endpoint(endpoint, context)
                enhanced_endpoints.append(enhanced_endpoint)
        
        return enhanced_endpoints


