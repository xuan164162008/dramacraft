"""
测试标准JSON配置格式
"""

import pytest
from pydantic import ValidationError

from src.dramacraft.config.json_schemas import (
    SeriesCompilationConfig,
    CommentaryGenerationConfig,
    VideoAnalysisConfig,
    JianYingProjectConfig,
    ConfigFactory,
    VideoStyle,
    TargetAudience,
    OutputQuality
)


class TestSeriesCompilationConfig:
    """测试系列合集制作配置"""
    
    def test_valid_config(self):
        """测试有效配置"""
        config = SeriesCompilationConfig(
            video_paths=["video1.mp4", "video2.mp4"],
            series_title="测试系列"
        )
        
        assert config.video_paths == ["video1.mp4", "video2.mp4"]
        assert config.series_title == "测试系列"
        assert config.target_duration == 120.0  # 默认值
        assert config.style == VideoStyle.HUMOROUS
        assert config.create_jianying_project is True
    
    def test_custom_values(self):
        """测试自定义值"""
        config = SeriesCompilationConfig(
            video_paths=["video1.mp4"],
            series_title="自定义测试",
            target_duration=180.0,
            style=VideoStyle.PROFESSIONAL,
            quality_threshold=0.8,
            excitement_threshold=0.9,
            create_jianying_project=False,
            max_concurrent=5
        )
        
        assert config.target_duration == 180.0
        assert config.style == VideoStyle.PROFESSIONAL
        assert config.quality_threshold == 0.8
        assert config.excitement_threshold == 0.9
        assert config.create_jianying_project is False
        assert config.max_concurrent == 5
    
    def test_missing_required_fields(self):
        """测试缺少必需字段"""
        with pytest.raises(ValidationError):
            SeriesCompilationConfig()  # 缺少video_paths和series_title
        
        with pytest.raises(ValidationError):
            SeriesCompilationConfig(video_paths=["video1.mp4"])  # 缺少series_title
        
        with pytest.raises(ValidationError):
            SeriesCompilationConfig(series_title="测试")  # 缺少video_paths
    
    def test_invalid_values(self):
        """测试无效值"""
        # 无效的时长范围
        with pytest.raises(ValidationError):
            SeriesCompilationConfig(
                video_paths=["video1.mp4"],
                series_title="测试",
                target_duration=10.0  # 小于最小值30
            )
        
        with pytest.raises(ValidationError):
            SeriesCompilationConfig(
                video_paths=["video1.mp4"],
                series_title="测试",
                target_duration=700.0  # 大于最大值600
            )
        
        # 无效的阈值范围
        with pytest.raises(ValidationError):
            SeriesCompilationConfig(
                video_paths=["video1.mp4"],
                series_title="测试",
                quality_threshold=1.5  # 大于1
            )
        
        with pytest.raises(ValidationError):
            SeriesCompilationConfig(
                video_paths=["video1.mp4"],
                series_title="测试",
                excitement_threshold=-0.1  # 小于0
            )
    
    def test_enum_values(self):
        """测试枚举值"""
        config = SeriesCompilationConfig(
            video_paths=["video1.mp4"],
            series_title="测试",
            style=VideoStyle.DRAMATIC,
            target_audience=TargetAudience.TEENAGERS,
            output_quality=OutputQuality.ULTRA
        )
        
        assert config.style == VideoStyle.DRAMATIC
        assert config.target_audience == TargetAudience.TEENAGERS
        assert config.output_quality == OutputQuality.ULTRA
    
    def test_dict_conversion(self):
        """测试字典转换"""
        config = SeriesCompilationConfig(
            video_paths=["video1.mp4"],
            series_title="测试",
            style=VideoStyle.HUMOROUS
        )
        
        config_dict = config.dict()
        
        assert config_dict["video_paths"] == ["video1.mp4"]
        assert config_dict["series_title"] == "测试"
        assert config_dict["style"] == "humorous"  # 枚举值转换


class TestCommentaryGenerationConfig:
    """测试解说生成配置"""
    
    def test_valid_config(self):
        """测试有效配置"""
        config = CommentaryGenerationConfig(
            video_path="test.mp4"
        )
        
        assert config.video_path == "test.mp4"
        assert config.style == VideoStyle.HUMOROUS
        assert config.include_intro is True
        assert config.emotion_emphasis == 0.7
    
    def test_custom_values(self):
        """测试自定义值"""
        config = CommentaryGenerationConfig(
            video_path="test.mp4",
            style=VideoStyle.PROFESSIONAL,
            target_audience=TargetAudience.PROFESSIONALS,
            include_intro=False,
            commentary_length="long",
            humor_level=0.3,
            output_format="srt"
        )
        
        assert config.style == VideoStyle.PROFESSIONAL
        assert config.target_audience == TargetAudience.PROFESSIONALS
        assert config.include_intro is False
        assert config.commentary_length == "long"
        assert config.humor_level == 0.3
        assert config.output_format == "srt"
    
    def test_missing_required_field(self):
        """测试缺少必需字段"""
        with pytest.raises(ValidationError):
            CommentaryGenerationConfig()  # 缺少video_path


