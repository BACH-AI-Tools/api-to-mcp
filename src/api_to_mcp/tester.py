"""
MCP 服务器测试模块
"""
import subprocess
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
import asyncio


class MCPTester:
    """MCP 服务器测试器"""
    
    def __init__(self, server_path: Path):
        self.server_path = Path(server_path)
        self.server_file = self.server_path / "server.py"
        
    def test_import(self) -> Dict[str, Any]:
        """测试服务器是否可以导入"""
        result = {
            "name": "导入测试",
            "status": "unknown",
            "message": "",
            "details": {}
        }
        
        try:
            # 检查文件是否存在
            if not self.server_file.exists():
                result["status"] = "failed"
                result["message"] = f"服务器文件不存在: {self.server_file}"
                return result
            
            # 尝试导入检查语法
            cmd = [
                sys.executable, "-c",
                f"import sys; sys.path.insert(0, '{self.server_path.parent}'); "
                f"exec(open('{self.server_file}', encoding='utf-8').read())"
            ]
            
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if proc.returncode == 0:
                result["status"] = "passed"
                result["message"] = "服务器代码可以成功导入"
            else:
                result["status"] = "failed"
                result["message"] = "导入失败"
                result["details"]["stderr"] = proc.stderr
                result["details"]["stdout"] = proc.stdout
            
        except subprocess.TimeoutExpired:
            result["status"] = "failed"
            result["message"] = "导入超时（可能是代码执行问题）"
        except Exception as e:
            result["status"] = "failed"
            result["message"] = f"测试异常: {str(e)}"
        
        return result
    
    def test_dependencies(self) -> Dict[str, Any]:
        """测试依赖是否安装"""
        result = {
            "name": "依赖测试",
            "status": "unknown",
            "message": "",
            "details": {}
        }
        
        try:
            # 检查 pyproject.toml
            pyproject = self.server_path / "pyproject.toml"
            if not pyproject.exists():
                result["status"] = "failed"
                result["message"] = "pyproject.toml 不存在"
                return result
            
            # 测试关键依赖
            required_packages = ["fastmcp", "httpx"]
            missing_packages = []
            
            for package in required_packages:
                cmd = [sys.executable, "-c", f"import {package}"]
                proc = subprocess.run(cmd, capture_output=True, timeout=5)
                if proc.returncode != 0:
                    missing_packages.append(package)
            
            if missing_packages:
                result["status"] = "failed"
                result["message"] = f"缺少依赖: {', '.join(missing_packages)}"
                result["details"]["missing"] = missing_packages
                result["details"]["hint"] = "运行: pip install -e ."
            else:
                result["status"] = "passed"
                result["message"] = "所有依赖已安装"
            
        except Exception as e:
            result["status"] = "failed"
            result["message"] = f"测试异常: {str(e)}"
        
        return result
    
    def test_syntax(self) -> Dict[str, Any]:
        """测试 Python 语法"""
        result = {
            "name": "语法测试",
            "status": "unknown",
            "message": "",
            "details": {}
        }
        
        try:
            cmd = [sys.executable, "-m", "py_compile", str(self.server_file)]
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if proc.returncode == 0:
                result["status"] = "passed"
                result["message"] = "Python 语法正确"
            else:
                result["status"] = "failed"
                result["message"] = "语法错误"
                result["details"]["error"] = proc.stderr
            
        except Exception as e:
            result["status"] = "failed"
            result["message"] = f"测试异常: {str(e)}"
        
        return result
    
    def test_structure(self) -> Dict[str, Any]:
        """测试项目结构"""
        result = {
            "name": "结构测试",
            "status": "unknown",
            "message": "",
            "details": {}
        }
        
        try:
            required_files = [
                "server.py",
                "pyproject.toml",
                "README.md"
            ]
            
            missing_files = []
            for file in required_files:
                if not (self.server_path / file).exists():
                    missing_files.append(file)
            
            if missing_files:
                result["status"] = "failed"
                result["message"] = f"缺少文件: {', '.join(missing_files)}"
                result["details"]["missing"] = missing_files
            else:
                result["status"] = "passed"
                result["message"] = "项目结构完整"
                result["details"]["files"] = required_files
            
        except Exception as e:
            result["status"] = "failed"
            result["message"] = f"测试异常: {str(e)}"
        
        return result
    
    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        print(f"🧪 测试 MCP 服务器: {self.server_path.name}")
        print("=" * 60)
        
        tests = [
            self.test_structure,
            self.test_syntax,
            self.test_dependencies,
            self.test_import,
        ]
        
        results = []
        passed = 0
        failed = 0
        
        for test_func in tests:
            result = test_func()
            results.append(result)
            
            # 打印结果
            status_icon = {
                "passed": "✅",
                "failed": "❌",
                "skipped": "⏭️",
                "unknown": "❓"
            }.get(result["status"], "❓")
            
            print(f"{status_icon} {result['name']}: {result['message']}")
            
            if result.get("details"):
                for key, value in result["details"].items():
                    if isinstance(value, str) and len(value) < 200:
                        print(f"   {key}: {value}")
            
            if result["status"] == "passed":
                passed += 1
            elif result["status"] == "failed":
                failed += 1
        
        print("=" * 60)
        print(f"📊 测试结果: {passed} 通过, {failed} 失败, 共 {len(results)} 项")
        
        summary = {
            "server_path": str(self.server_path),
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "success_rate": passed / len(results) if results else 0,
            "all_passed": failed == 0,
            "results": results
        }
        
        return summary


def test_mcp_server(server_path: str) -> Dict[str, Any]:
    """测试 MCP 服务器"""
    tester = MCPTester(Path(server_path))
    return tester.run_all_tests()


