# Obsidian语义搜索Docker镜像
# 使用Python 3.14作为基础镜像

FROM python:3.14-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 创建数据目录
RUN mkdir -p /app/data /app/logs

# 创建配置目录和默认配置
RUN mkdir -p /app/config
COPY config/config.yaml /app/config/config.yaml

# 设置权限
RUN chmod +x /app/cli.py

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.path.append('/app/src'); from bge_m3_client import BGE_M3_Client; client = BGE_M3_Client(base_url='http://localhost:1234'); print(client.test_connection())" || exit 1

# 默认命令
CMD ["python", "cli.py", "test"]