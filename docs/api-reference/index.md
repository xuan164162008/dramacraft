# API 参考文档

DramaCraft 提供了完整的 MCP (Model Context Protocol) 工具集，让您可以在 AI 编辑器中轻松进行视频编辑和处理。

## 🔧 MCP 工具概览

DramaCraft 提供以下 MCP 工具类别：

<div class="api-overview">
  <div class="api-category">
    <h3>🎬 视频分析</h3>
    <p>8个工具</p>
    <span>视频内容分析、场景检测、特征提取</span>
  </div>
  
  <div class="api-category">
    <h3>🎵 音频处理</h3>
    <p>6个工具</p>
    <span>音频分析、降噪、音效处理</span>
  </div>
  
  <div class="api-category">
    <h3>🤖 AI 导演</h3>
    <p>4个工具</p>
    <span>智能编辑建议、风格分析</span>
  </div>
  
  <div class="api-category">
    <h3>📁 项目管理</h3>
    <p>5个工具</p>
    <span>项目创建、管理、导出</span>
  </div>
  
  <div class="api-category">
    <h3>🔄 工作流</h3>
    <p>3个工具</p>
    <span>自动化工作流、批处理</span>
  </div>
</div>

## 📹 视频分析工具

### analyze_video

分析视频文件的基本信息和内容特征。

!!! info "工具信息"
    **工具名称**: `analyze_video`  
    **类别**: 视频分析  
    **响应时间**: < 30秒  

**参数:**

| 参数名 | 类型 | 必需 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `video_path` | string | ✅ | - | 视频文件路径 |
| `analysis_type` | string | ❌ | "comprehensive" | 分析类型 |

**analysis_type 选项:**

=== "basic"
    基础信息分析
    
    - 视频时长、分辨率、格式
    - 文件大小、比特率
    - 基本元数据

=== "comprehensive"
    全面分析（推荐）
    
    - 包含基础信息
    - 场景检测和分析
    - 运动强度分析
    - 色彩温度分析
    - 音频质量评估

=== "quick"
    快速分析
    
    - 仅基础技术信息
    - 最快响应时间

**响应示例:**

```json
{
  "video_info": {
    "path": "/path/to/video.mp4",
    "duration": 120.5,
    "resolution": [1920, 1080],
    "fps": 30.0,
    "format": "mp4",
    "size_mb": 245.8,
    "bitrate": 2500000
  },
  "content_analysis": {
    "scene_count": 15,
    "average_brightness": 0.65,
    "color_temperature": "warm",
    "motion_intensity": "medium",
    "audio_present": true
  },
  "technical_quality": {
    "sharpness_score": 0.85,
    "noise_level": 0.12,
    "stability_score": 0.92
  }
}
```

**使用示例:**

=== "Python"
    ```python
    # 基础分析
    result = await mcp_client.call_tool("analyze_video", {
        "video_path": "/videos/sample.mp4",
        "analysis_type": "basic"
    })
    
    # 全面分析
    result = await mcp_client.call_tool("analyze_video", {
        "video_path": "/videos/sample.mp4",
        "analysis_type": "comprehensive"
    })
    ```

=== "JavaScript"
    ```javascript
    // 基础分析
    const result = await mcpClient.callTool("analyze_video", {
        video_path: "/videos/sample.mp4",
        analysis_type: "basic"
    });
    
    // 全面分析
    const result = await mcpClient.callTool("analyze_video", {
        video_path: "/videos/sample.mp4",
        analysis_type: "comprehensive"
    });
    ```

=== "AI编辑器"
    ```
    请分析这个视频文件：/videos/sample.mp4
    
    请对 /videos/sample.mp4 进行全面分析，包括场景检测和质量评估
    ```

### detect_scenes

检测视频中的场景变化点。

!!! info "工具信息"
    **工具名称**: `detect_scenes`  
    **类别**: 视频分析  
    **响应时间**: < 15秒  

**参数:**

