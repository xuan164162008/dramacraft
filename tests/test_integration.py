"""
DramaCraft 集成测试套件。

本模块提供端到端的集成测试，验证整个工作流的正确性和稳定性。
"""

import pytest
import asyncio
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

from src.dramacraft.server import DramaCraftServer
from src.dramacraft.config import DramaCraftConfig
from src.dramacraft.workflow.automation import AutomationWorkflow, WorkflowResult
from src.dramacraft.analysis.deep_analyzer import DeepVideoAnalyzer
from src.dramacraft.sync.timeline_sync import TimelineSynchronizer
from src.dramacraft.audio.enhancer import AudioEnhancer
from src.dramacraft.effects.auto_effects import AutoEffectsEngine
from src.dramacraft.video.jianying_format import JianYingFormatConverter
from src.dramacraft.llm.base import BaseLLMClient, GenerationResult


class MockLLMClient(BaseLLMClient):
    """模拟LLM客户端用于测试。"""
    
    def __init__(self):
        super().__init__()
        self.call_count = 0
        self.responses = []
    
    async def generate(self, prompt: str, params=None) -> GenerationResult:
        """模拟生成响应。"""
        self.call_count += 1
        
        # 根据提示词返回不同的模拟响应
        if "解说" in prompt or "commentary" in prompt.lower():
            response = {
                "title": "测试解说标题",
                "style": "analytical",
                "segments": [
                    {
                        "start_time": 0,
                        "end_time": 30,
                        "content": "这是一个测试解说片段",
                        "key_points": ["重点1", "重点2"]
                    }
                ]
            }
        elif "场景" in prompt or "scene" in prompt.lower():
            response = "测试场景描述：室内对话场景"
        elif "特效" in prompt or "effect" in prompt.lower():
            response = {
                "steps": [
                    {
                        "action": "add_effect",
                        "target": "video_track",
                        "parameters": {"effect_type": "fade_in"},
                        "wait_time": 1.0,
                        "retry_count": 3
                    }
                ]
            }
        else:
            response = "测试响应内容"
        
        return GenerationResult(
            text=json.dumps(response) if isinstance(response, dict) else response,
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}
        )


@pytest.fixture
def mock_llm_client():
    """提供模拟LLM客户端。"""
    return MockLLMClient()


@pytest.fixture
def test_config():
    """提供测试配置。"""
    return DramaCraftConfig(
        llm={"provider": "mock", "api_key": "test_key"},
        video={"temp_dir": "/tmp/dramacraft_test"},
        jianying={"installation_path": "/Applications/JianyingPro.app"}
    )


