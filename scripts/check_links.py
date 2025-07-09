#!/usr/bin/env python3
"""
链接检查脚本

检查文档中的内部和外部链接有效性
"""

import re
import sys
import asyncio
import aiohttp
from pathlib import Path
from typing import List, Dict, Tuple, Set
from urllib.parse import urljoin, urlparse

class LinkChecker:
    def __init__(self, docs_dir: Path):
        self.docs_dir = docs_dir
        self.base_url = "https://agions.github.io/dramacraft/"
        self.internal_links: Set[str] = set()
        self.external_links: Set[str] = set()
        self.broken_links: List[Dict] = []
        self.valid_pages: Set[str] = set()
        
    def collect_pages(self) -> None:
        """收集所有有效页面"""
        for md_file in self.docs_dir.rglob("*.md"):
            rel_path = md_file.relative_to(self.docs_dir)
            
            # 转换为URL路径
            if rel_path.name == "index.md":
                if rel_path.parent == Path("."):
                    url_path = ""
                else:
                    url_path = str(rel_path.parent) + "/"
            else:
                url_path = str(rel_path.with_suffix("")) + "/"
            
            self.valid_pages.add(url_path)
            
            # 也添加带.html的版本
            if url_path.endswith("/"):
                html_path = url_path + "index.html"
            else:
                html_path = url_path + ".html"
            self.valid_pages.add(html_path)
    
    def extract_links_from_file(self, file_path: Path) -> Tuple[List[str], List[str]]:
        """从文件中提取链接"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"读取文件 {file_path} 失败: {e}")
            return [], []
        
        # 提取Markdown链接
        md_links = re.findall(r'\[([^\]]*)\]\(([^)]+)\)', content)
        
        # 提取HTML链接
        html_links = re.findall(r'href=["\']([^"\']+)["\']', content)
        
        internal_links = []
        external_links = []
        
        # 处理Markdown链接
        for text, url in md_links:
            url = url.split('#')[0]  # 移除锚点
            if url.startswith('http'):
                external_links.append(url)
            elif url and not url.startswith('mailto:'):
                internal_links.append(url)
        
        # 处理HTML链接
        for url in html_links:
            url = url.split('#')[0]  # 移除锚点
            if url.startswith('http'):
                external_links.append(url)
            elif url and not url.startswith('mailto:') and not url.startswith('javascript:'):
                internal_links.append(url)
        
        return internal_links, external_links
    
    def normalize_internal_link(self, link: str, current_file: Path) -> str:
        """标准化内部链接"""
        if link.startswith('/'):
            # 绝对路径
            return link[1:]  # 移除开头的/
        else:
            # 相对路径
            current_dir = current_file.parent.relative_to(self.docs_dir)
            if current_dir == Path("."):
                return link
            else:
                return str(current_dir / link)
    
    def check_internal_links(self) -> None:
        """检查内部链接"""
        print("🔍 检查内部链接...")
        
        for md_file in self.docs_dir.rglob("*.md"):
            internal_links, _ = self.extract_links_from_file(md_file)
            
            for link in internal_links:
                normalized_link = self.normalize_internal_link(link, md_file)
                
                # 标准化路径
                if normalized_link.endswith('/'):
                    check_paths = [normalized_link, normalized_link + "index.html"]
                elif '.' not in normalized_link.split('/')[-1]:
                    check_paths = [normalized_link + "/", normalized_link + "/index.html"]
                else:
                    check_paths = [normalized_link]
                
                # 检查是否存在
                found = any(path in self.valid_pages for path in check_paths)
                
                if not found:
                    self.broken_links.append({
                        'type': 'internal',
                        'file': str(md_file.relative_to(self.docs_dir)),
                        'link': link,
                        'normalized': normalized_link,
                        'reason': 'Page not found'
                    })
    
    async def check_external_link(self, session: aiohttp.ClientSession, url: str) -> Tuple[str, bool, str]:
        """检查单个外部链接"""
        try:
            async with session.head(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status < 400:
                    return url, True, f"OK ({response.status})"
                else:
                    return url, False, f"HTTP {response.status}"
        except asyncio.TimeoutError:
            return url, False, "Timeout"
        except Exception as e:
            return url, False, str(e)
    
    async def check_external_links(self) -> None:
        """检查外部链接"""
        print("🌐 检查外部链接...")
        
        # 收集所有外部链接
        all_external_links = set()
        for md_file in self.docs_dir.rglob("*.md"):
            _, external_links = self.extract_links_from_file(md_file)
            all_external_links.update(external_links)
        
        if not all_external_links:
            print("✅ 未找到外部链接")
            return
        
        # 异步检查链接
        async with aiohttp.ClientSession() as session:
            tasks = [self.check_external_link(session, url) for url in all_external_links]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        for result in results:
            if isinstance(result, Exception):
                continue
            
            url, is_valid, reason = result
            if not is_valid:
                self.broken_links.append({
                    'type': 'external',
                    'link': url,
                    'reason': reason
                })
    
    def generate_report(self) -> str:
        """生成检查报告"""
        report = "# 🔗 链接检查报告\n\n"
        
        if not self.broken_links:
            report += "✅ **所有链接都有效！**\n\n"
            report += f"- 检查了 {len(self.valid_pages)} 个页面\n"
            report += f"- 所有内部链接都指向有效页面\n"
            report += f"- 所有外部链接都可访问\n"
            return report
        
        # 分类统计
        internal_broken = [link for link in self.broken_links if link['type'] == 'internal']
        external_broken = [link for link in self.broken_links if link['type'] == 'external']
        
        report += f"❌ **发现 {len(self.broken_links)} 个无效链接**\n\n"
        
        if internal_broken:
            report += f"## 内部链接问题 ({len(internal_broken)}个)\n\n"
            for link in internal_broken:
                report += f"- **{link['file']}**: `{link['link']}` - {link['reason']}\n"
            report += "\n"
        
        if external_broken:
            report += f"## 外部链接问题 ({len(external_broken)}个)\n\n"
            for link in external_broken:
                report += f"- `{link['link']}` - {link['reason']}\n"
            report += "\n"
        
        return report
    
    async def run_check(self) -> bool:
        """运行完整检查"""
        print("🚀 开始链接检查...")
        
        # 收集页面
        self.collect_pages()
        print(f"📄 发现 {len(self.valid_pages)} 个有效页面")
        
        # 检查内部链接
        self.check_internal_links()
        
        # 检查外部链接
        await self.check_external_links()
        
        # 生成报告
        report = self.generate_report()
        print(report)
        
        # 保存报告
        report_file = self.docs_dir.parent / "link_check_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"📋 报告已保存: {report_file}")
        
        # 返回是否有问题
        return len(self.broken_links) == 0

async def main():
    """主函数"""
    docs_dir = Path(__file__).parent.parent / "docs"
    
    if not docs_dir.exists():
        print("❌ 文档目录不存在")
        sys.exit(1)
    
    checker = LinkChecker(docs_dir)
    success = await checker.run_check()
    
    if success:
        print("✅ 链接检查通过")
        sys.exit(0)
    else:
        print("❌ 发现无效链接")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