| 参数名 | 类型 | 必需 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `video_path` | string | ✅ | - | 视频文件路径 |
| `threshold` | float | ❌ | 0.3 | 场景变化阈值 (0.1-1.0) |
| `min_scene_length` | float | ❌ | 2.0 | 最小场景长度（秒） |

**响应示例:**

```json
{
  "scenes": [
    {
      "start_time": 0.0,
      "end_time": 15.2,
      "duration": 15.2,
      "confidence": 0.95,
      "scene_type": "indoor",
      "average_brightness": 0.7,
      "motion_intensity": 0.3
    },
    {
      "start_time": 15.2,
      "end_time": 32.8,
      "duration": 17.6,
      "confidence": 0.88,
      "scene_type": "outdoor",
      "average_brightness": 0.85,
      "motion_intensity": 0.6
    }
  ],
  "total_scenes": 2,
  "average_scene_length": 16.4
}
```

### extract_frames

从视频中提取关键帧。

!!! info "工具信息"
    **工具名称**: `extract_frames`  
    **类别**: 视频分析  
    **响应时间**: < 20秒  

**参数:**

| 参数名 | 类型 | 必需 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `video_path` | string | ✅ | - | 视频文件路径 |
| `method` | string | ❌ | "uniform" | 提取方法 |
| `count` | integer | ❌ | 10 | 提取帧数 |
| `output_dir` | string | ❌ | auto | 输出目录 |

**method 选项:**

- `uniform`: 均匀间隔提取
- `keyframes`: 提取关键帧
- `scenes`: 每个场景提取一帧

## 🎵 音频处理工具

### analyze_audio

分析视频中的音频内容。

!!! info "工具信息"
    **工具名称**: `analyze_audio`  
    **类别**: 音频处理  
    **响应时间**: < 10秒  

**参数:**

| 参数名 | 类型 | 必需 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `video_path` | string | ✅ | - | 视频文件路径 |
| `analysis_depth` | string | ❌ | "standard" | 分析深度 |

**analysis_depth 选项:**

=== "basic"
    基础音频信息
    
    - 采样率、声道数
    - 比特率、格式
    - 音频时长

=== "standard"
    标准分析
    
    - 包含基础信息
    - 音量分析
    - 频谱分析
    - 动态范围

=== "advanced"
    高级分析
    
    - 包含标准分析
    - 语音识别
    - 音乐检测
    - 情感分析

**响应示例:**

```json
{
  "audio_info": {
    "duration": 120.5,
    "sample_rate": 44100,
    "channels": 2,
    "bitrate": 128000,
    "format": "aac"
  },
  "content_analysis": {
    "average_volume": -12.5,
    "peak_volume": -3.2,
    "dynamic_range": 18.7,
    "silence_percentage": 5.2,
    "speech_detected": true,
    "music_detected": true
  },
  "quality_metrics": {
    "noise_level": 0.08,
    "clarity_score": 0.92,
    "balance_score": 0.88
  }
}
```

### enhance_audio

增强音频质量。

!!! info "工具信息"
    **工具名称**: `enhance_audio`  
    **类别**: 音频处理  
    **响应时间**: < 45秒  

**参数:**

| 参数名 | 类型 | 必需 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `video_path` | string | ✅ | - | 视频文件路径 |
| `enhancement_type` | string | ❌ | "auto" | 增强类型 |
| `output_path` | string | ❌ | auto | 输出文件路径 |

**enhancement_type 选项:**

- `auto`: 自动增强（推荐）
- `denoise`: 降噪处理
- `normalize`: 音量标准化
- `enhance_speech`: 语音增强

## 🤖 AI 导演工具

### analyze_content

使用 AI 分析视频内容并提供编辑建议。

!!! info "工具信息"
    **工具名称**: `analyze_content`  
    **类别**: AI 导演  
    **响应时间**: < 60秒  

**参数:**

| 参数名 | 类型 | 必需 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `video_path` | string | ✅ | - | 视频文件路径 |
| `analysis_focus` | string | ❌ | "general" | 分析重点 |

**analysis_focus 选项:**

