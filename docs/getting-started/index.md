# 快速开始

欢迎使用DramaCraft！本指南将帮助您在5分钟内完成安装配置并开始使用我们的企业级视频编辑MCP服务。

## 🎯 开始之前

### 系统要求

=== "最低要求"
    - **Python**: 3.9+
    - **内存**: 4GB RAM
    - **存储**: 2GB 可用空间
    - **操作系统**: Windows 10+, macOS 10.15+, Ubuntu 18.04+

=== "推荐配置"
    - **Python**: 3.11+
    - **内存**: 8GB+ RAM
    - **存储**: 10GB+ SSD
    - **GPU**: 支持CUDA的显卡（可选，用于加速视频处理）

=== "企业级配置"
    - **Python**: 3.11+
    - **内存**: 16GB+ RAM
    - **存储**: 50GB+ NVMe SSD
    - **GPU**: RTX 3070或更高
    - **网络**: 千兆网络

### 准备AI服务密钥

DramaCraft支持多个AI服务提供商，您需要至少配置一个：

!!! tip "推荐配置"
    建议优先使用百度千帆平台，它在中文视频内容分析方面表现优异。

=== "百度千帆"
    1. 访问 [百度智能云](https://cloud.baidu.com/)
    2. 注册并登录账户
    3. 进入"千帆大模型平台"
    4. 创建应用获取 API Key 和 Secret Key

=== "阿里通义"
    1. 访问 [阿里云](https://www.aliyun.com/)
    2. 开通"通义千问"服务
    3. 获取 API Key

=== "腾讯混元"
    1. 访问 [腾讯云](https://cloud.tencent.com/)
    2. 开通"混元大模型"服务
    3. 获取 Secret ID 和 Secret Key

## 📦 安装DramaCraft

### 方式一：使用uv（推荐）

uv是现代Python包管理器，速度更快，依赖解析更准确：

```bash
# 安装uv包管理器
curl -LsSf https://astral.sh/uv/install.sh | sh

# 克隆项目
git clone https://github.com/Agions/dramacraft.git
cd dramacraft

# 安装依赖
uv sync

# 激活虚拟环境
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate     # Windows

# 验证安装
uv run dramacraft --version
```

### 方式二：使用pip

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate   # Linux/macOS
# 或
venv\Scripts\activate      # Windows

# 安装DramaCraft
pip install dramacraft

# 验证安装
dramacraft --version
```

### 方式三：使用Docker

```bash
# 拉取最新镜像
docker pull dramacraft/dramacraft:latest

# 运行容器
docker run -p 8080:8080 \
  -e BAIDU_API_KEY=your_api_key \
  -e BAIDU_SECRET_KEY=your_secret_key \
  dramacraft/dramacraft:latest

# 验证运行
curl http://localhost:8080/health
```

## ⚙️ 基础配置

### 创建配置文件

```bash
# 生成默认配置
dramacraft init-config

# 配置文件位置：~/.dramacraft/config.yaml
```

### 编辑配置文件

打开 `~/.dramacraft/config.yaml` 并配置您的AI服务：

```yaml title="~/.dramacraft/config.yaml"
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
  temp_dir: "/tmp/dramacraft"
  quality:
    default: "high"  # low, medium, high, ultra
  formats:
    input: ["mp4", "avi", "mov", "mkv"]
    output: ["mp4", "webm"]

# 安全配置
security:
  jwt_secret_key: "your-super-secret-jwt-key-change-this"
  session_encryption_key: "your-session-encryption-key"
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

## 🚀 启动服务

### 启动MCP服务器

```bash
# 使用uv启动
uv run dramacraft start

# 或使用传统方式
dramacraft start
```

成功启动后，您将看到：

```
🎬 DramaCraft MCP Server v1.0.0
🚀 服务器已启动: http://localhost:8080
📚 API文档: http://localhost:8080/docs
🔧 健康检查: http://localhost:8080/health
```

### 验证服务状态

```bash
# 检查服务健康状态
curl http://localhost:8080/health

# 查看API文档
open http://localhost:8080/docs  # macOS
# 或
xdg-open http://localhost:8080/docs  # Linux
```

## 🔧 配置AI编辑器

### Cursor配置

在Cursor中添加MCP服务器配置：

1. 打开Cursor设置
2. 找到MCP服务器配置
3. 添加以下配置：

```json title="Cursor MCP配置"
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

### Claude Desktop配置

编辑 `~/.config/claude-desktop/claude_desktop_config.json`：

```json title="Claude Desktop配置"
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

### VS Code配置

1. 安装MCP扩展
2. 在设置中添加配置：

```json title="VS Code MCP配置"
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

## 🎬 第一个视频项目

### 创建项目

在您的AI编辑器中，您现在可以使用DramaCraft的功能：

```
请帮我分析这个视频文件：/path/to/your/video.mp4
```

AI编辑器将调用DramaCraft的MCP工具来：

- 分析视频内容
- 检测场景变化
- 提取音频特征
- 生成编辑建议

### 基本操作示例

```python
# 分析视频
result = await mcp_client.call_tool("analyze_video", {
    "video_path": "/path/to/video.mp4",
    "analysis_type": "comprehensive"
})

# 检测场景
scenes = await mcp_client.call_tool("detect_scenes", {
    "video_path": "/path/to/video.mp4",
    "threshold": 0.3
})

# 音频处理
enhanced = await mcp_client.call_tool("enhance_audio", {
    "video_path": "/path/to/video.mp4",
    "enhancement_type": "auto"
})
```

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

## ✅ 验证安装

运行以下命令验证DramaCraft是否正确安装和配置：

```bash
# 健康检查
dramacraft health-check

# 测试AI连接
dramacraft test-ai-connection

# 运行示例
dramacraft run-example basic-analysis
```

## 🆘 故障排除

### 常见问题

!!! question "安装时遇到权限错误"
    确保您有足够的权限安装软件包。在Linux/macOS上，您可能需要使用 `sudo`。

!!! question "AI服务连接失败"
    请检查：
    - API密钥是否正确
    - 网络连接是否正常
    - 服务商的服务状态

!!! question "视频处理速度很慢"
    可以尝试：
    - 降低视频质量设置
    - 使用GPU加速（如果可用）
    - 增加系统内存

!!! question "如何更新DramaCraft"
    ```bash
    # 使用uv
    uv sync --upgrade
    
    # 使用pip
    pip install --upgrade dramacraft
    ```

### 获取帮助

如果您遇到问题，可以通过以下方式获取帮助：

- **📖 文档**: [完整文档](https://agions.github.io/dramacraft)
- **💬 社区**: [GitHub 讨论](https://github.com/Agions/dramacraft/discussions)
- **🐛 报告问题**: [GitHub Issues](https://github.com/Agions/dramacraft/issues)
- **📧 邮件支持**: 1051736049@qq.com

## 📚 下一步

恭喜！您已经成功配置了DramaCraft。接下来您可以：

1. **📚 阅读用户指南**: [用户指南](../user-guide/)
2. **🔧 查看API文档**: [API参考](../api-reference/)
3. **💡 学习最佳实践**: [最佳实践](../best-practices/)
4. **🎯 查看示例**: [示例教程](../examples/)
5. **🤝 加入社区**: [GitHub 讨论](https://github.com/Agions/dramacraft/discussions)

---

**🎉 开始您的AI视频编辑之旅吧！**
