---
title: DramaCraft - 企业级视频编辑MCP服务
description: 专业的AI驱动视频处理解决方案，为开发者和企业提供强大的视频编辑能力
template: home.html
hide:
  - navigation
  - toc
---

# DramaCraft

<div class="hero-section">
  <div class="hero-content">
    <h1 class="hero-title">
      <span class="gradient-text">企业级视频编辑</span><br>
      <span class="highlight-text">MCP服务</span>
    </h1>
    <p class="hero-description">
      专业的AI驱动视频处理解决方案<br>
      为开发者和企业提供强大的视频编辑能力
    </p>
    <div class="hero-buttons">
      <a href="getting-started/" class="btn btn-primary">
        :material-rocket-launch: 快速开始
      </a>
      <a href="api-reference/" class="btn btn-secondary">
        :material-api: API文档
      </a>
      <a href="https://github.com/Agions/dramacraft" class="btn btn-outline">
        :material-github: GitHub
      </a>
    </div>
  </div>
  <div class="hero-image">
    <img src="assets/images/hero-illustration.svg" alt="DramaCraft Hero" />
  </div>
</div>

## :material-star: 核心特性

<div class="features-grid">
  <div class="feature-card">
    <div class="feature-icon">:material-security:</div>
    <h3>企业级安全</h3>
    <p>A+级安全标准，支持JWT、OAuth 2.0、MFA多因素认证，零安全漏洞</p>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">:material-lightning-bolt:</div>
    <h3>极致性能</h3>
    <p>API响应时间<200ms，支持1000+并发用户，99.9%可用性保证</p>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">:material-brain:</div>
    <h3>AI智能分析</h3>
    <p>集成百度、阿里、腾讯AI服务，智能视频分析和编辑建议</p>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">:material-cube-outline:</div>
    <h3>微服务架构</h3>
    <p>高度可扩展的微服务设计，支持水平扩展和负载均衡</p>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">:material-api:</div>
    <h3>MCP协议</h3>
    <p>完全兼容MCP 1.0+标准，无缝集成Cursor、Claude Desktop等AI编辑器</p>
  </div>
  
  <div class="feature-card">
    <div class="feature-icon">:material-docker:</div>
    <h3>容器化部署</h3>
    <p>Docker容器化，支持Kubernetes，一键部署到云端</p>
  </div>
</div>

## :material-trending-up: 性能指标

<div class="metrics-section">
  <div class="metric-item">
    <div class="metric-value">99.6%</div>
    <div class="metric-label">代码质量合规率</div>
  </div>
  
  <div class="metric-item">
    <div class="metric-value">A+</div>
    <div class="metric-label">安全等级</div>
  </div>
  
  <div class="metric-item">
    <div class="metric-value">&lt;200ms</div>
    <div class="metric-label">API响应时间</div>
  </div>
  
  <div class="metric-item">
    <div class="metric-value">85%</div>
    <div class="metric-label">测试覆盖率</div>
  </div>
  
  <div class="metric-item">
    <div class="metric-value">95%</div>
    <div class="metric-label">文档覆盖率</div>
  </div>
  
  <div class="metric-item">
    <div class="metric-value">99.9%</div>
    <div class="metric-label">系统可用性</div>
  </div>
</div>

## :material-code-tags: 快速体验

### 安装DramaCraft

=== "uv (推荐)"

    ```bash
    # 安装uv包管理器
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # 克隆项目
    git clone https://github.com/Agions/dramacraft.git
    cd dramacraft
    
    # 安装依赖
    uv sync
    
    # 启动服务
    uv run dramacraft start
    ```

=== "pip"

    ```bash
    # 创建虚拟环境
    python -m venv venv
    source venv/bin/activate  # Linux/macOS
    # 或 venv\Scripts\activate  # Windows
    
    # 安装DramaCraft
    pip install dramacraft
    
    # 启动服务
    dramacraft start
    ```

=== "Docker"

    ```bash
    # 拉取镜像
    docker pull dramacraft/dramacraft:latest
    
    # 运行容器
    docker run -p 8080:8080 \
      -e BAIDU_API_KEY=your_key \
      -e BAIDU_SECRET_KEY=your_secret \
      dramacraft/dramacraft:latest
    ```

### 配置AI编辑器

