#!/bin/bash

# DramaCraft 部署脚本
# 用于生产环境部署和配置

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查系统要求
check_requirements() {
    log_info "检查系统要求..."
    
    # 检查Python版本
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 未安装"
        exit 1
    fi
    
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if [[ $(echo "$python_version < 3.9" | bc -l) -eq 1 ]]; then
        log_error "需要 Python 3.9 或更高版本，当前版本: $python_version"
        exit 1
    fi
    
    # 检查uv
    if ! command -v uv &> /dev/null; then
        log_warning "uv 未安装，正在安装..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        source $HOME/.cargo/env
    fi
    
    # 检查系统依赖
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if ! command -v brew &> /dev/null; then
            log_warning "Homebrew 未安装，建议安装以管理系统依赖"
        fi
        
        # 检查ffmpeg
        if ! command -v ffmpeg &> /dev/null; then
            log_warning "ffmpeg 未安装，正在通过 Homebrew 安装..."
            brew install ffmpeg
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v apt-get &> /dev/null; then
            # Ubuntu/Debian
            sudo apt-get update
            sudo apt-get install -y ffmpeg libopencv-dev python3-dev
        elif command -v yum &> /dev/null; then
            # CentOS/RHEL
            sudo yum install -y ffmpeg opencv-devel python3-devel
        fi
    fi
    
    log_success "系统要求检查完成"
}

