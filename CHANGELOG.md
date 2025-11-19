# 更新日志

本文档记录了 API-to-MCP 项目的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [0.1.0] - 2025-11-18

### 新增
- ✨ 核心功能: 将 OpenAPI/Swagger 规范转换为 MCP 服务器
- ✨ **FastMCP 2.0 集成**: 使用 FastMCP 框架生成简洁优雅的服务器代码
- ✨ **多种传输协议**: 支持 stdio、SSE、Streamable HTTP 三种传输方式
- ✨ RapidAPI 平台集成支持
- ✨ Azure OpenAI 驱动的描述增强功能
- ✨ 命令行工具 (`api-to-mcp`)
- ✨ 支持 OpenAPI 3.0+ 和 Swagger 2.0
- ✨ 自动生成可用 uvx 启动的 MCP 服务器
- ✨ API 规范验证功能
- ✨ 配置管理和环境变量支持

### 文档
- 📝 完整的 README.md
- 📝 详细的使用指南 (USAGE.md)
- 📝 示例文件和说明
- 📝 快速开始脚本

### 工具
- 🔧 `convert` - 转换 API 规范文件（支持 `-t/--transport` 选择协议）
- 🔧 `from-url` - 从 URL 获取并转换（支持 `-t/--transport` 选择协议）
- 🔧 `validate` - 验证 API 规范
- 🔧 `config` - 显示配置

### 模块
- 📦 OpenAPI/Swagger 解析器
- 📦 FastMCP 驱动的代码生成器
- 📦 Azure OpenAI 描述增强器
- 📦 RapidAPI 集成模块
- 📦 配置管理模块

### 技术栈
- 🎯 **FastMCP 2.0**: 快速、Pythonic 的 MCP 框架
- 🤖 **Azure OpenAI**: GPT-4 驱动的描述增强
- 📋 **Jinja2**: 灵活的代码模板引擎
- 🌐 **httpx**: 现代异步 HTTP 客户端

## [未来计划]

### 即将推出
- [ ] 支持更多认证方式 (OAuth2, JWT)
- [ ] 请求缓存和速率限制
- [ ] 批量转换 UI 界面
- [ ] 更多 API 平台支持 (Postman, Insomnia)
- [ ] MCP 服务器测试工具
- [ ] Docker 部署支持
- [ ] 插件系统

### 考虑中
- [ ] 支持 GraphQL API
- [ ] 支持 gRPC API
- [ ] 在线转换服务
- [ ] MCP 服务器市场

---

**说明**: 
- 🎉 主要功能
- ✨ 新增功能
- 🐛 Bug 修复
- 📝 文档更新
- 🔧 工具改进
- ⚡️ 性能优化
- 🔒 安全更新

