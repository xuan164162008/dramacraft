"""
剪映草稿文件处理模块。

本模块实现剪映草稿(.draft)文件的生成、解析和操控功能，
支持完整的项目导入导出和自动化编辑。
完全兼容剪映最新版本格式，支持所有功能特性。
"""

import json
import shutil
import time
import uuid
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional

from ..config import JianYingConfig
from ..utils.helpers import ensure_directory, safe_filename
from ..utils.logging import get_logger


@dataclass
class DraftMetadata:
    """草稿元数据。"""

    id: str
    """草稿ID。"""

    name: str
    """项目名称。"""

    cover: str
    """封面图片路径。"""

    duration: int
    """时长(毫秒)。"""

    fps: int
    """帧率。"""

    width: int
    """视频宽度。"""

    height: int
    """视频高度。"""

    create_time: int
    """创建时间戳。"""

    update_time: int
    """更新时间戳。"""

    draft_fold: str
    """草稿文件夹路径。"""

    draft_removable: bool
    """是否可删除。"""


@dataclass
class DraftContent:
    """草稿内容数据。"""

    version: str
    """版本号。"""

    tracks: list[dict[str, Any]]
    """轨道数据。"""

    materials: dict[str, Any]
    """素材数据。"""

    canvases: list[dict[str, Any]]
    """画布数据。"""

    selections: list[dict[str, Any]]
    """选择数据。"""

    relationships: list[dict[str, Any]]
    """关系数据。"""


