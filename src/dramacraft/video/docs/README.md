# 🎬 视频处理模块

视频处理模块提供完整的视频处理和剪映集成功能，包括视频分析、格式转换、项目管理等核心能力。

## 🎯 模块概述

### 核心功能

- **视频处理**: 基础的视频读取、分析和处理
- **剪映格式**: 完整的剪映.draft文件生成和兼容性
- **项目管理**: 剪映项目的创建、导入和管理
- **自动化控制**: 剪映软件的自动化操作控制

### 主要组件

- `VideoProcessor`: 基础视频处理器
- `JianYingFormatConverter`: 剪映格式转换器
- `JianYingProjectManager`: 剪映项目管理器
- `JianYingController`: 剪映控制器
- `JianYingCompatibilityChecker`: 兼容性检查器

## 🔧 API 参考

### VideoProcessor

```python
from dramacraft.video.processor import VideoProcessor

class VideoProcessor:
    """视频处理器。"""
    
    def get_video_info(self, video_path: Path) -> Dict[str, Any]:
        """
        获取视频基本信息。
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            视频信息字典
        """
    
    def extract_frames(
        self, 
        video_path: Path, 
        max_frames: int = 100
    ) -> List[np.ndarray]:
        """
        提取视频帧。
        
        Args:
            video_path: 视频文件路径
            max_frames: 最大提取帧数
            
        Returns:
            帧数据列表
        """
    
    def detect_scenes(self, frames: List[np.ndarray]) -> List[Dict[str, Any]]:
        """
        检测场景变化。
        
        Args:
            frames: 视频帧列表
            
        Returns:
            场景信息列表
        """
```

### JianYingFormatConverter

```python
from dramacraft.video.jianying_format import JianYingFormatConverter

class JianYingFormatConverter:
    """剪映格式转换器。"""
    
    def __init__(self, jianying_version: str = "4.0.0"):
        """
        初始化转换器。
        
        Args:
            jianying_version: 剪映版本
        """
    
    def create_complete_project(
        self,
        video_paths: List[Path],
        analysis_result: DeepAnalysisResult,
        output_dir: Path,
        project_name: str,
        **kwargs
    ) -> Path:
        """
        创建完整的剪映项目。
        
        Args:
            video_paths: 视频文件路径列表
            analysis_result: 视频分析结果
            output_dir: 输出目录
            project_name: 项目名称
            
        Returns:
            生成的.draft文件路径
        """
```

### JianYingProjectManager

```python
from dramacraft.video.jianying_format import JianYingProjectManager

class JianYingProjectManager:
    """剪映项目管理器。"""
    
    def __init__(self, jianying_path: Optional[Path] = None):
        """
        初始化项目管理器。
        
        Args:
            jianying_path: 剪映安装路径
        """
    
    def import_project(
        self, 
        draft_file: Path, 
        project_name: Optional[str] = None
    ) -> bool:
        """
        导入项目到剪映。
        
        Args:
            draft_file: 草稿文件路径
            project_name: 项目名称
            
        Returns:
            是否导入成功
        """
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """
        列出所有剪映项目。
        
        Returns:
            项目信息列表
        """
```

## 💡 使用示例

### 基础视频处理

```python
import asyncio
from pathlib import Path
from dramacraft.video.processor import VideoProcessor

def basic_video_processing():
    """基础视频处理示例。"""
    
    processor = VideoProcessor()
    video_path = Path("path/to/your/video.mp4")
    
    # 获取视频信息
    info = processor.get_video_info(video_path)
    print(f"视频信息:")
    print(f"  时长: {info['duration']:.1f}秒")
    print(f"  分辨率: {info['width']}x{info['height']}")
    print(f"  帧率: {info['fps']}fps")
    
    # 提取关键帧
    frames = processor.extract_frames(video_path, max_frames=50)
    print(f"提取了 {len(frames)} 帧")
    
    # 检测场景
    scenes = processor.detect_scenes(frames)
    print(f"检测到 {len(scenes)} 个场景")
    
    for i, scene in enumerate(scenes):
        print(f"  场景 {i+1}: 帧 {scene['start_frame']}-{scene['end_frame']}")

# 运行示例
basic_video_processing()
```

