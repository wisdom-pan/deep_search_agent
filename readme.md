# GraphRAG Agent Docker 部署指南

## 概述

本 Docker Compose 配置提供完整的 GraphRAG Agent 部署方案，包括知识图谱初始化、API 服务和前端界面。

## 服务架构

```
┌─────────────────────────────────────────────────────────┐
│                    GraphRAG Agent                       │
├─────────────────────────────────────────────────────────┤
│  Frontend (Streamlit)          │  One-API (可选)        │
│  Port: 8501                    │  Port: 13000            │
├─────────────────────────────────────────────────────────┤
│  Backend (FastAPI)                                     │
│  Port: 8000                                            │
├─────────────────────────────────────────────────────────┤
│  Init-KG (知识图谱初始化)                              │
│  - 构建实体和关系                                      │
│  - 创建社区索引                                        │
│  - 生成向量索引                                        │
├─────────────────────────────────────────────────────────┤
│  Neo4j (图数据库)              │  缓存存储               │
│  Port: 7474, 7687              │  ./cache               │
└─────────────────────────────────────────────────────────┘
```

## 快速开始

### 1. 环境准备

确保已安装：
- Docker >= 20.10
- Docker Compose >= 1.29

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，配置必要的参数
vim .env
```

**必须配置的环境变量：**
```env
# OpenAI API 密钥（必须）
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# OpenAI 兼容服务地址（可选，默认使用 OpenAI）
OPENAI_BASE_URL=http://localhost:13000/v1

