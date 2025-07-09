#!/usr/bin/env python3
"""
文档统计脚本

分析文档质量和覆盖率
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any
import markdown
from collections import defaultdict

def count_words(text: str) -> int:
    """统计文字数量"""
    # 移除Markdown语法
    text = re.sub(r'[#*`_\[\]()]', '', text)
    # 移除HTML标签
    text = re.sub(r'<[^>]+>', '', text)
    # 统计中英文字符
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
    return chinese_chars + english_words

def extract_code_blocks(content: str) -> List[str]:
    """提取代码块"""
    pattern = r'```[\w]*\n(.*?)\n```'
    return re.findall(pattern, content, re.DOTALL)

def extract_links(content: str) -> Dict[str, List[str]]:
    """提取链接"""
    internal_links = re.findall(r'\[([^\]]+)\]\((?!http)([^)]+)\)', content)
    external_links = re.findall(r'\[([^\]]+)\]\((https?://[^)]+)\)', content)
    
    return {
        'internal': [link[1] for link in internal_links],
        'external': [link[1] for link in external_links]
    }

def extract_images(content: str) -> List[str]:
    """提取图片"""
    return re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', content)

def analyze_markdown_file(file_path: Path) -> Dict[str, Any]:
    """分析单个Markdown文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 基本统计
    stats = {
        'file': str(file_path),
        'size_bytes': file_path.stat().st_size,
        'lines': len(content.splitlines()),
        'words': count_words(content),
        'characters': len(content)
    }
    
    # 内容分析
    stats['headings'] = len(re.findall(r'^#+\s', content, re.MULTILINE))
    stats['code_blocks'] = len(extract_code_blocks(content))
    stats['links'] = extract_links(content)
    stats['images'] = len(extract_images(content))
    stats['tables'] = len(re.findall(r'^\|.*\|$', content, re.MULTILINE))
    stats['admonitions'] = len(re.findall(r'!!!\s+\w+', content))
    
    # 质量指标
    stats['has_title'] = bool(re.search(r'^#\s+', content, re.MULTILINE))
    stats['has_description'] = 'description:' in content or len(content) > 100
    stats['has_examples'] = stats['code_blocks'] > 0
    stats['has_navigation'] = len(stats['links']['internal']) > 0
    
    return stats

def calculate_quality_score(stats: Dict[str, Any]) -> float:
    """计算文档质量评分"""
    score = 0
    max_score = 100
    
    # 基础内容 (40分)
    if stats['has_title']:
        score += 10
    if stats['has_description']:
        score += 10
    if stats['words'] >= 100:
        score += 10
    if stats['headings'] >= 2:
        score += 10
    
    # 代码示例 (20分)
    if stats['has_examples']:
        score += 15
    if stats['code_blocks'] >= 3:
        score += 5
    
    # 导航和链接 (20分)
    if stats['has_navigation']:
        score += 10
    if len(stats['links']['internal']) >= 3:
        score += 5
    if len(stats['links']['external']) >= 1:
        score += 5
    
    # 丰富内容 (20分)
    if stats['images'] > 0:
        score += 5
    if stats['tables'] > 0:
        score += 5
    if stats['admonitions'] > 0:
        score += 5
    if stats['words'] >= 500:
        score += 5
    
    return min(score, max_score)

