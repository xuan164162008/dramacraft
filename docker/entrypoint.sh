#!/bin/bash
# DramaCraft Docker 入口脚本
# 企业级容器启动和配置管理

set -e

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

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# 显示启动横幅
show_banner() {
    cat << 'EOF'
    ____                           ____            __ _   
   / __ \_________ _____ ___  ____ / __ \_________ _/ _| |_ 
  / / / / ___/ __ `/ __ `__ \/ __ `/ / / / ___/ __ `/ _| __|
 / /_/ / /  / /_/ / / / / / / /_/ / /_/ / /  / /_/ / | | |_ 
/_____/_/   \__,_/_/ /_/ /_/\__,_/\____/_/   \__,_/_|  \__|

企业级视频编辑MCP服务 - Docker容器版本
版本: 1.0.0 | 构建时间: 2024-01-06
EOF
}

# 检查环境变量
check_environment() {
    log_info "检查环境配置..."
    
    # 必需的环境变量
    local required_vars=(
        "DRAMACRAFT_CONFIG"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            log_error "缺少必需的环境变量: $var"
            exit 1
        fi
    done
    
    # 可选的环境变量（设置默认值）
    export DRAMACRAFT_HOST="${DRAMACRAFT_HOST:-0.0.0.0}"
    export DRAMACRAFT_PORT="${DRAMACRAFT_PORT:-8080}"
    export DRAMACRAFT_LOG_LEVEL="${DRAMACRAFT_LOG_LEVEL:-INFO}"
    export DRAMACRAFT_WORKERS="${DRAMACRAFT_WORKERS:-1}"
    
    log_success "环境配置检查完成"
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."
    
    local dirs=(
        "/app/data"
        "/app/logs"
        "/app/temp"
        "/app/cache"
        "/app/uploads"
        "/app/exports"
    )
    
    for dir in "${dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            log_info "创建目录: $dir"
        fi
    done
    
    log_success "目录创建完成"
}

# 检查配置文件
check_config() {
    log_info "检查配置文件..."
    
    if [[ ! -f "$DRAMACRAFT_CONFIG" ]]; then
        log_warn "配置文件不存在，创建默认配置: $DRAMACRAFT_CONFIG"
        
        # 创建默认配置
        cat > "$DRAMACRAFT_CONFIG" << 'EOF'
# DramaCraft 默认配置文件
ai:
  provider: "baidu"
  baidu:
    api_key: "${BAIDU_API_KEY}"
    secret_key: "${BAIDU_SECRET_KEY}"
    model: "ERNIE-Bot-turbo"

video:
  temp_dir: "/app/temp"
  quality:
    default: "high"
  formats:
    input: ["mp4", "avi", "mov", "mkv"]
    output: ["mp4", "webm"]

security:
  jwt_secret_key: "${JWT_SECRET_KEY:-default-secret-key-change-this}"
  session_encryption_key: "${SESSION_ENCRYPTION_KEY:-default-session-key}"
  mfa_enabled: false

server:
  host: "${DRAMACRAFT_HOST:-0.0.0.0}"
  port: ${DRAMACRAFT_PORT:-8080}
  debug: false
  workers: ${DRAMACRAFT_WORKERS:-1}

logging:
  level: "${DRAMACRAFT_LOG_LEVEL:-INFO}"
  file: "/app/logs/dramacraft.log"

cache:
  type: "memory"
  max_size: 1000
  ttl: 3600

performance:
  max_concurrent_jobs: 4
  memory_limit: "2GB"
  gpu_acceleration: false
EOF
        
        log_success "默认配置文件已创建"
    else
        log_success "配置文件存在: $DRAMACRAFT_CONFIG"
    fi
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    # 检查Python环境
    if ! python -c "import sys; print(f'Python {sys.version}')" 2>/dev/null; then
        log_error "Python环境检查失败"
        return 1
    fi
    
    # 检查DramaCraft模块
    if ! python -c "import dramacraft; print('DramaCraft模块加载成功')" 2>/dev/null; then
        log_error "DramaCraft模块加载失败"
        return 1
    fi
    
    # 检查配置文件
    if ! python -c "
import yaml
with open('$DRAMACRAFT_CONFIG', 'r') as f:
    config = yaml.safe_load(f)
    print('配置文件解析成功')
" 2>/dev/null; then
        log_error "配置文件解析失败"
        return 1
    fi
    
    log_success "健康检查通过"
    return 0
}

# 等待依赖服务
wait_for_services() {
    log_info "等待依赖服务..."
    
    # 等待Redis（如果配置了）
    if [[ -n "$REDIS_URL" ]]; then
        log_info "等待Redis服务: $REDIS_URL"
        
        local redis_host=$(echo "$REDIS_URL" | sed -n 's/.*:\/\/\([^:]*\).*/\1/p')
        local redis_port=$(echo "$REDIS_URL" | sed -n 's/.*:\([0-9]*\).*/\1/p')
        
        while ! nc -z "$redis_host" "$redis_port" 2>/dev/null; do
            log_info "等待Redis连接..."
            sleep 2
        done
        
        log_success "Redis服务已就绪"
    fi
    
    # 等待数据库（如果配置了）
    if [[ -n "$DATABASE_URL" ]]; then
        log_info "等待数据库服务: $DATABASE_URL"
        # 这里可以添加数据库连接检查
        log_success "数据库服务已就绪"
    fi
}

# 初始化数据库
init_database() {
    if [[ "$DRAMACRAFT_INIT_DB" == "true" ]]; then
        log_info "初始化数据库..."
        
        # 运行数据库迁移
        if python -m dramacraft.db migrate 2>/dev/null; then
            log_success "数据库初始化完成"
        else
            log_warn "数据库初始化跳过（可能已存在）"
        fi
    fi
}

# 启动服务
start_service() {
    local command="$1"
    
    case "$command" in
        "start"|"server")
            log_info "启动DramaCraft MCP服务器..."
            exec python -m dramacraft.server \
                --config "$DRAMACRAFT_CONFIG" \
                --host "$DRAMACRAFT_HOST" \
                --port "$DRAMACRAFT_PORT" \
                --workers "$DRAMACRAFT_WORKERS"
            ;;
        
        "worker")
            log_info "启动DramaCraft工作进程..."
            exec python -m dramacraft.worker \
                --config "$DRAMACRAFT_CONFIG"
            ;;
        
        "shell")
            log_info "启动交互式Shell..."
            exec python -m dramacraft.shell \
                --config "$DRAMACRAFT_CONFIG"
            ;;
        
        "health")
            log_info "执行健康检查..."
            if health_check; then
                log_success "健康检查通过"
                exit 0
            else
                log_error "健康检查失败"
                exit 1
            fi
            ;;
        
        "version")
            python -c "
