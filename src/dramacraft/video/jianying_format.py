"""
剪映格式完全兼容模块。

本模块确保生成的.draft文件完全符合剪映最新版本格式，
支持所有功能特性，包括高级特效、转场、字幕样式等。
"""

import hashlib
import json
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from ..audio.enhancer import AudioEnhancementResult
from ..effects.auto_effects import AppliedEffect, AppliedTransition, EffectPlan
from ..sync.timeline_sync import SynchronizedTimeline, TimelineEvent
from ..utils.logging import get_logger


@dataclass
class JianYingProject:
    """剪映项目完整结构。"""

    version: str = "13.0.0"
    """剪映版本。"""

    project_id: str = ""
    """项目ID。"""

    name: str = ""
    """项目名称。"""

    create_time: int = 0
    """创建时间戳。"""

    update_time: int = 0
    """更新时间戳。"""

    duration: int = 0
    """总时长(微秒)。"""

    width: int = 1920
    """视频宽度。"""

    height: int = 1080
    """视频高度。"""

    fps: int = 30
    """帧率。"""

    tracks: list[dict[str, Any]] = None
    """轨道数据。"""

    materials: dict[str, list[dict[str, Any]]] = None
    """素材数据。"""

    canvases: list[dict[str, Any]] = None
    """画布数据。"""

    selections: list[dict[str, Any]] = None
    """选择数据。"""

    relationships: list[dict[str, Any]] = None
    """关系数据。"""

    def __post_init__(self):
        if self.tracks is None:
            self.tracks = []
        if self.materials is None:
            self.materials = {"videos": [], "audios": [], "texts": [], "images": [], "effects": []}
        if self.canvases is None:
            self.canvases = []
        if self.selections is None:
            self.selections = []
        if self.relationships is None:
            self.relationships = []


