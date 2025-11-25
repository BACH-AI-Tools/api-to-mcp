#!/usr/bin/env python3
"""
API to MCP GUI 启动器
"""
import subprocess
import sys

if __name__ == "__main__":
    print("🚀 启动 API to MCP GUI...")
    print("📍 访问: http://localhost:8501")
    print()
    
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        "src/api_to_mcp/gui.py",
        "--server.port=8501",
        "--server.headless=true"
    ])






