#!/bin/bash

# ==============================================
# 深度搜索代理 Docker 启动脚本
# ==============================================

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

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Docker和Docker Compose
check_prerequisites() {
    log_info "检查系统依赖..."

    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi

    log_success "系统依赖检查通过"
}

# 检查环境变量文件
check_env_file() {
    log_info "检查环境变量配置..."

    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            log_warning "未找到 .env 文件，正在从 .env.example 创建..."
            cp .env.example .env
            log_warning "请编辑 .env 文件设置正确的配置值"
        else
            log_error "未找到 .env 或 .env.example 文件"
            exit 1
        fi
    fi

    log_success "环境变量配置检查通过"
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."

    mkdir -p data logs cache
    mkdir -p docker/nginx/conf.d

    log_success "目录创建完成"
}

# 构建和启动服务
start_services() {
    local mode=${1:-"dev"}

    log_info "启动 Docker 服务 (模式: $mode)..."

    case $mode in
        "dev"|"development")
            log_info "启动开发环境..."
            docker-compose up -d neo4j redis
            ;;
        "full"|"complete")
            log_info "启动完整环境..."
            docker-compose up -d
            ;;
        "prod"|"production")
            log_info "启动生产环境..."
            docker-compose --profile production up -d
            ;;
        *)
            log_error "未知模式: $mode，支持的模式: dev, full, prod"
            exit 1
            ;;
    esac

    log_success "服务启动完成"
}

# 等待服务就绪
wait_for_services() {
    log_info "等待服务启动..."

    # 等待 Neo4j
    log_info "等待 Neo4j 启动..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if curl -f http://localhost:7474 &>/dev/null; then
            log_success "Neo4j 已启动"
            break
        fi
        sleep 2
        timeout=$((timeout-2))
    done

    if [ $timeout -le 0 ]; then
        log_error "Neo4j 启动超时"
        exit 1
    fi

    # 等待后端服务
    log_info "等待后端服务启动..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if curl -f http://localhost:8000/health &>/dev/null; then
            log_success "后端服务已启动"
            break
        fi
        sleep 2
        timeout=$((timeout-2))
    done

    if [ $timeout -le 0 ]; then
        log_warning "后端服务启动超时，请检查日志"
    fi

    # 等待前端服务
    log_info "等待前端服务启动..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if curl -f http://localhost:8501/_stcore/health &>/dev/null; then
            log_success "前端服务已启动"
            break
        fi
        sleep 2
        timeout=$((timeout-2))
    done

    if [ $timeout -le 0 ]; then
        log_warning "前端服务启动超时，请检查日志"
    fi
}

# 显示服务状态
show_status() {
    log_info "服务状态:"
    echo
    docker-compose ps
    echo
    log_info "服务访问地址:"
    echo "  🌐 Neo4j 浏览器: http://localhost:7474"
    echo "  🔧 Neo4j Bolt: bolt://localhost:7687"
    echo "  📡 后端 API: http://localhost:8000"
    echo "  📖 API 文档: http://localhost:8000/docs"
    echo "  🖥️ 前端界面: http://localhost:8501"
    echo "  🔴 Redis: localhost:6379"
    echo
}

# 显示日志
show_logs() {
    local service=${1:-""}

    if [ -n "$service" ]; then
        docker-compose logs -f "$service"
    else
        docker-compose logs -f
    fi
}

# 停止服务
stop_services() {
    log_info "停止所有服务..."
    docker-compose down
    log_success "服务已停止"
}

# 清理系统
cleanup() {
    log_info "清理 Docker 资源..."

    read -p "确认删除所有容器、网络和卷？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down -v --remove-orphans
        docker system prune -f
        log_success "清理完成"
    else
        log_info "清理已取消"
    fi
}

# 重启服务
restart_services() {
    local mode=${1:-"dev"}

    log_info "重启服务..."
    stop_services
    start_services "$mode"
    wait_for_services
    show_status
}

# 显示帮助信息
show_help() {
    echo "深度搜索代理 Docker 启动脚本"
    echo
    echo "用法: $0 [命令] [选项]"
    echo
    echo "命令:"
    echo "  start [mode]     启动服务 (模式: dev, full, prod，默认: dev)"
    echo "  stop             停止所有服务"
    echo "  restart [mode]   重启服务"
    echo "  status           显示服务状态"
    echo "  logs [service]   显示日志 (可指定服务名)"
    echo "  cleanup          清理所有 Docker 资源"
    echo "  help             显示此帮助信息"
    echo
    echo "示例:"
    echo "  $0 start dev     # 启动开发环境 (仅 Neo4j + Redis)"
    echo "  $0 start full    # 启动完整环境"
    echo "  $0 logs neo4j    # 查看 Neo4j 日志"
    echo "  $0 restart prod  # 重启生产环境"
    echo
}

# 主函数
main() {
    case ${1:-"start"} in
        "start")
            check_prerequisites
            check_env_file
            create_directories
            start_services "${2:-dev}"
            wait_for_services
            show_status
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            check_prerequisites
            restart_services "${2:-dev}"
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs "$2"
            ;;
        "cleanup")
            cleanup
            ;;
        "help"|"-h"|"--help")
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