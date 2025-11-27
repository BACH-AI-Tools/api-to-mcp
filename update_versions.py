#!/usr/bin/env python3
"""
批量更新所有项目的版本号到 2.0.0 并打 tag
"""
import os
import re
import subprocess
from pathlib import Path

GENERATED_MCPS_DIR = Path("generated_mcps")
NEW_VERSION = "2.0.0"

# 已经是 2.0.0 的项目跳过
SKIP_PROJECTS = {"idealista7"}


def update_version_in_file(file_path: Path, old_pattern: str, new_value: str) -> bool:
    """更新文件中的版本号"""
    if not file_path.exists():
        return False
    
    content = file_path.read_text(encoding='utf-8')
    new_content = re.sub(old_pattern, new_value, content)
    
    if content != new_content:
        file_path.write_text(new_content, encoding='utf-8')
        return True
    return False


def update_project_version(project_dir: Path) -> bool:
    """更新单个项目的版本"""
    project_name = project_dir.name
    print(f"\n📦 更新版本: {project_name}")
    
    updated = False
    
    # 更新 server.py
    server_py = project_dir / "server.py"
    if server_py.exists():
        content = server_py.read_text(encoding='utf-8')
        
        # 更新 __version__
        new_content = re.sub(
            r'__version__ = "[^"]+"',
            f'__version__ = "{NEW_VERSION}"',
            content
        )
        
        # 更新 __tag__
        new_content = re.sub(
            r'__tag__ = "[^"]+"',
            f'__tag__ = "{project_name}/{NEW_VERSION}"',
            new_content
        )
        
        if content != new_content:
            server_py.write_text(new_content, encoding='utf-8')
            print(f"  ✅ 更新 server.py")
            updated = True
    
    # 更新 pyproject.toml
    pyproject = project_dir / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text(encoding='utf-8')
        new_content = re.sub(
            r'version = "[^"]+"',
            f'version = "{NEW_VERSION}"',
            content,
            count=1  # 只替换第一个
        )
        if content != new_content:
            pyproject.write_text(new_content, encoding='utf-8')
            print(f"  ✅ 更新 pyproject.toml")
            updated = True
    
    # 更新 README 文件
    for readme_file in ["README.md", "README_EN.md", "README_ZH-TW.md"]:
        readme_path = project_dir / readme_file
        if readme_path.exists():
            content = readme_path.read_text(encoding='utf-8')
            # 更新版本号
            new_content = re.sub(
                r'(\*\*版本\*\*|\*\*Version\*\*): [0-9]+\.[0-9]+\.[0-9]+',
                f'\\1: {NEW_VERSION}',
                content
            )
            new_content = re.sub(
                r'(版本|Version): [0-9]+\.[0-9]+\.[0-9]+',
                f'\\1: {NEW_VERSION}',
                new_content
            )
            if content != new_content:
                readme_path.write_text(new_content, encoding='utf-8')
                print(f"  ✅ 更新 {readme_file}")
                updated = True
    
    return updated


def git_commit_tag_push(project_dir: Path):
    """提交、打 tag 并推送"""
    project_name = project_dir.name
    
    try:
        # 检查是否是 git 仓库
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"  ⚠️ 不是 git 仓库")
            return
        
        # 如果有更改，提交
        if result.stdout.strip():
            subprocess.run(["git", "add", "."], cwd=project_dir, check=True)
            subprocess.run(
                ["git", "commit", "-m", f"v{NEW_VERSION}: 更新版本号"],
                cwd=project_dir,
                capture_output=True
            )
            print(f"  ✅ 已提交")
        
        # 检查 tag 是否存在
        result = subprocess.run(
            ["git", "tag", "-l", f"v{NEW_VERSION}"],
            cwd=project_dir,
            capture_output=True,
            text=True
        )
        
        if f"v{NEW_VERSION}" not in result.stdout:
            # 创建 tag
            subprocess.run(
                ["git", "tag", f"v{NEW_VERSION}"],
                cwd=project_dir,
                check=True
            )
            print(f"  ✅ 创建 tag v{NEW_VERSION}")
        
        # 推送
        result = subprocess.run(
            ["git", "push"],
            cwd=project_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            # 推送 tag
            subprocess.run(
                ["git", "push", "origin", f"v{NEW_VERSION}"],
                cwd=project_dir,
                capture_output=True
            )
            print(f"  ✅ 已推送到 GitHub")
        else:
            if "no upstream" in result.stderr:
                subprocess.run(
                    ["git", "push", "--set-upstream", "origin", "main"],
                    cwd=project_dir,
                    capture_output=True
                )
                subprocess.run(
                    ["git", "push", "origin", f"v{NEW_VERSION}"],
                    cwd=project_dir,
                    capture_output=True
                )
                print(f"  ✅ 已推送到 GitHub (设置上游)")
            else:
                print(f"  ⚠️ 推送失败: {result.stderr[:100]}")
            
    except Exception as e:
        print(f"  ❌ Git 操作失败: {e}")


def main():
    print(f"🚀 批量更新版本到 v{NEW_VERSION}...")
    
    updated = 0
    skipped = 0
    
    for project_dir in sorted(GENERATED_MCPS_DIR.iterdir()):
        if not project_dir.is_dir():
            continue
        
        if project_dir.name in SKIP_PROJECTS:
            print(f"\n⏭️ 跳过: {project_dir.name}")
            skipped += 1
            continue
        
        # 检查是否有 openapi.json（已迁移的项目）
        if not (project_dir / "openapi.json").exists():
            print(f"\n⏭️ 跳过（未迁移）: {project_dir.name}")
            skipped += 1
            continue
        
        if update_project_version(project_dir):
            git_commit_tag_push(project_dir)
            updated += 1
        else:
            print(f"  ℹ️ 版本已是最新")
            # 仍然尝试打 tag
            git_commit_tag_push(project_dir)
            updated += 1
    
    print(f"\n✨ 完成! 更新了 {updated} 个项目，跳过了 {skipped} 个项目")


if __name__ == "__main__":
    main()