### 创建剪映项目

```python
import asyncio
from pathlib import Path
from dramacraft.video.jianying_format import JianYingFormatConverter
from dramacraft.analysis.deep_analyzer import DeepVideoAnalyzer
from dramacraft.llm.factory import create_llm_client
from dramacraft.config import DramaCraftConfig

async def create_jianying_project():
    """创建剪映项目示例。"""
    
    # 初始化组件
    config = DramaCraftConfig()
    llm_client = create_llm_client(config.llm)
    analyzer = DeepVideoAnalyzer(llm_client)
    converter = JianYingFormatConverter()
    
    # 分析视频
    video_path = Path("path/to/drama.mp4")
    analysis_result = await analyzer.analyze_video_deeply(video_path)
    
    # 创建剪映项目
    output_dir = Path("./output")
    project_name = "我的短剧项目"
    
    draft_file = converter.create_complete_project(
        video_paths=[video_path],
        analysis_result=analysis_result,
        output_dir=output_dir,
        project_name=project_name,
        include_subtitles=True,
        include_music=True
    )
    
    print(f"剪映项目已创建: {draft_file}")

asyncio.run(create_jianying_project())
```

### 项目管理

```python
from dramacraft.video.jianying_format import JianYingProjectManager

def project_management_example():
    """项目管理示例。"""
    
    # 初始化项目管理器
    manager = JianYingProjectManager()
    
    # 列出现有项目
    projects = manager.list_projects()
    print(f"现有项目数量: {len(projects)}")
    
    for project in projects[:5]:  # 显示前5个项目
        print(f"项目: {project['name']}")
        print(f"  创建时间: {project['created_time']}")
        print(f"  文件大小: {project['size']} bytes")
    
    # 导入新项目
    draft_file = Path("output/my_project.draft")
    if draft_file.exists():
        success = manager.import_project(draft_file, "新导入的项目")
        if success:
            print("项目导入成功！")
        else:
            print("项目导入失败")
    
    # 备份项目
    backup_dir = Path("./backups")
    backup_file = manager.backup_project("我的项目", backup_dir)
    if backup_file:
        print(f"项目备份完成: {backup_file}")

project_management_example()
```

### 自动化控制

```python
import asyncio
from dramacraft.video.jianying_control import (
    JianYingController, 
    JianYingCommand, 
    JianYingOperation
)

async def automation_control_example():
    """自动化控制示例。"""
    
    controller = JianYingController()
    
    # 创建命令序列
    commands = [
        # 导入项目
        JianYingCommand(
            operation=JianYingOperation.IMPORT_PROJECT,
            parameters={
                "draft_file": "output/project.draft",
                "project_name": "自动化项目"
            }
        ),
        
        # 添加字幕
        JianYingCommand(
            operation=JianYingOperation.ADD_SUBTITLE,
            parameters={
                "text": "这是自动添加的字幕",
                "start_time": 0,
                "end_time": 5
            }
        ),
        
        # 保存项目
        JianYingCommand(
            operation=JianYingOperation.SAVE_PROJECT,
            parameters={
                "project_name": "自动化项目"
            }
        )
    ]
    
    # 批量执行命令
    results = await controller.execute_batch_commands(commands)
    
    for i, result in enumerate(results):
        status = "成功" if result else "失败"
        print(f"命令 {i+1}: {status}")
    
    # 查看操作历史
    history = controller.get_operation_history()
    print(f"操作历史: {len(history)} 条记录")

asyncio.run(automation_control_example())
```

## ⚙️ 配置说明

### 视频处理配置

