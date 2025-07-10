#!/usr/bin/env python3
"""
部署状态检查脚本

检查GitHub Pages部署状态和文档可访问性
"""

import requests
import time
import sys
from urllib.parse import urljoin

def check_url(url: str, timeout: int = 10) -> tuple[bool, int, str]:
    """检查URL是否可访问"""
    try:
        response = requests.get(url, timeout=timeout)
        return True, response.status_code, response.reason
    except requests.exceptions.RequestException as e:
        return False, 0, str(e)

def check_github_pages_deployment():
    """检查GitHub Pages部署状态"""
    base_url = "https://agions.github.io/dramacraft"

    print("🔍 检查DramaCraft文档部署状态...")
    print(f"📍 基础URL: {base_url}")
    print("-" * 60)

    # 要检查的页面
    pages_to_check = [
        ("主页", ""),
        ("快速开始", "/getting-started/"),
        ("API参考", "/api-reference/"),
        ("CSS样式", "/assets/stylesheets/extra.css"),
    ]
    
    results = []
    
    for page_name, path in pages_to_check:
        full_url = urljoin(base_url + "/", path.lstrip("/"))
        print(f"🌐 检查 {page_name}: {full_url}")
        
        success, status_code, reason = check_url(full_url)
        
        if success:
            if status_code == 200:
                print(f"  ✅ 成功 (HTTP {status_code})")
                results.append((page_name, True, status_code))
            else:
                print(f"  ⚠️  HTTP {status_code} - {reason}")
                results.append((page_name, False, status_code))
        else:
            print(f"  ❌ 失败: {reason}")
            results.append((page_name, False, 0))
        
        time.sleep(1)  # 避免请求过快
    
    print("-" * 60)
    
    # 统计结果
    successful = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    print(f"📊 检查结果: {successful}/{total} 页面可访问")
    
    if successful == total:
        print("🎉 所有页面都可以正常访问！")
        print(f"🌐 文档网站: {base_url}")
        print("\n📚 可用页面:")
        for page_name, _, _ in results:
            print(f"  - {page_name}")
        
        print("\n🔗 重要链接:")
        print(f"  - 主页: {base_url}")
        print(f"  - 快速开始: {base_url}/getting-started/")
        print(f"  - API文档: {base_url}/api-reference/")
        
        return True
    else:
        print("⚠️  部分页面无法访问，可能还在部署中...")
        print("💡 建议:")
        print("  1. 等待几分钟后重试")
        print("  2. 检查GitHub Actions构建状态")
        print("  3. 确认GitHub Pages已启用")
        
        return False

def check_github_actions_status():
    """检查GitHub Actions状态"""
    print("\n🔧 GitHub Actions信息:")
    print("  - 仓库: https://github.com/Agions/dramacraft")
    print("  - Actions: https://github.com/Agions/dramacraft/actions")
    print("  - Pages设置: https://github.com/Agions/dramacraft/settings/pages")

def main():
    """主函数"""
    print("🚀 DramaCraft 部署状态检查工具")
    print("=" * 60)
    
    # 检查部署状态
    deployment_success = check_github_pages_deployment()
    
    # 显示GitHub Actions信息
    check_github_actions_status()
    
    print("\n" + "=" * 60)
    
    if deployment_success:
        print("✅ 部署检查完成 - 文档网站运行正常！")
        sys.exit(0)
    else:
        print("⏳ 部署可能还在进行中，请稍后重试")
        sys.exit(1)

if __name__ == "__main__":
    main()
