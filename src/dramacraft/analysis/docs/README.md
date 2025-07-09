# 📊 视频分析模块

视频分析模块提供深度的视频内容分析功能，包括场景识别、情绪检测、角色分析等核心能力。

## 🎯 模块概述

### 核心功能

- **逐帧分析**: 毫秒级精度的视频内容分析
- **场景识别**: 自动识别场景变化和转换点
- **情绪检测**: 分析视频中的情绪变化和氛围
- **角色分析**: 识别人物、动作和表情变化
- **音频分析**: 语音识别和背景音乐检测

### 主要组件

- `DeepVideoAnalyzer`: 深度视频分析器
- `FrameAnalysis`: 帧分析结果
- `SceneSegment`: 场景片段
- `DeepAnalysisResult`: 完整分析结果

## 🔧 API 参考

### DeepVideoAnalyzer

```python
from dramacraft.analysis.deep_analyzer import DeepVideoAnalyzer

class DeepVideoAnalyzer:
    """深度视频分析器。"""
    
    def __init__(self, llm_client: BaseLLMClient):
        """
        初始化分析器。
        
        Args:
            llm_client: LLM客户端，用于智能分析
        """
    
    async def analyze_video_deeply(
        self, 
        video_path: Path,
        analysis_options: Optional[Dict[str, Any]] = None
    ) -> DeepAnalysisResult:
        """
        深度分析视频内容。
        
        Args:
            video_path: 视频文件路径
            analysis_options: 分析选项配置
            
        Returns:
            完整的分析结果
        """
```

### FrameAnalysis

```python
@dataclass
class FrameAnalysis:
    """单帧分析结果。"""
    
    timestamp: float
    """时间戳(秒)。"""
    
    frame_number: int
    """帧编号。"""
    
    scene_type: str
    """场景类型。"""
    
    dominant_colors: List[str]
    """主要颜色。"""
    
    brightness: float
    """亮度(0-1)。"""
    
    motion_intensity: float
    """运动强度(0-1)。"""
    
    face_count: int
    """人脸数量。"""
    
    objects: List[str]
    """检测到的物体。"""
    
    composition: str
    """画面构图。"""
    
    emotional_tone: str
    """情感基调。"""
```

### SceneSegment

```python
@dataclass
class SceneSegment:
    """场景片段。"""
    
    start_time: float
    """开始时间(秒)。"""
    
    end_time: float
    """结束时间(秒)。"""
    
    scene_id: str
    """场景ID。"""
    
    scene_description: str
    """场景描述。"""
    
    location: str
    """拍摄地点。"""
    
    characters: List[str]
    """出现的角色。"""
    
    actions: List[str]
    """主要动作。"""
    
    dialogue_summary: str
    """对话摘要。"""
    
    emotional_arc: List[str]
    """情感变化。"""
    
    visual_style: str
    """视觉风格。"""
    
    narrative_importance: float
    """叙事重要性(0-1)。"""
```

## 💡 使用示例

### 基础视频分析

```python
import asyncio
from pathlib import Path
from dramacraft.analysis.deep_analyzer import DeepVideoAnalyzer
from dramacraft.llm.factory import create_llm_client
from dramacraft.config import DramaCraftConfig

async def analyze_video_example():
    """视频分析示例。"""
    
    # 初始化配置和LLM客户端
    config = DramaCraftConfig()
    llm_client = create_llm_client(config.llm)
    
    # 创建分析器
    analyzer = DeepVideoAnalyzer(llm_client)
    
    # 分析视频
    video_path = Path("path/to/your/video.mp4")
    result = await analyzer.analyze_video_deeply(video_path)
    
    # 查看分析结果
    print(f"视频时长: {result.total_duration}秒")
    print(f"帧率: {result.frame_rate}fps")
    print(f"分辨率: {result.resolution}")
    print(f"场景数量: {len(result.scene_segments)}")
    
    # 查看场景信息
    for scene in result.scene_segments:
        print(f"场景 {scene.scene_id}: {scene.scene_description}")
        print(f"  时间: {scene.start_time:.1f}s - {scene.end_time:.1f}s")
        print(f"  角色: {', '.join(scene.characters)}")
        print(f"  重要性: {scene.narrative_importance:.2f}")

# 运行示例
asyncio.run(analyze_video_example())
```

### 自定义分析选项

