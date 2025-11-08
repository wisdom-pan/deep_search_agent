#!/bin/bash

# GraphRAG Agent Docker 启动脚本
# 使用方法: ./docker-start.sh [start|stop|restart|logs|status]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 功能函数
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 Docker 和 Docker Compose
check_dependencies() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
}

# 检查 .env 文件
check_env() {
    if [ ! -f .env ]; then
        print_warning ".env 文件不存在，将使用 .env.example 模板"
        if [ -f .env.example ]; then
            cp .env.example .env
            print_info "已复制 .env.example 到 .env"
            print_warning "请编辑 .env 文件，配置您的 API 密钥"
        else
            print_error ".env.example 文件不存在"
            exit 1
        fi
    fi

    # 检查必要的环境变量
    source .env
    if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" == "sk-xxx" ]; then
        print_warning "请在 .env 文件中配置 OPENAI_API_KEY"
    fi
}

# 检查文件目录
check_directories() {
    print_info "检查必要的目录结构..."

    # 确保 files 目录存在（用于存放待处理文档）
    if [ ! -d "files" ]; then
        mkdir -p files
        print_info "创建 files 目录"
        print_info "请将需要处理的文档放入 files 目录"
    fi

    # 确保 config 目录存在
    if [ ! -d "graphrag_agent/config" ]; then
        print_error "graphrag_agent/config 目录不存在"
        exit 1
    fi
}

# 启动服务
start_services() {
    print_info "启动 GraphRAG Agent 服务..."
    docker-compose up -d

    print_info "等待服务启动..."
    sleep 10

    # 显示服务状态
    show_status
}

# 停止服务
stop_services() {
    print_info "停止 GraphRAG Agent 服务..."
    docker-compose down
    print_success "所有服务已停止"
}

# 重启服务
restart_services() {
    print_info "重启 GraphRAG Agent 服务..."
    docker-compose restart
    print_success "服务已重启"
    show_status
}

# 显示日志
show_logs() {
    docker-compose logs -f
}

# 显示状态
show_status() {
    print_info "服务状态:"
    docker-compose ps

    echo ""
    print_info "访问地址:"
    echo "  - Neo4j Web UI: http://localhost:7474 (用户名: neo4j, 密码: 12345678)"
    echo "  - GraphRAG API: http://localhost:8000/docs"
    echo "  - Streamlit 前端: http://localhost:8501"
    echo "  - One-API 管理: http://localhost:13000 (如果使用)"

    echo ""
    print_info "初始化状态:"
    if docker-compose ps | grep -q "graphrag-init-kg.*Up"; then
        print_info "知识图谱初始化正在运行..."
    elif docker-compose ps | grep -q "graphrag-init-kg.*Exited"; then
        print_success "知识图谱初始化已完成"
    else
        print_info "知识图谱初始化待执行"
    fi
}

# 清理数据
clean_data() {
    print_warning "这将删除所有数据包括 Neo4j 数据库和缓存！"
    read -p "确认继续? (y/N): " confirm
    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        print_info "清理数据..."
        docker-compose down -v
        docker volume prune -f
        print_success "数据已清理"
    else
        print_info "取消清理"
    fi
}

# 重建服务
rebuild_services() {
    print_info "重建 Docker 镜像..."
    docker-compose build --no-cache
    print_success "镜像重建完成"
    start_services
}

# 显示帮助
show_help() {
    echo "GraphRAG Agent Docker 管理脚本"
    echo ""
    echo "使用方法:"
    echo "  $0 start        - 启动所有服务"
    echo "  $0 stop         - 停止所有服务"
    echo "  $0 restart      - 重启所有服务"
    echo "  $0 logs         - 查看服务日志"
    echo "  $0 status       - 显示服务状态"
    echo "  $0 rebuild      - 重建镜像并启动"
    echo "  $0 clean        - 清理所有数据"
    echo "  $0 help         - 显示帮助信息"
    echo ""
}

# 主逻辑
main() {
    check_dependencies
    check_env
    check_directories

    case "$1" in
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        logs)
            show_logs
            ;;
        status)
            show_status
            ;;
        clean)
            clean_data
            ;;
        rebuild)
            rebuild_services
            ;;
        help|*)
            show_help
            ;;
    esac
}

# 执行主函数
main "$@"
