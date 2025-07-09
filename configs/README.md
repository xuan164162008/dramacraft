# ⚙️ DramaCraft 配置指南

本目录包含 DramaCraft 项目的所有配置文件和模板，用于不同环境和AI编辑器的集成配置。

## 📁 配置文件结构

```
configs/
├── README.md                    # 本配置指南
├── mcp/                        # MCP服务器配置
│   ├── cursor.json             # Cursor编辑器配置
│   ├── claude-desktop.json     # Claude Desktop配置
│   ├── vscode.json             # VS Code配置
│   └── generic-mcp.json        # 通用MCP配置
├── environments/               # 环境配置
│   ├── development.env         # 开发环境
│   ├── production.env          # 生产环境
│   └── testing.env             # 测试环境
├── llm/                       # 大模型配置
│   ├── baidu.json             # 百度千帆配置
│   ├── alibaba.json           # 阿里通义配置
│   └── tencent.json           # 腾讯混元配置
└── deployment/                # 部署配置
    ├── docker-compose.yml     # Docker部署
    ├── kubernetes.yaml        # K8s部署
    └── nginx.conf             # Nginx配置
```

## 🔌 MCP 服务器配置

### Cursor 编辑器配置

**文件**: `mcp/cursor.json`

```json
{
  "mcpServers": {
    "DramaCraft": {
      "command": "uv",
      "args": ["run", "dramacraft", "start"],
      "env": {
        "LLM__PROVIDER": "baidu",
        "LLM__API_KEY": "${BAIDU_API_KEY}",
        "LLM__SECRET_KEY": "${BAIDU_SECRET_KEY}",
        "VIDEO__TEMP_DIR": "./temp",
        "VIDEO__OUTPUT_DIR": "./output",
        "JIANYING__INSTALLATION_PATH": "/Applications/JianyingPro.app"
      }
    }
  }
}
```

**配置步骤**:
1. 打开 Cursor 设置 (Cmd/Ctrl + ,)
2. 搜索 "MCP" 或 "Model Context Protocol"
3. 添加上述配置到 MCP 服务器列表
4. 替换环境变量为实际值
5. 重启 Cursor 生效

### Claude Desktop 配置

**文件**: `mcp/claude-desktop.json`

```json
{
  "mcpServers": {
    "DramaCraft": {
      "command": "uv",
      "args": ["run", "dramacraft", "start"],
      "env": {
        "LLM__PROVIDER": "baidu",
        "LLM__API_KEY": "your_baidu_api_key",
        "LLM__SECRET_KEY": "your_baidu_secret_key"
      }
    }
  }
}
```

**配置步骤**:
1. 找到 Claude Desktop 配置文件:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
2. 编辑或创建配置文件
3. 添加上述配置内容
4. 重启 Claude Desktop

### VS Code 配置

**文件**: `mcp/vscode.json`

```json
{
  "mcp.servers": [
    {
      "name": "DramaCraft",
      "command": "uv",
      "args": ["run", "dramacraft", "start"],
      "env": {
        "LLM__PROVIDER": "baidu",
        "LLM__API_KEY": "${env:BAIDU_API_KEY}",
        "LLM__SECRET_KEY": "${env:BAIDU_SECRET_KEY}"
      }
    }
  ]
}
```

**配置步骤**:
1. 安装 MCP 扩展
2. 打开 VS Code 设置 (Cmd/Ctrl + ,)
3. 搜索 "mcp.servers"
4. 添加上述配置
5. 设置环境变量或直接填入密钥

## 🌍 环境配置

### 开发环境配置

**文件**: `environments/development.env`

```env
# 开发环境配置
NODE_ENV=development
DEBUG=true

# LLM 配置
LLM__PROVIDER=baidu
LLM__API_KEY=your_development_api_key
LLM__SECRET_KEY=your_development_secret_key
LLM__MODEL=ernie-bot-turbo
LLM__TEMPERATURE=0.7
LLM__MAX_TOKENS=2000
LLM__TIMEOUT=30.0
LLM__MAX_RETRIES=3

# 视频处理配置
VIDEO__TEMP_DIR=./temp
VIDEO__OUTPUT_DIR=./output
VIDEO__MAX_FILE_SIZE_MB=100
VIDEO__SUPPORTED_FORMATS=mp4,avi,mov

# 剪映配置
JIANYING__INSTALLATION_PATH=/Applications/JianyingPro.app
JIANYING__PROJECTS_DIR=~/Movies/JianyingPro
JIANYING__AUTO_BACKUP=true
JIANYING__BACKUP_DIR=./backups

# 性能配置
PERFORMANCE__MAX_CONCURRENT_TASKS=3
PERFORMANCE__CACHE_ENABLED=true
PERFORMANCE__CACHE_SIZE=500
PERFORMANCE__MONITORING_ENABLED=true

# 日志配置
LOG_LEVEL=DEBUG
LOG_FORMAT=detailed
LOG_FILE=./logs/dramacraft-dev.log
```

