#!/usr/bin/env python3
"""
批量迁移旧 MCP 项目到新格式
- 提取 OpenAPI 规范到 openapi.json
- 更新 server.py 从文件读取
- 添加 LICENSE 文件
- 更新 pyproject.toml
- 更新 README（不包含 LobeHub）
"""
import os
import re
import json
import subprocess
from pathlib import Path
from datetime import datetime

GENERATED_MCPS_DIR = Path("generated_mcps")

# 要跳过的项目（已经更新过了）
SKIP_PROJECTS = {"idealista7"}


def extract_openapi_spec(server_py_content: str) -> dict | None:
    """从 server.py 中提取 OPENAPI_SPEC"""
    match = re.search(r'OPENAPI_SPEC = """(.+?)"""', server_py_content, re.DOTALL)
    if match:
        spec_str = match.group(1)
        try:
            # 处理转义字符：先将 \n 替换为实际换行，\" 替换为 "
            # 但由于它已经是一个 Python 字符串，我们需要用 exec 来正确解析
            exec_globals = {}
            exec(f'result = """{spec_str}"""', exec_globals)
            spec_json = exec_globals['result']
            return json.loads(spec_json)
        except Exception as e:
            print(f"  ⚠️ JSON 解析失败: {e}")
            return None
    return None


def update_server_py(server_py_content: str) -> str:
    """更新 server.py 内容"""
    # 替换文件头描述
    content = re.sub(
        r'使用 FastMCP 的 from_openapi 方法自动生成',
        'MCP server for accessing API.',
        server_py_content
    )
    
    # 添加 pathlib import
    if 'from pathlib import Path' not in content:
        content = content.replace(
            'import json',
            'import json\nfrom pathlib import Path'
        )
    
    # 替换 OPENAPI_SPEC 定义为函数
    openapi_pattern = r'# OpenAPI 规范\nOPENAPI_SPEC = """.*?"""'
    load_func = '''# 从文件加载 OpenAPI 规范
def load_openapi_spec():
    """从 openapi.json 文件加载 OpenAPI 规范"""
    openapi_path = Path(__file__).parent / "openapi.json"
    with open(openapi_path, "r", encoding="utf-8") as f:
        return json.load(f)'''
    
    content = re.sub(openapi_pattern, load_func, content, flags=re.DOTALL)
    
    # 替换 json.loads(OPENAPI_SPEC) 为 load_openapi_spec()
    content = content.replace('json.loads(OPENAPI_SPEC)', 'load_openapi_spec()')
    
    return content


def get_project_info(server_py_content: str) -> dict:
    """从 server.py 提取项目信息"""
    info = {}
    
    # 提取版本
    match = re.search(r'__version__ = "([^"]+)"', server_py_content)
    info['version'] = match.group(1) if match else "1.0.0"
    
    # 提取名称
    match = re.search(r'name="([^"]+)"', server_py_content)
    info['name'] = match.group(1) if match else "unknown"
    
    return info


def generate_license() -> str:
    """生成 MIT 许可证"""
    year = datetime.now().year
    return f'''MIT License

Copyright (c) {year} bachstudio

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''


def update_pyproject(pyproject_content: str, project_name: str) -> str:
    """更新 pyproject.toml"""
    # 检查是否已经有 license
    if 'license = {file = "LICENSE"}' in pyproject_content:
        return pyproject_content
    
    # 在 requires-python 后添加 license 和其他元数据
    if 'license = ' not in pyproject_content:
        pyproject_content = pyproject_content.replace(
            'requires-python = ">=3.10"',
            '''requires-python = ">=3.10"
license = {file = "LICENSE"}
authors = [
    {name = "bachstudio"}
]
keywords = ["mcp", "api", "model-context-protocol"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]'''
        )
    
    # 添加 Bug Tracker URL
    if '"Bug Tracker"' not in pyproject_content:
        pyproject_content = pyproject_content.replace(
            'Documentation = "https://github.com/bachstudio/',
            '"Bug Tracker" = "https://github.com/bachstudio/' + project_name + '/issues"\nDocumentation = "https://github.com/bachstudio/'
        )
    
    # 添加 openapi.json 打包配置
    if 'artifacts = ["openapi.json"]' not in pyproject_content:
        pyproject_content = pyproject_content.replace(
            '[tool.hatch.build.targets.wheel]\npackages = ["."]',
            '''[tool.hatch.build.targets.wheel]
packages = ["."]
artifacts = ["openapi.json"]

