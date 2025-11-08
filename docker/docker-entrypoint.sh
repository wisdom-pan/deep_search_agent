#!/bin/bash

# ==============================================
# 深度搜索代理 Docker 入口脚本
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

# 等待依赖服务
wait_for_dependencies() {
    log_info "等待依赖服务启动..."

    # 等待 Neo4j
    if [ -n "$NEO4J_URI" ]; then
        log_info "等待 Neo4j ($NEO4J_URI)..."
        timeout=60
        while [ $timeout -gt 0 ]; do
            if python -c "
import os
try:
    from neo4j import GraphDatabase
    driver = GraphDatabase.driver('$NEO4J_URI', auth=('$NEO4J_USER', '$NEO4J_PASSWORD'))
    driver.verify_connectivity()
    driver.close()
    print('Neo4j connected successfully')
except Exception as e:
    print(f'Neo4j connection failed: {e}')
    exit(1)
" 2>/dev/null; then
                log_success "Neo4j 连接成功"
                break
            fi
            sleep 2
            timeout=$((timeout-2))
        done

        if [ $timeout -le 0 ]; then
            log_error "Neo4j 连接超时"
            exit 1
        fi
    fi

    # 等待 Redis
    if [ -n "$REDIS_URL" ]; then
        log_info "等待 Redis ($REDIS_URL)..."
        timeout=30
        while [ $timeout -gt 0 ]; do
            if python -c "
import redis
try:
    r = redis.from_url('$REDIS_URL')
    r.ping()
    print('Redis connected successfully')
except Exception as e:
    print(f'Redis connection failed: {e}')
    exit(1)
" 2>/dev/null; then
                log_success "Redis 连接成功"
                break
            fi
            sleep 2
            timeout=$((timeout-2))
        done

        if [ $timeout -le 0 ]; then
            log_warning "Redis 连接超时，将继续启动"
        fi
    fi

    log_success "依赖服务检查完成"
}

# 初始化应用
init_application() {
    log_info "初始化应用..."

    # 创建必要的目录
    mkdir -p /app/data /app/logs /app/cache

    # 设置权限
    if [ "$(id -u)" -eq 0 ]; then
        chown -R appuser:appuser /app
    fi

    # 检查配置文件
    if [ ! -f "/app/.env" ] && [ -f "/app/.env.example" ]; then
        log_warning "未找到 .env 文件，使用默认配置"
        cp /app/.env.example /app/.env
    fi

    log_success "应用初始化完成"
}

# 数据库迁移
run_migrations() {
    log_info "运行数据库迁移..."

    # 检查知识图谱是否已有数据
    existing_nodes=$(python -c "
from server.server_config.database import get_db_manager
try:
    db = get_db_manager()
    result = db.execute_query('MATCH (n) RETURN count(n) as count')
    count = result.iloc[0]['count'] if not result.empty else 0
    print(count)
except Exception as e:
    print('0')
" 2>/dev/null || echo "0")

    # 初始化知识图谱
    if [ "$existing_nodes" -gt 0 ]; then
        log_info "检测到现有知识图谱数据 ($existing_nodes 个节点)，跳过初始化"
        log_success "数据库迁移完成"
    else
        log_info "未检测到知识图谱数据，开始初始化..."
        if python init_kg.py; then
            log_success "知识图谱初始化完成"

            # 检查知识图谱数据
            node_count=$(python -c "
from server.server_config.database import get_db_manager
db = get_db_manager()
result = db.execute_query('MATCH (n) RETURN count(n) as count')
count = result.iloc[0]['count'] if not result.empty else 0
print(count)
" 2>/dev/null || echo "0")

            if [ "$node_count" -gt 0 ]; then
                log_success "知识图谱数据已就绪，共有 $node_count 个节点"
            else
                log_warning "知识图谱数据为空，问答功能可能受限"
            fi
        else
            log_error "知识图谱初始化失败"
        fi

        log_success "数据库迁移完成"
    fi
}

# 健康检查
health_check() {
    log_info "执行健康检查..."

    # 检查 Python 环境
    python --version

    # 检查关键依赖
    python -c "
import sys
try:
    import fastapi
    import streamlit
    import neo4j
    print('关键依赖检查通过')
except ImportError as e:
    print(f'依赖缺失: {e}')
    sys.exit(1)
"

    log_success "健康检查完成"
}

# 启动应用
start_application() {
    log_info "启动应用..."

    case "${START_MODE:-backend}" in
        "backend")
            log_info "启动后端服务..."
            exec python -m uvicorn server.main:app \
                --host "${BACKEND_HOST:-0.0.0.0}" \
                --port "${BACKEND_PORT:-8000}" \
                --workers "${WORKERS:-1}"
            ;;
        "frontend")
            log_info "启动前端服务..."
            exec streamlit run frontend/app.py \
                --server.port "${FRONTEND_PORT:-8501}" \
                --server.address "${FRONTEND_HOST:-0.0.0.0}" \
                --server.headless true
            ;;
        "both"|"all")
            log_info "启动所有服务..."
            # 这里可以使用 supervisor 或其他进程管理器
            # 暂时只启动后端
            exec python -m uvicorn server.main:app \
                --host "${BACKEND_HOST:-0.0.0.0}" \
                --port "${BACKEND_PORT:-8000}" \
                --workers "${WORKERS:-1}"
            ;;
        *)
            log_error "未知启动模式: $START_MODE"
            exit 1
            ;;
    esac
}

# 清理函数
cleanup() {
    log_info "执行清理操作..."
    # 这里可以添加清理逻辑
}

# 信号处理
trap cleanup SIGTERM SIGINT

# 主函数
main() {
    log_info "深度搜索代理 Docker 容器启动中..."

    # 显示环境信息
    log_info "Python 版本: $(python --version)"
    log_info "工作目录: $(pwd)"
    log_info "启动模式: ${START_MODE:-backend}"

    # 执行初始化步骤
    init_application
    wait_for_dependencies
    health_check
    run_migrations

    # 启动应用
    start_application
}

# 执行主函数
main "$@"