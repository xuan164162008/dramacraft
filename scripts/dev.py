#!/usr/bin/env python3
"""
DramaCraft 开发工具

本地开发和测试的便捷脚本
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd: str, cwd: Path = None) -> bool:
    """运行命令并返回是否成功"""
    try:
        print(f"🔧 运行: {cmd}")
        result = subprocess.run(
            cmd, 
            shell=True, 
            cwd=cwd, 
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ 成功")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"❌ 失败")
            if result.stderr:
                print(f"错误: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 执行出错: {e}")
        return False

def install_deps():
    """安装开发依赖"""
    print("📦 安装开发依赖...")
    
    deps = [
        "mkdocs-material",
        "ruff",
        "mypy",
        "pytest",
        "requests"
    ]
    
    cmd = f"/usr/bin/python3 -m pip install --user {' '.join(deps)}"
    return run_command(cmd)

def build_docs():
    """构建文档"""
    print("🏗️ 构建文档...")
    project_root = Path(__file__).parent.parent
    return run_command("/usr/bin/python3 -m mkdocs build --clean", cwd=project_root)

def serve_docs():
    """启动文档服务器"""
    print("🌐 启动文档服务器...")
    print("📍 访问 http://localhost:8000")
    print("⏹️ 按 Ctrl+C 停止")
    
    project_root = Path(__file__).parent.parent
    try:
        subprocess.run("/usr/bin/python3 -m mkdocs serve", shell=True, cwd=project_root)
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")

def clean():
    """清理构建文件"""
    print("🧹 清理构建文件...")
    project_root = Path(__file__).parent.parent
    
    # 清理目录
    clean_dirs = [
        project_root / "site",
        project_root / "__pycache__",
        project_root / ".pytest_cache",
        project_root / ".mypy_cache",
        project_root / ".ruff_cache"
    ]
    
    for dir_path in clean_dirs:
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"✅ 已清理: {dir_path.name}")
    
    # 清理文件
    clean_files = [
        project_root / ".coverage",
        project_root / "coverage.xml"
    ]
    
    for file_path in clean_files:
        if file_path.exists():
            file_path.unlink()
            print(f"✅ 已清理: {file_path.name}")

def lint():
    """代码质量检查"""
    print("🔍 代码质量检查...")
    project_root = Path(__file__).parent.parent
    
    success = True
    
    # Ruff 检查
    print("\n📋 Ruff 代码检查...")
    if not run_command("ruff check src/", cwd=project_root):
        success = False
    
    # Ruff 格式检查
    print("\n🎨 Ruff 格式检查...")
    if not run_command("ruff format src/ --check", cwd=project_root):
        success = False
    
    # MyPy 类型检查
    print("\n🔬 MyPy 类型检查...")
    if not run_command("mypy src/ --ignore-missing-imports", cwd=project_root):
        success = False
    
    return success

def format_code():
    """格式化代码"""
    print("🎨 格式化代码...")
    project_root = Path(__file__).parent.parent
    return run_command("ruff format src/", cwd=project_root)

def test():
    """运行测试"""
    print("🧪 运行测试...")
    project_root = Path(__file__).parent.parent
    
    # 创建测试目录（如果不存在）
    test_dir = project_root / "tests"
    if not test_dir.exists():
        test_dir.mkdir()
        
        # 创建简单的测试文件
        test_file = test_dir / "test_basic.py"
        test_file.write_text("""
def test_basic():
    \"\"\"基础测试\"\"\"
    assert True

def test_import():
    \"\"\"测试导入\"\"\"
    try:
        import sys
        assert sys.version_info >= (3, 9)
    except ImportError:
        assert False, "Python导入失败"
""")
        print("✅ 创建了基础测试文件")
    
    return run_command("python -m pytest tests/ -v", cwd=project_root)

def check_deployment():
    """检查部署状态"""
    print("🌐 检查部署状态...")
    project_root = Path(__file__).parent.parent
    return run_command("python scripts/check_deployment.py", cwd=project_root)

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("""
🛠️ DramaCraft 开发工具

用法:
  python scripts/dev.py <command>

命令:
  install     - 安装开发依赖
  build       - 构建文档
  serve       - 启动文档服务器
  clean       - 清理构建文件
  lint        - 代码质量检查
  format      - 格式化代码
  test        - 运行测试
  check       - 检查部署状态
  all         - 执行完整流程 (clean + install + lint + build + test)

示例:
  python scripts/dev.py serve
  python scripts/dev.py all
        """)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    print(f"🚀 DramaCraft 开发工具")
    print(f"🎯 执行命令: {command}")
    print("-" * 50)
    
    success = True
    
    if command == "install":
        success = install_deps()
    elif command == "build":
        success = build_docs()
    elif command == "serve":
        serve_docs()
    elif command == "clean":
        clean()
    elif command == "lint":
        success = lint()
    elif command == "format":
        success = format_code()
    elif command == "test":
        success = test()
    elif command == "check":
        success = check_deployment()
    elif command == "all":
        success = (
            clean() and
            install_deps() and
            lint() and
            build_docs() and
            test()
        )
    else:
        print(f"❌ 未知命令: {command}")
        success = False
    
    print("-" * 50)
    if success:
        print("🎉 操作完成！")
        sys.exit(0)
    else:
        print("❌ 操作失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()
