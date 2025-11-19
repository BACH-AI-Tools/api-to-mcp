# 贡献指南

感谢你考虑为 API-to-MCP 项目做出贡献！

## 行为准则

请友善和尊重地对待每一个人。

## 如何贡献

### 报告 Bug

如果你发现了 bug，请创建一个 Issue 并包含：

1. **问题描述**: 清楚地描述问题
2. **重现步骤**: 详细的重现步骤
3. **期望行为**: 你期望发生什么
4. **实际行为**: 实际发生了什么
5. **环境信息**: 
   - 操作系统
   - Python 版本
   - 相关依赖版本

### 提出新功能

如果你有新功能的想法：

1. 先查看是否已有类似的 Issue
2. 创建一个 Feature Request Issue
3. 描述功能的用途和价值
4. 如果可能，提供使用示例

### 提交 Pull Request

1. **Fork 项目**

2. **创建分支**
   ```bash
   git checkout -b feature/amazing-feature
   ```

3. **进行修改**
   - 保持代码风格一致
   - 添加必要的测试
   - 更新文档

4. **提交修改**
   ```bash
   git commit -m "Add amazing feature"
   ```

5. **推送到 Fork**
   ```bash
   git push origin feature/amazing-feature
   ```

6. **创建 Pull Request**
   - 清楚描述修改内容
   - 关联相关 Issue
   - 等待 Review

## 开发环境设置

### 1. 克隆仓库

```bash
git clone https://github.com/yourusername/APItoMCP.git
cd APItoMCP
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
pip install -e ".[dev]"  # 安装开发依赖
```

### 4. 运行测试

```bash
pytest
```

### 5. 代码格式化

```bash
black src/
ruff check src/
```

## 代码风格

- 遵循 PEP 8
- 使用 Black 格式化代码
- 使用 Ruff 进行 Linting
- 添加类型注解
- 编写清晰的文档字符串

### 示例

```python
from typing import List, Optional

def parse_api_spec(file_path: str, enhance: bool = True) -> APISpec:
    """
    解析 API 规范文件
    
    Args:
        file_path: API 规范文件路径
        enhance: 是否使用 LLM 增强描述
    
    Returns:
        解析后的 API 规范对象
    
    Raises:
        ValueError: 如果文件格式不支持
    """
    # 实现...
    pass
```

## 测试指南

- 为新功能添加测试
- 确保所有测试通过
- 测试覆盖率应 > 80%

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_parser.py

# 查看覆盖率
pytest --cov=src/api_to_mcp
```

## 文档

更新文档很重要！

- 更新 README.md
- 更新 USAGE.md
- 更新代码文档字符串
- 添加示例（如果适用）

## 提交信息格式

使用清晰的提交信息：

```
类型: 简短描述

详细描述（可选）

关联 Issue: #123
```

**类型**:
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式化
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

**示例**:
```
feat: 添加 GraphQL API 支持

实现了 GraphQL API 的解析和转换功能

关联 Issue: #42
```

## Review 流程

1. 提交 Pull Request
2. 自动运行 CI 检查
3. 维护者 Review
4. 根据反馈修改
5. 合并到主分支

## 发布流程

1. 更新版本号 (pyproject.toml)
2. 更新 CHANGELOG.md
3. 创建 Git Tag
4. 发布到 PyPI（由维护者完成）

## 获取帮助

- 💬 讨论区: GitHub Discussions
- 🐛 Bug 报告: GitHub Issues
- 📧 邮件: your.email@example.com

## 致谢

感谢所有贡献者！你们的贡献让这个项目变得更好。

---

再次感谢你的贡献！🎉


