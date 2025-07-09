"""
测试系列合集制作功能
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.dramacraft.tools.series_compilation import SeriesCompilationTool
from src.dramacraft.models.series import (
    SeriesInfo, EpisodeInfo, SeriesMetadata, CompilationSettings,
    SeriesProcessingConfig, ProcessingStatus
)
from src.dramacraft.config.json_schemas import SeriesCompilationConfig


class TestSeriesCompilationTool:
    """系列合集制作工具测试"""
    
    @pytest.fixture
    def config(self):
        """创建测试配置"""
        return SeriesProcessingConfig(
            enable_deep_analysis=True,
            parallel_processing=True,
            max_concurrent_episodes=2
        )
    
    @pytest.fixture
    def tool(self, config):
        """创建测试工具实例"""
        return SeriesCompilationTool(config)
    
    @pytest.fixture
    def sample_video_paths(self, tmp_path):
        """创建示例视频文件路径"""
        video_paths = []
        for i in range(3):
            video_file = tmp_path / f"episode_{i+1}.mp4"
            video_file.write_text("fake video content")
            video_paths.append(str(video_file))
        return video_paths
    
    def test_tool_definition(self, tool):
        """测试工具定义"""
        definition = tool.get_tool_definition()
        
        assert definition.name == "create_series_compilation"
        assert "多集智能合并" in definition.description
        assert "video_paths" in definition.inputSchema["properties"]
        assert "series_title" in definition.inputSchema["properties"]
        assert definition.inputSchema["required"] == ["video_paths", "series_title"]
    
    @pytest.mark.asyncio
    async def test_create_series_info(self, tool, sample_video_paths):
        """测试创建系列信息"""
        params = SeriesCompilationConfig(
            video_paths=sample_video_paths,
            series_title="测试系列",
            target_duration=120.0
        )
        
        with patch.object(tool.file_manager, 'get_video_info') as mock_get_info:
            mock_get_info.return_value = {
                "duration": 60.0,
                "resolution": "1920x1080",
                "fps": 30.0,
                "file_size": 1000000,
                "format": "mp4",
                "width": 1920,
                "height": 1080
            }
            
            series_info = await tool._create_series_info(params)
            
            assert series_info.metadata.title == "测试系列"
            assert len(series_info.episodes) == 3
            assert series_info.total_episodes == 3
            assert series_info.total_duration == 180.0  # 3 * 60.0
            assert series_info.status == ProcessingStatus.PENDING
    
    @pytest.mark.asyncio
    async def test_analyze_single_episode(self, tool):
        """测试单集分析"""
        episode = EpisodeInfo(
            index=0,
            title="第1集",
            file_path=Path("test.mp4"),
            duration=60.0,
            resolution="1920x1080",
            fps=30.0,
            file_size=1000000,
            format="mp4"
        )
        
        with patch.object(tool.analyzer, 'analyze_video_deeply') as mock_analyze:
            mock_analyze.return_value = Mock(
                quality_score=0.85,
                highlight_segments=[],
                scenes=[],
                characters=[]
            )
            
            await tool._analyze_single_episode(episode)
            
            assert episode.analysis_completed is True
            assert episode.quality_score == 0.85
            assert episode.analyzed_at is not None
    
    @pytest.mark.asyncio
    async def test_extract_highlights(self, tool):
        """测试精彩片段提取"""
        # 创建测试系列信息
        series_info = SeriesInfo(
            series_id="test_series",
            metadata=SeriesMetadata(title="测试系列"),
            episodes=[],
            total_episodes=0,
            compilation_settings=CompilationSettings(
                quality_threshold=0.6,
                excitement_threshold=0.7
            )
        )
        
        with patch.object(series_info, 'get_total_highlights') as mock_highlights:
            mock_highlights.return_value = []
            
            with patch.object(tool.extractor, 'select_optimal_segments') as mock_select:
                mock_select.return_value = []
                
                segments = await tool._extract_highlights(series_info)
                
                assert isinstance(segments, list)
                mock_select.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_success(self, tool, sample_video_paths):
        """测试成功执行"""
        params = {
            "video_paths": sample_video_paths,
            "series_title": "测试合集",
            "target_duration": 120,
            "style": "humorous"
        }
        
        # Mock所有依赖
        with patch.object(tool, '_create_series_info') as mock_create_series:
            mock_series = Mock()
            mock_create_series.return_value = mock_series
            
            with patch.object(tool, '_process_series_compilation') as mock_process:
                mock_result = Mock()
                mock_result.output_path = Path("output.mp4")
                mock_result.duration = 118.5
                mock_result.segment_count = 10
                mock_process.return_value = mock_result
                
                result = await tool.execute(params)
                
                assert result.type == "text"
                assert "合集制作完成" in result.text
                assert "118.5秒" in result.text
    
    @pytest.mark.asyncio
    async def test_execute_validation_error(self, tool):
        """测试参数验证错误"""
        params = {
            "video_paths": [],  # 空列表应该失败
            "series_title": "测试合集"
        }
        
        result = await tool.execute(params)
        
        assert result.type == "text"
        assert "失败" in result.text
    
    def test_config_validation(self):
        """测试配置验证"""
        # 有效配置
        valid_config = {
            "video_paths": ["video1.mp4", "video2.mp4"],
            "series_title": "测试系列",
            "target_duration": 120
        }
        
        config = SeriesCompilationConfig(**valid_config)
        assert config.video_paths == ["video1.mp4", "video2.mp4"]
        assert config.series_title == "测试系列"
        assert config.target_duration == 120
        
        # 无效配置 - 缺少必需参数
        with pytest.raises(ValueError):
            SeriesCompilationConfig(video_paths=[])
    
    def test_config_defaults(self):
        """测试配置默认值"""
        config = SeriesCompilationConfig(
            video_paths=["video1.mp4"],
            series_title="测试"
        )
        
        assert config.target_duration == 120.0
        assert config.style == "humorous"
        assert config.quality_threshold == 0.6
        assert config.excitement_threshold == 0.7
        assert config.create_jianying_project is True
        assert config.generate_commentary is True
    
    @pytest.mark.asyncio
    async def test_parallel_analysis(self, tool):
        """测试并行分析"""
        episodes = [
            EpisodeInfo(
                index=i,
                title=f"第{i+1}集",
                file_path=Path(f"test_{i}.mp4"),
                duration=60.0,
                resolution="1920x1080",
                fps=30.0,
                file_size=1000000,
                format="mp4"
            )
            for i in range(3)
        ]
        
        series_info = SeriesInfo(
            series_id="test",
            metadata=SeriesMetadata(title="测试"),
            episodes=episodes,
            total_episodes=3
        )
        
        params = SeriesCompilationConfig(
            video_paths=["test_0.mp4", "test_1.mp4", "test_2.mp4"],
            series_title="测试",
            parallel_analysis=True,
            max_concurrent=2
        )
        
        with patch.object(tool, '_analyze_single_episode') as mock_analyze:
            mock_analyze.return_value = None
            
            await tool._analyze_episodes(series_info, params)
            
            # 验证所有集数都被分析
            assert mock_analyze.call_count == 3
            assert series_info.analysis_completed is True


class TestSeriesModels:
    """测试系列数据模型"""
    
    def test_episode_info_validation(self, tmp_path):
        """测试集数信息验证"""
        video_file = tmp_path / "test.mp4"
        video_file.write_text("fake content")
        
        episode = EpisodeInfo(
            index=0,
            title="第1集",
            file_path=video_file,
            duration=60.0,
            resolution="1920x1080",
            fps=30.0,
            file_size=1000000,
            format="mp4"
        )
        
        assert episode.index == 0
        assert episode.title == "第1集"
        assert episode.file_path == video_file
        assert episode.analysis_completed is False
    
    def test_episode_info_file_not_exists(self):
        """测试文件不存在的验证"""
        with pytest.raises(ValueError, match="视频文件不存在"):
            EpisodeInfo(
                index=0,
                title="第1集",
                file_path=Path("nonexistent.mp4"),
                duration=60.0,
                resolution="1920x1080",
                fps=30.0,
                file_size=1000000,
                format="mp4"
            )
    
    def test_series_info_validation(self):
        """测试系列信息验证"""
        # 空集数列表应该失败
        with pytest.raises(ValueError, match="至少需要一集视频"):
            SeriesInfo(
                series_id="test",
                metadata=SeriesMetadata(title="测试"),
                episodes=[],
                total_episodes=0
            )
    
    def test_series_info_episode_count_mismatch(self, tmp_path):
        """测试集数不匹配验证"""
        video_file = tmp_path / "test.mp4"
        video_file.write_text("fake content")
        
        episode = EpisodeInfo(
            index=0,
            title="第1集",
            file_path=video_file,
            duration=60.0,
            resolution="1920x1080",
            fps=30.0,
            file_size=1000000,
            format="mp4"
        )
        
        with pytest.raises(ValueError, match="总集数与实际集数不匹配"):
            SeriesInfo(
                series_id="test",
                metadata=SeriesMetadata(title="测试"),
                episodes=[episode],
                total_episodes=2  # 不匹配
            )
    
    def test_series_info_methods(self, tmp_path):
        """测试系列信息方法"""
        video_file = tmp_path / "test.mp4"
        video_file.write_text("fake content")
        
        episode = EpisodeInfo(
            index=0,
            title="第1集",
            file_path=video_file,
            duration=60.0,
            resolution="1920x1080",
            fps=30.0,
            file_size=1000000,
            format="mp4"
        )
        
        series_info = SeriesInfo(
            series_id="test",
            metadata=SeriesMetadata(title="测试"),
            episodes=[episode],
            total_episodes=1
        )
        
        # 测试更新进度
        series_info.update_progress(ProcessingStatus.ANALYZING, 0.5)
        assert series_info.status == ProcessingStatus.ANALYZING
        assert series_info.progress == 0.5
        
        # 测试统计信息
        stats = series_info.calculate_statistics()
        assert stats["total_episodes"] == 1
        assert stats["total_duration"] == 60.0
