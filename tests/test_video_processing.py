"""
视频处理测试模块。

测试视频分析、处理和剪映集成功能。
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from src.dramacraft.video.processor import VideoProcessor
from src.dramacraft.video.jianying_format import JianYingFormatConverter, JianYingCompatibilityChecker
from src.dramacraft.video.jianying_control import JianYingController, JianYingCommand, JianYingOperation
from src.dramacraft.analysis.deep_analyzer import DeepVideoAnalyzer, FrameAnalysis, SceneSegment


class TestVideoProcessor:
    """视频处理器测试。"""
    
    @pytest.fixture
    def video_processor(self):
        """视频处理器实例。"""
        return VideoProcessor()
    
    @pytest.fixture
    def sample_video_path(self):
        """示例视频路径。"""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            # 写入一些测试数据
            f.write(b"fake video data")
            return Path(f.name)
    
    def test_processor_initialization(self, video_processor):
        """测试处理器初始化。"""
        assert video_processor is not None
        assert hasattr(video_processor, 'logger')
    
    def test_get_video_info_invalid_file(self, video_processor):
        """测试获取无效视频文件信息。"""
        invalid_path = Path("/nonexistent/video.mp4")
        
        with pytest.raises(FileNotFoundError):
            video_processor.get_video_info(invalid_path)
    
    @patch('cv2.VideoCapture')
    def test_get_video_info_success(self, mock_cv2, video_processor, sample_video_path):
        """测试成功获取视频信息。"""
        # 模拟OpenCV VideoCapture
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            0: 30.0,    # CAP_PROP_FPS
            1: 1920.0,  # CAP_PROP_FRAME_WIDTH
            2: 1080.0,  # CAP_PROP_FRAME_HEIGHT
            7: 900.0,   # CAP_PROP_FRAME_COUNT
        }.get(prop, 0.0)
        mock_cv2.return_value = mock_cap
        
        info = video_processor.get_video_info(sample_video_path)
        
        assert info["fps"] == 30.0
        assert info["width"] == 1920.0
        assert info["height"] == 1080.0
        assert info["duration"] == 30.0  # 900 frames / 30 fps
    
    @patch('cv2.VideoCapture')
    def test_extract_frames(self, mock_cv2, video_processor, sample_video_path):
        """测试提取视频帧。"""
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.side_effect = [
            (True, np.zeros((1080, 1920, 3), dtype=np.uint8)),
            (True, np.zeros((1080, 1920, 3), dtype=np.uint8)),
            (False, None)
        ]
        mock_cv2.return_value = mock_cap
        
        frames = video_processor.extract_frames(sample_video_path, max_frames=2)
        
        assert len(frames) == 2
        assert all(isinstance(frame, np.ndarray) for frame in frames)
    
    def test_detect_scenes_empty_frames(self, video_processor):
        """测试空帧列表的场景检测。"""
        scenes = video_processor.detect_scenes([])
        assert scenes == []
    
    def test_detect_scenes_single_frame(self, video_processor):
        """测试单帧场景检测。"""
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        scenes = video_processor.detect_scenes([frame])
        
        assert len(scenes) == 1
        assert scenes[0]["start_frame"] == 0
        assert scenes[0]["end_frame"] == 0


class TestJianYingFormatConverter:
    """剪映格式转换器测试。"""
    
    @pytest.fixture
    def converter(self):
        """格式转换器实例。"""
        return JianYingFormatConverter()
    
    @pytest.fixture
    def sample_analysis_result(self):
        """示例分析结果。"""
        from src.dramacraft.analysis.deep_analyzer import DeepAnalysisResult
        
        frame_analyses = [
            FrameAnalysis(
                timestamp=0.0,
                frame_number=0,
                scene_type="close_up",
                dominant_colors=["红色"],
                brightness=0.7,
                motion_intensity=0.3,
                face_count=1,
                objects=["人物"],
                composition="center",
                emotional_tone="happy"
            )
        ]
        
        scene_segments = [
            SceneSegment(
                start_time=0.0,
                end_time=10.0,
                scene_id="scene_1",
                scene_description="测试场景",
                location="室内",
                characters=["主角"],
                actions=["对话"],
                dialogue_summary="测试对话",
                emotional_arc=["happy"],
                visual_style="close_up",
                narrative_importance=0.8
            )
        ]
        
        return DeepAnalysisResult(
            video_path=Path("test.mp4"),
            total_duration=10.0,
            frame_rate=30.0,
            resolution=(1920, 1080),
            frame_analyses=frame_analyses,
            audio_segments=[],
            scene_segments=scene_segments,
            overall_summary={"quality": "high"},
            content_timeline=[]
        )
    
    def test_converter_initialization(self, converter):
        """测试转换器初始化。"""
        assert converter.jianying_version == "4.0.0"
        assert converter.time_scale == 1000000
    
    def test_create_basic_project_structure(self, converter):
        """测试创建基础项目结构。"""
        project_data = converter._create_basic_project_structure()
        
        assert "version" in project_data
        assert "tracks" in project_data
        assert "materials" in project_data
        assert "canvases" in project_data
        assert project_data["version"] == "4.0.0"
    
    def test_convert_time_to_jianying(self, converter):
        """测试时间转换。"""
        # 测试秒转换为剪映时间单位
        jy_time = converter._convert_time_to_jianying(1.5)  # 1.5秒
        assert jy_time == 1500000  # 1.5 * 1000000
    
    def test_create_video_track(self, converter, sample_analysis_result):
        """测试创建视频轨道。"""
        video_path = Path("test.mp4")
        track = converter._create_video_track(video_path, sample_analysis_result)
        
        assert track["type"] == "video"
        assert len(track["segments"]) > 0
        
        segment = track["segments"][0]
        assert "material_id" in segment
        assert "target_timerange" in segment
        assert "source_timerange" in segment
    
    def test_create_subtitle_track(self, converter):
        """测试创建字幕轨道。"""
        subtitles = [
            {"start_time": 0.0, "end_time": 2.0, "text": "测试字幕1"},
            {"start_time": 2.0, "end_time": 4.0, "text": "测试字幕2"}
        ]
        
        track = converter._create_subtitle_track(subtitles)
        
        assert track["type"] == "text"
        assert len(track["segments"]) == 2
        
        for i, segment in enumerate(track["segments"]):
            assert segment["content"] == subtitles[i]["text"]
    
    def test_create_complete_project(self, converter, sample_analysis_result):
        """测试创建完整项目。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            video_path = Path("test.mp4")
            
            # 创建模拟视频文件
            (output_dir / "test.mp4").write_bytes(b"fake video")
            
            draft_file = converter.create_complete_project(
                video_paths=[video_path],
                analysis_result=sample_analysis_result,
                output_dir=output_dir,
                project_name="测试项目"
            )
            
            assert draft_file.exists()
            assert draft_file.suffix == ".draft"