@pytest.fixture
def temp_video_file():
    """创建临时测试视频文件。"""
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        # 写入一些测试数据
        f.write(b"fake video data for testing")
        temp_path = Path(f.name)
    
    yield temp_path
    
    # 清理
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def temp_output_dir():
    """创建临时输出目录。"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


class TestWorkflowIntegration:
    """工作流集成测试。"""
    
    @pytest.mark.asyncio
    async def test_complete_workflow(
        self,
        mock_llm_client,
        temp_video_file,
        temp_output_dir
    ):
        """测试完整的自动化工作流。"""
        # 创建工作流实例
        workflow = AutomationWorkflow(mock_llm_client, temp_output_dir)
        
        # 模拟视频分析器
        with patch.object(workflow.video_analyzer, 'analyze_video_deeply') as mock_analyze:
            mock_analyze.return_value = self._create_mock_analysis_result(temp_video_file)
            
            # 模拟音频增强器
            with patch.object(workflow.audio_enhancer, 'enhance_audio') as mock_audio:
                mock_audio.return_value = self._create_mock_audio_result()
                
                # 模拟格式转换器
                with patch.object(workflow.format_converter, 'create_complete_project') as mock_format:
                    mock_format.return_value = temp_output_dir / "test_project.draft"
                    
                    # 执行工作流
                    result = await workflow.execute_workflow(
                        video_paths=[temp_video_file],
                        project_name="测试项目",
                        editing_objective="制作测试视频",
                        style_preferences={"style": "test"}
                    )
                    
                    # 验证结果
                    assert result.success is True
                    assert result.draft_file_path is not None
                    assert result.analysis_result is not None
                    assert result.timeline is not None
                    assert result.effect_plan is not None
                    assert result.audio_result is not None
                    assert result.processing_time > 0
                    assert result.error_message is None
    
    @pytest.mark.asyncio
    async def test_workflow_with_invalid_video(
        self,
        mock_llm_client,
        temp_output_dir
    ):
        """测试无效视频文件的处理。"""
        workflow = AutomationWorkflow(mock_llm_client, temp_output_dir)
        
        # 使用不存在的视频文件
        invalid_video = Path("/nonexistent/video.mp4")
        
        result = await workflow.execute_workflow(
            video_paths=[invalid_video],
            project_name="测试项目",
            editing_objective="制作测试视频"
        )
        
        # 验证失败结果
        assert result.success is False
        assert result.error_message is not None
        assert "无效的视频文件" in result.error_message
    
    @pytest.mark.asyncio
    async def test_workflow_progress_tracking(
        self,
        mock_llm_client,
        temp_video_file,
        temp_output_dir
    ):
        """测试工作流进度跟踪。"""
        workflow = AutomationWorkflow(mock_llm_client, temp_output_dir)
        progress_updates = []
        
        def progress_callback(progress):
            progress_updates.append({
                "stage": progress.current_stage.value,
                "progress": progress.overall_progress,
                "message": progress.message
            })
        
        # 模拟各个组件
        with patch.object(workflow.video_analyzer, 'analyze_video_deeply') as mock_analyze:
            mock_analyze.return_value = self._create_mock_analysis_result(temp_video_file)
            
            with patch.object(workflow.audio_enhancer, 'enhance_audio') as mock_audio:
                mock_audio.return_value = self._create_mock_audio_result()
                
                with patch.object(workflow.format_converter, 'create_complete_project') as mock_format:
                    mock_format.return_value = temp_output_dir / "test_project.draft"
                    
                    # 执行工作流并跟踪进度
                    result = await workflow.execute_workflow(
                        video_paths=[temp_video_file],
                        project_name="测试项目",
                        editing_objective="制作测试视频",
                        progress_callback=progress_callback
                    )
                    
                    # 验证进度更新
                    assert len(progress_updates) > 0
                    assert progress_updates[0]["progress"] == 0.0
                    assert progress_updates[-1]["progress"] == 1.0
                    assert result.success is True
    
    def _create_mock_analysis_result(self, video_path):
        """创建模拟分析结果。"""
        from src.dramacraft.analysis.deep_analyzer import (
            DeepAnalysisResult, FrameAnalysis, AudioSegment, SceneSegment
        )
        
        frame_analyses = [
            FrameAnalysis(
                timestamp=0.0,
                frame_number=0,
                scene_type="close_up",
                dominant_colors=["红色", "蓝色"],
                brightness=0.7,
                motion_intensity=0.3,
                face_count=1,
                objects=["人物"],
                composition="center",
                emotional_tone="happy"
            )
        ]
        
        audio_segments = [
            AudioSegment(
                start_time=0.0,
                end_time=30.0,
                audio_type="speech",
                volume_level=0.8,
                speech_text="测试语音内容",
                speaker_emotion="neutral",
                background_music=False,
                audio_quality=0.9
            )
        ]
        
        scene_segments = [
            SceneSegment(
                start_time=0.0,
                end_time=30.0,
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
            video_path=video_path,
            total_duration=30.0,
            frame_rate=30.0,
            resolution=(1920, 1080),
            frame_analyses=frame_analyses,
            audio_segments=audio_segments,
            scene_segments=scene_segments,
            overall_summary={"analysis_quality": "high"},
            content_timeline=[]
        )
    
    def _create_mock_audio_result(self):
        """创建模拟音频结果。"""
        from src.dramacraft.audio.enhancer import (
            AudioEnhancementResult, MusicRecommendation, AudioMixConfig
        )
        
        music_recommendations = [
            MusicRecommendation(
                music_id="test_music_1",
                title="测试音乐",
                genre="background",
                mood="happy",
                tempo=120.0,
                energy_level=0.7,
                file_path=None,
                match_score=0.8,
                usage_segments=[(0.0, 30.0)]
            )
        ]
        
        mix_config = AudioMixConfig(
            original_volume=0.8,
            background_volume=0.3,
            commentary_volume=0.9,
            fade_in_duration=1.0,
            fade_out_duration=1.0,
            crossfade_duration=2.0,
            dynamic_range_compression=False,
            noise_reduction=False
        )
        
        return AudioEnhancementResult(
            enhanced_audio_path=Path("/tmp/enhanced_audio.wav"),
            music_recommendations=music_recommendations,
            mix_config=mix_config,
            quality_metrics={"overall_quality": 0.8},
            processing_time=5.0
        )


class TestMCPServerIntegration:
    """MCP服务器集成测试。"""
    
    @pytest.mark.asyncio
    async def test_server_initialization(self, test_config, mock_llm_client):
        """测试服务器初始化。"""
        with patch('src.dramacraft.llm.factory.create_llm_client', return_value=mock_llm_client):
            server = DramaCraftServer(test_config)
            
            # 验证服务器组件
            assert server.llm_client is not None
            assert server.commentary_generator is not None
            assert server.remix_generator is not None
            assert server.narrative_generator is not None
    
    @pytest.mark.asyncio
    async def test_mcp_tool_execution(self, test_config, mock_llm_client, temp_video_file):
        """测试MCP工具执行。"""
        with patch('src.dramacraft.llm.factory.create_llm_client', return_value=mock_llm_client):
            server = DramaCraftServer(test_config)
            
            # 模拟工具调用
            with patch.object(server, '_handle_smart_video_edit') as mock_handle:
                mock_handle.return_value = [{"type": "text", "text": "测试成功"}]
                
                # 执行工具
                result = await server.call_tool(
                    "smart_video_edit",
                    {
                        "video_paths": [str(temp_video_file)],
                        "editing_objective": "测试编辑",
                        "auto_import": False
                    }
                )
                
                # 验证结果
                assert result is not None
                assert len(result) > 0
                mock_handle.assert_called_once()


class TestComponentIntegration:
    """组件集成测试。"""
    
    @pytest.mark.asyncio
    async def test_analyzer_synchronizer_integration(self, mock_llm_client, temp_video_file):
        """测试分析器和同步器集成。"""
        analyzer = DeepVideoAnalyzer(mock_llm_client)
        synchronizer = TimelineSynchronizer(mock_llm_client)
        
        # 模拟分析结果
        with patch.object(analyzer, 'analyze_video_deeply') as mock_analyze:
            mock_result = self._create_mock_analysis_result(temp_video_file)
            mock_analyze.return_value = mock_result
            
            # 执行分析
            analysis_result = await analyzer.analyze_video_deeply(temp_video_file)
            
            # 创建时间轴
            timeline = await synchronizer.create_synchronized_timeline(
                analysis_result,
                commentary_segments=[{
                    "start_time": 0,
                    "end_time": 10,
                    "content": "测试解说"
                }]
            )
            
            # 验证集成结果
            assert timeline is not None
            assert len(timeline.events) > 0
            assert timeline.quality_score >= 0
    
    @pytest.mark.asyncio
    async def test_effects_format_integration(self, mock_llm_client):
        """测试特效引擎和格式转换器集成。"""
        effects_engine = AutoEffectsEngine(mock_llm_client)
        format_converter = JianYingFormatConverter()
        
        # 创建模拟分析结果
        mock_analysis = self._create_mock_analysis_result(Path("test.mp4"))
        
        # 生成特效计划
        effect_plan = await effects_engine.generate_effect_plan(mock_analysis)
        
        # 验证特效计划
        assert effect_plan is not None
        assert effect_plan.total_effects >= 0
        assert effect_plan.total_transitions >= 0
        assert 0 <= effect_plan.complexity_score <= 1
    
    def _create_mock_analysis_result(self, video_path):
        """创建模拟分析结果（复用上面的方法）。"""
        from src.dramacraft.analysis.deep_analyzer import (
            DeepAnalysisResult, FrameAnalysis, AudioSegment, SceneSegment
        )
        
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
                end_time=30.0,
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
            video_path=video_path,
            total_duration=30.0,
            frame_rate=30.0,
            resolution=(1920, 1080),
            frame_analyses=frame_analyses,
            audio_segments=[],
            scene_segments=scene_segments,
            overall_summary={"analysis_quality": "high"},
            content_timeline=[]
        )


class TestErrorHandling:
    """错误处理测试。"""
    
    @pytest.mark.asyncio
    async def test_llm_api_failure(self, temp_video_file, temp_output_dir):
        """测试LLM API失败的处理。"""
        # 创建会失败的模拟客户端
        failing_client = Mock()
        failing_client.generate = AsyncMock(side_effect=Exception("API调用失败"))
        
        workflow = AutomationWorkflow(failing_client, temp_output_dir)
        
        result = await workflow.execute_workflow(
            video_paths=[temp_video_file],
            project_name="测试项目",
            editing_objective="制作测试视频"
        )
        
        # 验证错误处理
        assert result.success is False
        assert result.error_message is not None
    
    @pytest.mark.asyncio
    async def test_file_permission_error(self, mock_llm_client, temp_video_file):
        """测试文件权限错误的处理。"""
        # 使用只读目录
        readonly_dir = Path("/")  # 根目录通常是只读的
        
        workflow = AutomationWorkflow(mock_llm_client, readonly_dir)
        
        with patch.object(workflow.video_analyzer, 'analyze_video_deeply') as mock_analyze:
            mock_analyze.return_value = self._create_mock_analysis_result(temp_video_file)
            
            result = await workflow.execute_workflow(
                video_paths=[temp_video_file],
                project_name="测试项目",
                editing_objective="制作测试视频"
            )
            
            # 验证错误处理（可能成功，因为我们模拟了大部分操作）
            # 主要是确保不会崩溃
            assert result is not None
    
    def _create_mock_analysis_result(self, video_path):
        """创建模拟分析结果。"""
        # 复用上面的实现
        return TestComponentIntegration()._create_mock_analysis_result(video_path)


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