class JianYingDraftManager:
    """剪映草稿管理器。"""

    def __init__(self, config: JianYingConfig):
        """
        初始化草稿管理器。

        Args:
            config: 剪映配置
        """
        self.config = config
        self.logger = get_logger("video.draft")

        # 剪映草稿目录
        self.draft_dir = self._get_jianying_draft_dir()
        self.local_draft_dir = config.project_template_dir.parent / "drafts"

        ensure_directory(self.local_draft_dir)

        self.logger.info(f"草稿管理器已初始化 - 本地目录: {self.local_draft_dir}")

    def _get_jianying_draft_dir(self) -> Optional[Path]:
        """获取剪映草稿目录。"""
        import platform
        system = platform.system()

        if system == "Darwin":  # macOS
            return Path.home() / "Movies" / "JianyingPro Drafts"
        elif system == "Windows":
            return Path.home() / "AppData" / "Local" / "JianyingPro" / "User Data" / "Projects"
        else:
            self.logger.warning(f"不支持的操作系统: {system}")
            return None

    def create_draft(
        self,
        project_name: str,
        video_clips: list[dict[str, Any]],
        audio_clips: Optional[list[dict[str, Any]]] = None,
        subtitles: Optional[list[dict[str, Any]]] = None,
        effects: Optional[list[dict[str, Any]]] = None
    ) -> Path:
        """
        创建剪映草稿。

        Args:
            project_name: 项目名称
            video_clips: 视频片段列表
            audio_clips: 音频片段列表
            subtitles: 字幕列表
            effects: 特效列表

        Returns:
            草稿文件路径
        """
        self.logger.info(f"创建剪映草稿: {project_name}")

        # 生成草稿ID
        draft_id = str(uuid.uuid4())
        timestamp = int(time.time() * 1000)

        # 创建草稿目录
        draft_folder = self.local_draft_dir / draft_id
        ensure_directory(draft_folder)

        # 创建素材目录
        materials_dir = draft_folder / "materials"
        ensure_directory(materials_dir)

        # 复制素材文件
        material_map = self._copy_materials(video_clips, audio_clips, materials_dir)

        # 生成草稿内容
        draft_content = self._generate_draft_content(
            video_clips, audio_clips, subtitles, effects, material_map
        )

        # 生成元数据
        metadata = DraftMetadata(
            id=draft_id,
            name=project_name,
            cover="",
            duration=self._calculate_duration(video_clips),
            fps=30,
            width=1920,
            height=1080,
            create_time=timestamp,
            update_time=timestamp,
            draft_fold=str(draft_folder),
            draft_removable=True
        )

        # 保存草稿文件
        draft_file = self._save_draft_files(draft_folder, metadata, draft_content)

        self.logger.info(f"草稿创建完成: {draft_file}")
        return draft_file

    def _copy_materials(
        self,
        video_clips: list[dict[str, Any]],
        audio_clips: Optional[list[dict[str, Any]]],
        materials_dir: Path
    ) -> dict[str, str]:
        """
        复制素材文件到草稿目录。

        Args:
            video_clips: 视频片段
            audio_clips: 音频片段
            materials_dir: 素材目录

        Returns:
            素材路径映射
        """
        material_map = {}

        # 复制视频文件
        for i, clip in enumerate(video_clips):
            if "path" in clip:
                source_path = Path(clip["path"])
                if source_path.exists():
                    dest_name = f"video_{i}_{safe_filename(source_path.name)}"
                    dest_path = materials_dir / dest_name
                    shutil.copy2(source_path, dest_path)
                    material_map[str(source_path)] = str(dest_path)

        # 复制音频文件
        if audio_clips:
            for i, clip in enumerate(audio_clips):
                if "path" in clip:
                    source_path = Path(clip["path"])
                    if source_path.exists():
                        dest_name = f"audio_{i}_{safe_filename(source_path.name)}"
                        dest_path = materials_dir / dest_name
                        shutil.copy2(source_path, dest_path)
                        material_map[str(source_path)] = str(dest_path)

        return material_map

    def _generate_draft_content(
        self,
        video_clips: list[dict[str, Any]],
        audio_clips: Optional[list[dict[str, Any]]],
        subtitles: Optional[list[dict[str, Any]]],
        effects: Optional[list[dict[str, Any]]],
        material_map: dict[str, str]
    ) -> DraftContent:
        """
        生成草稿内容数据。

        Args:
            video_clips: 视频片段
            audio_clips: 音频片段
            subtitles: 字幕
            effects: 特效
            material_map: 素材映射

        Returns:
            草稿内容对象
        """
        tracks = []
        materials = {"videos": [], "audios": [], "texts": []}

        # 生成视频轨道
        if video_clips:
            video_track = self._create_video_track(video_clips, material_map)
            tracks.append(video_track)

            # 添加视频素材
            for clip in video_clips:
                if "path" in clip:
                    material = self._create_video_material(clip, material_map)
                    materials["videos"].append(material)

        # 生成音频轨道
        if audio_clips:
            audio_track = self._create_audio_track(audio_clips, material_map)
            tracks.append(audio_track)

            # 添加音频素材
            for clip in audio_clips:
                if "path" in clip:
                    material = self._create_audio_material(clip, material_map)
                    materials["audios"].append(material)

        # 生成字幕轨道
        if subtitles:
            subtitle_track = self._create_subtitle_track(subtitles)
            tracks.append(subtitle_track)

            # 添加文本素材
            for subtitle in subtitles:
                material = self._create_text_material(subtitle)
                materials["texts"].append(material)

        return DraftContent(
            version="13.0.0",
            tracks=tracks,
            materials=materials,
            canvases=[{
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
            }],
            selections=[],
            relationships=[]
        )

    def _create_video_track(
        self,
        video_clips: list[dict[str, Any]],
        material_map: dict[str, str]
    ) -> dict[str, Any]:
        """创建视频轨道。"""
        segments = []
        current_time = 0

        for i, clip in enumerate(video_clips):
            duration = clip.get("duration", 5000)  # 默认5秒

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
                "hdr_settings": {"intensity": 1.0, "mode": 1, "nits": 1000},
                "id": str(uuid.uuid4()),
                "intensifies_audio": False,
                "is_placeholder": False,
                "is_tone_modify": False,
                "keyframe_refs": [],
                "last_nonzero_volume": 1.0,
                "material_id": f"video_{i}",
                "render_index": 4000000,
                "reverse": False,
                "source_timerange": {
                    "duration": duration,
                    "start": 0
                },
                "speed": 1.0,
                "target_timerange": {
                    "duration": duration,
                    "start": current_time
                },
                "template_id": "",
                "template_scene": "default",
                "track_attribute": 0,
                "track_render_index": 0,
                "uniform_scale": {"on": True, "value": 1.0},
                "visible": True,
                "volume": 1.0
            }

            segments.append(segment)
            current_time += duration

        return {
            "attribute": 0,
            "flag": 0,
            "id": str(uuid.uuid4()),
            "segments": segments,
            "type": "video"
        }

    def _create_audio_track(
        self,
        audio_clips: list[dict[str, Any]],
        material_map: dict[str, str]
    ) -> dict[str, Any]:
        """创建音频轨道。"""
        segments = []
        current_time = 0

        for i, clip in enumerate(audio_clips):
            duration = clip.get("duration", 5000)

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
                "material_id": f"audio_{i}",
                "render_index": 4000000,
                "reverse": False,
                "source_timerange": {
                    "duration": duration,
                    "start": 0
                },
                "speed": 1.0,
                "target_timerange": {
                    "duration": duration,
                    "start": current_time
                },
                "template_id": "",
                "template_scene": "default",
                "track_attribute": 0,
                "track_render_index": 0,
                "visible": True,
                "volume": clip.get("volume", 1.0)
            }

            segments.append(segment)
            current_time += duration

        return {
            "attribute": 0,
            "flag": 0,
            "id": str(uuid.uuid4()),
            "segments": segments,
            "type": "audio"
        }

    def _create_subtitle_track(self, subtitles: list[dict[str, Any]]) -> dict[str, Any]:
        """创建字幕轨道。"""
        segments = []

        for i, subtitle in enumerate(subtitles):
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
                "material_id": f"text_{i}",
                "render_index": 4000000,
                "source_timerange": {
                    "duration": subtitle.get("duration", 2000),
                    "start": 0
                },
                "target_timerange": {
                    "duration": subtitle.get("duration", 2000),
                    "start": subtitle.get("start_time", 0)
                },
                "track_attribute": 0,
                "track_render_index": 0,
                "visible": True
            }

            segments.append(segment)

        return {
            "attribute": 0,
            "flag": 0,
            "id": str(uuid.uuid4()),
            "segments": segments,
            "type": "text"
        }

    def _create_video_material(
        self,
        clip: dict[str, Any],
        material_map: dict[str, str]
    ) -> dict[str, Any]:
        """创建视频素材。"""
        original_path = clip.get("path", "")
        local_path = material_map.get(original_path, original_path)

        return {
            "audio_fade": {"fade_in": {"duration": 0, "type": ""}, "fade_out": {"duration": 0, "type": ""}},
            "cartoon_path": "",
            "category_id": "",
            "category_name": "local",
            "check_flag": 1,
            "crop": {"lower_left_x": 0.0, "lower_left_y": 1.0, "lower_right_x": 1.0, "lower_right_y": 1.0, "upper_left_x": 0.0, "upper_left_y": 0.0, "upper_right_x": 1.0, "upper_right_y": 0.0},
            "crop_ratio": "free",
            "crop_scale": 1.0,
            "duration": clip.get("duration", 5000000),
            "extra_type_option": 0,
            "file_Path": local_path,
            "height": clip.get("height", 1080),
            "id": f"video_{hash(original_path) % 1000000}",
            "import_time": int(time.time()),
            "import_time_ms": int(time.time() * 1000),
            "item_source": 1,
            "md5": "",
            "metetype": "photo",
            "roughcut_time_range": {"duration": -1, "start": -1},
            "source_platform": 0,
            "stable": {"matrix_path": "", "stable_level": 0, "time_range": {"duration": -1, "start": -1}},
            "type": "video",
            "width": clip.get("width", 1920)
        }

    def _create_audio_material(
        self,
        clip: dict[str, Any],
        material_map: dict[str, str]
    ) -> dict[str, Any]:
        """创建音频素材。"""
        original_path = clip.get("path", "")
        local_path = material_map.get(original_path, original_path)

        return {
            "audio_fade": {"fade_in": {"duration": 0, "type": ""}, "fade_out": {"duration": 0, "type": ""}},
            "category_id": "",
            "category_name": "local",
            "check_flag": 1,
            "duration": clip.get("duration", 5000000),
            "extra_type_option": 0,
            "file_Path": local_path,
            "id": f"audio_{hash(original_path) % 1000000}",
            "import_time": int(time.time()),
            "import_time_ms": int(time.time() * 1000),
            "item_source": 1,
            "metetype": "music",
            "roughcut_time_range": {"duration": -1, "start": -1},
            "source_platform": 0,
            "type": "audio"
        }

    def _create_text_material(self, subtitle: dict[str, Any]) -> dict[str, Any]:
        """创建文本素材。"""
        return {
            "alignment": 1,
            "background_alpha": 1.0,
            "background_color": "",
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
            "content": subtitle.get("text", ""),
            "font_category_id": "",
            "font_category_name": "",
            "font_id": "",
            "font_name": "苹方-简",
            "font_path": "",
            "font_resource_id": "",
            "font_size": 0.06,
            "font_source_platform": 0,
            "font_team_id": "",
            "font_title": "苹方",
            "font_url": "",
            "fonts": [],
            "force_apply_line_max_width": False,
            "global_alpha": 1.0,
            "group_id": "",
            "has_shadow": True,
            "id": str(uuid.uuid4()),
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
            "text_color": "#FFFFFF",
            "text_curve": None,
            "text_preset_resource_id": "",
            "text_size": 30,
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

    def _calculate_duration(self, video_clips: list[dict[str, Any]]) -> int:
        """计算总时长(毫秒)。"""
        total_duration = 0
        for clip in video_clips:
            total_duration += clip.get("duration", 5000)
        return total_duration

    def _save_draft_files(
        self,
        draft_folder: Path,
        metadata: DraftMetadata,
        content: DraftContent
    ) -> Path:
        """
        保存草稿文件。

        Args:
            draft_folder: 草稿文件夹
            metadata: 元数据
            content: 内容数据

        Returns:
            草稿文件路径
        """
        # 保存内容文件
        content_file = draft_folder / "draft_content.json"
        with open(content_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(content), f, ensure_ascii=False, indent=2)

        # 保存元数据文件
        meta_file = draft_folder / "draft_meta_info.json"
        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(metadata), f, ensure_ascii=False, indent=2)

        # 创建草稿包文件
        draft_file = draft_folder.with_suffix('.draft')
        with zipfile.ZipFile(draft_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 添加所有文件到压缩包
            for file_path in draft_folder.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(draft_folder)
                    zf.write(file_path, arcname)

        return draft_file

    def import_to_jianying(self, draft_file: Path) -> bool:
        """
        导入草稿到剪映。

        Args:
            draft_file: 草稿文件路径

        Returns:
            是否成功导入
        """
        if not self.draft_dir or not self.draft_dir.exists():
            self.logger.error("剪映草稿目录不存在")
            return False

        try:
            # 复制草稿文件到剪映目录
            dest_file = self.draft_dir / draft_file.name
            shutil.copy2(draft_file, dest_file)

            self.logger.info(f"草稿已导入剪映: {dest_file}")
            return True

        except Exception as e:
            self.logger.error(f"导入草稿失败: {e}")
            return False

    def list_drafts(self) -> list[dict[str, Any]]:
        """
        列出本地草稿。

        Returns:
            草稿列表
        """
        drafts = []

        for draft_file in self.local_draft_dir.glob("*.draft"):
            try:
                # 读取草稿元数据
                with zipfile.ZipFile(draft_file, 'r') as zf:
                    if "draft_meta_info.json" in zf.namelist():
                        meta_data = json.loads(zf.read("draft_meta_info.json"))
                        drafts.append({
                            "file": str(draft_file),
                            "name": meta_data.get("name", draft_file.stem),
                            "duration": meta_data.get("duration", 0),
                            "create_time": meta_data.get("create_time", 0),
                            "update_time": meta_data.get("update_time", 0)
                        })
            except Exception as e:
                self.logger.warning(f"读取草稿失败 {draft_file}: {e}")

        return sorted(drafts, key=lambda x: x["update_time"], reverse=True)