class TestJianYingCompatibilityChecker:
    """剪映兼容性检查器测试。"""
    
    @pytest.fixture
    def checker(self):
        """兼容性检查器实例。"""
        return JianYingCompatibilityChecker()
    
    def test_checker_initialization(self, checker):
        """测试检查器初始化。"""
        assert len(checker.supported_versions) > 0
        assert "4.0.0" in checker.supported_versions
        assert checker.format_limits["max_tracks"] > 0
    
    def test_check_version_compatibility(self, checker):
        """测试版本兼容性检查。"""
        # 支持的版本
        assert checker.check_version_compatibility("4.0.0") is True
        assert checker.check_version_compatibility("3.8.0") is True
        
        # 不支持的版本
        assert checker.check_version_compatibility("2.0.0") is False
        assert checker.check_version_compatibility("5.0.0") is False
    
    def test_validate_project_structure(self, checker):
        """测试项目结构验证。"""
        valid_project = {
            "version": "4.0.0",
            "tracks": [],
            "materials": {},
            "canvases": []
        }
        
        result = checker.validate_project_structure(valid_project)
        assert result["valid"] is True
        assert len(result["errors"]) == 0
        
        # 无效项目
        invalid_project = {
            "version": "4.0.0"
            # 缺少必需字段
        }
        
        result = checker.validate_project_structure(invalid_project)
        assert result["valid"] is False
        assert len(result["errors"]) > 0
    
    def test_validate_draft_file(self, checker):
        """测试草稿文件验证。"""
        with tempfile.NamedTemporaryFile(suffix=".draft", delete=False) as f:
            draft_path = Path(f.name)
            f.write(b"fake draft content")
        
        try:
            result = checker.validate_draft_file(draft_path)
            # 由于是假文件，应该有错误
            assert result["valid"] is False
        finally:
            draft_path.unlink()