```python
video_config = {
    # 基础配置
    "temp_dir": "./temp",              # 临时文件目录
    "output_dir": "./output",          # 输出目录
    "cache_dir": "./cache",            # 缓存目录
    
    # 文件限制
    "max_file_size_mb": 500,           # 最大文件大小(MB)
    "supported_formats": [             # 支持的格式
        "mp4", "avi", "mov", "mkv", "wmv"
    ],
    
    # 处理参数
    "frame_extraction_interval": 1.0,  # 帧提取间隔(秒)
    "max_frames_per_video": 1000,     # 每个视频最大帧数
    "scene_detection_threshold": 0.3,  # 场景检测阈值
    
    # 质量设置
    "video_quality": "high",           # 视频质量: low/medium/high
    "audio_quality": "high",           # 音频质量: low/medium/high
    "compression_level": 5,            # 压缩级别(1-10)
    
    # 性能配置
    "parallel_processing": True,       # 并行处理
    "gpu_acceleration": False,         # GPU加速
    "memory_limit_mb": 2048           # 内存限制(MB)
}
```

### 剪映集成配置

```python
jianying_config = {
    # 安装配置
    "installation_path": "/Applications/JianyingPro.app",  # 剪映安装路径
    "projects_dir": "~/Movies/JianyingPro",                # 项目目录
    "version": "4.0.0",                                    # 剪映版本
    
    # 项目设置
    "auto_backup": True,               # 自动备份
    "backup_dir": "./backups",         # 备份目录
    "max_backups": 10,                 # 最大备份数量
    
    # 兼容性设置
    "supported_versions": [            # 支持的版本
        "4.0.0", "3.8.0", "3.7.0"
    ],
    "format_limits": {                 # 格式限制
        "max_tracks": 20,              # 最大轨道数
        "max_clips": 1000,             # 最大片段数
        "max_duration": 7200           # 最大时长(秒)
    },
    
    # 自动化配置
    "auto_import": True,               # 自动导入
    "auto_open": False,                # 自动打开
    "wait_timeout": 30,                # 等待超时(秒)
    "retry_count": 3                   # 重试次数
}
```

## 🔍 故障排除

### 常见问题

**Q: 视频文件无法读取？**
A: 检查以下问题：
- 确认文件格式在支持列表中
- 检查文件是否损坏
- 验证文件权限
- 确认FFmpeg正确安装

**Q: 剪映项目导入失败？**
A: 尝试以下解决方案：
- 检查剪映是否正确安装
- 验证.draft文件格式
- 确认项目目录权限
- 检查剪映版本兼容性

**Q: 场景检测不准确？**
A: 调整以下参数：
- 修改 `scene_detection_threshold`
- 增加 `frame_extraction_interval`
- 提高视频质量设置
- 检查视频内容质量

**Q: 处理速度慢？**
A: 优化方法：
- 启用 `parallel_processing`
- 减少 `max_frames_per_video`
- 启用 `gpu_acceleration`
- 调整 `compression_level`

### 性能优化

1. **并行处理**: 启用多线程处理提升速度
2. **GPU加速**: 使用GPU加速视频处理
3. **缓存策略**: 缓存中间结果避免重复计算
4. **内存管理**: 合理设置内存限制
5. **格式优化**: 选择合适的视频格式和质量

### 兼容性检查

```python
from dramacraft.video.jianying_format import JianYingCompatibilityChecker

def check_compatibility():
    """检查兼容性。"""
    checker = JianYingCompatibilityChecker()
    
    # 检查版本兼容性
    version_ok = checker.check_version_compatibility("4.0.0")
    print(f"版本兼容性: {version_ok}")
    
    # 验证项目结构
    project_data = {...}  # 项目数据
    result = checker.validate_project_structure(project_data)
    
    if result["valid"]:
        print("项目结构验证通过")
    else:
        print(f"验证失败: {result['errors']}")
```

## 📚 相关文档

- [视频分析模块](../analysis/docs/README.md)
- [自动化引擎](../automation/docs/README.md)
- [配置管理](../../config.py)
- [使用示例](../../../examples/video_examples.py)