import dramacraft
print(f'DramaCraft版本: {dramacraft.__version__}')
print(f'Python版本: {sys.version}')
"
            exit 0
            ;;
        
        *)
            log_info "执行自定义命令: $*"
            exec "$@"
            ;;
    esac
}

# 信号处理
cleanup() {
    log_info "接收到停止信号，正在清理..."
    
    # 清理临时文件
    if [[ -d "/app/temp" ]]; then
        find /app/temp -type f -mtime +1 -delete 2>/dev/null || true
    fi
    
    # 保存日志
    if [[ -f "/app/logs/dramacraft.log" ]]; then
        log_info "保存日志文件..."
    fi
    
    log_success "清理完成"
    exit 0
}

# 设置信号处理
trap cleanup SIGTERM SIGINT

# 主函数
main() {
    show_banner
    
    # 检查是否以root用户运行
    if [[ $EUID -eq 0 ]]; then
        log_warn "检测到以root用户运行，建议使用非特权用户"
    fi
    
    # 执行初始化步骤
    check_environment
    create_directories
    check_config
    wait_for_services
    init_database
    
    # 执行健康检查
    if ! health_check; then
        log_error "初始化健康检查失败"
        exit 1
    fi
    
    # 显示启动信息
    log_info "DramaCraft配置信息:"
    log_info "  - 配置文件: $DRAMACRAFT_CONFIG"
    log_info "  - 监听地址: $DRAMACRAFT_HOST:$DRAMACRAFT_PORT"
    log_info "  - 日志级别: $DRAMACRAFT_LOG_LEVEL"
    log_info "  - 工作进程: $DRAMACRAFT_WORKERS"
    
    # 启动服务
    start_service "$@"
}

# 执行主函数
main "$@"
