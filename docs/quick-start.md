# DramaCraft 快速开始指南

欢迎使用 DramaCraft！本指南将帮助您在 5 分钟内完成基础配置并开始使用我们的企业级视频编辑MCP服务。

## 🚀 系统要求

### 最低要求
- **Python**: 3.9+
- **内存**: 4GB RAM
- **存储**: 2GB 可用空间
- **操作系统**: Windows 10+, macOS 10.15+, Ubuntu 18.04+

### 推荐配置
- **Python**: 3.11+
- **内存**: 8GB+ RAM
- **存储**: 10GB+ SSD
- **GPU**: 支持CUDA的显卡（可选，用于加速视频处理）

## 📦 安装步骤

### 1. 安装 DramaCraft

使用 uv 包管理器（推荐）：

```bash
# 安装 uv（如果尚未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 克隆项目
git clone https://github.com/dramacraft/dramacraft.git
cd dramacraft

# 安装依赖
uv sync

# 激活虚拟环境
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate     # Windows
```

或使用传统的 pip 方式：

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate   # Linux/macOS
# 或
venv\Scripts\activate      # Windows

# 安装 DramaCraft
pip install dramacraft
```

### 2. 验证安装

```bash
# 检查版本
dramacraft --version

# 运行健康检查
dramacraft health-check
```

## ⚙️ 基础配置

### 1. 创建配置文件

```bash
# 生成默认配置
dramacraft init-config

# 这将创建 ~/.dramacraft/config.yaml
```

### 2. 配置 AI 服务

编辑配置文件 `~/.dramacraft/config.yaml`：

```yaml
# DramaCraft 配置文件
ai:
  # 选择您的AI提供商
  provider: "baidu"  # 支持: baidu, alibaba, tencent, openai
  
  # 百度千帆配置
  baidu:
    api_key: "your_baidu_api_key"
    secret_key: "your_baidu_secret_key"
    model: "ERNIE-Bot-turbo"
  
  # 阿里云通义千问配置
  alibaba:
    api_key: "your_alibaba_api_key"
    model: "qwen-turbo"
  
  # 腾讯混元配置
  tencent:
    secret_id: "your_tencent_secret_id"
    secret_key: "your_tencent_secret_key"
    model: "hunyuan-lite"

# 视频处理配置
video:
  # 临时文件目录
  temp_dir: "/tmp/dramacraft"
  
  # 输出质量设置
  quality:
    default: "high"  # low, medium, high, ultra
    
  # 支持的格式
  formats:
    input: ["mp4", "avi", "mov", "mkv"]
    output: ["mp4", "webm"]

# 安全配置
security:
  # JWT密钥（请更改为您自己的密钥）
  jwt_secret_key: "your-super-secret-jwt-key-change-this"
  
  # 会话加密密钥
  session_encryption_key: "your-session-encryption-key"
  
  # 启用多因素认证
  mfa_enabled: false

# 服务器配置
server:
  host: "0.0.0.0"
  port: 8080
  debug: false
  
# 日志配置
logging:
  level: "INFO"
  file: "~/.dramacraft/logs/dramacraft.log"
```

### 3. 获取 AI 服务密钥

#### 百度千帆平台
1. 访问 [百度智能云](https://cloud.baidu.com/)
2. 注册并登录账户
3. 进入"千帆大模型平台"
4. 创建应用获取 API Key 和 Secret Key

#### 阿里云通义千问
1. 访问 [阿里云](https://www.aliyun.com/)
2. 开通"通义千问"服务
3. 获取 API Key

#### 腾讯混元
1. 访问 [腾讯云](https://cloud.tencent.com/)
2. 开通"混元大模型"服务
3. 获取 Secret ID 和 Secret Key

## 🎬 第一个视频项目

### 1. 启动 MCP 服务器

```bash
# 启动 DramaCraft MCP 服务器
uv run dramacraft start

