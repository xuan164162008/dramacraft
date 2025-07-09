#!/usr/bin/env python3
"""
文档结构验证脚本

验证文档结构的完整性和一致性
"""

import sys
from pathlib import Path
import yaml
import re
from typing import List, Dict, Set

def validate_mkdocs_config() -> bool:
    """验证mkdocs.yml配置文件"""
    print("🔍 验证MkDocs配置...")
    
    config_file = Path("mkdocs.yml")
    if not config_file.exists():
        print("❌ mkdocs.yml文件不存在")
        return False
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 检查必需的配置项
        required_keys = ['site_name', 'site_url', 'theme', 'nav']
        for key in required_keys:
            if key not in config:
                print(f"❌ 缺少必需的配置项: {key}")
                return False
        
        print("✅ MkDocs配置验证通过")
        return True
        
    except yaml.YAMLError as e:
        print(f"❌ YAML解析错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 配置验证失败: {e}")
        return False

def validate_navigation_structure() -> bool:
    """验证导航结构"""
    print("🔍 验证导航结构...")
    
    try:
        with open("mkdocs.yml", 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        nav = config.get('nav', [])
        if not nav:
            print("❌ 导航结构为空")
            return False
        
        # 检查导航项对应的文件是否存在
        def check_nav_item(item, prefix=""):
            if isinstance(item, dict):
                for key, value in item.items():
                    if isinstance(value, str):
                        # 这是一个文件路径
                        file_path = Path("docs") / value
                        if not file_path.exists():
                            print(f"❌ 导航文件不存在: {value}")
                            return False
                    elif isinstance(value, list):
                        # 这是一个子导航
                        for sub_item in value:
                            if not check_nav_item(sub_item, f"{prefix}{key}/"):
                                return False
            return True
        
        for item in nav:
            if not check_nav_item(item):
                return False
        
        print("✅ 导航结构验证通过")
        return True
        
    except Exception as e:
        print(f"❌ 导航结构验证失败: {e}")
        return False

def validate_markdown_files() -> bool:
    """验证Markdown文件"""
    print("🔍 验证Markdown文件...")
    
    docs_dir = Path("docs")
    if not docs_dir.exists():
        print("❌ docs目录不存在")
        return False
    
    md_files = list(docs_dir.rglob("*.md"))
    if not md_files:
        print("❌ 未找到Markdown文件")
        return False
    
    issues = []
    
    for md_file in md_files:
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查文件是否为空
            if not content.strip():
                issues.append(f"空文件: {md_file.relative_to(docs_dir)}")
                continue
            
            # 检查是否有标题
            if not re.search(r'^#\s+', content, re.MULTILINE):
                issues.append(f"缺少主标题: {md_file.relative_to(docs_dir)}")
            
            # 检查是否有无效的链接格式
            invalid_links = re.findall(r'\]\([^)]*\s[^)]*\)', content)
            if invalid_links:
                issues.append(f"无效链接格式: {md_file.relative_to(docs_dir)}")
            
        except Exception as e:
            issues.append(f"读取文件失败 {md_file.relative_to(docs_dir)}: {e}")
    
    if issues:
        print("❌ Markdown文件验证失败:")
        for issue in issues[:10]:  # 只显示前10个问题
            print(f"  - {issue}")
        if len(issues) > 10:
            print(f"  ... 还有 {len(issues) - 10} 个问题")
        return False
    
    print(f"✅ Markdown文件验证通过 ({len(md_files)} 个文件)")
    return True

def validate_assets() -> bool:
    """验证资源文件"""
    print("🔍 验证资源文件...")
    
    assets_dir = Path("docs/assets")
    if not assets_dir.exists():
        print("⚠️ assets目录不存在，跳过验证")
        return True
    
    # 检查CSS文件
    css_files = list(assets_dir.rglob("*.css"))
    for css_file in css_files:
        try:
            with open(css_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 简单的CSS语法检查
            if content.count('{') != content.count('}'):
                print(f"❌ CSS语法错误: {css_file.relative_to(assets_dir)}")
                return False
                
        except Exception as e:
            print(f"❌ 读取CSS文件失败 {css_file.relative_to(assets_dir)}: {e}")
            return False
    
    print(f"✅ 资源文件验证通过 ({len(css_files)} 个CSS文件)")
    return True

def validate_required_pages() -> bool:
    """验证必需的页面"""
    print("🔍 验证必需页面...")
    
    required_pages = [
        "docs/index.md",
        "docs/getting-started/index.md",
        "docs/api-reference/index.md"
    ]
    
    missing_pages = []
    for page in required_pages:
        if not Path(page).exists():
            missing_pages.append(page)
    
    if missing_pages:
        print("❌ 缺少必需页面:")
        for page in missing_pages:
            print(f"  - {page}")
        return False
    
    print("✅ 必需页面验证通过")
    return True

def validate_frontmatter() -> bool:
    """验证前置元数据"""
    print("🔍 验证前置元数据...")
    
    docs_dir = Path("docs")
    md_files = list(docs_dir.rglob("*.md"))
    
    issues = []
    
    for md_file in md_files:
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否有前置元数据
            if content.startswith('---'):
                # 提取前置元数据
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    try:
                        frontmatter = yaml.safe_load(parts[1])
                        
                        # 检查title字段
                        if 'title' not in frontmatter:
                            issues.append(f"缺少title: {md_file.relative_to(docs_dir)}")
                        
                    except yaml.YAMLError:
                        issues.append(f"前置元数据格式错误: {md_file.relative_to(docs_dir)}")
            
        except Exception as e:
            issues.append(f"检查前置元数据失败 {md_file.relative_to(docs_dir)}: {e}")
    
    if issues:
        print("⚠️ 前置元数据问题:")
        for issue in issues[:5]:  # 只显示前5个问题
            print(f"  - {issue}")
        if len(issues) > 5:
            print(f"  ... 还有 {len(issues) - 5} 个问题")
    else:
        print("✅ 前置元数据验证通过")
    
    return True  # 前置元数据问题不阻止构建

def main():
    """主函数"""
    print("📋 DramaCraft 文档结构验证")
    print("=" * 50)
    
    validations = [
        ("MkDocs配置", validate_mkdocs_config),
        ("导航结构", validate_navigation_structure),
        ("Markdown文件", validate_markdown_files),
        ("资源文件", validate_assets),
        ("必需页面", validate_required_pages),
        ("前置元数据", validate_frontmatter),
    ]
    
    all_passed = True
    
    for name, validator in validations:
        print(f"\n🔍 {name}验证:")
        try:
            if not validator():
                all_passed = False
        except Exception as e:
            print(f"❌ {name}验证出错: {e}")
            all_passed = False
    
    print("\n" + "=" * 50)
    
    if all_passed:
        print("✅ 所有验证通过！文档结构正确")
        sys.exit(0)
    else:
        print("❌ 部分验证失败，请检查上述问题")
        sys.exit(1)

if __name__ == "__main__":
    main()