class TestJianYingController:
    """剪映控制器测试。"""
    
    @pytest.fixture
    def controller(self):
        """剪映控制器实例。"""
        return JianYingController()
    
    def test_controller_initialization(self, controller):
        """测试控制器初始化。"""
        assert controller.current_status is not None
        assert controller.operation_history == []
        assert hasattr(controller, 'project_manager')
    
    @pytest.mark.asyncio
    async def test_execute_import_command(self, controller):
        """测试执行导入命令。"""
        with tempfile.NamedTemporaryFile(suffix=".draft", delete=False) as f:
            draft_path = Path(f.name)
            f.write(b"fake draft")
        
        try:
            command = JianYingCommand(
                operation=JianYingOperation.IMPORT_PROJECT,
                parameters={
                    "draft_file": str(draft_path),
                    "project_name": "测试项目",
                    "auto_open": False
                }
            )
            
            with patch.object(controller.project_manager, 'import_project', return_value=True):
                result = await controller.execute_command(command)
                assert result is True
                assert controller.current_status.current_project == "测试项目"
        finally:
            draft_path.unlink()
    
    @pytest.mark.asyncio
    async def test_execute_batch_commands(self, controller):
        """测试批量执行命令。"""
        commands = [
            JianYingCommand(
                operation=JianYingOperation.SAVE_PROJECT,
                parameters={"project_name": "项目1"}
            ),
            JianYingCommand(
                operation=JianYingOperation.SAVE_PROJECT,
                parameters={"project_name": "项目2"}
            )
        ]
        
        results = await controller.execute_batch_commands(commands)
        
        assert len(results) == 2
        assert all(results)  # 所有命令都应该成功（模拟）
    
    def test_create_automation_script(self, controller):
        """测试创建自动化脚本。"""
        commands = [
            JianYingCommand(
                operation=JianYingOperation.IMPORT_PROJECT,
                parameters={"draft_file": "test.draft"}
            )
        ]
        
        script = controller.create_automation_script(commands)
        script_data = json.loads(script)
        
        assert script_data["version"] == "1.0"
        assert len(script_data["commands"]) == 1
        assert script_data["commands"][0]["operation"] == "import_project"
    
    def test_load_automation_script(self, controller):
        """测试加载自动化脚本。"""
        script_data = {
            "version": "1.0",
            "commands": [
                {
                    "operation": "import_project",
                    "parameters": {"draft_file": "test.draft"},
                    "wait_time": 2.0,
                    "retry_count": 5
                }
            ]
        }
        
        script_content = json.dumps(script_data)
        commands = controller.load_automation_script(script_content)
        
        assert len(commands) == 1
        assert commands[0].operation == JianYingOperation.IMPORT_PROJECT
        assert commands[0].wait_time == 2.0
        assert commands[0].retry_count == 5
    
    def test_get_operation_history(self, controller):
        """测试获取操作历史。"""
        # 添加一些历史记录
        controller.operation_history = [
            {"operation": "test1", "success": True, "timestamp": 1000},
            {"operation": "test2", "success": False, "timestamp": 2000},
            {"operation": "test3", "success": True, "timestamp": 3000}
        ]
        
        history = controller.get_operation_history(limit=2)
        assert len(history) == 2
        assert history[0]["operation"] == "test2"  # 最近的两个
        assert history[1]["operation"] == "test3"


class TestVideoAnalysisIntegration:
    """视频分析集成测试。"""
    
    @pytest.mark.asyncio
    async def test_video_to_jianying_workflow(self):
        """测试从视频到剪映的完整工作流。"""
        # 创建模拟组件
        from src.dramacraft.llm.base import BaseLLMClient, GenerationResult
        
        class MockLLMClient(BaseLLMClient):
            async def generate(self, prompt: str, params=None) -> GenerationResult:
                return GenerationResult(text="模拟分析结果", usage={})
        
        llm_client = MockLLMClient()
        analyzer = DeepVideoAnalyzer(llm_client)
        converter = JianYingFormatConverter()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 创建模拟视频文件
            video_path = temp_path / "test.mp4"
            video_path.write_bytes(b"fake video data")
            
            # 模拟分析过程
            with patch.object(analyzer, 'analyze_video_deeply') as mock_analyze:
                # 创建模拟分析结果
                mock_result = Mock()
                mock_result.video_path = video_path
                mock_result.total_duration = 10.0
                mock_result.frame_rate = 30.0
                mock_result.resolution = (1920, 1080)
                mock_result.scene_segments = []
                mock_result.frame_analyses = []
                mock_result.audio_segments = []
                mock_result.overall_summary = {}
                mock_result.content_timeline = []
                
                mock_analyze.return_value = mock_result
                
                # 执行分析
                analysis_result = await analyzer.analyze_video_deeply(video_path)
                
                # 创建剪映项目
                draft_file = converter.create_complete_project(
                    video_paths=[video_path],
                    analysis_result=analysis_result,
                    output_dir=temp_path,
                    project_name="集成测试项目"
                )
                
                # 验证结果
                assert draft_file.exists()
                assert draft_file.suffix == ".draft"