class TestVideoAnalysisConfig:
    """测试视频分析配置"""
    
    def test_valid_config(self):
        """测试有效配置"""
        config = VideoAnalysisConfig(
            video_path="test.mp4"
        )
        
        assert config.video_path == "test.mp4"
        assert config.analysis_depth == "comprehensive"
        assert config.include_scenes is True
        assert config.frame_sampling_rate == 1.0
    
    def test_custom_values(self):
        """测试自定义值"""
        config = VideoAnalysisConfig(
            video_path="test.mp4",
            analysis_depth="basic",
            include_emotions=False,
            frame_sampling_rate=2.0,
            quality_threshold=0.8,
            output_format="yaml"
        )
        
        assert config.analysis_depth == "basic"
        assert config.include_emotions is False
        assert config.frame_sampling_rate == 2.0
        assert config.quality_threshold == 0.8
        assert config.output_format == "yaml"
    
    def test_invalid_sampling_rate(self):
        """测试无效采样率"""
        with pytest.raises(ValidationError):
            VideoAnalysisConfig(
                video_path="test.mp4",
                frame_sampling_rate=0.05  # 小于最小值0.1
            )
        
        with pytest.raises(ValidationError):
            VideoAnalysisConfig(
                video_path="test.mp4",
                frame_sampling_rate=6.0  # 大于最大值5.0
            )


class TestJianYingProjectConfig:
    """测试剪映项目配置"""
    
    def test_valid_config(self):
        """测试有效配置"""
        config = JianYingProjectConfig(
            video_path="test.mp4",
            project_name="测试项目"
        )
        
        assert config.video_path == "test.mp4"
        assert config.project_name == "测试项目"
        assert config.resolution == "1920x1080"
        assert config.frame_rate == 30.0
        assert config.include_subtitles is True
    
    def test_custom_values(self):
        """测试自定义值"""
        config = JianYingProjectConfig(
            video_path="test.mp4",
            project_name="自定义项目",
            resolution="3840x2160",
            frame_rate=60.0,
            commentary_text="解说文案",
            include_background_music=True,
            auto_import=False
        )
        
        assert config.resolution == "3840x2160"
        assert config.frame_rate == 60.0
        assert config.commentary_text == "解说文案"
        assert config.include_background_music is True
        assert config.auto_import is False
    
    def test_missing_required_fields(self):
        """测试缺少必需字段"""
        with pytest.raises(ValidationError):
            JianYingProjectConfig()  # 缺少所有必需字段
        
        with pytest.raises(ValidationError):
            JianYingProjectConfig(video_path="test.mp4")  # 缺少project_name


class TestConfigFactory:
    """测试配置工厂"""
    
    def test_create_series_compilation_config(self):
        """测试创建系列合集配置"""
        config_dict = ConfigFactory.create_series_compilation_config(
            video_paths=["video1.mp4", "video2.mp4"],
            series_title="测试系列",
            target_duration=150
        )
        
        assert config_dict["video_paths"] == ["video1.mp4", "video2.mp4"]
        assert config_dict["series_title"] == "测试系列"
        assert config_dict["target_duration"] == 150
        assert config_dict["style"] == "humorous"  # 默认值
    
    def test_create_commentary_config(self):
        """测试创建解说配置"""
        config_dict = ConfigFactory.create_commentary_config(
            video_path="test.mp4",
            style="professional"
        )
        
        assert config_dict["video_path"] == "test.mp4"
        assert config_dict["style"] == "professional"
        assert config_dict["include_intro"] is True  # 默认值
    
    def test_create_analysis_config(self):
        """测试创建分析配置"""
        config_dict = ConfigFactory.create_analysis_config(
            video_path="test.mp4",
            analysis_depth="detailed"
        )
        
        assert config_dict["video_path"] == "test.mp4"
        assert config_dict["analysis_depth"] == "detailed"
        assert config_dict["include_scenes"] is True  # 默认值
    
    def test_create_jianying_config(self):
        """测试创建剪映配置"""
        config_dict = ConfigFactory.create_jianying_config(
            video_path="test.mp4",
            project_name="测试项目",
            resolution="4K"
        )
        
        assert config_dict["video_path"] == "test.mp4"
        assert config_dict["project_name"] == "测试项目"
        assert config_dict["resolution"] == "4K"
    
    def test_get_config_template(self):
        """测试获取配置模板"""
        template = ConfigFactory.get_config_template("create_series_compilation")
        
        assert "video_paths" in template
        assert "series_title" in template
        assert "target_duration" in template
        assert template["target_duration"] == 120
        
        # 测试不存在的工具
        empty_template = ConfigFactory.get_config_template("nonexistent_tool")
        assert empty_template == {}
    
    def test_validate_config(self):
        """测试配置验证"""
        # 有效配置
        valid_config = {
            "video_paths": ["video1.mp4"],
            "series_title": "测试"
        }
        assert ConfigFactory.validate_config("create_series_compilation", valid_config) is True
        
        # 无效配置
        invalid_config = {
            "video_paths": [],  # 空列表
            "series_title": "测试"
        }
        assert ConfigFactory.validate_config("create_series_compilation", invalid_config) is False
        
        # 不存在的工具
        assert ConfigFactory.validate_config("nonexistent_tool", {}) is False


class TestEnums:
    """测试枚举类型"""
    
    def test_video_style_enum(self):
        """测试视频风格枚举"""
        assert VideoStyle.HUMOROUS == "humorous"
        assert VideoStyle.PROFESSIONAL == "professional"
        assert VideoStyle.DRAMATIC == "dramatic"
        assert VideoStyle.SUSPENSE == "suspense"
        assert VideoStyle.ROMANTIC == "romantic"
        assert VideoStyle.ACTION == "action"
    
    def test_target_audience_enum(self):
        """测试目标受众枚举"""
        assert TargetAudience.YOUNG_ADULTS == "年轻人"
        assert TargetAudience.TEENAGERS == "青少年"
        assert TargetAudience.MIDDLE_AGED == "中年人"
        assert TargetAudience.GENERAL == "大众"
        assert TargetAudience.PROFESSIONALS == "专业人士"
    
    def test_output_quality_enum(self):
        """测试输出质量枚举"""
        assert OutputQuality.LOW == "low"
        assert OutputQuality.MEDIUM == "medium"
        assert OutputQuality.HIGH == "high"
        assert OutputQuality.ULTRA == "ultra"