[tool.hatch.build.targets.sdist]
include = [
    "server.py",
    "openapi.json",
    "README.md",
    "LICENSE",
    "__init__.py",
]'''
        )
    
    return pyproject_content


def update_readme(readme_content: str, lang: str = 'zh') -> str:
    """更新 README 内容，移除 FastMCP 和 LobeHub 描述"""
    # 移除 LobeHub Badge
    readme_content = re.sub(r'\[!\[MCP Badge\].*?\n', '', readme_content)
    readme_content = re.sub(r'lobehub\.com[^\s\)]*', '', readme_content)
    
    # 移除 FastMCP 描述
    if lang == 'zh':
        readme_content = re.sub(
            r'这是一个使用 \[FastMCP\]\([^\)]+\) 自动生成的 MCP 服务器',
            '这是一个 MCP 服务器',
            readme_content
        )
        readme_content = readme_content.replace(
            '- **FastMCP**: 快速、Pythonic 的 MCP 服务器框架\n',
            ''
        )
    elif lang == 'en':
        readme_content = re.sub(
            r'This is an automatically generated MCP server using \[FastMCP\]\([^\)]+\)',
            'This is an MCP server',
            readme_content
        )
    elif lang == 'zh_tw':
        readme_content = re.sub(
            r'這是一個使用 \[FastMCP\]\([^\)]+\) 自動生成的 MCP 伺服器',
            '這是一個 MCP 伺服器',
            readme_content
        )
        readme_content = readme_content.replace(
            '- **FastMCP**: 快速、Pythonic 的 MCP 服务器框架\n',
            ''
        )
    
    # 更新 Claude Desktop 配置为 uvx 方式
    # 查找包名
    match = re.search(r'pip install (bach-[^\s]+)', readme_content)
    if match:
        package_name = match.group(1)
        cmd_name = package_name.replace('-', '_')
        
        # 替换旧的 python 配置
        old_config_pattern = r'"command": "python",\s*\n\s*"args": \["[^"]+server\.py"\]'
        new_config = f'"command": "uvx",\n      "args": ["--from", "{package_name}", "{cmd_name}"]'
        readme_content = re.sub(old_config_pattern, new_config, readme_content)
    
    return readme_content


def migrate_project(project_dir: Path) -> bool:
    """迁移单个项目"""
    project_name = project_dir.name
    print(f"\n📦 处理项目: {project_name}")
    
    server_py = project_dir / "server.py"
    if not server_py.exists():
        print(f"  ⚠️ 跳过: server.py 不存在")
        return False
    
    # 检查是否已经迁移过
    openapi_json = project_dir / "openapi.json"
    if openapi_json.exists():
        print(f"  ✅ 已迁移过，跳过")
        return False
    
    # 读取 server.py
    server_content = server_py.read_text(encoding='utf-8')
    
    # 提取 OpenAPI 规范
    openapi_spec = extract_openapi_spec(server_content)
    if not openapi_spec:
        print(f"  ⚠️ 无法提取 OpenAPI 规范")
        return False
    
    # 保存 openapi.json
    openapi_json.write_text(json.dumps(openapi_spec, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"  ✅ 创建 openapi.json")
    
    # 更新 server.py
    new_server_content = update_server_py(server_content)
    server_py.write_text(new_server_content, encoding='utf-8')
    print(f"  ✅ 更新 server.py")
    
    # 创建 LICENSE
    license_file = project_dir / "LICENSE"
    if not license_file.exists():
        license_file.write_text(generate_license(), encoding='utf-8')
        print(f"  ✅ 创建 LICENSE")
    
    # 更新 pyproject.toml
    pyproject_file = project_dir / "pyproject.toml"
    if pyproject_file.exists():
        pyproject_content = pyproject_file.read_text(encoding='utf-8')
        # 获取包名
        match = re.search(r'name = "([^"]+)"', pyproject_content)
        package_name = match.group(1) if match else f"bach-{project_name}"
        new_pyproject = update_pyproject(pyproject_content, package_name)
        pyproject_file.write_text(new_pyproject, encoding='utf-8')
        print(f"  ✅ 更新 pyproject.toml")
    
    # 更新 README 文件
    for readme_file, lang in [
        ("README.md", "zh"),
        ("README_EN.md", "en"),
        ("README_ZH-TW.md", "zh_tw")
    ]:
        readme_path = project_dir / readme_file
        if readme_path.exists():
            readme_content = readme_path.read_text(encoding='utf-8')
            new_readme = update_readme(readme_content, lang)
            readme_path.write_text(new_readme, encoding='utf-8')
            print(f"  ✅ 更新 {readme_file}")
    
    return True


def git_commit_and_push(project_dir: Path):
    """提交并推送到 GitHub"""
    project_name = project_dir.name
    
    try:
        # 检查是否是 git 仓库
        result = subprocess.run(
            ["git", "status"],
            cwd=project_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"  ⚠️ 不是 git 仓库，跳过提交")
            return
        
        # 添加所有更改
        subprocess.run(["git", "add", "."], cwd=project_dir, check=True)
        
        # 提交
        commit_msg = "v2.0.0: 重构代码结构\n\n- 提取 OpenAPI 规范到 openapi.json\n- 添加 LICENSE 文件\n- 更新配置使用 uvx\n- 移除 FastMCP 描述"
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=project_dir,
            capture_output=True
        )
        
        # 推送
        result = subprocess.run(
            ["git", "push"],
            cwd=project_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"  ✅ 已推送到 GitHub")
        else:
            print(f"  ⚠️ 推送失败: {result.stderr}")
            
    except Exception as e:
        print(f"  ❌ Git 操作失败: {e}")


def main():
    print("🚀 开始批量迁移 MCP 项目...")
    
    migrated = 0
    skipped = 0
    
    for project_dir in sorted(GENERATED_MCPS_DIR.iterdir()):
        if not project_dir.is_dir():
            continue
        
        if project_dir.name in SKIP_PROJECTS:
            print(f"\n⏭️ 跳过已更新的项目: {project_dir.name}")
            skipped += 1
            continue
        
        if migrate_project(project_dir):
            git_commit_and_push(project_dir)
            migrated += 1
        else:
            skipped += 1
    
    print(f"\n✨ 完成! 迁移了 {migrated} 个项目，跳过了 {skipped} 个项目")


if __name__ == "__main__":
    main()