# 或者使用传统方式
dramacraft start
```

服务器启动后，您将看到：

```
🎬 DramaCraft MCP Server v1.0.0
🚀 服务器已启动: http://localhost:8080
📚 API文档: http://localhost:8080/docs
🔧 健康检查: http://localhost:8080/health
```

### 2. 配置 AI 编辑器

#### Cursor 配置

在 Cursor 中添加 MCP 服务器配置：

```json
{
  "mcpServers": {
    "dramacraft": {
      "command": "uv",
      "args": ["run", "dramacraft", "start"],
      "env": {
        "DRAMACRAFT_CONFIG": "~/.dramacraft/config.yaml"
      }
    }
  }
}
```

#### Claude Desktop 配置

编辑 `~/.config/claude-desktop/claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "dramacraft": {
      "command": "uv",
      "args": ["run", "dramacraft", "start"],
      "env": {
        "DRAMACRAFT_CONFIG": "~/.dramacraft/config.yaml"
      }
    }
  }
}
```

#### VS Code 配置

安装 MCP 扩展并添加配置：

```json
{
  "mcp.servers": [
    {
      "name": "dramacraft",
      "command": "uv run dramacraft start",
      "args": [],
      "env": {
        "DRAMACRAFT_CONFIG": "~/.dramacraft/config.yaml"
      }
    }
  ]
}
```

### 3. 创建第一个项目

在您的 AI 编辑器中，您现在可以使用 DramaCraft 的功能：

```
请帮我分析这个视频文件：/path/to/your/video.mp4
```

AI 编辑器将调用 DramaCraft 的 MCP 工具来：
- 分析视频内容
- 检测场景变化
- 提取音频特征
- 生成编辑建议

## 🔧 常用命令

### 服务管理
```bash
# 启动服务
dramacraft start

# 停止服务
dramacraft stop

# 重启服务
dramacraft restart

# 查看状态
dramacraft status
```

### 项目管理
```bash
# 创建新项目
dramacraft create-project "我的第一个项目"

# 列出项目
dramacraft list-projects

# 删除项目
dramacraft delete-project <project-id>
```

### 视频处理
```bash
# 分析视频
dramacraft analyze-video /path/to/video.mp4

# 批量处理
dramacraft batch-process /path/to/videos/

# 导出项目
dramacraft export-project <project-id> --format mp4
```

## 📖 下一步

恭喜！您已经成功配置了 DramaCraft。接下来您可以：

1. **📚 阅读完整文档**: [API 参考](./api-reference.md)
2. **💡 查看示例**: [使用示例](./examples.md)
3. **🎯 最佳实践**: [最佳实践指南](./best-practices.md)
4. **🔧 高级配置**: [高级配置指南](./advanced-config.md)
5. **🤝 加入社区**: [GitHub 讨论](https://github.com/dramacraft/dramacraft/discussions)

## ❓ 常见问题

### Q: 安装时遇到权限错误怎么办？
A: 确保您有足够的权限安装软件包。在 Linux/macOS 上，您可能需要使用 `sudo`。

### Q: AI 服务连接失败怎么办？
A: 请检查：
- API 密钥是否正确
- 网络连接是否正常
- 服务商的服务状态

### Q: 视频处理速度很慢怎么办？
A: 可以尝试：
- 降低视频质量设置
- 使用 GPU 加速（如果可用）
- 增加系统内存

### Q: 如何更新 DramaCraft？
A: 使用以下命令：
```bash
# 使用 uv
uv sync --upgrade

# 使用 pip
pip install --upgrade dramacraft
```

## 🆘 获取帮助

如果您遇到问题，可以通过以下方式获取帮助：

- **📖 文档**: [完整文档](https://dramacraft.github.io/docs)
- **💬 社区**: [GitHub 讨论](https://github.com/dramacraft/dramacraft/discussions)
- **🐛 报告问题**: [GitHub Issues](https://github.com/dramacraft/dramacraft/issues)
- **📧 邮件支持**: support@dramacraft.com

---

**🎉 开始您的视频编辑之旅吧！**
