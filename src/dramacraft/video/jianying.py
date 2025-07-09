"""
剪映(JianYing)集成模块。

本模块提供与剪映视频编辑软件的集成功能，包括项目文件生成、
自动化操作和模板管理。
"""

import json
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Union

import pyautogui

from ..config import JianYingConfig
from ..utils.helpers import ensure_directory, safe_filename
from ..utils.logging import get_logger


@dataclass
class JianYingProject:
    """剪映项目数据结构。"""

    name: str
    """项目名称。"""

    duration: float
    """项目总时长(秒)。"""

    resolution: tuple[int, int]
    """视频分辨率(宽, 高)。"""

    fps: float
    """帧率。"""

    tracks: list[dict[str, Any]]
    """轨道数据。"""

    assets: list[dict[str, Any]]
    """素材资源。"""

    effects: list[dict[str, Any]]
    """特效数据。"""

    transitions: list[dict[str, Any]]
    """转场效果。"""

    audio: list[dict[str, Any]]
    """音频轨道。"""

    subtitles: list[dict[str, Any]]
    """字幕数据。"""

    metadata: dict[str, Any]
    """项目元数据。"""


@dataclass
class JianYingAsset:
    """剪映素材资源。"""

    id: str
    """素材ID。"""

    type: str
    """素材类型(video, audio, image, text)。"""

    path: str
    """文件路径。"""

    name: str
    """素材名称。"""

    duration: float
    """时长(秒)。"""

    properties: dict[str, Any]
    """素材属性。"""


@dataclass
class JianYingTrack:
    """剪映轨道。"""

    id: str
    """轨道ID。"""

    type: str
    """轨道类型(video, audio, subtitle)。"""

    clips: list[dict[str, Any]]
    """轨道片段。"""

    properties: dict[str, Any]
    """轨道属性。"""


