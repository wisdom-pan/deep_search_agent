FROM m.daocloud.io/docker.io/library/python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONPATH=/app

# 安装构建工具和系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    curl \
    libxml2-dev \
    libxslt1-dev \
    antiword \
    unrtf \
    poppler-utils \
    wget \
    && rm -rf /var/lib/apt/lists/*

# 升级pip并配置国内源
RUN pip config set global.index-url https://mirrors.cloud.tencent.com/pypi/simple/ && \
    pip install --no-cache-dir --upgrade pip setuptools wheel


COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.cloud.tencent.com/pypi/simple/

# 复制其余应用代码
COPY . /app/
# 创建必要的目录
RUN mkdir -p /app/data /app/logs /app/cache

# 设置权限
RUN chmod +x /app/docker/docker-entrypoint.sh 2>/dev/null || echo "entrypoint script not found, will create later"

# 暴露端口
EXPOSE 8000 8501

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 设置默认用户
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# 默认启动命令
CMD ["/app/docker/docker-entrypoint.sh"]