#!/usr/bin/env python3
"""
RapidAPI 批量转 MCP 一键工具

自动完成：发现 → 订阅 → 测试 → 生成 MCP 的完整流程

使用方法：
    # 完整流程（推荐晚上挂机）
    python rapidapi_batch_100.py --target 100
    
    # 只执行特定阶段
    python rapidapi_batch_100.py --stage discovery
    python rapidapi_batch_100.py --stage subscribe
    python rapidapi_batch_100.py --stage test
    python rapidapi_batch_100.py --stage generate
"""
import os
import sys
import json
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import click


class RapidAPIBatchPipeline:
    """RapidAPI 批量处理管道"""
    
    def __init__(self, target: int = 100, output_dir: str = "generated_mcps"):
        self.target = target
        self.output_dir = output_dir
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 文件名
        self.discovered_file = f"discovered_{self.timestamp}.json"
        self.subscribed_file = f"subscribed_{self.timestamp}.txt"
        self.tested_file = f"tested_{self.timestamp}.txt"
        
        # 统计
        self.stats = {
            "discovered": 0,
            "subscribed": 0,
            "tested": 0,
            "generated": 0
        }
    
    def log(self, msg: str, level: str = "INFO"):
        """日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {msg}")
    
    async def stage_1_discovery(self) -> bool:
        """阶段 1: API 发现"""
        self.log("=" * 60)
        self.log("📊 阶段 1: API 发现")
        self.log("=" * 60)
        
        # 计算需要发现的数量（考虑到筛选损耗，多发现一些）
        discover_target = self.target * 5  # 5x 冗余
        
        cmd = [
            sys.executable, "rapidapi_discovery.py",
            "--category", "all",
            "--limit", str(discover_target),
            "--output", self.discovered_file
        ]
        
        self.log(f"运行: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, check=True)
            
            # 读取结果
            if Path(self.discovered_file).exists():
                data = json.loads(Path(self.discovered_file).read_text(encoding="utf-8"))
                self.stats["discovered"] = data.get("total_count", 0)
                self.log(f"✅ 发现 {self.stats['discovered']} 个 API")
                return True
            else:
                self.log("❌ 发现文件不存在", "ERROR")
                return False
                
        except subprocess.CalledProcessError as e:
            self.log(f"❌ 发现失败: {e}", "ERROR")
            return False
    
    async def stage_2_subscribe(self, apis_file: str = None) -> bool:
        """阶段 2: 智能订阅"""
        self.log("=" * 60)
        self.log("📊 阶段 2: 智能订阅")
        self.log("=" * 60)
        
        input_file = apis_file or self.discovered_file
        
        if not Path(input_file).exists():
            self.log(f"❌ 输入文件不存在: {input_file}", "ERROR")
            return False
        
        self.log("⚠️  订阅阶段需要先登录 RapidAPI")
        self.log("   如果是首次运行，请使用以下命令手动登录：")
        self.log(f"   python rapidapi_subscriber.py {input_file} --login --no-headless")
        self.log("")
        
        # 检查是否已有 Cookie
        if not Path("rapidapi_cookies.json").exists():
            self.log("❌ 未找到登录 Cookie，请先手动登录", "ERROR")
            self.log("   运行: python rapidapi_subscriber.py {input_file} --login --no-headless")
            return False
        
        cmd = [
            sys.executable, "rapidapi_subscriber.py",
            input_file,
            "--delay", "5",
            "--limit", str(self.target * 3)  # 3x 冗余
        ]
        
        self.log(f"运行: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, check=True)
            
            # 读取结果
            state_file = "rapidapi_subscription_state.json"
            if Path(state_file).exists():
                data = json.loads(Path(state_file).read_text(encoding="utf-8"))
                stats = data.get("stats", {})
                self.stats["subscribed"] = stats.get("subscribed", 0) + stats.get("already", 0)
                self.log(f"✅ 成功订阅 {self.stats['subscribed']} 个 API")
                
                # 重命名订阅列表
                if Path("subscribed_apis.txt").exists():
                    Path("subscribed_apis.txt").rename(self.subscribed_file)
                
                return True
            
        except subprocess.CalledProcessError as e:
            self.log(f"❌ 订阅失败: {e}", "ERROR")
        
        return False
    
    async def stage_3_test(self, apis_file: str = None) -> bool:
        """阶段 3: 端点测试"""
        self.log("=" * 60)
        self.log("📊 阶段 3: 端点测试")
        self.log("=" * 60)
        
        input_file = apis_file or self.subscribed_file
        
        if not Path(input_file).exists():
            self.log(f"❌ 输入文件不存在: {input_file}", "ERROR")
            return False
        
        # 检查 API Key
        api_key = os.getenv("RAPIDAPI_KEY") or os.getenv("API_KEY")
        if not api_key:
            self.log("⚠️  未设置 RAPIDAPI_KEY 环境变量", "WARN")
            self.log("   设置方法: export RAPIDAPI_KEY=your_key")
        
        cmd = [
            sys.executable, "rapidapi_tester.py",
            input_file,
            "--delay", "3"
        ]
        
        self.log(f"运行: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, check=True)
            
            # 读取结果
            if Path("tested_apis.txt").exists():
                with open("tested_apis.txt", "r", encoding="utf-8") as f:
                    lines = [l for l in f.readlines() if l.strip() and not l.startswith("#")]
                    self.stats["tested"] = len(lines)
                
                Path("tested_apis.txt").rename(self.tested_file)
                self.log(f"✅ 测试通过 {self.stats['tested']} 个 API")
                return True
                
        except subprocess.CalledProcessError as e:
            self.log(f"❌ 测试失败: {e}", "ERROR")
        
        return False
    
    async def stage_4_generate(self, apis_file: str = None) -> bool:
        """阶段 4: 生成 MCP"""
        self.log("=" * 60)
        self.log("📊 阶段 4: 生成 MCP")
        self.log("=" * 60)
        
        input_file = apis_file or self.tested_file
        
        if not Path(input_file).exists():
            self.log(f"❌ 输入文件不存在: {input_file}", "ERROR")
            return False
        
        # 计算实际要生成的数量
        with open(input_file, "r", encoding="utf-8") as f:
            urls = [l.strip() for l in f.readlines() if l.strip() and not l.startswith("#")]
        
        # 限制到目标数量
        urls_to_generate = urls[:self.target]
        
        # 创建临时文件
        temp_file = f"to_generate_{self.timestamp}.txt"
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(f"# MCP 生成列表 - {datetime.now()}\n")
            for url in urls_to_generate:
                f.write(f"{url}\n")
        
        self.log(f"📊 准备生成 {len(urls_to_generate)} 个 MCP")
        
        cmd = [
            sys.executable, "batch_rapidapi.py",
            temp_file,
            "--use-selenium",
            "--delay", "20",
            "--output-dir", self.output_dir
        ]
        
        self.log(f"运行: {' '.join(cmd)}")
        
        try:
            # 使用 Popen 以便实时显示输出
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            for line in process.stdout:
                print(line, end="")
            
            process.wait()
            
            if process.returncode == 0:
                # 统计生成的 MCP 数量
                output_path = Path(self.output_dir)
                if output_path.exists():
                    mcp_dirs = [d for d in output_path.iterdir() if d.is_dir()]
                    self.stats["generated"] = len(mcp_dirs)
                
                self.log(f"✅ 成功生成 {self.stats['generated']} 个 MCP")
                return True
                
        except Exception as e:
            self.log(f"❌ 生成失败: {e}", "ERROR")
        
        # 清理临时文件
        Path(temp_file).unlink(missing_ok=True)
        
        return False
    
    async def run_full_pipeline(self):
        """运行完整管道"""
        self.log("🚀 开始 RapidAPI 批量转 MCP 管道")
        self.log(f"📊 目标: {self.target} 个 MCP")
        self.log(f"📁 输出目录: {self.output_dir}")
        self.log("=" * 60)
        
        start_time = datetime.now()
        
        # 阶段 1: 发现
        if not await self.stage_1_discovery():
            self.log("❌ 阶段 1 失败，停止管道")
            return
        
        # 阶段 2: 订阅
        if not await self.stage_2_subscribe():
            self.log("❌ 阶段 2 失败，停止管道")
            return
        
        # 阶段 3: 测试
        if not await self.stage_3_test():
            self.log("❌ 阶段 3 失败，停止管道")
            return
        
        # 阶段 4: 生成
        if not await self.stage_4_generate():
            self.log("❌ 阶段 4 失败")
        
        # 总结
        elapsed = datetime.now() - start_time
        
        self.log("")
        self.log("=" * 60)
        self.log("🎉 管道完成!")
        self.log("=" * 60)
        self.log(f"📊 统计:")
        self.log(f"   发现: {self.stats['discovered']} 个 API")
        self.log(f"   订阅: {self.stats['subscribed']} 个 API")
        self.log(f"   测试通过: {self.stats['tested']} 个 API")
        self.log(f"   生成 MCP: {self.stats['generated']} 个")
        self.log(f"⏱️  总耗时: {elapsed}")
        self.log("=" * 60)
        
        if self.stats["generated"] >= self.target:
            self.log(f"✅ 已达到目标 {self.target} 个 MCP!")
        else:
            self.log(f"⚠️  生成 {self.stats['generated']}/{self.target} 个，未达目标")
            self.log("   可能原因：免费 API 数量不足，或部分 API 测试失败")
        
        self.log("")
        self.log(f"📁 MCP 项目位于: {self.output_dir}/")


@click.command()
@click.option("--target", "-t", default=100, type=int, help="目标 MCP 数量")
@click.option("--stage", "-s", type=click.Choice(["all", "discovery", "subscribe", "test", "generate"]), default="all", help="运行特定阶段")
@click.option("--input", "-i", "input_file", default=None, help="输入文件（用于单独运行某阶段）")
@click.option("--output-dir", "-o", default="generated_mcps", help="输出目录")
def main(target: int, stage: str, input_file: str, output_dir: str):
    """
    RapidAPI 批量转 MCP 一键工具
    
    自动完成：发现 → 订阅 → 测试 → 生成 MCP
    
    \b
    完整流程（推荐晚上挂机）：
        python rapidapi_batch_100.py --target 100
    
    \b
    只执行特定阶段：
        python rapidapi_batch_100.py --stage discovery
        python rapidapi_batch_100.py --stage subscribe --input discovered.json
        python rapidapi_batch_100.py --stage test --input subscribed.txt
        python rapidapi_batch_100.py --stage generate --input tested.txt
    
    \b
    首次使用前，需要先登录 RapidAPI：
        python rapidapi_subscriber.py discovered.json --login --no-headless
    """
    print("=" * 60)
    print("🚀 RapidAPI 批量转 MCP 一键工具")
    print("=" * 60)
    print(f"📊 目标: {target} 个 MCP")
    print(f"📍 阶段: {stage}")
    print(f"📁 输出: {output_dir}")
    print("=" * 60)
    
    pipeline = RapidAPIBatchPipeline(target=target, output_dir=output_dir)
    
    async def run():
        if stage == "all":
            await pipeline.run_full_pipeline()
        elif stage == "discovery":
            await pipeline.stage_1_discovery()
        elif stage == "subscribe":
            await pipeline.stage_2_subscribe(input_file)
        elif stage == "test":
            await pipeline.stage_3_test(input_file)
        elif stage == "generate":
            await pipeline.stage_4_generate(input_file)
    
    asyncio.run(run())


if __name__ == "__main__":
    main()