# 创建项目目录结构
setup_directories() {
    log_info "创建项目目录结构..."
    
    # 创建必要的目录
    mkdir -p logs
    mkdir -p output
    mkdir -p temp
    mkdir -p assets/music
    mkdir -p configs
    mkdir -p docs/website/assets/{css,js,images}
    
    # 设置权限
    chmod 755 logs output temp
    chmod 644 configs/*.json 2>/dev/null || true
    
    log_success "目录结构创建完成"
}

# 安装依赖
install_dependencies() {
    log_info "安装项目依赖..."
    
    # 使用uv安装依赖
    uv sync --all-extras
    
    # 验证安装
    if uv run python -c "import dramacraft; print('DramaCraft 导入成功')"; then
        log_success "依赖安装完成"
    else
        log_error "依赖安装失败"
        exit 1
    fi
}

# 配置环境
configure_environment() {
    log_info "配置环境..."
    
    # 创建环境配置文件
    if [[ ! -f .env ]]; then
        cp .env.example .env
        log_warning "请编辑 .env 文件配置您的 API 密钥"
    fi
    
    # 创建MCP配置文件
    cat > configs/cursor_mcp.json << EOF
{
  "mcpServers": {
    "DramaCraft": {
      "command": "uv",
      "args": ["run", "dramacraft", "start"],
      "env": {
        "LLM__PROVIDER": "baidu",
        "LLM__API_KEY": "\${BAIDU_API_KEY}",
        "LLM__SECRET_KEY": "\${BAIDU_SECRET_KEY}"
      }
    }
  }
}
EOF
    
    cat > configs/claude_desktop_config.json << EOF
{
  "mcpServers": {
    "DramaCraft": {
      "command": "uv",
      "args": ["run", "dramacraft", "start"],
      "env": {
        "LLM__PROVIDER": "baidu",
        "LLM__API_KEY": "\${BAIDU_API_KEY}",
        "LLM__SECRET_KEY": "\${BAIDU_SECRET_KEY}"
      }
    }
  }
}
EOF
    
    log_success "环境配置完成"
}

# 运行测试
run_tests() {
    log_info "运行测试套件..."
    
    # 运行单元测试
    if uv run pytest tests/ -v --tb=short; then
        log_success "所有测试通过"
    else
        log_warning "部分测试失败，请检查日志"
    fi
}

# 启动服务
start_service() {
    log_info "启动 DramaCraft MCP 服务..."
    
    # 检查配置
    if uv run dramacraft config --validate; then
        log_success "配置验证通过"
    else
        log_error "配置验证失败"
        exit 1
    fi
    
    # 启动服务
    log_info "服务启动中..."
    log_info "请在您的 AI 编辑器中配置 MCP 服务"
    log_info "配置文件位置："
    log_info "  - Cursor: configs/cursor_mcp.json"
    log_info "  - Claude Desktop: configs/claude_desktop_config.json"
    
    # 后台启动服务
    nohup uv run dramacraft start > logs/service.log 2>&1 &
    echo $! > .service.pid
    
    sleep 3
    
    if ps -p $(cat .service.pid) > /dev/null; then
        log_success "服务启动成功 (PID: $(cat .service.pid))"
        log_info "日志文件: logs/service.log"
    else
        log_error "服务启动失败"
        exit 1
    fi
}

# 停止服务
stop_service() {
    log_info "停止 DramaCraft 服务..."
    
    if [[ -f .service.pid ]]; then
        pid=$(cat .service.pid)
        if ps -p $pid > /dev/null; then
            kill $pid
            sleep 2
            if ps -p $pid > /dev/null; then
                kill -9 $pid
            fi
            rm .service.pid
            log_success "服务已停止"
        else
            log_warning "服务进程不存在"
            rm .service.pid
        fi
    else
        log_warning "未找到服务PID文件"
    fi
}

# 重启服务
restart_service() {
    stop_service
    sleep 2
    start_service
}

# 查看服务状态
status_service() {
    if [[ -f .service.pid ]]; then
        pid=$(cat .service.pid)
        if ps -p $pid > /dev/null; then
            log_success "服务运行中 (PID: $pid)"
            
            # 显示资源使用情况
            if command -v ps &> /dev/null; then
                echo "资源使用情况:"
                ps -p $pid -o pid,ppid,pcpu,pmem,etime,cmd
            fi
        else
            log_warning "服务进程不存在"
        fi
    else
        log_warning "服务未启动"
    fi
}

# 查看日志
view_logs() {
    if [[ -f logs/service.log ]]; then
        tail -f logs/service.log
    else
        log_warning "日志文件不存在"
    fi
}

# 清理
cleanup() {
    log_info "清理临时文件..."
    
    # 清理临时文件
    rm -rf temp/*
    rm -rf output/*.tmp
    
    # 清理旧日志
    find logs/ -name "*.log" -mtime +7 -delete 2>/dev/null || true
    
    log_success "清理完成"
}

# 更新
update() {
    log_info "更新 DramaCraft..."
    
    # 停止服务
    stop_service
    
    # 拉取最新代码
    git pull origin main
    
    # 更新依赖
    uv sync --all-extras
    
    # 重启服务
    start_service
    
    log_success "更新完成"
}

# 卸载
uninstall() {
    log_warning "这将完全卸载 DramaCraft"
    read -p "确认继续? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        stop_service
        
        # 删除虚拟环境
        uv clean
        
        # 删除配置文件
        rm -f .env
        rm -rf configs/
        
        # 删除日志
        rm -rf logs/
        
        log_success "卸载完成"
    else
        log_info "取消卸载"
    fi
}

# 显示帮助
show_help() {
    echo "DramaCraft 部署脚本"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  install     完整安装和配置"
    echo "  start       启动服务"
    echo "  stop        停止服务"
    echo "  restart     重启服务"
    echo "  status      查看服务状态"
    echo "  logs        查看服务日志"
    echo "  test        运行测试"
    echo "  cleanup     清理临时文件"
    echo "  update      更新到最新版本"
    echo "  uninstall   卸载服务"
    echo "  help        显示此帮助"
    echo ""
}

# 主函数
main() {
    case "${1:-help}" in
        install)
            check_requirements
            setup_directories
            install_dependencies
            configure_environment
            run_tests
            log_success "DramaCraft 安装完成！"
            log_info "运行 '$0 start' 启动服务"
            ;;
        start)
            start_service
            ;;
        stop)
            stop_service
            ;;
        restart)
            restart_service
            ;;
        status)
            status_service
            ;;
        logs)
            view_logs
            ;;
        test)
            run_tests
            ;;
        cleanup)
            cleanup
            ;;
        update)
            update
            ;;
        uninstall)
            uninstall
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