# Neo4j 配置
NEO4J_URI=neo4j://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=12345678
```

### 3. 准备文档

将需要处理的数据文件放入 `files/` 目录：

```bash
mkdir -p files
# 复制您的文档文件到 files/ 目录
cp your_documents/* files/
```

支持的文件格式：PDF, TXT, MD, DOCX, CSV, JSON, YAML

### 4. 启动服务

#### 使用启动脚本（推荐）

```bash
# 赋予执行权限
chmod +x docker-start.sh

# 启动所有服务
./docker-start.sh start

# 查看服务状态
./docker-start.sh status

# 查看日志
./docker-start.sh logs
```

#### 手动启动

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看初始化日志
docker-compose logs init-kg
```

### 5. 访问服务

启动后可以通过以下地址访问：

- **Neo4j Web UI**: http://localhost:7474
  - 用户名: `neo4j`
  - 密码: `12345678`

- **GraphRAG API 文档**: http://localhost:8000/docs
  - 包含所有 API 端点的交互式文档

- **Streamlit 前端**: http://localhost:8501
  - 图形化用户界面，支持知识图谱可视化

- **One-API 管理** (可选): http://localhost:13000
  - 用于管理 API 密钥和调用统计

## 服务详解

### Neo4j 图数据库

- **版本**: Neo4j 5.22.0
- **插件**: APOC, Graph Data Science (GDS)
- **内存配置**:
  - Heap: 4GB
  - Page Cache: 2GB
  - GDS: 6GB
- **数据持久化**: 使用 Docker 卷
  - `neo4j_data`: 存储数据库文件
  - `neo4j_logs`: 存储日志
  - `neo4j_plugins`: 存储插件

### 知识图谱初始化 (init-kg)

自动执行以下步骤：
1. 清除旧索引
2. 构建基础图谱（实体、关系提取）
3. 创建实体索引和社区检测
4. 构建文本块向量索引

**触发条件**:
- 只在第一次启动时运行
- 手动触发：`docker-compose run --rm init-kg`

### 后端 API (backend)

- **框架**: FastAPI
- **端口**: 8000
- **功能**: 提供所有 GraphRAG 查询 API
- **健康检查**: `/health` 端点

### 前端界面 (frontend)

- **框架**: Streamlit
- **端口**: 8501
- **功能**: 交互式查询、知识图谱可视化、调试面板

### One-API 代理 (可选)

- **用途**: API 密钥管理、调用统计
- **端口**: 13000
- **配置**: 在 One-API 中添加 OpenAI API Key 即可使用

## 管理命令

### 查看服务状态
```bash
./docker-start.sh status
# 或
docker-compose ps
```

### 查看日志
```bash
# 查看所有服务日志
./docker-start.sh logs

# 查看特定服务日志
docker-compose logs -f neo4j
docker-compose logs -f init-kg
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 重启服务
```bash
./docker-start.sh restart
# 或
docker-compose restart
```

### 停止服务
```bash
./docker-start.sh stop
# 或
docker-compose down
```

### 完全重置

```bash
# 停止并删除所有数据
./docker-start.sh clean
# 或手动执行
docker-compose down -v
docker volume prune -f
```

### 重新构建镜像

```bash
./docker-start.sh rebuild
# 或
docker-compose build --no-cache
docker-compose up -d
```

## 常见问题

### Q1: Neo4j 启动失败

**现象**: Neo4j 容器无法启动

**解决方案**:
```bash
# 检查端口是否被占用
netstat -tlnp | grep 7474

# 查看 Neo4j 日志
docker-compose logs neo4j

# 重新创建 Neo4j 卷
docker-compose down -v
docker volume prune -f
docker-compose up -d neo4j
```

### Q2: 知识图谱初始化失败

**现象**: init-kg 服务报错

**解决方案**:
1. 检查 OpenAI API Key 是否正确配置
2. 检查 files/ 目录是否有文档文件
3. 检查 Neo4j 是否完全启动
4. 查看详细日志:
   ```bash
   docker-compose logs init-kg
   ```

### Q3: 内存不足

**现象**: 容器因 OOM 被杀死

**解决方案**:
1. 增加系统内存
2. 调整 Docker 内存限制
3. 调整 Neo4j 内存配置（在 docker-compose.yaml 中修改 `NEO4J_dbms_memory_heap_max__size`）

### Q4: API 调用失败

**现象**: 前后端无法通信

**解决方案**:
1. 检查 backend 服务是否健康
   ```bash
   curl http://localhost:8000/health
   ```
2. 检查环境变量 `FRONTEND_API_URL` 是否正确
3. 查看前后端日志

### Q5: 重新初始化知识图谱

**方案**:
```bash
# 停止当前服务
docker-compose down

# 删除 Neo4j 数据（可选）
docker-compose down -v
docker volume prune -f

# 重新启动
docker-compose up -d
```

## 性能调优

### 内存配置

编辑 `docker-compose.yaml` 中的 Neo4j 环境变量：

```yaml
neo4j:
  environment:
    NEO4J_dbms_memory_heap_max__size: "8G"  # 根据系统内存调整
    NEO4J_dbms_memory_pagecache_size: "4G"
    NEO4J_dbms_memory_gds_early释放: "10G"
```

### 并发配置

在 `.env` 文件中调整：

```env
# 增加工作线程数
MAX_WORKERS=8

# 调整批处理大小
BATCH_SIZE=200
ENTITY_BATCH_SIZE=100
```

### 缓存优化

```env
# 启用向量相似度缓存
CACHE_ENABLE_VECTOR_SIMILARITY=true

# 调整缓存大小
CACHE_MAX_MEMORY_SIZE=200
CACHE_MAX_DISK_SIZE=5000
```

## 数据备份与恢复

### 备份 Neo4j 数据

```bash
# 备份数据卷
docker run --rm -v graphrag_neo4j_data:/data -v $(pwd):/backup alpine tar czf /backup/neo4j-backup.tar.gz /data
```

### 恢复 Neo4j 数据

```bash
# 停止服务
docker-compose down

# 恢复数据卷
docker run --rm -v graphrag_neo4j_data:/data -v $(pwd):/backup alpine tar xzf /backup/neo4j-backup.tar.gz -C /

# 重启服务
docker-compose up -d
```



### 重新构建镜像

```bash
# 只重新构建特定服务
docker-compose build backend

# 重新构建所有镜像
docker-compose build --no-cache
```

### 调试

```bash
# 进入容器
docker-compose exec backend bash

# 查看实时日志
docker-compose logs -f <service_name>

# 检查服务健康状态
docker-compose ps
```