def analyze_documentation() -> Dict[str, Any]:
    """分析整个文档"""
    docs_dir = Path(__file__).parent.parent / "docs"
    
    if not docs_dir.exists():
        return {"error": "文档目录不存在"}
    
    # 收集所有Markdown文件
    md_files = list(docs_dir.rglob("*.md"))
    
    if not md_files:
        return {"error": "未找到Markdown文件"}
    
    # 分析每个文件
    file_stats = []
    total_stats = defaultdict(int)
    
    for md_file in md_files:
        try:
            stats = analyze_markdown_file(md_file)
            stats['quality_score'] = calculate_quality_score(stats)
            file_stats.append(stats)
            
            # 累计统计
            for key in ['words', 'lines', 'code_blocks', 'images', 'tables', 'headings']:
                total_stats[key] += stats.get(key, 0)
            
            total_stats['internal_links'] += len(stats['links']['internal'])
            total_stats['external_links'] += len(stats['links']['external'])
            
        except Exception as e:
            print(f"分析文件 {md_file} 时出错: {e}")
    
    # 计算总体统计
    total_files = len(file_stats)
    avg_quality = sum(f['quality_score'] for f in file_stats) / total_files if total_files > 0 else 0
    
    # 文档覆盖率分析
    coverage_stats = analyze_coverage(docs_dir)
    
    # 生成最终统计
    final_stats = {
        'generated_at': '2024-01-15T10:30:00Z',
        'total_pages': total_files,
        'total_words': total_stats['words'],
        'total_lines': total_stats['lines'],
        'code_examples': total_stats['code_blocks'],
        'images': total_stats['images'],
        'tables': total_stats['tables'],
        'headings': total_stats['headings'],
        'internal_links': total_stats['internal_links'],
        'external_links': total_stats['external_links'],
        'average_quality_score': round(avg_quality, 1),
        'quality_score': round(avg_quality, 0),
        'coverage': coverage_stats['coverage_percentage'],
        'file_details': file_stats,
        'coverage_details': coverage_stats
    }
    
    return final_stats

def analyze_coverage(docs_dir: Path) -> Dict[str, Any]:
    """分析文档覆盖率"""
    # 预期的文档结构
    expected_docs = [
        'index.md',
        'getting-started/index.md',
        'getting-started/installation.md',
        'getting-started/configuration.md',
        'user-guide/index.md',
        'api-reference/index.md',
        'api-reference/mcp-tools.md',
        'best-practices/index.md',
        'examples/index.md',
        'changelog.md'
    ]
    
    existing_docs = []
    missing_docs = []
    
    for doc in expected_docs:
        doc_path = docs_dir / doc
        if doc_path.exists():
            existing_docs.append(doc)
        else:
            missing_docs.append(doc)
    
    coverage_percentage = round((len(existing_docs) / len(expected_docs)) * 100, 1)
    
    return {
        'expected_count': len(expected_docs),
        'existing_count': len(existing_docs),
        'missing_count': len(missing_docs),
        'coverage_percentage': coverage_percentage,
        'existing_docs': existing_docs,
        'missing_docs': missing_docs
    }

def generate_quality_report(stats: Dict[str, Any]) -> str:
    """生成质量报告"""
    report = f"""# 📊 文档质量报告

## 总体统计

- **总页面数**: {stats['total_pages']}
- **总字数**: {stats['total_words']:,}
- **代码示例**: {stats['code_examples']}
- **图片数量**: {stats['images']}
- **内部链接**: {stats['internal_links']}
- **外部链接**: {stats['external_links']}

## 质量评分

**总体评分**: {stats['quality_score']}/100

## 覆盖率分析

**文档覆盖率**: {stats['coverage']}%

### 已完成文档
"""
    
    for doc in stats['coverage_details']['existing_docs']:
        report += f"- ✅ {doc}\n"
    
    if stats['coverage_details']['missing_docs']:
        report += "\n### 缺失文档\n"
        for doc in stats['coverage_details']['missing_docs']:
            report += f"- ❌ {doc}\n"
    
    report += f"""
## 详细统计

| 文件 | 字数 | 质量评分 | 代码示例 | 链接数 |
|------|------|----------|----------|--------|
"""
    
    for file_stat in stats['file_details'][:10]:  # 显示前10个文件
        file_name = Path(file_stat['file']).name
        report += f"| {file_name} | {file_stat['words']} | {file_stat['quality_score']}/100 | {file_stat['code_blocks']} | {len(file_stat['links']['internal'])} |\n"
    
    return report

def main():
    """主函数"""
    print("📊 分析文档统计...")
    
    # 分析文档
    stats = analyze_documentation()
    
    if 'error' in stats:
        print(f"❌ 错误: {stats['error']}")
        return
    
    # 输出JSON格式的统计信息
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    
    # 生成质量报告
    report = generate_quality_report(stats)
    
    # 保存报告
    report_file = Path(__file__).parent.parent / "docs_quality_report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📋 质量报告已保存: {report_file}", file=sys.stderr)
    print(f"📈 总体质量评分: {stats['quality_score']}/100", file=sys.stderr)
    print(f"📊 文档覆盖率: {stats['coverage']}%", file=sys.stderr)

if __name__ == "__main__":
    import sys
    main()
