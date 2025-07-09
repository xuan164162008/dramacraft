# DramaCraft API 参考文档

本文档提供了 DramaCraft MCP 服务的完整 API 参考，包括所有可用的工具、参数和响应格式。

## 🔧 MCP 工具概览

DramaCraft 提供以下 MCP 工具类别：

| 类别 | 工具数量 | 描述 |
|------|----------|------|
| 视频分析 | 8 | 视频内容分析、场景检测、特征提取 |
| 音频处理 | 6 | 音频分析、降噪、音效处理 |
| AI 导演 | 4 | 智能编辑建议、风格分析 |
| 项目管理 | 5 | 项目创建、管理、导出 |
| 工作流 | 3 | 自动化工作流、批处理 |

## 📹 视频分析工具

### analyze_video

分析视频文件的基本信息和内容特征。

**参数:**
- `video_path` (string, 必需): 视频文件路径
- `analysis_type` (string, 可选): 分析类型，默认 "comprehensive"
  - `basic`: 基础信息（时长、分辨率、格式）
  - `comprehensive`: 全面分析（包含场景、运动、色彩）
  - `quick`: 快速分析（仅基础信息）

**响应:**
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

**示例:**
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

### detect_scenes

检测视频中的场景变化点。

**参数:**
- `video_path` (string, 必需): 视频文件路径
- `threshold` (float, 可选): 场景变化阈值，默认 0.3
- `min_scene_length` (float, 可选): 最小场景长度（秒），默认 2.0

**响应:**
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

**参数:**
- `video_path` (string, 必需): 视频文件路径
- `method` (string, 可选): 提取方法，默认 "uniform"
  - `uniform`: 均匀间隔提取
  - `keyframes`: 提取关键帧
  - `scenes`: 每个场景提取一帧
- `count` (integer, 可选): 提取帧数，默认 10
- `output_dir` (string, 可选): 输出目录

**响应:**
```json
{
  "frames": [
    {
      "timestamp": 5.2,
      "frame_number": 156,
      "file_path": "/output/frame_001.jpg",
      "resolution": [1920, 1080],
      "file_size": 245678
    }
  ],
  "total_frames": 10,
  "extraction_method": "uniform"
}
```

### analyze_motion

分析视频中的运动模式。

**参数:**
- `video_path` (string, 必需): 视频文件路径
- `sensitivity` (float, 可选): 运动检测敏感度，默认 0.5

**响应:**
```json
{
  "motion_analysis": {
    "overall_motion_level": "medium",
    "motion_score": 0.65,
    "motion_segments": [
      {
        "start_time": 0.0,
        "end_time": 10.5,
        "motion_type": "camera_pan",
        "intensity": 0.4
      }
    ],
    "static_periods": [
      {
        "start_time": 10.5,
        "end_time": 15.0,
        "duration": 4.5
      }
    ]
  }
}
```

## 🎵 音频处理工具

### analyze_audio

分析视频中的音频内容。

**参数:**
- `video_path` (string, 必需): 视频文件路径
- `analysis_depth` (string, 可选): 分析深度，默认 "standard"
  - `basic`: 基础音频信息
  - `standard`: 标准分析（包含音量、频谱）
  - `advanced`: 高级分析（包含语音识别、音乐检测）

**响应:**
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

**参数:**
- `video_path` (string, 必需): 视频文件路径
- `enhancement_type` (string, 可选): 增强类型，默认 "auto"
  - `auto`: 自动增强
  - `denoise`: 降噪
  - `normalize`: 音量标准化
  - `enhance_speech`: 语音增强
- `output_path` (string, 可选): 输出文件路径

**响应:**
```json
{
  "enhanced_audio": {
    "input_path": "/input/video.mp4",
    "output_path": "/output/enhanced_video.mp4",
    "enhancement_applied": ["denoise", "normalize"],
    "quality_improvement": {
      "noise_reduction": 0.75,
      "volume_consistency": 0.92,
      "clarity_improvement": 0.15
    }
  },
  "processing_time": 45.2
}
```

## 🤖 AI 导演工具

### analyze_content

使用 AI 分析视频内容并提供编辑建议。

**参数:**
- `video_path` (string, 必需): 视频文件路径
- `analysis_focus` (string, 可选): 分析重点，默认 "general"
  - `general`: 通用分析
  - `narrative`: 叙事结构分析
  - `technical`: 技术质量分析
  - `aesthetic`: 美学分析

**响应:**
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

### generate_edit_plan

生成详细的编辑计划。

**参数:**
- `video_analysis` (object, 必需): 视频分析结果
- `editing_objective` (string, 必需): 编辑目标
- `style_preferences` (object, 可选): 风格偏好

**响应:**
```json
{
  "edit_plan": {
    "project_name": "Documentary Edit",
    "estimated_duration": 95.0,
    "complexity_score": 6.5,
    "editing_decisions": [
      {
        "action": "trim",
        "target": "intro_segment",
        "parameters": {
          "start_time": 5.0,
          "end_time": 12.0
        },
        "reasoning": "Remove unnecessary intro content"
      },
      {
        "action": "add_transition",
        "target": "scene_break",
        "parameters": {
          "type": "crossfade",
          "duration": 1.5,
          "position": 45.2
        },
        "reasoning": "Smooth scene transition"
      }
    ]
  }
}
```

## 📁 项目管理工具

### create_project

创建新的视频编辑项目。

**参数:**
- `project_name` (string, 必需): 项目名称
- `description` (string, 可选): 项目描述
- `video_files` (array, 可选): 初始视频文件列表

**响应:**
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

### list_projects

列出所有项目。

**参数:**
- `status` (string, 可选): 项目状态过滤
- `limit` (integer, 可选): 返回数量限制，默认 50

**响应:**
```json
{
  "projects": [
    {
      "id": "proj_abc123",
      "name": "My Video Project",
      "status": "active",
      "created_at": "2024-01-15T10:30:00Z",
      "last_modified": "2024-01-15T14:20:00Z",
      "video_count": 2
    }
  ],
  "total_count": 1,
  "page": 1
}
```

## 🔄 工作流工具

### create_workflow

创建自动化工作流。

**参数:**
- `workflow_name` (string, 必需): 工作流名称
- `steps` (array, 必需): 工作流步骤
- `trigger` (object, 可选): 触发条件

**响应:**
```json
{
  "workflow": {
    "id": "wf_xyz789",
    "name": "Auto Edit Workflow",
    "steps": [
      {
        "step": 1,
        "action": "analyze_video",
        "parameters": {"analysis_type": "comprehensive"}
      },
      {
        "step": 2,
        "action": "detect_scenes",
        "parameters": {"threshold": 0.3}
      }
    ],
    "status": "active",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

## 🔐 认证和安全

### 认证方式

DramaCraft 支持多种认证方式：

1. **JWT Token 认证**
```http
Authorization: Bearer <jwt_token>
```

2. **API Key 认证**
```http
X-API-Key: <api_key>
```

3. **OAuth 2.0**
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

## 📈 性能优化

### 最佳实践

1. **批量处理**: 使用工作流处理多个文件
2. **缓存利用**: 重复分析时利用缓存结果
3. **质量设置**: 根据需求调整处理质量
4. **并发控制**: 合理设置并发处理数量

### 性能指标

| 操作 | 平均响应时间 | 内存使用 |
|------|--------------|----------|
| 视频分析 | < 30秒 | 500MB |
| 场景检测 | < 15秒 | 300MB |
| 音频分析 | < 10秒 | 200MB |
| AI 分析 | < 60秒 | 800MB |

---

**📚 更多信息请参考 [完整文档](https://dramacraft.github.io/docs)**
