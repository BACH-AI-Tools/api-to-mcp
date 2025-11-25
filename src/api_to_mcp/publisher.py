"""
PyPI 发布模块
"""
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import shutil


class PyPIPublisher:
    """PyPI 发布器"""
    
    def __init__(self, server_path: Path):
        self.server_path = Path(server_path)
        self.pyproject_file = self.server_path / "pyproject.toml"
        
    def check_prerequisites(self) -> Dict[str, Any]:
        """检查发布前置条件"""
        result = {
            "ready": True,
            "issues": []
        }
        
        # 检查文件
        if not self.pyproject_file.exists():
            result["ready"] = False
            result["issues"].append("pyproject.toml 不存在")
        
        # 检查构建工具
        try:
            subprocess.run(
                [sys.executable, "-m", "build", "--version"],
                capture_output=True,
                timeout=5
            )
        except:
            result["ready"] = False
            result["issues"].append("未安装 build 工具: pip install build")
        
        # 检查 twine
        try:
            subprocess.run(
                [sys.executable, "-m", "twine", "--version"],
                capture_output=True,
                timeout=5
            )
        except:
            result["ready"] = False
            result["issues"].append("未安装 twine 工具: pip install twine")
        
        return result
    
    def build_package(self) -> Dict[str, Any]:
        """构建包"""
        result = {
            "success": False,
            "message": "",
            "dist_files": []
        }
        
        try:
            print("📦 构建包...")
            
            # 清理旧的构建
            dist_dir = self.server_path / "dist"
            if dist_dir.exists():
                shutil.rmtree(dist_dir)
            
            # 构建
            proc = subprocess.run(
                [sys.executable, "-m", "build"],
                cwd=self.server_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if proc.returncode == 0:
                result["success"] = True
                result["message"] = "构建成功"
                
                # 列出构建的文件
                if dist_dir.exists():
                    result["dist_files"] = [f.name for f in dist_dir.iterdir()]
                
                print("✅ 构建成功")
                for file in result["dist_files"]:
                    print(f"   📄 {file}")
            else:
                result["message"] = f"构建失败: {proc.stderr}"
                print(f"❌ 构建失败")
                print(proc.stderr)
            
        except subprocess.TimeoutExpired:
            result["message"] = "构建超时"
            print("❌ 构建超时")
        except Exception as e:
            result["message"] = f"构建异常: {str(e)}"
            print(f"❌ 构建异常: {e}")
        
        return result
    
    def check_package(self) -> Dict[str, Any]:
        """检查包"""
        result = {
            "success": False,
            "message": "",
            "warnings": []
        }
        
        try:
            print("🔍 检查包...")
            
            dist_dir = self.server_path / "dist"
            if not dist_dir.exists():
                result["message"] = "dist 目录不存在，请先构建"
                print("❌ dist 目录不存在")
                return result
            
            # 使用 twine 检查
            proc = subprocess.run(
                [sys.executable, "-m", "twine", "check", "dist/*"],
                cwd=self.server_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if proc.returncode == 0:
                result["success"] = True
                result["message"] = "包检查通过"
                print("✅ 包检查通过")
            else:
                result["message"] = f"检查失败: {proc.stderr}"
                print(f"⚠️ 检查失败")
                print(proc.stderr)
            
        except Exception as e:
            result["message"] = f"检查异常: {str(e)}"
            print(f"❌ 检查异常: {e}")
        
        return result
    
    def upload_to_testpypi(self) -> Dict[str, Any]:
        """上传到 TestPyPI"""
        result = {
            "success": False,
            "message": ""
        }
        
        try:
            print("🚀 上传到 TestPyPI...")
            print("💡 需要 TestPyPI API Token")
            
            proc = subprocess.run(
                [
                    sys.executable, "-m", "twine", "upload",
                    "--repository", "testpypi",
                    "dist/*"
                ],
                cwd=self.server_path,
                timeout=120
            )
            
            if proc.returncode == 0:
                result["success"] = True
                result["message"] = "上传到 TestPyPI 成功"
                print("✅ 上传成功")
            else:
                result["message"] = "上传失败"
                print("❌ 上传失败")
            
        except Exception as e:
            result["message"] = f"上传异常: {str(e)}"
            print(f"❌ 上传异常: {e}")
        
        return result
    
    def upload_to_pypi(self) -> Dict[str, Any]:
        """上传到 PyPI"""
        result = {
            "success": False,
            "message": ""
        }
        
        try:
            print("🚀 上传到 PyPI...")
            print("💡 需要 PyPI API Token")
            print("⚠️  警告: 这将发布到正式的 PyPI，请确认!")
            
            proc = subprocess.run(
                [sys.executable, "-m", "twine", "upload", "dist/*"],
                cwd=self.server_path,
                timeout=120
            )
            
            if proc.returncode == 0:
                result["success"] = True
                result["message"] = "上传到 PyPI 成功"
                print("✅ 上传成功")
            else:
                result["message"] = "上传失败"
                print("❌ 上传失败")
            
        except Exception as e:
            result["message"] = f"上传异常: {str(e)}"
            print(f"❌ 上传异常: {e}")
        
        return result
    
    def publish_workflow(self, target: str = "testpypi") -> Dict[str, Any]:
        """完整发布流程"""
        print(f"📦 开始发布到 {target.upper()}...")
        print("=" * 60)
        
        # 1. 检查前置条件
        print("\n1️⃣ 检查前置条件...")
        prereq = self.check_prerequisites()
        if not prereq["ready"]:
            print("❌ 前置条件未满足:")
            for issue in prereq["issues"]:
                print(f"   - {issue}")
            return {"success": False, "stage": "prerequisites", "details": prereq}
        print("✅ 前置条件满足")
        
        # 2. 构建包
        print("\n2️⃣ 构建包...")
        build_result = self.build_package()
        if not build_result["success"]:
            return {"success": False, "stage": "build", "details": build_result}
        
        # 3. 检查包
        print("\n3️⃣ 检查包...")
        check_result = self.check_package()
        if not check_result["success"]:
            return {"success": False, "stage": "check", "details": check_result}
        
        # 4. 上传
        print(f"\n4️⃣ 上传到 {target.upper()}...")
        if target == "testpypi":
            upload_result = self.upload_to_testpypi()
        else:
            upload_result = self.upload_to_pypi()
        
        print("\n" + "=" * 60)
        if upload_result["success"]:
            print("🎉 发布成功!")
            return {
                "success": True,
                "target": target,
                "details": {
                    "build": build_result,
                    "check": check_result,
                    "upload": upload_result
                }
            }
        else:
            print("❌ 发布失败")
            return {
                "success": False,
                "stage": "upload",
                "details": upload_result
            }


def publish_mcp_server(server_path: str, target: str = "testpypi") -> Dict[str, Any]:
    """发布 MCP 服务器到 PyPI"""
    publisher = PyPIPublisher(Path(server_path))
    return publisher.publish_workflow(target)






