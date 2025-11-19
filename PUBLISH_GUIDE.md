# 📦 MCP 服务器发布指南

本指南说明如何测试和发布生成的 MCP 服务器到 PyPI。

## 🎯 完整流程

### 1️⃣ 生成 MCP 服务器

```bash
# 从文件转换
api-to-mcp convert api-spec.json -n my_awesome_api

# 或从 URL 转换
api-to-mcp from-url https://example.com/openapi.json -n my_awesome_api --no-verify-ssl
```

### 2️⃣ 测试 MCP 服务器

生成后，先测试确保一切正常：

```bash
# 测试服务器
api-to-mcp test generated_mcps/my_awesome_api
```

**测试内容包括：**
- ✅ 项目结构完整性
- ✅ Python 语法检查
- ✅ 依赖项检查
- ✅ 代码导入测试

**输出示例：**
```
🧪 测试 MCP 服务器: my_awesome_api
============================================================
✅ 结构测试: 项目结构完整
✅ 语法测试: Python 语法正确
✅ 依赖测试: 所有依赖已安装
✅ 导入测试: 服务器代码可以成功导入
============================================================
📊 测试结果: 4 通过, 0 失败, 共 4 项

🎉 所有测试通过! MCP 服务器可以发布
```

### 3️⃣ 安装依赖（如果测试失败）

```bash
cd generated_mcps/my_awesome_api
pip install -e .
```

### 4️⃣ 配置 PyPI Token

#### 获取 Token

1. 注册账号:
   - **TestPyPI**: https://test.pypi.org/account/register/
   - **PyPI**: https://pypi.org/account/register/

2. 创建 API Token:
   - **TestPyPI**: https://test.pypi.org/manage/account/token/
   - **PyPI**: https://pypi.org/manage/account/token/

#### 配置 Token

创建或编辑 `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-your-api-token-here

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-your-test-api-token-here
```

### 5️⃣ 发布到 TestPyPI（推荐先测试）

```bash
# 发布到 TestPyPI
api-to-mcp publish generated_mcps/my_awesome_api --target testpypi
```

**流程说明：**
1. 检查前置条件（build, twine）
2. 构建包（wheel 和 sdist）
3. 检查包的完整性
4. 上传到 TestPyPI

**输出示例：**
```
📦 开始发布到 TESTPYPI...
============================================================

1️⃣ 检查前置条件...
✅ 前置条件满足

2️⃣ 构建包...
📦 构建包...
✅ 构建成功
   📄 my_awesome_api-1.0.0-py3-none-any.whl
   📄 my_awesome_api-1.0.0.tar.gz

3️⃣ 检查包...
🔍 检查包...
✅ 包检查通过

4️⃣ 上传到 TESTPYPI...
🚀 上传到 TestPyPI...
💡 需要 TestPyPI API Token
✅ 上传成功

============================================================
🎉 发布成功!

📝 测试安装:
   pip install -i https://test.pypi.org/simple/ my_awesome_api
```

### 6️⃣ 测试安装

```bash
# 从 TestPyPI 安装
pip install -i https://test.pypi.org/simple/ my_awesome_api

# 测试运行
python -c "import my_awesome_api"
```

### 7️⃣ 发布到正式 PyPI

确认一切正常后，发布到正式 PyPI：

```bash
# 发布到 PyPI
api-to-mcp publish generated_mcps/my_awesome_api --target pypi
```

⚠️ **注意**: 发布到 PyPI 后无法删除，只能发布新版本！

### 8️⃣ 安装和使用

```bash
# 从 PyPI 安装
pip install my-awesome-api

# 使用 uvx 运行
uvx my-awesome-api
```

## 📝 命令参考

### 测试命令

```bash
# 基本测试
api-to-mcp test <server_path>

# 示例
api-to-mcp test generated_mcps/weather_api
```

### 发布命令

```bash
# 发布到 TestPyPI
api-to-mcp publish <server_path> --target testpypi

# 发布到 PyPI
api-to-mcp publish <server_path> --target pypi

# 示例
api-to-mcp publish generated_mcps/weather_api --target testpypi
```

## 🔧 故障排查

### 测试失败

**问题: 缺少依赖**
```bash
# 解决方案
cd generated_mcps/your_api
pip install -e .
```

**问题: Python 语法错误**
```bash
# 查看详细错误
python -m py_compile generated_mcps/your_api/server.py
```

### 构建失败

**问题: 未安装 build**
```bash
pip install build
```

**问题: pyproject.toml 配置错误**
- 检查 `generated_mcps/your_api/pyproject.toml`
- 确保所有字段正确

### 上传失败

**问题: 认证失败**
- 检查 `~/.pypirc` 配置
- 确认 API Token 正确
- Token 应以 `pypi-` 开头

**问题: 包名已存在**
- 修改包名（重新生成时使用 `-n` 选项）
- 或更新版本号

**问题: 包大小超限**
- PyPI 限制单个文件 < 60MB
- 考虑减少依赖或优化代码

## 🎯 最佳实践

### 1. 版本管理

遵循语义化版本：
- **主版本号**: 不兼容的 API 更改
- **次版本号**: 向后兼容的功能添加
- **修订号**: 向后兼容的问题修复

```bash
# 更新版本（手动编辑 pyproject.toml）
# version = "1.0.0" -> "1.0.1"
```

### 2. 测试流程

```bash
# 1. 本地测试
api-to-mcp test generated_mcps/my_api

# 2. 发布到 TestPyPI
api-to-mcp publish generated_mcps/my_api --target testpypi

# 3. 测试安装
pip install -i https://test.pypi.org/simple/ my-api

# 4. 确认无误后发布到 PyPI
api-to-mcp publish generated_mcps/my_api --target pypi
```

### 3. 文档和元数据

确保以下内容完整：
- ✅ README.md 描述清晰
- ✅ pyproject.toml 元数据正确
- ✅ 许可证信息
- ✅ 作者信息

### 4. 安全性

- ❌ 不要在代码中硬编码 API Key
- ✅ 使用环境变量
- ✅ 在文档中说明如何配置
- ✅ 添加 .gitignore 忽略敏感文件

## 📚 相关资源

- [PyPI 官方文档](https://packaging.python.org/)
- [语义化版本](https://semver.org/lang/zh-CN/)
- [Twine 文档](https://twine.readthedocs.io/)
- [FastMCP 文档](https://fastmcp.wiki)

## 🆘 获取帮助

遇到问题？
1. 查看本指南的故障排查部分
2. 运行 `api-to-mcp test` 获取详细错误信息
3. 提交 Issue 到项目仓库

---

**祝你发布顺利！🎉**