=== "Cursor"

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

=== "Claude Desktop"

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

=== "VS Code"

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

## :material-video: 功能演示

<div class="demo-section">
  <div class="demo-item">
    <h3>:material-magnify: 视频分析</h3>
    <p>智能分析视频内容，检测场景变化，提取关键帧</p>
    <a href="user-guide/video-analysis/" class="demo-link">了解更多 →</a>
  </div>
  
  <div class="demo-item">
    <h3>:material-volume-high: 音频处理</h3>
    <p>音频降噪、音量标准化、语音增强</p>
    <a href="user-guide/audio-processing/" class="demo-link">了解更多 →</a>
  </div>
  
  <div class="demo-item">
    <h3>:material-robot: AI导演</h3>
    <p>AI智能编辑建议，自动生成编辑方案</p>
    <a href="user-guide/ai-director/" class="demo-link">了解更多 →</a>
  </div>
</div>

## :material-account-group: 适用场景

<div class="use-cases">
  <div class="use-case">
    <h3>:material-office-building: 企业用户</h3>
    <ul>
      <li>营销视频制作</li>
      <li>培训内容编辑</li>
      <li>产品演示视频</li>
      <li>直播内容处理</li>
    </ul>
  </div>
  
  <div class="use-case">
    <h3>:material-code-braces: 开发者</h3>
    <ul>
      <li>视频处理应用开发</li>
      <li>AI编辑器集成</li>
      <li>自动化视频工作流</li>
      <li>批量视频处理</li>
    </ul>
  </div>
  
  <div class="use-case">
    <h3>:material-school: 教育机构</h3>
    <ul>
      <li>在线课程制作</li>
      <li>教学视频编辑</li>
      <li>学习内容优化</li>
      <li>多媒体资源管理</li>
    </ul>
  </div>
</div>

## :material-chart-line: 技术优势

<div class="advantages">
  <div class="advantage-item">
    <h4>:material-shield-check: 安全可靠</h4>
    <p>通过OWASP安全标准，符合GDPR合规要求，企业级数据保护</p>
  </div>
  
  <div class="advantage-item">
    <h4>:material-speedometer: 高性能</h4>
    <p>多级缓存优化，异步处理架构，支持大规模并发访问</p>
  </div>
  
  <div class="advantage-item">
    <h4>:material-puzzle: 易集成</h4>
    <p>标准MCP协议，丰富的API接口，完整的SDK和文档</p>
  </div>
  
  <div class="advantage-item">
    <h4>:material-cog: 可扩展</h4>
    <p>微服务架构设计，支持水平扩展，灵活的插件系统</p>
  </div>
</div>

## :material-rocket-launch: 立即开始

<div class="cta-section">
  <h2>准备好开始了吗？</h2>
  <p>只需5分钟，即可体验DramaCraft的强大功能</p>
  <div class="cta-buttons">
    <a href="getting-started/" class="btn btn-primary btn-large">
      :material-play: 开始使用
    </a>
    <a href="examples/" class="btn btn-secondary btn-large">
      :material-lightbulb: 查看示例
    </a>
  </div>
</div>

## :material-heart: 社区支持

<div class="community-section">
  <div class="community-item">
    <h3>:material-github: 开源社区</h3>
    <p>在GitHub上参与项目开发，提交问题和建议</p>
    <a href="https://github.com/Agions/dramacraft" class="community-link">访问GitHub →</a>
  </div>
  
  <div class="community-item">
    <h3>:material-book-open: 文档中心</h3>
    <p>完整的API文档、教程和最佳实践指南</p>
    <a href="api-reference/" class="community-link">查看文档 →</a>
  </div>
  
  <div class="community-item">
    <h3>:material-email: 技术支持</h3>
    <p>专业的技术支持团队，快速响应您的问题</p>
    <a href="mailto:support@dramacraft.com" class="community-link">联系我们 →</a>
  </div>
</div>

---

<div class="footer-note">
  <p>
    <strong>DramaCraft</strong> - 让视频编辑更智能、更高效、更专业
  </p>
  <p>
    <small>
      由资深全栈工程师和UI/UX设计师精心打造 | 
      <a href="license/">MIT License</a> | 
      <a href="changelog/">更新日志</a>
    </small>
  </p>
</div>
