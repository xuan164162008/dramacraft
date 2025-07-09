# DramaCraft Docker Image
# 基于官方Python镜像构建的专业短剧视频编辑MCP服务

FROM python:3.11-slim as base

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    # 基础工具
    curl \
    wget \
    git \
    # 视频处理依赖
    ffmpeg \
    libopencv-dev \
    # Python构建依赖
    build-essential \
    python3-dev \
    # 清理缓存
    && rm -rf /var/lib/apt/lists/*

# 安装uv
RUN pip install uv

# 创建应用用户
RUN useradd --create-home --shell /bin/bash dramacraft
USER dramacraft
WORKDIR /home/dramacraft

# 复制项目文件
COPY --chown=dramacraft:dramacraft pyproject.toml uv.lock ./
COPY --chown=dramacraft:dramacraft src/ ./src/
COPY --chown=dramacraft:dramacraft README.md LICENSE ./

# 安装Python依赖
RUN uv sync --frozen

# 创建必要的目录
RUN mkdir -p logs output temp assets/music configs

# 复制配置文件
COPY --chown=dramacraft:dramacraft configs/ ./configs/
COPY --chown=dramacraft:dramacraft .env.example ./.env

# 设置权限
RUN chmod +x ./src/dramacraft/cli.py

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD uv run python -c "import dramacraft; print('OK')" || exit 1

# 暴露端口（MCP服务通常使用stdio，但可能需要HTTP端口）
EXPOSE 8000

# 设置工作目录
WORKDIR /home/dramacraft

# 启动命令
CMD ["uv", "run", "dramacraft", "start"]

# 多阶段构建 - 开发版本
FROM base as development

USER root

# 安装开发依赖
RUN apt-get update && apt-get install -y \
    vim \
    htop \
    && rm -rf /var/lib/apt/lists/*

USER dramacraft

# 安装开发依赖
RUN uv sync --all-extras

# 开发模式启动
CMD ["uv", "run", "dramacraft", "start", "--debug"]

# 多阶段构建 - 生产版本
FROM base as production

# 优化生产环境
ENV PYTHONOPTIMIZE=1

# 只安装生产依赖
RUN uv sync --no-dev

# 生产模式启动
CMD ["uv", "run", "dramacraft", "start", "--production"]

# 默认使用生产版本
FROM production
