# 🐳 深度搜索代理 Docker 部署指南

这是一个基于知识图谱的深度搜索代理系统，支持多模态文档处理和智能问答。

## 📋 目录

- [系统要求](#系统要求)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [服务说明](#服务说明)
- [常用命令](#常用命令)
- [故障排除](#故障排除)
- [生产部署](#生产部署)

## 🔧 系统要求

- Docker >= 20.10
- Docker Compose >= 2.0
- 至少 4GB RAM
- 至少 10GB 可用磁盘空间

## 🚀 快速开始

### 1. 克隆项目
```bash
git clone <repository-url>
cd deep-search-agent
```

### 2. 配置环境变量
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件（必须设置 OPENAI_API_KEY）
nano .env
```

### 3. 启动服务
```bash
# 使用启动脚本（推荐）
./docker/scripts/start.sh start full

# 或者使用 docker-compose
docker-compose up -d
```

### 4. 访问应用
- 🌐 **前端界面**: http://localhost:8501
- 📖 **API 文档**: http://localhost:8000/docs
- 🔧 **Neo4j 浏览器**: http://localhost:7474 (neo4j/12345678)

## ⚙️ 配置说明

### 环境变量配置 (.env)

#### 必需配置
```bash
# OpenAI API 配置
OPENAI_API_KEY=your_actual_api_key_here
OPENAI_BASE_URL=http://localhost:13000/v1  # 或 https://api.openai.com/v1
```

#### 可选配置
```bash
# 模型配置
OPENAI_LLM_MODEL=gpt-4o
OPENAI_EMBEDDINGS_MODEL=text-embedding-3-large
TEMPERATURE=0
MAX_TOKENS=2000

# 应用配置
DEBUG=false
LOG_LEVEL=INFO
WORKERS=1

# 搜索配置
SEARCH_TOP_K=10
SIMILARITY_THRESHOLD=0.8
```

### Docker Compose 配置

主要服务包括：

1. **neo4j** - 图数据库
2. **backend** - FastAPI 后端服务
3. **frontend** - Streamlit 前端界面
4. **redis** - 缓存服务（可选）
5. **nginx** - 反向代理（生产环境）

## 🏗️ 服务说明

### 开发环境启动模式

```bash
# 仅启动基础服务（Neo4j + Redis）
./docker/scripts/start.sh start dev

# 启动完整环境
./docker/scripts/start.sh start full

# 启动生产环境（包含 Nginx）
./docker/scripts/start.sh start prod
```

### 服务依赖关系

```
neo4j → backend → frontend
  ↓
redis (可选缓存)
```

## 📋 常用命令

### 服务管理
```bash
# 启动服务
./docker/scripts/start.sh start [mode]

# 停止服务
./docker/scripts/start.sh stop

# 重启服务
./docker/scripts/start.sh restart [mode]

# 查看状态
./docker/scripts/start.sh status

# 查看日志
./docker/scripts/start.sh logs [service_name]
```

### Docker Compose 命令
```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f [service_name]

# 停止所有服务
docker-compose down

# 重建镜像
docker-compose build --no-cache

# 清理资源
docker-compose down -v --remove-orphans
```

### 数据管理
```bash
# 备份 Neo4j 数据
docker exec deep-search-neo4j neo4j-admin database backup neo4j --to-path=/backup

# 查看 Redis 数据
docker exec -it deep-search-redis redis-cli

# 进入容器
docker exec -it deep-search-backend bash
```

## 🔍 故障排除

### 常见问题

#### 1. Neo4j 启动失败
```bash
# 检查内存配置
docker-compose logs neo4j

# 重置 Neo4j 数据
docker-compose down -v
docker-compose up -d neo4j
```

#### 2. OpenAI API 连接失败
```bash
# 检查 API 密钥
docker-compose logs backend | grep -i "openai"

# 测试网络连接
docker exec deep-search-backend curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
```

#### 3. 前端无法连接后端
```bash
# 检查网络配置
docker network ls
docker network inspect deep-search-agent_deep-search-network

# 检查端口映射
docker-compose port backend 8000
```

#### 4. 性能问题
```bash
# 查看资源使用
docker stats

# 调整内存配置
# 编辑 docker-compose.yaml 中的内存限制
```

### 调试模式

启用调试模式：
```bash
# 编辑 .env
DEBUG=true
LOG_LEVEL=DEBUG

# 重启服务
./docker/scripts/start.sh restart
```

查看详细日志：
```bash
# 实时查看所有日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
```

## 🏭 生产部署

### 安全配置

1. **更改默认密码**
```bash
# 生成强密码
openssl rand -base64 32

# 更新 .env 和 docker-compose.yaml
```

2. **启用 HTTPS**
```bash
# 使用 Nginx 反向代理
./docker/scripts/start.sh start prod

# 配置 SSL 证书（在 docker/nginx/ 目录下）
```

3. **网络安全**
```bash
# 仅暴露必要端口
# 配置防火墙规则
```

### 性能优化

1. **资源配置**
```yaml
# 在 docker-compose.yaml 中调整资源限制
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2'
        reservations:
          memory: 2G
          cpus: '1'
```

2. **缓存配置**
```bash
# 启用 Redis 缓存
REDIS_URL=redis://redis:6379/0
ENABLE_CACHE=true
```

3. **数据库优化**
```bash
# 调整 Neo4j 内存配置
NEO4J_dbms_memory_heap_max__size: "4G"
NEO4J_dbms_memory_pagecache_size: "2G"
```

### 监控配置

1. **健康检查**
```bash
# 检查所有服务状态
curl http://localhost:8000/health
curl http://localhost:8501/_stcore/health
```

2. **日志管理**
```bash
# 配置日志轮转
# 在 docker-compose.yaml 中添加日志配置
```

## 📚 更多信息

- [API 文档](http://localhost:8000/docs)
- [Neo4j 文档](https://neo4j.com/docs/)
- [Streamlit 文档](https://docs.streamlit.io/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)

## 🆘 获取帮助

如果遇到问题：

1. 查看日志：`./docker/scripts/start.sh logs`
2. 检查配置：确保 `.env` 文件配置正确
3. 验证依赖：确保 Docker 和 Docker Compose 版本正确
4. 重置环境：`./docker/scripts/start.sh cleanup`

---

**注意**: 这是一个开发环境配置。生产部署请参考 [生产部署](#生产部署) 部分进行安全配置。