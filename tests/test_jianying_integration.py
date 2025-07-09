"""
测试剪映集成功能
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch

from src.dramacraft.integration.jianying_draft_v2 import JianYingDraftGeneratorV2


class TestJianYingDraftGenerator:
    """剪映草稿生成器测试"""
    
    @pytest.fixture
    def generator(self):
        """创建测试生成器实例"""
        return JianYingDraftGeneratorV2()
    
    @pytest.fixture
    def sample_video_path(self, tmp_path):
        """创建示例视频文件"""
        video_file = tmp_path / "test_video.mp4"
        video_file.write_text("fake video content")
        return video_file
    
    @pytest.fixture
    def sample_audio_path(self, tmp_path):
        """创建示例音频文件"""
        audio_file = tmp_path / "background_music.mp3"
        audio_file.write_text("fake audio content")
        return audio_file
    
    def test_generator_initialization(self, generator):
        """测试生成器初始化"""
        assert generator.draft_version == "13.0.0"
        assert generator.platform == "mac"
    
    def test_create_complete_draft(self, generator, sample_video_path, tmp_path):
        """测试创建完整草稿文件"""
        project_name = "测试项目"
        output_dir = tmp_path / "output"
        
        with patch.object(generator, '_get_video_info') as mock_get_info:
            mock_get_info.return_value = {
                "width": 1920,
                "height": 1080,
                "fps": 30.0,
                "duration": 120.0
            }
            
            draft_path = generator.create_complete_draft(
                video_path=sample_video_path,
                project_name=project_name,
                output_dir=output_dir
            )
            
            # 验证文件创建
            assert draft_path.exists()
            assert draft_path.name == f"{project_name}.draft"
            
            # 验证文件内容
            with open(draft_path, 'r', encoding='utf-8') as f:
                draft_data = json.load(f)
            
            assert "content" in draft_data
            assert "create_time" in draft_data
            assert draft_data["draft_name"] == project_name
    
    def test_create_draft_structure(self, generator, sample_video_path):
        """测试创建草稿数据结构"""
        with patch.object(generator, '_get_video_info') as mock_get_info:
            mock_get_info.return_value = {
                "width": 1920,
                "height": 1080,
                "fps": 30.0,
                "duration": 120.0
            }
            
            draft_data = generator._create_draft_structure(
                draft_id="test-id",
                project_name="测试项目",
                video_path=sample_video_path
            )
            
            # 验证基本结构
            assert "content" in draft_data
            assert "create_time" in draft_data
            assert "draft_id" in draft_data
            assert "draft_name" in draft_data
            assert "version" in draft_data
            
            # 验证内容结构
            content = draft_data["content"]
            assert "canvas_config" in content
            assert "materials" in content
            assert "tracks" in content
            assert "duration" in content
            
            # 验证画布配置
            canvas = content["canvas_config"]
            assert canvas["width"] == 1920
            assert canvas["height"] == 1080
            
            # 验证时长（微秒）
            assert content["duration"] == 120000000  # 120秒 * 1000000
    
    def test_create_materials(self, generator, sample_video_path, sample_audio_path):
        """测试创建材料库"""
        materials = generator._create_materials(sample_video_path, sample_audio_path)
        
        # 验证材料库结构
        expected_keys = [
            "audios", "canvases", "chromakeys", "colorwheels", "effects",
            "flowers", "handwrites", "images", "shapeclips", "sounds",
            "stickers", "texts", "transitions", "videos"
        ]
        
        for key in expected_keys:
            assert key in materials
        
        # 验证视频材料
        assert len(materials["videos"]) == 1
        video_material = materials["videos"][0]
        assert video_material["type"] == "video"
        assert video_material["file_Path"] == str(sample_video_path.absolute())
        assert video_material["material_name"] == sample_video_path.stem
        
        # 验证音频材料
        assert len(materials["audios"]) == 1
        audio_material = materials["audios"][0]
        assert audio_material["type"] == "audio"
        assert audio_material["file_Path"] == str(sample_audio_path.absolute())
    
    def test_create_video_material(self, generator, sample_video_path):
        """测试创建视频材料"""
        with patch.object(generator, '_get_video_info') as mock_get_info:
            mock_get_info.return_value = {
                "width": 1920,
                "height": 1080,
                "fps": 30.0,
                "duration": 120.0
            }
            
            material = generator._create_video_material(sample_video_path)
            
            # 验证材料属性
            assert material["type"] == "video"
            assert material["width"] == 1920
            assert material["height"] == 1080
            assert material["duration"] == 120000000  # 微秒
            assert material["has_audio"] is True
            assert material["file_Path"] == str(sample_video_path.absolute())
            assert material["material_name"] == sample_video_path.stem
            
            # 验证必需字段
            required_fields = [
                "id", "material_id", "local_material_id", "path",
                "crop", "audio_fade", "category_name"
            ]
            for field in required_fields:
                assert field in material
    
    def test_create_audio_material(self, generator, sample_audio_path):
        """测试创建音频材料"""
        material = generator._create_audio_material(sample_audio_path)
        
        # 验证材料属性
        assert material["type"] == "audio"
        assert material["file_Path"] == str(sample_audio_path.absolute())
        assert material["material_name"] == sample_audio_path.stem
        assert material["duration"] == 180000000  # 3分钟默认时长
        
        # 验证必需字段
        required_fields = [
            "id", "material_id", "local_material_id", "path",
            "audio_fade", "category_name"
        ]
        for field in required_fields:
            assert field in material
    
    def test_create_tracks(self, generator):
        """测试创建轨道"""
        video_info = {
            "width": 1920,
            "height": 1080,
            "fps": 30.0,
            "duration": 120.0
        }
        
        video_material = {
            "id": "test-video-id",
            "duration": 120000000
        }
        
        materials = {
            "videos": [video_material],
            "audios": []
        }
        
        commentary_segments = [
            {
                "start_time": 0.0,
                "duration": 5.0,
                "text": "测试解说"
            }
        ]
        
        tracks = generator._create_tracks(
            video_info=video_info,
            materials=materials,
            commentary_segments=commentary_segments
        )
        
        # 验证轨道数量和类型
        assert len(tracks) >= 3  # 至少有视频、音频、字幕轨道
        
        track_types = [track["type"] for track in tracks]
        assert "video" in track_types
        assert "audio" in track_types
        assert "text" in track_types
        
        # 验证视频轨道
        video_track = next(track for track in tracks if track["type"] == "video")
        assert video_track["attribute"] == 0
        assert len(video_track["segments"]) == 1
        
        # 验证字幕轨道
        text_track = next(track for track in tracks if track["type"] == "text")
        assert len(text_track["segments"]) == 1
    
    def test_create_video_track(self, generator):
        """测试创建视频轨道"""
        video_info = {
            "duration": 120.0
        }
        
        video_material = {
            "id": "test-video-id"
        }
        
        track = generator._create_video_track(video_info, video_material)
        
        # 验证轨道属性
        assert track["type"] == "video"
        assert track["attribute"] == 0
        assert len(track["segments"]) == 1
        
        # 验证片段属性
        segment = track["segments"][0]
        assert segment["material_id"] == "test-video-id"
        assert segment["visible"] is True
        assert segment["volume"] == 1.0
        assert segment["speed"] == 1.0
        
        # 验证时间范围
        duration_us = int(120.0 * 1000000)
        assert segment["source_timerange"]["duration"] == duration_us
        assert segment["target_timerange"]["duration"] == duration_us
    
    def test_create_text_track(self, generator):
        """测试创建字幕轨道"""
        commentary_segments = [
            {
                "start_time": 0.0,
                "duration": 5.0,
                "text": "第一段解说"
            },
            {
                "start_time": 5.0,
                "duration": 3.0,
                "text": "第二段解说"
            }
        ]
        
        track = generator._create_text_track(commentary_segments)
        
        # 验证轨道属性
        assert track["type"] == "text"
        assert track["attribute"] == 0
        assert len(track["segments"]) == 2
        
        # 验证第一个片段
        segment1 = track["segments"][0]
        assert segment1["target_timerange"]["start"] == 0
        assert segment1["target_timerange"]["duration"] == 5000000  # 5秒
        
        # 验证第二个片段
        segment2 = track["segments"][1]
        assert segment2["target_timerange"]["start"] == 5000000  # 5秒
        assert segment2["target_timerange"]["duration"] == 3000000  # 3秒
    
    def test_get_video_info_default(self, generator, sample_video_path):
        """测试获取视频信息默认值"""
        info = generator._get_video_info(sample_video_path)
        
        # 验证默认值
        assert info["width"] == 1920
        assert info["height"] == 1080
        assert info["fps"] == 30.0
        assert info["duration"] == 120.0
    
    def test_draft_file_format_validation(self, generator, sample_video_path, tmp_path):
        """测试草稿文件格式验证"""
        project_name = "格式验证测试"
        output_dir = tmp_path / "output"
        
        with patch.object(generator, '_get_video_info') as mock_get_info:
            mock_get_info.return_value = {
                "width": 1920,
                "height": 1080,
                "fps": 30.0,
                "duration": 120.0
            }
            
            draft_path = generator.create_complete_draft(
                video_path=sample_video_path,
                project_name=project_name,
                output_dir=output_dir
            )
            
            # 验证JSON格式
            with open(draft_path, 'r', encoding='utf-8') as f:
                draft_data = json.load(f)
            
            # 验证关键字段存在
            assert "content" in draft_data
            assert "draft_id" in draft_data
            assert "version" in draft_data
            
            # 验证版本信息
            assert draft_data["version"] == "13.0.0"
            
            # 验证平台信息
            platform_info = draft_data["last_modified_platform"]
            assert platform_info["os"] == "mac"
            assert platform_info["app_id"] == "com.lemon.lvpro"
    
    def test_with_background_music(self, generator, sample_video_path, sample_audio_path, tmp_path):
        """测试包含背景音乐的草稿"""
        project_name = "背景音乐测试"
        output_dir = tmp_path / "output"
        
        with patch.object(generator, '_get_video_info') as mock_get_info:
            mock_get_info.return_value = {
                "width": 1920,
                "height": 1080,
                "fps": 30.0,
                "duration": 120.0
            }
            
            draft_path = generator.create_complete_draft(
                video_path=sample_video_path,
                project_name=project_name,
                background_music_path=sample_audio_path,
                output_dir=output_dir
            )
            
            # 验证文件创建
            assert draft_path.exists()
            
            # 验证包含背景音乐
            with open(draft_path, 'r', encoding='utf-8') as f:
                draft_data = json.load(f)
            
            materials = draft_data["content"]["materials"]
            assert len(materials["audios"]) == 1
            
            # 验证轨道包含背景音乐
            tracks = draft_data["content"]["tracks"]
            audio_tracks = [track for track in tracks if track["type"] == "audio"]
            assert len(audio_tracks) >= 2  # 原声 + 背景音乐