### 生产环境配置

**文件**: `environments/production.env`

```env
# 生产环境配置
NODE_ENV=production
DEBUG=false

# LLM 配置
LLM__PROVIDER=baidu
LLM__API_KEY=${BAIDU_API_KEY}
LLM__SECRET_KEY=${BAIDU_SECRET_KEY}
LLM__MODEL=ernie-bot-4
LLM__TEMPERATURE=0.6
LLM__MAX_TOKENS=4000
LLM__TIMEOUT=60.0
LLM__MAX_RETRIES=5

# 视频处理配置
VIDEO__TEMP_DIR=/var/tmp/dramacraft
VIDEO__OUTPUT_DIR=/var/output/dramacraft
VIDEO__MAX_FILE_SIZE_MB=1000
VIDEO__SUPPORTED_FORMATS=mp4,avi,mov,mkv

# 剪映配置
JIANYING__INSTALLATION_PATH=/opt/jianying/JianyingPro
JIANYING__PROJECTS_DIR=/var/projects/jianying
JIANYING__AUTO_BACKUP=true
JIANYING__BACKUP_DIR=/var/backups/jianying

# 性能配置
PERFORMANCE__MAX_CONCURRENT_TASKS=10
PERFORMANCE__CACHE_ENABLED=true
PERFORMANCE__CACHE_SIZE=2000
PERFORMANCE__MONITORING_ENABLED=true

# 安全配置
SECURITY__RATE_LIMIT=100
SECURITY__MAX_REQUEST_SIZE=50MB
SECURITY__ALLOWED_ORIGINS=*

# 日志配置
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/var/log/dramacraft/app.log
```

## 🤖 大模型配置

### 百度千帆配置

**文件**: `llm/baidu.json`

```json
{
  "provider": "baidu",
  "api_key": "${BAIDU_API_KEY}",
  "secret_key": "${BAIDU_SECRET_KEY}",
  "endpoint": "https://aip.baidubce.com",
  "models": {
    "default": "ernie-bot-turbo",
    "creative": "ernie-bot-4",
    "fast": "ernie-bot-turbo",
    "precise": "ernie-bot-4"
  },
  "parameters": {
    "temperature": 0.7,
    "max_tokens": 2000,
    "top_p": 0.9,
    "frequency_penalty": 0.0,
    "presence_penalty": 0.0
  },
  "limits": {
    "requests_per_minute": 60,
    "tokens_per_minute": 100000,
    "concurrent_requests": 5
  },
  "retry": {
    "max_retries": 3,
    "retry_delay": 1.0,
    "backoff_factor": 2.0
  }
}
```

### 阿里通义配置

**文件**: `llm/alibaba.json`

```json
{
  "provider": "alibaba",
  "api_key": "${ALIBABA_API_KEY}",
  "region": "cn-beijing",
  "endpoint": "https://dashscope.aliyuncs.com",
  "models": {
    "default": "qwen-turbo",
    "creative": "qwen-plus",
    "fast": "qwen-turbo",
    "precise": "qwen-max"
  },
  "parameters": {
    "temperature": 0.7,
    "max_tokens": 2000,
    "top_p": 0.9,
    "repetition_penalty": 1.1
  },
  "limits": {
    "requests_per_minute": 100,
    "tokens_per_minute": 200000,
    "concurrent_requests": 10
  }
}
```

### 腾讯混元配置

**文件**: `llm/tencent.json`

```json
{
  "provider": "tencent",
  "secret_id": "${TENCENT_SECRET_ID}",
  "secret_key": "${TENCENT_SECRET_KEY}",
  "region": "ap-beijing",
  "endpoint": "https://hunyuan.tencentcloudapi.com",
  "models": {
    "default": "hunyuan-lite",
    "creative": "hunyuan-standard",
    "fast": "hunyuan-lite",
    "precise": "hunyuan-pro"
  },
  "parameters": {
    "temperature": 0.7,
    "max_tokens": 2000,
    "top_p": 0.9
  },
  "limits": {
    "requests_per_minute": 50,
    "tokens_per_minute": 80000,
    "concurrent_requests": 3
  }
}
```