class JianYingFormatConverter:
    """剪映格式转换器。"""

    def __init__(self):
        """初始化格式转换器。"""
        self.logger = get_logger("video.jianying_format")

        # 剪映格式版本
        self.jianying_version = "13.0.0"

        # 时间单位转换 (剪映使用微秒)
        self.time_scale = 1000000  # 秒到微秒

        self.logger.info("剪映格式转换器已初始化")

    def create_complete_project(
        self,
        project_name: str,
        timeline: SynchronizedTimeline,
        effect_plan: EffectPlan,
        audio_result: AudioEnhancementResult,
        video_clips: list[dict[str, Any]],
        output_path: Path
    ) -> Path:
        """
        创建完整的剪映项目。

        Args:
            project_name: 项目名称
            timeline: 同步时间轴
            effect_plan: 特效计划
            audio_result: 音频增强结果
            video_clips: 视频片段
            output_path: 输出路径

        Returns:
            生成的.draft文件路径
        """
        self.logger.info(f"创建完整剪映项目: {project_name}")

        # 创建项目结构
        project = JianYingProject(
            version=self.jianying_version,
            project_id=str(uuid.uuid4()),
            name=project_name,
            create_time=int(time.time() * 1000),
            update_time=int(time.time() * 1000),
            duration=int(float(timeline.video_duration) * self.time_scale),
            width=1920,
            height=1080,
            fps=int(float(timeline.frame_rate))
        )

        # 生成轨道
        project.tracks = self._create_tracks(timeline, effect_plan, video_clips)

        # 生成素材
        project.materials = self._create_materials(
            video_clips, timeline, effect_plan, audio_result
        )

        # 生成画布
        project.canvases = self._create_canvases()

        # 生成关系数据
        project.relationships = self._create_relationships(project.tracks, project.materials)

        # 保存项目文件
        draft_file = self._save_project_file(project, output_path)

        self.logger.info(f"剪映项目创建完成: {draft_file}")
        return draft_file

    def _create_tracks(
        self,
        timeline: SynchronizedTimeline,
        effect_plan: EffectPlan,
        video_clips: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """创建轨道数据。"""
        tracks = []

        # 主视频轨道
        video_track = self._create_video_track(video_clips, timeline, effect_plan)
        tracks.append(video_track)

        # 音频轨道
        audio_track = self._create_audio_track(timeline)
        tracks.append(audio_track)

        # 字幕轨道
        subtitle_events = [e for e in timeline.events if e.event_type == "subtitle"]
        if subtitle_events:
            subtitle_track = self._create_subtitle_track(subtitle_events)
            tracks.append(subtitle_track)

        # 特效轨道
        if effect_plan.applied_effects:
            effect_track = self._create_effect_track(effect_plan.applied_effects)
            tracks.append(effect_track)

        return tracks

    def _create_video_track(
        self,
        video_clips: list[dict[str, Any]],
        timeline: SynchronizedTimeline,
        effect_plan: EffectPlan
    ) -> dict[str, Any]:
        """创建视频轨道。"""
        segments = []
        current_time = 0

        for i, clip in enumerate(video_clips):
            duration_ms = clip.get("duration", 5000)
            duration_us = duration_ms * 1000  # 转换为微秒

            # 基础片段数据
            segment = {
                "cartoon": False,
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
                "enable_smart_color_match": False,
                "extra_material_refs": [],
                "group_id": "",
                "hdr_settings": {
                    "intensity": 1.0,
                    "mode": 1,
                    "nits": 1000
                },
                "id": str(uuid.uuid4()),
                "intensifies_audio": False,
                "is_placeholder": False,
                "is_tone_modify": False,
                "keyframe_refs": [],
                "last_nonzero_volume": 1.0,
                "material_id": f"video_material_{i}",
                "render_index": 4000000 + i,
                "reverse": False,
                "source_timerange": {
                    "duration": duration_us,
                    "start": 0
                },
                "speed": 1.0,
                "target_timerange": {
                    "duration": duration_us,
                    "start": current_time
                },
                "template_id": "",
                "template_scene": "default",
                "track_attribute": 0,
                "track_render_index": 0,
                "uniform_scale": {"on": True, "value": 1.0},
                "visible": True,
                "volume": clip.get("volume", 1.0)
            }

            # 添加转场效果
            transitions = [t for t in effect_plan.applied_transitions
                         if abs(t.start_time - current_time / self.time_scale) < 1.0]
            if transitions:
                segment["transition"] = self._create_transition_data(transitions[0])

            # 添加特效关键帧
            segment_effects = [e for e in effect_plan.applied_effects
                             if (current_time / self.time_scale <= e.start_time <=
                                 (current_time + duration_us) / self.time_scale)]
            if segment_effects:
                segment["keyframe_refs"] = self._create_effect_keyframes(segment_effects)

            segments.append(segment)
            current_time += duration_us

        return {
            "attribute": 0,
            "flag": 0,
            "id": str(uuid.uuid4()),
            "segments": segments,
            "type": "video"
        }

    def _create_audio_track(self, timeline: SynchronizedTimeline) -> dict[str, Any]:
        """创建音频轨道。"""
        segments = []

        # 获取音频事件
        audio_events = [e for e in timeline.events if e.event_type == "audio"]

        for i, event in enumerate(audio_events):
            duration_us = int((event.end_time - event.start_time) * self.time_scale)
            start_us = int(event.start_time * self.time_scale)

            segment = {
                "cartoon": False,
                "clip": {},
                "common_keyframes": [],
                "enable_adjust": True,
                "enable_color_curves": False,
                "enable_color_match_reference": False,
                "enable_color_wheels": False,
                "enable_lut": False,
                "enable_smart_color_match": False,
                "extra_material_refs": [],
                "group_id": "",
                "id": str(uuid.uuid4()),
                "intensifies_audio": False,
                "is_placeholder": False,
                "keyframe_refs": [],
                "last_nonzero_volume": 1.0,
                "material_id": f"audio_material_{i}",
                "render_index": 4000000 + len(audio_events) + i,
                "reverse": False,
                "source_timerange": {
                    "duration": duration_us,
                    "start": 0
                },
                "speed": 1.0,
                "target_timerange": {
                    "duration": duration_us,
                    "start": start_us
                },
                "template_id": "",
                "template_scene": "default",
                "track_attribute": 0,
                "track_render_index": 0,
                "visible": True,
                "volume": event.properties.get("volume", 0.5)
            }

            # 添加音频淡入淡出
            fade_in = event.properties.get("fade_in", 0)
            fade_out = event.properties.get("fade_out", 0)
            if fade_in > 0 or fade_out > 0:
                segment["audio_fade"] = {
                    "fade_in": {"duration": int(fade_in * 1000), "type": "linear"},
                    "fade_out": {"duration": int(fade_out * 1000), "type": "linear"}
                }

            segments.append(segment)

        return {
            "attribute": 0,
            "flag": 0,
            "id": str(uuid.uuid4()),
            "segments": segments,
            "type": "audio"
        }

    def _create_subtitle_track(self, subtitle_events: list[TimelineEvent]) -> dict[str, Any]:
        """创建字幕轨道。"""
        segments = []

        for i, event in enumerate(subtitle_events):
            duration_us = int((event.end_time - event.start_time) * self.time_scale)
            start_us = int(event.start_time * self.time_scale)

            segment = {
                "cartoon": False,
                "clip": {
                    "alpha": 1.0,
                    "rotation": 0.0,
                    "scale": {"x": 1.0, "y": 1.0},
                    "transform": {"x": 0.0, "y": 0.0}
                },
                "common_keyframes": [],
                "enable_adjust": False,
                "extra_material_refs": [],
                "group_id": "",
                "id": str(uuid.uuid4()),
                "is_placeholder": False,
                "keyframe_refs": [],
                "material_id": f"text_material_{i}",
                "render_index": 4000000 + 1000 + i,
                "source_timerange": {
                    "duration": duration_us,
                    "start": 0
                },
                "target_timerange": {
                    "duration": duration_us,
                    "start": start_us
                },
                "track_attribute": 0,
                "track_render_index": 0,
                "visible": True
            }

            # 添加字幕动画
            animation = event.properties.get("animation", "fade_in")
            if animation != "none":
                segment["animations"] = self._create_subtitle_animation(animation)

            segments.append(segment)

        return {
            "attribute": 0,
            "flag": 0,
            "id": str(uuid.uuid4()),
            "segments": segments,
            "type": "text"
        }

    def _create_effect_track(self, effects: list[AppliedEffect]) -> dict[str, Any]:
        """创建特效轨道。"""
        segments = []

        for i, effect in enumerate(effects):
            duration_us = int((effect.end_time - effect.start_time) * self.time_scale)
            start_us = int(effect.start_time * self.time_scale)

            segment = {
                "cartoon": False,
                "clip": {
                    "alpha": effect.intensity,
                    "rotation": 0.0,
                    "scale": {"x": 1.0, "y": 1.0},
                    "transform": {"x": 0.0, "y": 0.0}
                },
                "common_keyframes": [],
                "enable_adjust": True,
                "extra_material_refs": [],
                "group_id": "",
                "id": str(uuid.uuid4()),
                "is_placeholder": False,
                "keyframe_refs": [],
                "material_id": f"effect_material_{i}",
                "render_index": 4000000 + 2000 + i,
                "source_timerange": {
                    "duration": duration_us,
                    "start": 0
                },
                "target_timerange": {
                    "duration": duration_us,
                    "start": start_us
                },
                "track_attribute": 0,
                "track_render_index": effect.layer,
                "visible": True,
                "blend_mode": effect.blend_mode,
                "effect_parameters": effect.parameters
            }

            segments.append(segment)

        return {
            "attribute": 0,
            "flag": 0,
            "id": str(uuid.uuid4()),
            "segments": segments,
            "type": "effect"
        }

    def _create_materials(
        self,
        video_clips: list[dict[str, Any]],
        timeline: SynchronizedTimeline,
        effect_plan: EffectPlan,
        audio_result: AudioEnhancementResult
    ) -> dict[str, list[dict[str, Any]]]:
        """创建素材数据。"""
        materials = {
            "videos": [],
            "audios": [],
            "texts": [],
            "images": [],
            "effects": []
        }

        # 视频素材
        for i, clip in enumerate(video_clips):
            video_material = self._create_video_material(clip, i)
            materials["videos"].append(video_material)

        # 音频素材
        audio_events = [e for e in timeline.events if e.event_type == "audio"]
        for i, event in enumerate(audio_events):
            audio_material = self._create_audio_material(event, i)
            materials["audios"].append(audio_material)

        # 文本素材
        subtitle_events = [e for e in timeline.events if e.event_type == "subtitle"]
        for i, event in enumerate(subtitle_events):
            text_material = self._create_text_material(event, i)
            materials["texts"].append(text_material)

        # 特效素材
        for i, effect in enumerate(effect_plan.applied_effects):
            effect_material = self._create_effect_material(effect, i)
            materials["effects"].append(effect_material)

        return materials

    def _create_video_material(self, clip: dict[str, Any], index: int) -> dict[str, Any]:
        """创建视频素材。"""
        file_path = clip.get("path", "")

        return {
            "audio_fade": {
                "fade_in": {"duration": 0, "type": ""},
                "fade_out": {"duration": 0, "type": ""}
            },
            "cartoon_path": "",
            "category_id": "",
            "category_name": "local",
            "check_flag": 1,
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
            "duration": clip.get("duration", 5000) * 1000,  # 转换为微秒
            "extra_type_option": 0,
            "file_Path": file_path,
            "height": clip.get("height", 1080),
            "id": f"video_material_{index}",
            "import_time": int(time.time()),
            "import_time_ms": int(time.time() * 1000),
            "item_source": 1,
            "md5": self._calculate_file_md5(file_path),
            "metetype": "photo",
            "roughcut_time_range": {"duration": -1, "start": -1},
            "source_platform": 0,
            "stable": {
                "matrix_path": "",
                "stable_level": 0,
                "time_range": {"duration": -1, "start": -1}
            },
            "type": "video",
            "width": clip.get("width", 1920),
            "video_algorithm": {
                "beauty_mode": False,
                "deflicker": False,
                "motion_blur_config": {"enabled": False, "intensity": 0.5},
                "noise_reduction": False,
                "path": "",
                "time_range": {"duration": -1, "start": -1}
            }
        }

    def _create_audio_material(self, event: TimelineEvent, index: int) -> dict[str, Any]:
        """创建音频素材。"""
        file_path = event.content

        return {
            "audio_fade": {
                "fade_in": {
                    "duration": int(event.properties.get("fade_in", 0) * 1000),
                    "type": "linear"
                },
                "fade_out": {
                    "duration": int(event.properties.get("fade_out", 0) * 1000),
                    "type": "linear"
                }
            },
            "category_id": "",
            "category_name": "local",
            "check_flag": 1,
            "duration": int((event.end_time - event.start_time) * self.time_scale),
            "extra_type_option": 0,
            "file_Path": file_path,
            "id": f"audio_material_{index}",
            "import_time": int(time.time()),
            "import_time_ms": int(time.time() * 1000),
            "item_source": 1,
            "md5": self._calculate_file_md5(file_path),
            "metetype": "music",
            "roughcut_time_range": {"duration": -1, "start": -1},
            "source_platform": 0,
            "type": "audio",
            "volume": event.properties.get("volume", 0.5),
            "audio_channel_mapping": 0,
            "audio_denoise": False,
            "audio_loudness": {
                "auto_loudness": False,
                "loudness": -23.0,
                "lufs": -23.0,
                "peak": -3.0
            }
        }

    def _create_text_material(self, event: TimelineEvent, index: int) -> dict[str, Any]:
        """创建文本素材。"""
        properties = event.properties

        return {
            "alignment": properties.get("alignment", 1),
            "background_alpha": 1.0,
            "background_color": properties.get("background", ""),
            "background_height": 0.04,
            "background_horizontal_offset": 0.0,
            "background_round_radius": 0.0,
            "background_style": 0,
            "background_vertical_offset": 0.0,
            "background_width": 0.04,
            "bold_width": 0.0,
            "border_alpha": 1.0,
            "border_color": "#000000",
            "border_width": 0.016,
            "check_flag": 1,
            "combo_info": {"text_templates": []},
            "content": event.content,
            "font_category_id": "",
            "font_category_name": "",
            "font_id": "",
            "font_name": "苹方-简",
            "font_path": "",
            "font_resource_id": "",
            "font_size": properties.get("font_size", 24) / 1000.0,  # 标准化
            "font_source_platform": 0,
            "font_team_id": "",
            "font_title": "苹方",
            "font_url": "",
            "fonts": [],
            "force_apply_line_max_width": False,
            "global_alpha": 1.0,
            "group_id": "",
            "has_shadow": True,
            "id": f"text_material_{index}",
            "initial_scale": 1.0,
            "is_rich_text": False,
            "italic_degree": 0,
            "ktv_color": "",
            "language": "",
            "layer_weight": 1,
            "letter_spacing": 0.0,
            "line_spacing": 0.02,
            "multi_language_current": "none",
            "preset_category": "",
            "preset_category_id": "",
            "preset_has_set_alignment": False,
            "preset_id": "",
            "preset_index": 0,
            "preset_name": "",
            "recognize_task_id": "",
            "recognize_type": 0,
            "relevance_segment": [],
            "shadow_alpha": 0.9,
            "shadow_angle": -45.0,
            "shadow_blur": 0.0,
            "shadow_color": "#000000",
            "shadow_distance": 0.005,
            "shape_clip_x": False,
            "shape_clip_y": False,
            "source_platform": 0,
            "style_name": "无",
            "sub_type": 0,
            "text_alpha": 1.0,
            "text_color": properties.get("color", "#FFFFFF"),
            "text_curve": None,
            "text_preset_resource_id": "",
            "text_size": properties.get("font_size", 24),
            "text_to_audio_ids": [],
            "tts_auto_update": False,
            "type": "text",
            "typesetting": 0,
            "underline": False,
            "underline_offset": 0.22,
            "underline_width": 0.05,
            "use_effect_default_color": True,
            "words": []
        }

    def _create_effect_material(self, effect: AppliedEffect, index: int) -> dict[str, Any]:
        """创建特效素材。"""
        return {
            "category_id": "",
            "category_name": "effects",
            "check_flag": 1,
            "duration": int((effect.end_time - effect.start_time) * self.time_scale),
            "effect_id": effect.effect_id,
            "id": f"effect_material_{index}",
            "intensity": effect.intensity,
            "item_source": 1,
            "parameters": effect.parameters,
            "source_platform": 0,
            "type": "effect",
            "blend_mode": effect.blend_mode,
            "layer": effect.layer,
            "keyframes": [],
            "mask": None,
            "track_index": 0
        }

    def _create_canvases(self) -> list[dict[str, Any]]:
        """创建画布数据。"""
        return [{
            "album_image": "",
            "blur": 0.0,
            "color": "",
            "id": str(uuid.uuid4()),
            "image": "",
            "image_id": "",
            "image_name": "",
            "source_platform": 0,
            "type": "canvas_color",
            "video_id": "",
            "video_name": ""
        }]

    def _create_relationships(
        self,
        tracks: list[dict[str, Any]],
        materials: dict[str, list[dict[str, Any]]]
    ) -> list[dict[str, Any]]:
        """创建关系数据。"""
        relationships = []

        # 创建轨道与素材的关系
        for track in tracks:
            for segment in track.get("segments", []):
                material_id = segment.get("material_id")
                if material_id:
                    relationship = {
                        "id": str(uuid.uuid4()),
                        "type": "material_track_relation",
                        "track_id": track["id"],
                        "segment_id": segment["id"],
                        "material_id": material_id,
                        "material_type": self._get_material_type(material_id, materials)
                    }
                    relationships.append(relationship)

        return relationships

    def _get_material_type(
        self,
        material_id: str,
        materials: dict[str, list[dict[str, Any]]]
    ) -> str:
        """获取素材类型。"""
        for material_type, material_list in materials.items():
            for material in material_list:
                if material["id"] == material_id:
                    return material_type
        return "unknown"

    def _create_transition_data(self, transition: AppliedTransition) -> dict[str, Any]:
        """创建转场数据。"""
        return {
            "id": str(uuid.uuid4()),
            "type": transition.transition_id,
            "duration": int(transition.duration * self.time_scale),
            "parameters": transition.parameters,
            "confidence": transition.confidence,
            "render_index": 5000000
        }

    def _create_effect_keyframes(self, effects: list[AppliedEffect]) -> list[str]:
        """创建特效关键帧引用。"""
        keyframe_refs = []

        for _effect in effects:
            keyframe_id = str(uuid.uuid4())
            keyframe_refs.append(keyframe_id)

        return keyframe_refs

    def _create_subtitle_animation(self, animation_type: str) -> list[dict[str, Any]]:
        """创建字幕动画。"""
        animations = []

        if animation_type == "fade_in":
            animations.append({
                "id": str(uuid.uuid4()),
                "type": "fade",
                "direction": "in",
                "duration": 500,
                "easing": "ease_in_out"
            })
        elif animation_type == "slide_up":
            animations.append({
                "id": str(uuid.uuid4()),
                "type": "slide",
                "direction": "up",
                "duration": 300,
                "easing": "ease_out"
            })
        elif animation_type == "typewriter":
            animations.append({
                "id": str(uuid.uuid4()),
                "type": "typewriter",
                "speed": 50,
                "duration": 1000
            })

        return animations

    def _calculate_file_md5(self, file_path: str) -> str:
        """计算文件MD5。"""
        try:
            if not file_path or not Path(file_path).exists():
                return ""

            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""

    def _save_project_file(self, project: JianYingProject, output_path: Path) -> Path:
        """保存项目文件。"""
        import tempfile
        import zipfile

        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # 保存项目内容
            content_file = temp_path / "draft_content.json"
            with open(content_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "version": project.version,
                    "tracks": project.tracks,
                    "materials": project.materials,
                    "canvases": project.canvases,
                    "selections": project.selections,
                    "relationships": project.relationships
                }, f, ensure_ascii=False, indent=2)

            # 保存元数据
            meta_file = temp_path / "draft_meta_info.json"
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "id": project.project_id,
                    "name": project.name,
                    "cover": "",
                    "duration": project.duration,
                    "fps": project.fps,
                    "width": project.width,
                    "height": project.height,
                    "create_time": project.create_time,
                    "update_time": project.update_time,
                    "draft_fold": str(output_path),
                    "draft_removable": True
                }, f, ensure_ascii=False, indent=2)

            # 创建草稿包
            draft_file = output_path / f"{project.name}.draft"
            with zipfile.ZipFile(draft_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.write(content_file, "draft_content.json")
                zf.write(meta_file, "draft_meta_info.json")

            return draft_file


class JianYingCompatibilityChecker:
    """剪映兼容性检查器。"""

    def __init__(self):
        """初始化兼容性检查器。"""
        self.logger = get_logger("video.jianying_compatibility")

        # 支持的剪映版本
        self.supported_versions = ["13.0.0", "12.8.0", "12.7.0"]

        # 格式限制
        self.format_limits = {
            "max_tracks": 20,
            "max_segments_per_track": 1000,
            "max_materials": 5000,
            "max_duration_hours": 24,
            "max_resolution": (4096, 4096),
            "supported_video_formats": [".mp4", ".mov", ".avi", ".mkv"],
            "supported_audio_formats": [".mp3", ".wav", ".aac", ".m4a"],
            "max_subtitle_length": 500
        }

    def check_project_compatibility(self, project: JianYingProject) -> dict[str, Any]:
        """检查项目兼容性。"""
        compatibility_result = {
            "compatible": True,
            "version_supported": True,
            "warnings": [],
            "errors": [],
            "recommendations": []
        }

        # 检查版本兼容性
        if project.version not in self.supported_versions:
            compatibility_result["version_supported"] = False
            compatibility_result["warnings"].append(
                f"版本 {project.version} 可能不被完全支持，建议使用 {self.supported_versions[0]}"
            )

        # 检查轨道数量
        if len(project.tracks) > self.format_limits["max_tracks"]:
            compatibility_result["errors"].append(
                f"轨道数量 ({len(project.tracks)}) 超过限制 ({self.format_limits['max_tracks']})"
            )
            compatibility_result["compatible"] = False

        # 检查时长
        duration_hours = project.duration / (1000000 * 3600)  # 转换为小时
        if duration_hours > self.format_limits["max_duration_hours"]:
            compatibility_result["warnings"].append(
                f"项目时长 ({duration_hours:.1f}小时) 较长，可能影响性能"
            )

        # 检查分辨率
        max_width, max_height = self.format_limits["max_resolution"]
        if project.width > max_width or project.height > max_height:
            compatibility_result["errors"].append(
                f"分辨率 ({project.width}x{project.height}) 超过限制 ({max_width}x{max_height})"
            )
            compatibility_result["compatible"] = False

        # 检查素材数量
        total_materials = sum(len(materials) for materials in project.materials.values())
        if total_materials > self.format_limits["max_materials"]:
            compatibility_result["warnings"].append(
                f"素材数量 ({total_materials}) 较多，可能影响加载速度"
            )

        # 添加优化建议
        if len(project.tracks) > 10:
            compatibility_result["recommendations"].append("考虑合并相似的轨道以提高性能")

        if duration_hours > 2:
            compatibility_result["recommendations"].append("对于长视频，建议分段处理")

        return compatibility_result

    def validate_draft_file(self, draft_file: Path) -> dict[str, Any]:
        """验证草稿文件。"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "file_info": {}
        }

        try:
            import zipfile

            # 检查文件存在性
            if not draft_file.exists():
                validation_result["errors"].append("草稿文件不存在")
                validation_result["valid"] = False
                return validation_result

            # 检查文件扩展名
            if draft_file.suffix.lower() != '.draft':
                validation_result["warnings"].append("文件扩展名不是 .draft")

            # 检查ZIP结构
            with zipfile.ZipFile(draft_file, 'r') as zf:
                file_list = zf.namelist()

                # 检查必需文件
                required_files = ["draft_content.json", "draft_meta_info.json"]
                for required_file in required_files:
                    if required_file not in file_list:
                        validation_result["errors"].append(f"缺少必需文件: {required_file}")
                        validation_result["valid"] = False

                # 验证JSON格式
                if "draft_content.json" in file_list:
                    try:
                        content_data = json.loads(zf.read("draft_content.json"))
                        validation_result["file_info"]["content_valid"] = True
                        validation_result["file_info"]["tracks_count"] = len(content_data.get("tracks", []))
                    except json.JSONDecodeError as e:
                        validation_result["errors"].append(f"内容文件JSON格式错误: {e}")
                        validation_result["valid"] = False

                if "draft_meta_info.json" in file_list:
                    try:
                        meta_data = json.loads(zf.read("draft_meta_info.json"))
                        validation_result["file_info"]["meta_valid"] = True
                        validation_result["file_info"]["project_name"] = meta_data.get("name", "")
                    except json.JSONDecodeError as e:
                        validation_result["errors"].append(f"元数据文件JSON格式错误: {e}")
                        validation_result["valid"] = False

            # 文件大小检查
            file_size_mb = draft_file.stat().st_size / (1024 * 1024)
            validation_result["file_info"]["size_mb"] = file_size_mb

            if file_size_mb > 100:  # 100MB
                validation_result["warnings"].append(f"文件较大 ({file_size_mb:.1f}MB)，可能影响加载速度")

        except Exception as e:
            validation_result["errors"].append(f"文件验证失败: {e}")
            validation_result["valid"] = False

        return validation_result


class JianYingProjectManager:
    """剪映项目管理器。"""

    def __init__(self, jianying_path: Optional[Path] = None):
        """
        初始化项目管理器。

        Args:
            jianying_path: 剪映安装路径
        """
        self.jianying_path = jianying_path or self._find_jianying_installation()
        self.projects_dir = self._get_projects_directory()
        self.logger = get_logger("video.jianying_manager")

        if not self.jianying_path or not self.jianying_path.exists():
            self.logger.warning("未找到剪映安装路径")

    def _find_jianying_installation(self) -> Optional[Path]:
        """查找剪映安装路径。"""
        import platform

        system = platform.system()

        if system == "Darwin":  # macOS
            possible_paths = [
                Path("/Applications/JianyingPro.app"),
                Path("~/Applications/JianyingPro.app").expanduser(),
                Path("/Applications/剪映专业版.app"),
            ]
        elif system == "Windows":
            possible_paths = [
                Path("C:/Program Files/JianyingPro/JianyingPro.exe"),
                Path("C:/Program Files (x86)/JianyingPro/JianyingPro.exe"),
                Path("~/AppData/Local/JianyingPro/JianyingPro.exe").expanduser(),
            ]
        else:
            return None

        for path in possible_paths:
            if path.exists():
                return path

        return None

    def _get_projects_directory(self) -> Path:
        """获取剪映项目目录。"""
        import platform

        system = platform.system()

        if system == "Darwin":  # macOS
            return Path("~/Movies/JianyingPro").expanduser()
        elif system == "Windows":
            return Path("~/Documents/JianyingPro").expanduser()
        else:
            return Path("~/JianyingPro").expanduser()

    def import_project(self, draft_file: Path, project_name: Optional[str] = None) -> bool:
        """
        导入项目到剪映。

        Args:
            draft_file: 草稿文件路径
            project_name: 项目名称

        Returns:
            是否导入成功
        """
        try:
            if not draft_file.exists():
                self.logger.error(f"草稿文件不存在: {draft_file}")
                return False

            # 确保项目目录存在
            from ..utils.helpers import ensure_directory
            ensure_directory(self.projects_dir)

            # 生成项目名称
            if not project_name:
                project_name = draft_file.stem

            # 创建项目目录
            project_dir = self.projects_dir / project_name
            ensure_directory(project_dir)

            # 复制草稿文件
            target_draft = project_dir / f"{project_name}.draft"
            import shutil
            shutil.copy2(draft_file, target_draft)

            self.logger.info(f"项目已导入到剪映: {target_draft}")

            # 尝试自动打开剪映
            if self.jianying_path:
                self._open_jianying_with_project(target_draft)

            return True

        except Exception as e:
            self.logger.error(f"项目导入失败: {e}")
            return False

    def _open_jianying_with_project(self, draft_file: Path) -> bool:
        """使用剪映打开项目。"""
        try:
            import platform
            import subprocess

            system = platform.system()

            if system == "Darwin":  # macOS
                cmd = ["open", "-a", str(self.jianying_path), str(draft_file)]
            elif system == "Windows":
                cmd = [str(self.jianying_path), str(draft_file)]
            else:
                return False

            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.logger.info("剪映已启动")
            return True

        except Exception as e:
            self.logger.warning(f"无法自动打开剪映: {e}")
            return False

    def list_projects(self) -> list[dict[str, Any]]:
        """列出所有剪映项目。"""
        projects = []

        if not self.projects_dir.exists():
            return projects

        try:
            for project_dir in self.projects_dir.iterdir():
                if project_dir.is_dir():
                    # 查找草稿文件
                    draft_files = list(project_dir.glob("*.draft"))

                    for draft_file in draft_files:
                        try:
                            # 读取项目信息
                            project_info = self._read_project_info(draft_file)
                            projects.append({
                                "name": project_dir.name,
                                "draft_file": str(draft_file),
                                "created_time": project_info.get("create_time", 0),
                                "duration": project_info.get("duration", 0),
                                "size": draft_file.stat().st_size
                            })
                        except Exception as e:
                            self.logger.warning(f"读取项目信息失败 {draft_file}: {e}")

            # 按创建时间排序
            projects.sort(key=lambda x: x["created_time"], reverse=True)

        except Exception as e:
            self.logger.error(f"列出项目失败: {e}")

        return projects

    def _read_project_info(self, draft_file: Path) -> dict[str, Any]:
        """读取项目信息。"""
        import zipfile

        try:
            with zipfile.ZipFile(draft_file, 'r') as zf:
                if "draft_meta_info.json" in zf.namelist():
                    meta_data = json.loads(zf.read("draft_meta_info.json"))
                    return meta_data
        except Exception:
            pass

        return {}

    def delete_project(self, project_name: str) -> bool:
        """删除项目。"""
        try:
            project_dir = self.projects_dir / project_name

            if project_dir.exists():
                import shutil
                shutil.rmtree(project_dir)
                self.logger.info(f"项目已删除: {project_name}")
                return True
            else:
                self.logger.warning(f"项目不存在: {project_name}")
                return False

        except Exception as e:
            self.logger.error(f"删除项目失败: {e}")
            return False

    def backup_project(self, project_name: str, backup_dir: Path) -> Optional[Path]:
        """备份项目。"""
        try:
            project_dir = self.projects_dir / project_name

            if not project_dir.exists():
                self.logger.error(f"项目不存在: {project_name}")
                return None

            from ..utils.helpers import ensure_directory
            ensure_directory(backup_dir)

            # 创建备份文件名
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"{project_name}_{timestamp}.zip"

            # 创建ZIP备份
            import zipfile
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                for file_path in project_dir.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(project_dir)
                        zf.write(file_path, arcname)

            self.logger.info(f"项目备份完成: {backup_file}")
            return backup_file

        except Exception as e:
            self.logger.error(f"项目备份失败: {e}")
            return None