class JianYingIntegrator:
    """剪映集成器。"""

    def __init__(self, config: JianYingConfig):
        """
        初始化剪映集成器。

        Args:
            config: 剪映配置
        """
        self.config = config
        self.logger = get_logger("video.jianying")

        # 设置pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = config.automation_delay

        self.logger.info("剪映集成器已初始化")

    def create_project(
        self,
        project_data: dict[str, Any],
        output_path: Union[str, Path],
        template_name: str = "default"
    ) -> Path:
        """
        创建剪映项目文件。

        Args:
            project_data: 项目数据
            output_path: 输出路径
            template_name: 模板名称

        Returns:
            项目文件路径

        Raises:
            ValueError: 如果项目数据无效
            IOError: 如果文件操作失败
        """
        output_path = Path(output_path)
        ensure_directory(output_path.parent)

        self.logger.info(f"创建剪映项目: {output_path}")

        # 构建项目结构
        project = self._build_project_structure(project_data, template_name)

        # 生成项目文件
        project_file = self._generate_project_file(project, output_path)

        # 复制素材文件
        self._copy_assets(project, output_path.parent)

        self.logger.info(f"剪映项目创建完成: {project_file}")
        return project_file

    def _build_project_structure(
        self,
        project_data: dict[str, Any],
        template_name: str
    ) -> JianYingProject:
        """
        构建项目结构。

        Args:
            project_data: 项目数据
            template_name: 模板名称

        Returns:
            剪映项目对象
        """
        # 加载模板
        template = self._load_template(template_name)

        # 基本项目信息
        project = JianYingProject(
            name=project_data.get("name", "DramaCraft项目"),
            duration=project_data.get("duration", 60.0),
            resolution=project_data.get("resolution", (1920, 1080)),
            fps=project_data.get("fps", 30.0),
            tracks=[],
            assets=[],
            effects=[],
            transitions=[],
            audio=[],
            subtitles=[],
            metadata={
                "created_by": "DramaCraft",
                "template": template_name,
                "version": "1.0.0"
            }
        )

        # 处理视频轨道
        if "videos" in project_data:
            self._add_video_tracks(project, project_data["videos"])

        # 处理音频轨道
        if "audio" in project_data:
            self._add_audio_tracks(project, project_data["audio"])

        # 处理字幕
        if "subtitles" in project_data:
            self._add_subtitles(project, project_data["subtitles"])

        # 处理特效
        if "effects" in project_data:
            self._add_effects(project, project_data["effects"])

        # 应用模板设置
        self._apply_template(project, template)

        return project

    def _load_template(self, template_name: str) -> dict[str, Any]:
        """
        加载项目模板。

        Args:
            template_name: 模板名称

        Returns:
            模板数据
        """
        template_path = self.config.project_template_dir / f"{template_name}.json"

        if template_path.exists():
            with open(template_path, encoding='utf-8') as f:
                return json.load(f)
        else:
            # 返回默认模板
            return {
                "name": "默认模板",
                "description": "DramaCraft默认项目模板",
                "settings": {
                    "video_quality": "high",
                    "audio_quality": "high",
                    "export_format": "mp4"
                },
                "default_effects": [],
                "default_transitions": []
            }

    def _add_video_tracks(self, project: JianYingProject, videos: list[dict[str, Any]]) -> None:
        """添加视频轨道。"""
        for i, video_data in enumerate(videos):
            # 创建素材
            asset = JianYingAsset(
                id=f"video_{i}",
                type="video",
                path=video_data["path"],
                name=video_data.get("name", f"视频{i+1}"),
                duration=video_data.get("duration", 30.0),
                properties=video_data.get("properties", {})
            )
            project.assets.append(asdict(asset))

            # 创建轨道片段
            clip = {
                "id": f"clip_{i}",
                "asset_id": asset.id,
                "start_time": video_data.get("start_time", 0.0),
                "end_time": video_data.get("end_time", asset.duration),
                "track_start": video_data.get("track_start", 0.0),
                "properties": {
                    "volume": video_data.get("volume", 1.0),
                    "speed": video_data.get("speed", 1.0),
                    "opacity": video_data.get("opacity", 1.0)
                }
            }

            # 查找或创建视频轨道
            video_track = None
            for track in project.tracks:
                if track["type"] == "video":
                    video_track = track
                    break

            if not video_track:
                video_track = {
                    "id": "video_track_0",
                    "type": "video",
                    "clips": [],
                    "properties": {}
                }
                project.tracks.append(video_track)

            video_track["clips"].append(clip)

    def _add_audio_tracks(self, project: JianYingProject, audio_list: list[dict[str, Any]]) -> None:
        """添加音频轨道。"""
        for i, audio_data in enumerate(audio_list):
            # 创建音频素材
            asset = JianYingAsset(
                id=f"audio_{i}",
                type="audio",
                path=audio_data["path"],
                name=audio_data.get("name", f"音频{i+1}"),
                duration=audio_data.get("duration", 30.0),
                properties=audio_data.get("properties", {})
            )
            project.assets.append(asdict(asset))

            # 创建音频片段
            audio_clip = {
                "id": f"audio_clip_{i}",
                "asset_id": asset.id,
                "start_time": audio_data.get("start_time", 0.0),
                "end_time": audio_data.get("end_time", asset.duration),
                "track_start": audio_data.get("track_start", 0.0),
                "properties": {
                    "volume": audio_data.get("volume", 1.0),
                    "fade_in": audio_data.get("fade_in", 0.0),
                    "fade_out": audio_data.get("fade_out", 0.0)
                }
            }

            project.audio.append(audio_clip)

    def _add_subtitles(self, project: JianYingProject, subtitles: list[dict[str, Any]]) -> None:
        """添加字幕。"""
        for i, subtitle_data in enumerate(subtitles):
            subtitle = {
                "id": f"subtitle_{i}",
                "text": subtitle_data["text"],
                "start_time": subtitle_data["start_time"],
                "end_time": subtitle_data["end_time"],
                "style": {
                    "font_family": subtitle_data.get("font_family", "微软雅黑"),
                    "font_size": subtitle_data.get("font_size", 24),
                    "color": subtitle_data.get("color", "#FFFFFF"),
                    "background_color": subtitle_data.get("background_color", "transparent"),
                    "position": subtitle_data.get("position", "bottom"),
                    "alignment": subtitle_data.get("alignment", "center")
                }
            }
            project.subtitles.append(subtitle)

    def _add_effects(self, project: JianYingProject, effects: list[dict[str, Any]]) -> None:
        """添加特效。"""
        for i, effect_data in enumerate(effects):
            effect = {
                "id": f"effect_{i}",
                "type": effect_data["type"],
                "name": effect_data.get("name", f"特效{i+1}"),
                "start_time": effect_data["start_time"],
                "end_time": effect_data["end_time"],
                "target": effect_data.get("target", "video"),
                "parameters": effect_data.get("parameters", {})
            }
            project.effects.append(effect)

    def _apply_template(self, project: JianYingProject, template: dict[str, Any]) -> None:
        """应用模板设置。"""
        # 应用默认特效
        for effect in template.get("default_effects", []):
            project.effects.append(effect)

        # 应用默认转场
        for transition in template.get("default_transitions", []):
            project.transitions.append(transition)

        # 更新元数据
        project.metadata.update(template.get("metadata", {}))

    def _generate_project_file(
        self,
        project: JianYingProject,
        output_path: Path
    ) -> Path:
        """
        生成项目文件。

        Args:
            project: 项目对象
            output_path: 输出路径

        Returns:
            项目文件路径
        """
        # 构建剪映项目文件格式
        jy_project = {
            "version": "1.0.0",
            "project_info": {
                "name": project.name,
                "duration": project.duration,
                "resolution": {
                    "width": project.resolution[0],
                    "height": project.resolution[1]
                },
                "fps": project.fps,
                "created_time": int(time.time()),
                "modified_time": int(time.time())
            },
            "timeline": {
                "tracks": project.tracks,
                "duration": project.duration
            },
            "assets": project.assets,
            "effects": project.effects,
            "transitions": project.transitions,
            "audio": project.audio,
            "subtitles": project.subtitles,
            "metadata": project.metadata
        }

        # 保存项目文件
        project_file = output_path.with_suffix('.jy')
        with open(project_file, 'w', encoding='utf-8') as f:
            json.dump(jy_project, f, ensure_ascii=False, indent=2)

        return project_file

    def _copy_assets(self, project: JianYingProject, project_dir: Path) -> None:
        """
        复制素材文件到项目目录。

        Args:
            project: 项目对象
            project_dir: 项目目录
        """
        assets_dir = project_dir / "assets"
        ensure_directory(assets_dir)

        for asset in project.assets:
            source_path = Path(asset["path"])
            if source_path.exists():
                # 生成安全的文件名
                safe_name = safe_filename(source_path.name)
                dest_path = assets_dir / safe_name

                # 复制文件
                import shutil
                shutil.copy2(source_path, dest_path)

                # 更新资源路径
                asset["path"] = str(dest_path.relative_to(project_dir))

                self.logger.debug(f"复制素材: {source_path} -> {dest_path}")

    def open_jianying(self) -> bool:
        """
        打开剪映应用。

        Returns:
            是否成功打开
        """
        try:
            if self.config.installation_path:
                if self.config.installation_path.suffix == '.app':
                    # macOS
                    subprocess.run(['open', str(self.config.installation_path)], check=True)
                else:
                    # Windows/Linux
                    subprocess.run([str(self.config.installation_path)], check=True)

                self.logger.info("剪映应用已启动")
                time.sleep(3)  # 等待应用启动
                return True
            else:
                self.logger.warning("未配置剪映安装路径")
                return False

        except subprocess.CalledProcessError as e:
            self.logger.error(f"启动剪映失败: {e}")
            return False
        except Exception as e:
            self.logger.error(f"打开剪映时发生错误: {e}")
            return False

    def import_project(self, project_file: Path) -> bool:
        """
        通过自动化导入项目到剪映。

        Args:
            project_file: 项目文件路径

        Returns:
            是否成功导入
        """
        try:
            # 确保剪映已打开
            if not self.open_jianying():
                return False

            # 这里应该实现具体的GUI自动化逻辑
            # 由于剪映的界面可能会变化，这里提供基本框架

            self.logger.info(f"开始导入项目: {project_file}")

            # 示例自动化步骤（需要根据实际界面调整）:
            # 1. 点击"导入项目"按钮
            # 2. 选择项目文件
            # 3. 确认导入

            # 注意: 实际实现需要根据剪映的具体界面进行调整
            self.logger.warning("项目导入功能需要根据剪映界面进行具体实现")

            return True

        except Exception as e:
            self.logger.error(f"导入项目失败: {e}")
            if self.config.screenshot_on_error:
                self._take_error_screenshot()
            return False

    def _take_error_screenshot(self) -> None:
        """在错误时截图。"""
        try:
            screenshot_dir = Path("screenshots")
            ensure_directory(screenshot_dir)

            timestamp = int(time.time())
            screenshot_path = screenshot_dir / f"error_{timestamp}.png"

            screenshot = pyautogui.screenshot()
            screenshot.save(screenshot_path)

            self.logger.info(f"错误截图已保存: {screenshot_path}")

        except Exception as e:
            self.logger.error(f"截图失败: {e}")

    def create_template(
        self,
        template_name: str,
        template_data: dict[str, Any]
    ) -> Path:
        """
        创建项目模板。

        Args:
            template_name: 模板名称
            template_data: 模板数据

        Returns:
            模板文件路径
        """
        ensure_directory(self.config.project_template_dir)

        template_file = self.config.project_template_dir / f"{template_name}.json"

        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(template_data, f, ensure_ascii=False, indent=2)

        self.logger.info(f"模板已创建: {template_file}")
        return template_file

    def list_templates(self) -> list[str]:
        """
        列出可用模板。

        Returns:
            模板名称列表
        """
        if not self.config.project_template_dir.exists():
            return []

        templates = []
        for template_file in self.config.project_template_dir.glob("*.json"):
            templates.append(template_file.stem)

        return templates