## 🚀 部署配置

### Docker Compose 配置

**文件**: `deployment/docker-compose.yml`

```yaml
version: '3.8'

services:
  dramacraft:
    build:
      context: ..
      dockerfile: Dockerfile
    container_name: dramacraft-mcp
    restart: unless-stopped
    environment:
      - LLM__PROVIDER=${LLM__PROVIDER:-baidu}
      - LLM__API_KEY=${LLM__API_KEY}
      - LLM__SECRET_KEY=${LLM__SECRET_KEY}
    volumes:
      - ../output:/app/output
      - ../temp:/app/temp
      - ../logs:/app/logs
    ports:
      - "8000:8000"
    networks:
      - dramacraft-network

  redis:
    image: redis:7-alpine
    container_name: dramacraft-redis
    restart: unless-stopped
    volumes:
      - redis-data:/data
    networks:
      - dramacraft-network

networks:
  dramacraft-network:
    driver: bridge

volumes:
  redis-data:
```

### Kubernetes 配置

**文件**: `deployment/kubernetes.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dramacraft-mcp
  labels:
    app: dramacraft
spec:
  replicas: 3
  selector:
    matchLabels:
      app: dramacraft
  template:
    metadata:
      labels:
        app: dramacraft
    spec:
      containers:
      - name: dramacraft
        image: dramacraft/dramacraft:latest
        ports:
        - containerPort: 8000
        env:
        - name: LLM__PROVIDER
          value: "baidu"
        - name: LLM__API_KEY
          valueFrom:
            secretKeyRef:
              name: dramacraft-secrets
              key: llm-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: dramacraft-service
spec:
  selector:
    app: dramacraft
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

## 🔧 配置使用指南

### 1. 选择配置文件

根据您的使用场景选择合适的配置：

- **开发调试**: 使用 `environments/development.env`
- **生产部署**: 使用 `environments/production.env`
- **AI编辑器**: 选择对应的 MCP 配置文件

### 2. 设置环境变量

```bash
# 方法1: 直接设置
export LLM__API_KEY="your_api_key"
export LLM__SECRET_KEY="your_secret_key"

# 方法2: 使用.env文件
cp configs/environments/development.env .env
# 编辑.env文件填入实际值

# 方法3: 使用配置文件
uv run dramacraft start --config configs/environments/production.env
```

### 3. 验证配置

```bash
# 验证配置文件
uv run dramacraft config --validate

# 显示当前配置
uv run dramacraft config --show

# 测试连接
uv run dramacraft test --tool generate_commentary
```

## 🔍 配置故障排除

### 常见问题

**Q: MCP服务器无法启动？**
A: 检查以下配置：
- 确认 `uv` 已正确安装
- 验证项目路径正确
- 检查环境变量设置
- 查看日志文件错误信息

**Q: LLM API调用失败？**
A: 验证以下设置：
- API密钥是否正确且有效
- 网络连接是否正常
- 账户余额是否充足
- 请求频率是否超限

**Q: 剪映集成不工作？**
A: 检查以下配置：
- 剪映安装路径是否正确
- 项目目录权限是否足够
- 剪映版本是否兼容
- 系统环境是否支持

### 配置验证脚本

```bash
#!/bin/bash
# 配置验证脚本

echo "验证 DramaCraft 配置..."

# 检查Python环境
python --version
uv --version

# 检查配置文件
if [ -f ".env" ]; then
    echo "✅ 环境配置文件存在"
else
    echo "❌ 环境配置文件缺失"
fi

# 测试LLM连接
uv run python -c "
from dramacraft.config import DramaCraftConfig
from dramacraft.llm.factory import create_llm_client
try:
    config = DramaCraftConfig()
    client = create_llm_client(config.llm)
    print('✅ LLM配置正确')
except Exception as e:
    print(f'❌ LLM配置错误: {e}')
"

echo "配置验证完成"
```

## 📚 相关文档

- [快速开始指南](../docs/getting-started.md)
- [API参考文档](../docs/api/README.md)
- [部署指南](../docs/deployment.md)
- [故障排除](../docs/troubleshooting.md)
