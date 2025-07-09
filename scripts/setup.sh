#!/bin/bash
# DramaCraft 项目设置脚本

set -e

echo "🎬 DramaCraft 项目设置开始..."

# 检查 uv 是否安装
if ! command -v uv &> /dev/null; then
    echo "❌ uv 未安装，正在安装..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
fi

echo "✅ uv 已安装: $(uv --version)"

# 创建虚拟环境并安装依赖
echo "📦 安装项目依赖..."
uv sync

# 创建必要的目录
echo "📁 创建项目目录..."
mkdir -p output
mkdir -p temp
mkdir -p logs
mkdir -p drafts
mkdir -p templates
mkdir -p screenshots

# 复制环境配置文件
if [ ! -f .env ]; then
    echo "⚙️ 创建环境配置文件..."
    cp .env.example .env
    echo "请编辑 .env 文件并填入您的 API 密钥"
fi

# 设置 Git hooks（如果是 Git 仓库）
if [ -d .git ]; then
    echo "🔧 设置 Git hooks..."
    uv run pre-commit install
fi

echo "🎉 DramaCraft 项目设置完成！"
echo ""
echo "下一步："
echo "1. 编辑 .env 文件，填入您的大模型 API 密钥"
echo "2. 运行 'uv run dramacraft --help' 查看可用命令"
echo "3. 运行 'uv run dramacraft start' 启动 MCP 服务"
echo ""
echo "MCP 配置文件位置："
echo "- Cursor: configs/cursor_mcp.json"
echo "- Claude Desktop: configs/claude_desktop_config.json"
echo "- VS Code: configs/vscode_mcp.json"
