# 批量爬取 RapidAPI 脚本（Windows PowerShell）

param(
    [string]$UrlsFile = "rapidapi_urls_example.txt",
    [int]$Delay = 20,
    [string]$Transport = "stdio",
    [switch]$UseSelenium
)

Write-Host "🚀 开始批量爬取 RapidAPI" -ForegroundColor Green
Write-Host "📝 URL 文件: $UrlsFile"
Write-Host "⏱️  延迟: $Delay 秒"
Write-Host "🔧 传输协议: $Transport"
Write-Host "🌐 使用 Selenium: $(if ($UseSelenium) {'是'} else {'否'})"
Write-Host ""

# 构建命令参数
$args = @(
    "batch_rapidapi.py",
    $UrlsFile,
    "--delay", $Delay,
    "--retry", "3",
    "--transport", $Transport
)

if ($UseSelenium) {
    $args += "--use-selenium"
}

# 运行批量爬取
& python $args

Write-Host ""
Write-Host "✅ 批量爬取完成！" -ForegroundColor Green
Write-Host "📁 查看结果: generated_mcps/"

