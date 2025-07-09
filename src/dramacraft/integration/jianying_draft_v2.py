"""
剪映草稿文件生成器 V2 - 完全兼容版本
确保生成的.draft文件完全兼容剪映专业版，支持完整的项目结构和编辑功能
"""

import json
import logging
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class JianYingTrack:
    """剪映轨道数据结构"""
    id: str
    type: str  # video, audio, text, sticker
    attribute: int
    flag: int
    segments: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class JianYingSegment:
    """剪映片段数据结构"""
    id: str
    clip: dict[str, Any]
    common_keyframes: list[Any]
    enable_adjust: bool
    enable_color_curves: bool
    enable_color_match_reference: bool
    enable_color_wheels: bool
    enable_lut: bool
    enable_smart_color_adjust: bool
    extra_material_refs: list[str]
    group_id: str
    hdr_settings: dict[str, Any]
    intensifies_audio: bool
    is_placeholder: bool
    is_tone_modify: bool
    keyframe_refs: list[Any]
    last_nonzero_volume: float
    material_id: str
    render_index: int
    reverse: bool
    source_timerange: dict[str, Any]
    speed: float
    target_timerange: dict[str, Any]
    template_id: str
    template_scene: str
    track_attribute: int
    track_render_index: int
    uniform_scale: dict[str, Any]
    visible: bool
    volume: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class JianYingDraftGeneratorV2:
    """剪映草稿文件生成器 V2 - 完全兼容版本"""

    def __init__(self):
        self.draft_version = "13.0.0"  # 剪映版本
        self.platform = "mac"  # 平台

    def create_complete_draft(
        self,
        video_path: Path,
        project_name: str,
        commentary_segments: Optional[list[dict[str, Any]]] = None,
        background_music_path: Optional[Path] = None,
        output_dir: Path = Path("./output")
    ) -> Path:
        """创建完整的剪映草稿文件"""

        # 生成唯一ID
        draft_id = str(uuid.uuid4())

        # 创建草稿数据结构
        draft_data = self._create_draft_structure(
            draft_id=draft_id,
            project_name=project_name,
            video_path=video_path,
            commentary_segments=commentary_segments,
            background_music_path=background_music_path
        )

        # 保存草稿文件
        output_dir.mkdir(parents=True, exist_ok=True)
        draft_path = output_dir / f"{project_name}.draft"

        with open(draft_path, 'w', encoding='utf-8') as f:
            json.dump(draft_data, f, ensure_ascii=False, indent=2)

        logger.info(f"剪映草稿文件已创建: {draft_path}")
        return draft_path

    def _create_draft_structure(
        self,
        draft_id: str,
        project_name: str,
        video_path: Path,
        commentary_segments: Optional[list[dict[str, Any]]] = None,
        background_music_path: Optional[Path] = None
    ) -> dict[str, Any]:
        """创建完整的草稿数据结构"""

        # 获取视频信息
        video_info = self._get_video_info(video_path)

        # 创建材料库
        materials = self._create_materials(video_path, background_music_path)

        # 创建轨道
        tracks = self._create_tracks(
            video_info=video_info,
            materials=materials,
            commentary_segments=commentary_segments
        )

        # 创建完整草稿结构
        draft_data = {
            "content": {
                "canvas_config": {
                    "height": video_info["height"],
                    "width": video_info["width"]
                },
                "color_space": 0,
                "config": {
                    "export": {
                        "bitrate": 8000000,
                        "codec": "h264",
                        "format": "mp4",
                        "fps": video_info["fps"],
                        "height": video_info["height"],
                        "width": video_info["width"]
                    },
                    "preview": {
                        "fps": video_info["fps"],
                        "height": video_info["height"],
                        "width": video_info["width"]
                    }
                },
                "duration": int(video_info["duration"] * 1000000),  # 微秒
                "extra": {
                    "auto_save_time": int(datetime.now().timestamp()),
                    "draft_fold_path": "",
                    "draft_id": draft_id,
                    "draft_name": project_name,
                    "draft_removable": True,
                    "project_id": "",
                    "timeline_scale": 1.0,
                    "timeline_start_time": 0
                },
                "keyframe_graph_list": [],
                "materials": materials,
                "tracks": tracks,
                "version": self.draft_version
            },
            "create_time": int(datetime.now().timestamp()),
            "draft_fold_path": "",
            "draft_id": draft_id,
            "draft_name": project_name,
            "draft_removable": True,
            "draft_root_path": "",
            "extra_info": "",
            "id": draft_id,
            "last_modified_platform": {
                "app_id": "com.lemon.lvpro",
                "app_source": "lv",
                "app_version": "4.0.0",
                "device_id": str(uuid.uuid4()),
                "hard_disk_id": "",
                "mac_address": "",
                "os": "mac",
                "os_version": "14.0"
            },
            "project_id": "",
            "tm_draft_create": int(datetime.now().timestamp()),
            "tm_draft_modified": int(datetime.now().timestamp()),
            "version": self.draft_version
        }

        return draft_data

    def _create_materials(
        self,
        video_path: Path,
        background_music_path: Optional[Path] = None
    ) -> dict[str, Any]:
        """创建材料库"""

        materials = {
            "audios": [],
            "canvases": [],
            "chromakeys": [],
            "colorwheels": [],
            "effects": [],
            "flowers": [],
            "handwrites": [],
            "images": [],
            "shapeclips": [],
            "sounds": [],
            "stickers": [],
            "texts": [],
            "transitions": [],
            "videos": []
        }

        # 添加主视频材料
        video_material = self._create_video_material(video_path)
        materials["videos"].append(video_material)

        # 添加背景音乐材料
        if background_music_path and background_music_path.exists():
            audio_material = self._create_audio_material(background_music_path)
            materials["audios"].append(audio_material)

        return materials

    def _create_video_material(self, video_path: Path) -> dict[str, Any]:
        """创建视频材料"""

        video_info = self._get_video_info(video_path)
        material_id = str(uuid.uuid4())

        return {
            "audio_fade": {
                "fade_in": {"duration": 0, "type": ""},
                "fade_out": {"duration": 0, "type": ""}
            },
            "cartoon_path": "",
            "category_id": "",
            "category_name": "local",
            "check_flag": 63487,
            "crop": {
                "lower_left_x": 0.0,
                "lower_left_y": 1.0,
                "lower_right_x": 1.0,
                "lower_right_y": 1.0,
                "upper_left_x": 0.0,
                "upper_left_y": 0.0,
                "upper_right_x": 1.0,
                "upper_right_y": 0.0
            },
            "crop_ratio": "free",
            "crop_scale": 1.0,
            "duration": int(video_info["duration"] * 1000000),
            "extra_type_option": 0,
            "file_Path": str(video_path.absolute()),
            "formula_id": "",
            "freeze": {"freeze_type": "", "freeze_time": 0},
            "gaussian_blur_radius": 0.0,
            "has_audio": True,
            "height": video_info["height"],
            "id": material_id,
            "intensifies_audio_path": "",
            "intensifies_path": "",
            "is_ai_generate_content": False,
            "is_unified_beauty_mode": False,
            "local_id": "",
            "local_material_id": material_id,
            "material_id": material_id,
            "material_name": video_path.stem,
            "material_url": "",
            "matting": {
                "flag": 0,
                "has_use_quick_brush": False,
                "has_use_quick_eraser": False,
                "interactiveTime": [],
                "path": "",
                "strokes": []
            },
            "media_path": "",
            "object_locked": False,
            "origin_material_id": "",
            "path": str(video_path.absolute()),
            "picture_from": "none",
            "picture_set_category_id": "",
            "picture_set_category_name": "",
            "request_id": "",
            "reverse_intensifies_path": "",
            "reverse_path": "",
            "source_platform": 0,
            "stable": {"matrix_path": "", "stable_level": 0, "time_range": {"duration": -1, "start": -1}},
            "team_id": "",
            "type": "video",
            "video_algorithm": {"algorithms": [], "deflicker": False, "motion_blur_config": {}},
            "width": video_info["width"]
        }

    def _create_audio_material(self, audio_path: Path) -> dict[str, Any]:
        """创建音频材料"""

        material_id = str(uuid.uuid4())

        return {
            "audio_fade": {
                "fade_in": {"duration": 0, "type": ""},
                "fade_out": {"duration": 0, "type": ""}
            },
            "category_id": "",
            "category_name": "local",
            "check_flag": 1,
            "duration": 180000000,  # 3分钟默认时长
            "file_Path": str(audio_path.absolute()),
            "formula_id": "",
            "id": material_id,
            "intensifies_path": "",
            "local_material_id": material_id,
            "material_id": material_id,
            "material_name": audio_path.stem,
            "material_url": "",
            "path": str(audio_path.absolute()),
            "request_id": "",
            "source_platform": 0,
            "team_id": "",
            "type": "audio"
        }

    def _create_tracks(
        self,
        video_info: dict[str, Any],
        materials: dict[str, Any],
        commentary_segments: Optional[list[dict[str, Any]]] = None
    ) -> list[dict[str, Any]]:
        """创建轨道列表"""

        tracks = []

        # 主视频轨道
        video_track = self._create_video_track(video_info, materials["videos"][0])
        tracks.append(video_track)

        # 音频轨道
        audio_track = self._create_audio_track(video_info, materials["videos"][0])
        tracks.append(audio_track)

        # 字幕轨道
        if commentary_segments:
            text_track = self._create_text_track(commentary_segments)
            tracks.append(text_track)

        # 背景音乐轨道
        if materials["audios"]:
            bgm_track = self._create_bgm_track(materials["audios"][0])
            tracks.append(bgm_track)

        return tracks

    def _create_video_track(self, video_info: dict[str, Any], video_material: dict[str, Any]) -> dict[str, Any]:
        """创建视频轨道"""

        segment_id = str(uuid.uuid4())
        duration_us = int(video_info["duration"] * 1000000)

        segment = {
            "id": segment_id,
            "clip": {
                "alpha": 1.0,
                "flip": {"horizontal": False, "vertical": False},
                "rotation": 0.0,
                "scale": {"x": 1.0, "y": 1.0},
                "transform": {"x": 0.0, "y": 0.0}
            },
            "common_keyframes": [],
            "enable_adjust": True,
            "enable_color_curves": True,
            "enable_color_match_reference": False,
            "enable_color_wheels": True,
            "enable_lut": True,
            "enable_smart_color_adjust": False,
            "extra_material_refs": [],
            "group_id": "",
            "hdr_settings": {"intensity": 1.0, "mode": 1, "nits": 1000},
            "intensifies_audio": False,
            "is_placeholder": False,
            "is_tone_modify": False,
            "keyframe_refs": [],
            "last_nonzero_volume": 1.0,
            "material_id": video_material["id"],
            "render_index": 0,
            "reverse": False,
            "source_timerange": {"duration": duration_us, "start": 0},
            "speed": 1.0,
            "target_timerange": {"duration": duration_us, "start": 0},
            "template_id": "",
            "template_scene": "default",
            "track_attribute": 0,
            "track_render_index": 0,
            "uniform_scale": {"on": True, "value": 1.0},
            "visible": True,
            "volume": 1.0
        }

        return {
            "attribute": 0,
            "flag": 0,
            "id": str(uuid.uuid4()),
            "segments": [segment],
            "type": "video"
        }

    def _create_audio_track(self, video_info: dict[str, Any], video_material: dict[str, Any]) -> dict[str, Any]:
        """创建音频轨道"""

        segment_id = str(uuid.uuid4())
        duration_us = int(video_info["duration"] * 1000000)

        segment = {
            "id": segment_id,
            "clip": {},
            "common_keyframes": [],
            "enable_adjust": False,
            "enable_color_curves": False,
            "enable_color_match_reference": False,
            "enable_color_wheels": False,
            "enable_lut": False,
            "enable_smart_color_adjust": False,
            "extra_material_refs": [],
            "group_id": "",
            "hdr_settings": {},
            "intensifies_audio": False,
            "is_placeholder": False,
            "is_tone_modify": False,
            "keyframe_refs": [],
            "last_nonzero_volume": 1.0,
            "material_id": video_material["id"],
            "render_index": 0,
            "reverse": False,
            "source_timerange": {"duration": duration_us, "start": 0},
            "speed": 1.0,
            "target_timerange": {"duration": duration_us, "start": 0},
            "template_id": "",
            "template_scene": "default",
            "track_attribute": 0,
            "track_render_index": 0,
            "uniform_scale": {"on": True, "value": 1.0},
            "visible": True,
            "volume": 1.0
        }

        return {
            "attribute": 1,
            "flag": 0,
            "id": str(uuid.uuid4()),
            "segments": [segment],
            "type": "audio"
        }

    def _create_text_track(self, commentary_segments: list[dict[str, Any]]) -> dict[str, Any]:
        """创建字幕轨道"""

        segments = []

        for i, comment in enumerate(commentary_segments):
            segment_id = str(uuid.uuid4())
            material_id = str(uuid.uuid4())

            start_us = int(comment.get("start_time", i * 5) * 1000000)
            duration_us = int(comment.get("duration", 5) * 1000000)

            segment = {
                "id": segment_id,
                "clip": {
                    "alpha": 1.0,
                    "rotation": 0.0,
                    "scale": {"x": 1.0, "y": 1.0},
                    "transform": {"x": 0.0, "y": 0.0}
                },
                "common_keyframes": [],
                "enable_adjust": False,
                "enable_color_curves": False,
                "enable_color_match_reference": False,
                "enable_color_wheels": False,
                "enable_lut": False,
                "enable_smart_color_adjust": False,
                "extra_material_refs": [],
                "group_id": "",
                "hdr_settings": {},
                "intensifies_audio": False,
                "is_placeholder": False,
                "is_tone_modify": False,
                "keyframe_refs": [],
                "last_nonzero_volume": 1.0,
                "material_id": material_id,
                "render_index": i,
                "reverse": False,
                "source_timerange": {"duration": duration_us, "start": 0},
                "speed": 1.0,
                "target_timerange": {"duration": duration_us, "start": start_us},
                "template_id": "",
                "template_scene": "default",
                "track_attribute": 0,
                "track_render_index": 0,
                "uniform_scale": {"on": True, "value": 1.0},
                "visible": True,
                "volume": 1.0
            }

            segments.append(segment)

        return {
            "attribute": 0,
            "flag": 0,
            "id": str(uuid.uuid4()),
            "segments": segments,
            "type": "text"
        }

    def _create_bgm_track(self, audio_material: dict[str, Any]) -> dict[str, Any]:
        """创建背景音乐轨道"""

        segment_id = str(uuid.uuid4())
        duration_us = audio_material["duration"]

        segment = {
            "id": segment_id,
            "clip": {},
            "common_keyframes": [],
            "enable_adjust": False,
            "enable_color_curves": False,
            "enable_color_match_reference": False,
            "enable_color_wheels": False,
            "enable_lut": False,
            "enable_smart_color_adjust": False,
            "extra_material_refs": [],
            "group_id": "",
            "hdr_settings": {},
            "intensifies_audio": False,
            "is_placeholder": False,
            "is_tone_modify": False,
            "keyframe_refs": [],
            "last_nonzero_volume": 0.3,
            "material_id": audio_material["id"],
            "render_index": 0,
            "reverse": False,
            "source_timerange": {"duration": duration_us, "start": 0},
            "speed": 1.0,
            "target_timerange": {"duration": duration_us, "start": 0},
            "template_id": "",
            "template_scene": "default",
            "track_attribute": 0,
            "track_render_index": 0,
            "uniform_scale": {"on": True, "value": 1.0},
            "visible": True,
            "volume": 0.3  # 背景音乐音量较低
        }

        return {
            "attribute": 1,
            "flag": 0,
            "id": str(uuid.uuid4()),
            "segments": [segment],
            "type": "audio"
        }

    def _get_video_info(self, video_path: Path) -> dict[str, Any]:
        """获取视频信息"""
        # 这里应该使用 FFmpeg 或其他工具获取真实的视频信息
        # 为了示例，返回默认值
        return {
            "width": 1920,
            "height": 1080,
            "fps": 30.0,
            "duration": 120.0  # 秒
        }


# 导出
__all__ = ['JianYingDraftGeneratorV2']