- `general`: 通用分析
- `narrative`: 叙事结构分析
- `technical`: 技术质量分析
- `aesthetic`: 美学分析

**响应示例:**

```json
{
  "content_analysis": {
    "genre": "documentary",
    "mood": "informative",
    "pacing": "moderate",
    "visual_style": "professional",
    "narrative_structure": {
      "introduction": {"start": 0, "end": 15},
      "development": {"start": 15, "end": 90},
      "conclusion": {"start": 90, "end": 120}
    }
  },
  "editing_suggestions": [
    {
      "type": "cut",
      "timestamp": 45.2,
      "reason": "Natural pause in narration",
      "confidence": 0.85
    },
    {
      "type": "transition",
      "start_time": 30.0,
      "end_time": 32.0,
      "suggestion": "fade",
      "reason": "Scene change detected"
    }
  ],
  "quality_assessment": {
    "overall_score": 8.2,
    "technical_quality": 8.5,
    "content_quality": 7.8,
    "engagement_level": 8.0
  }
}
```

## 📁 项目管理工具

### create_project

创建新的视频编辑项目。

!!! info "工具信息"
    **工具名称**: `create_project`  
    **类别**: 项目管理  
    **响应时间**: < 5秒  

**参数:**

| 参数名 | 类型 | 必需 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `project_name` | string | ✅ | - | 项目名称 |
| `description` | string | ❌ | "" | 项目描述 |
| `video_files` | array | ❌ | [] | 初始视频文件列表 |

**响应示例:**

```json
{
  "project": {
    "id": "proj_abc123",
    "name": "My Video Project",
    "description": "A sample video project",
    "created_at": "2024-01-15T10:30:00Z",
    "status": "active",
    "video_files": [
      "/videos/clip1.mp4",
      "/videos/clip2.mp4"
    ],
    "project_path": "/projects/proj_abc123"
  }
}
```

## 🔐 认证和安全

### 认证方式

DramaCraft 支持多种认证方式：

=== "JWT Token"
    ```http
    Authorization: Bearer <jwt_token>
    ```

=== "API Key"
    ```http
    X-API-Key: <api_key>
    ```

=== "OAuth 2.0"
    ```http
    Authorization: Bearer <oauth_token>
    ```

### 权限级别

| 权限级别 | 描述 | 可用操作 |
|----------|------|----------|
| `read` | 只读权限 | 查看项目、分析结果 |
| `write` | 读写权限 | 创建项目、编辑内容 |
| `admin` | 管理员权限 | 所有操作、用户管理 |

## 📊 错误代码

| 错误代码 | 描述 | 解决方案 |
|----------|------|----------|
| `E001` | 文件不存在 | 检查文件路径是否正确 |
| `E002` | 格式不支持 | 使用支持的视频格式 |
| `E003` | 权限不足 | 检查文件访问权限 |
| `E004` | 内存不足 | 释放内存或降低处理质量 |
| `E005` | AI 服务不可用 | 检查 AI 服务配置和网络连接 |

## 📈 性能指标

### 响应时间

| 操作类型 | 平均响应时间 | 最大响应时间 |
|----------|--------------|--------------|
| 视频分析 | < 30秒 | < 60秒 |
| 场景检测 | < 15秒 | < 30秒 |
| 音频分析 | < 10秒 | < 20秒 |
| AI 分析 | < 60秒 | < 120秒 |

### 资源使用

| 操作类型 | 内存使用 | CPU使用 |
|----------|----------|---------|
| 视频分析 | 500MB | 中等 |
| 场景检测 | 300MB | 中等 |
| 音频分析 | 200MB | 低 |
| AI 分析 | 800MB | 高 |

## 🔗 相关链接

- [快速开始](../getting-started/) - 5分钟上手指南
- [用户指南](../user-guide/) - 详细使用说明
- [最佳实践](../best-practices/) - 专业使用技巧
- [示例教程](../examples/) - 实际应用案例

---

**📚 需要更多帮助？** 查看我们的 [完整文档](https://agions.github.io/dramacraft) 或 [联系支持团队](mailto:1051736049@qq.com)。
