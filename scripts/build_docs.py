#!/usr/bin/env python3
"""
文档构建脚本

本地构建和测试文档
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd: str, cwd: Path = None) -> bool:
    """运行命令并返回是否成功"""
    try:
        print(f"🔧 运行命令: {cmd}")
        result = subprocess.run(
            cmd, 
            shell=True, 
            cwd=cwd, 
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ 命令成功: {cmd}")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"❌ 命令失败: {cmd}")
            print(f"错误输出: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 执行命令时出错: {e}")
        return False

def check_dependencies() -> bool:
    """检查依赖是否安装"""
    print("📦 检查依赖...")
    
    dependencies = [
        "mkdocs",
        "mkdocs-material",
        "mkdocs-git-revision-date-localized-plugin",
        "mkdocs-git-authors-plugin"
    ]
    
    missing_deps = []
    
    for dep in dependencies:
        try:
            __import__(dep.replace('-', '_'))
            print(f"✅ {dep} 已安装")
        except ImportError:
            missing_deps.append(dep)
            print(f"❌ {dep} 未安装")
    
    if missing_deps:
        print(f"📥 安装缺失的依赖: {' '.join(missing_deps)}")
        cmd = f"pip install {' '.join(missing_deps)}"
        return run_command(cmd)
    
    return True

def build_docs(project_root: Path) -> bool:
    """构建文档"""
    print("🏗️ 构建文档...")
    
    # 检查mkdocs.yml是否存在
    mkdocs_config = project_root / "mkdocs.yml"
    if not mkdocs_config.exists():
        print(f"❌ 未找到mkdocs.yml配置文件: {mkdocs_config}")
        return False
    
    # 构建文档
    return run_command("mkdocs build --clean", cwd=project_root)

def serve_docs(project_root: Path) -> bool:
    """启动文档服务器"""
    print("🌐 启动文档服务器...")
    print("📍 文档将在 http://localhost:8000 提供服务")
    print("⏹️ 按 Ctrl+C 停止服务器")
    
    try:
        subprocess.run(
            "mkdocs serve", 
            shell=True, 
            cwd=project_root
        )
        return True
    except KeyboardInterrupt:
        print("\n🛑 文档服务器已停止")
        return True
    except Exception as e:
        print(f"❌ 启动服务器时出错: {e}")
        return False

def validate_docs(project_root: Path) -> bool:
    """验证文档"""
    print("🔍 验证文档...")
    
    site_dir = project_root / "site"
    if not site_dir.exists():
        print("❌ 文档未构建，请先运行构建命令")
        return False
    
    # 检查关键文件
    required_files = [
        "index.html",
        "getting-started/index.html",
        "api-reference/index.html"
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = site_dir / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            missing_files.append(file_path)
            print(f"❌ {file_path}")
    
    if missing_files:
        print(f"❌ 缺失文件: {missing_files}")
        return False
    
    # 检查文件大小
    index_file = site_dir / "index.html"
    if index_file.stat().st_size < 1000:
        print("⚠️ index.html文件过小，可能构建不完整")
        return False
    
    print("✅ 文档验证通过")
    return True

def clean_docs(project_root: Path) -> bool:
    """清理文档"""
    print("🧹 清理文档...")
    
    site_dir = project_root / "site"
    if site_dir.exists():
        shutil.rmtree(site_dir)
        print("✅ 已清理site目录")
    
    return True

def main():
    """主函数"""
    project_root = Path(__file__).parent.parent
    
    if len(sys.argv) < 2:
        print("""
📚 DramaCraft 文档构建工具

用法:
  python scripts/build_docs.py <command>

命令:
  build    - 构建文档
  serve    - 启动文档服务器
  validate - 验证文档
  clean    - 清理文档
  all      - 执行完整流程 (clean + build + validate)

示例:
  python scripts/build_docs.py build
  python scripts/build_docs.py serve
  python scripts/build_docs.py all
        """)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    print(f"🚀 DramaCraft 文档构建工具")
    print(f"📁 项目根目录: {project_root}")
    print(f"🎯 执行命令: {command}")
    print("-" * 50)
    
    success = True
    
    if command == "build":
        success = check_dependencies() and build_docs(project_root)
    
    elif command == "serve":
        success = check_dependencies() and serve_docs(project_root)
    
    elif command == "validate":
        success = validate_docs(project_root)
    
    elif command == "clean":
        success = clean_docs(project_root)
    
    elif command == "all":
        success = (
            check_dependencies() and
            clean_docs(project_root) and
            build_docs(project_root) and
            validate_docs(project_root)
        )
    
    else:
        print(f"❌ 未知命令: {command}")
        success = False
    
    print("-" * 50)
    if success:
        print("🎉 操作完成！")
        
        if command in ["build", "all"]:
            print("\n📍 下一步:")
            print("  - 运行 'python scripts/build_docs.py serve' 预览文档")
            print("  - 或推送到GitHub自动部署到GitHub Pages")
            print("  - 文档URL: https://agions.github.io/dramacraft")
        
        sys.exit(0)
    else:
        print("❌ 操作失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()