```python
async def custom_analysis_example():
    """自定义分析选项示例。"""
    
    config = DramaCraftConfig()
    llm_client = create_llm_client(config.llm)
    analyzer = DeepVideoAnalyzer(llm_client)
    
    # 自定义分析选项
    analysis_options = {
        "frame_interval": 0.5,  # 每0.5秒分析一帧
        "focus_areas": ["emotions", "characters", "dialogue"],
        "detail_level": "high",
        "include_audio": True,
        "detect_faces": True,
        "analyze_composition": True
    }
    
    video_path = Path("path/to/drama.mp4")
    result = await analyzer.analyze_video_deeply(
        video_path, 
        analysis_options
    )
    
    # 查看详细的帧分析
    for frame in result.frame_analyses[:10]:  # 前10帧
        print(f"帧 {frame.frame_number} ({frame.timestamp:.1f}s):")
        print(f"  场景类型: {frame.scene_type}")
        print(f"  情感基调: {frame.emotional_tone}")
        print(f"  人脸数量: {frame.face_count}")
        print(f"  运动强度: {frame.motion_intensity:.2f}")

asyncio.run(custom_analysis_example())
```

### 批量分析

```python
async def batch_analysis_example():
    """批量分析示例。"""
    
    config = DramaCraftConfig()
    llm_client = create_llm_client(config.llm)
    analyzer = DeepVideoAnalyzer(llm_client)
    
    # 批量分析多个视频
    video_files = [
        Path("episode1.mp4"),
        Path("episode2.mp4"),
        Path("episode3.mp4")
    ]
    
    results = []
    for video_path in video_files:
        print(f"分析视频: {video_path.name}")
        result = await analyzer.analyze_video_deeply(video_path)
        results.append(result)
    
    # 汇总分析结果
    total_duration = sum(r.total_duration for r in results)
    total_scenes = sum(len(r.scene_segments) for r in results)
    
    print(f"批量分析完成:")
    print(f"  视频数量: {len(results)}")
    print(f"  总时长: {total_duration:.1f}秒")
    print(f"  总场景数: {total_scenes}")

asyncio.run(batch_analysis_example())
```

## ⚙️ 配置说明

### 分析选项配置

```python
analysis_options = {
    # 帧分析配置
    "frame_interval": 1.0,          # 帧分析间隔(秒)
    "max_frames": 1000,             # 最大分析帧数
    
    # 分析重点
    "focus_areas": [                # 重点分析领域
        "scenes",                   # 场景分析
        "emotions",                 # 情绪分析
        "characters",               # 角色分析
        "actions",                  # 动作分析
        "dialogue",                 # 对话分析
        "music"                     # 音乐分析
    ],
    
    # 分析深度
    "detail_level": "high",         # 分析详细程度: low/medium/high
    
    # 功能开关
    "include_audio": True,          # 是否包含音频分析
    "detect_faces": True,           # 是否检测人脸
    "analyze_composition": True,    # 是否分析构图
    "extract_colors": True,         # 是否提取颜色
    
    # 性能配置
    "parallel_processing": True,    # 是否并行处理
    "cache_enabled": True,          # 是否启用缓存
    "gpu_acceleration": False       # 是否使用GPU加速
}
```

### 输出格式配置

```python
output_options = {
    "format": "detailed",           # 输出格式: basic/detailed/full
    "include_timestamps": True,     # 是否包含时间戳
    "include_confidence": True,     # 是否包含置信度
    "export_json": True,           # 是否导出JSON
    "export_csv": False,           # 是否导出CSV
    "save_thumbnails": False       # 是否保存缩略图
}
```

## 🔍 故障排除

### 常见问题

**Q: 分析速度很慢怎么办？**
A: 可以调整以下参数：
- 增大 `frame_interval` 减少分析帧数
- 设置 `detail_level` 为 "low" 或 "medium"
- 启用 `parallel_processing`
- 减少 `focus_areas` 的数量

**Q: 内存使用过高？**
A: 尝试以下解决方案：
- 减少 `max_frames` 限制
- 关闭 `cache_enabled`
- 分批处理大文件
- 使用较低的 `detail_level`

**Q: 分析结果不准确？**
A: 检查以下设置：
- 确保视频质量良好
- 调整 `detail_level` 为 "high"
- 检查 LLM 配置是否正确
- 验证视频格式是否支持

### 性能优化建议

1. **合理设置分析间隔**: 根据视频内容调整 `frame_interval`
2. **选择重点分析**: 只启用需要的 `focus_areas`
3. **使用缓存**: 启用 `cache_enabled` 避免重复分析
4. **并行处理**: 启用 `parallel_processing` 提升速度
5. **GPU加速**: 如有条件可启用 `gpu_acceleration`

## 📚 相关文档

- [时间轴同步模块](../sync/docs/README.md)
- [音频处理模块](../audio/docs/README.md)
- [特效生成模块](../effects/docs/README.md)
- [工作流自动化](../workflow/docs/README.md)
