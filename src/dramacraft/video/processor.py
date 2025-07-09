"""
视频处理核心模块。

本模块提供视频分析、处理和编辑的核心功能，包括场景检测、
字幕生成、视频合成等。
"""

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Union

import cv2
import numpy as np

try:
    from moviepy.audio.fx import volumex
    from moviepy.editor import (
        AudioFileClip,
        CompositeVideoClip,
        TextClip,
        VideoFileClip,
    )
    from moviepy.video.fx import resize, speedx
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

from ..config import VideoConfig
from ..utils.helpers import ensure_directory, format_duration, validate_video_file
from ..utils.logging import get_logger


@dataclass
class VideoInfo:
    """视频信息。"""

    path: Path
    """视频文件路径。"""

    duration: float
    """视频时长(秒)。"""

    fps: float
    """帧率。"""

    resolution: tuple[int, int]
    """分辨率(宽, 高)。"""

    size_mb: float
    """文件大小(MB)。"""

    codec: str
    """视频编码。"""

    audio_codec: str
    """音频编码。"""

    bitrate: int
    """比特率。"""


@dataclass
class SceneInfo:
    """场景信息。"""

    start_time: float
    """开始时间(秒)。"""

    end_time: float
    """结束时间(秒)。"""

    duration: float
    """场景时长(秒)。"""

    description: str
    """场景描述。"""

    confidence: float
    """置信度(0-1)。"""

    keyframes: list[float]
    """关键帧时间点。"""

    average_brightness: float
    """平均亮度。"""

    motion_intensity: float
    """运动强度。"""


@dataclass
class SubtitleSegment:
    """字幕片段。"""

    start_time: float
    """开始时间(秒)。"""

    end_time: float
    """结束时间(秒)。"""

    text: str
    """字幕文本。"""

    confidence: float
    """识别置信度。"""

    position: tuple[int, int]
    """字幕位置(x, y)。"""

    style: dict[str, Any]
    """字幕样式。"""


class VideoProcessor:
    """视频处理器。"""

    def __init__(self, config: VideoConfig):
        """
        初始化视频处理器。

        Args:
            config: 视频配置
        """
        self.config = config
        self.logger = get_logger("video.processor")

        if not MOVIEPY_AVAILABLE:
            self.logger.warning("MoviePy未安装，部分功能可能不可用")

        # 确保输出目录存在
        ensure_directory(config.output_dir)
        ensure_directory(config.temp_dir)

        self.logger.info("视频处理器已初始化")

    def get_video_info(self, video_path: Union[str, Path]) -> VideoInfo:
        """
        获取视频信息。

        Args:
            video_path: 视频文件路径

        Returns:
            视频信息对象

        Raises:
            ValueError: 如果视频文件无效
        """
        video_path = Path(video_path)

        if not validate_video_file(video_path):
            raise ValueError(f"无效的视频文件: {video_path}")

        self.logger.info(f"获取视频信息: {video_path}")

        # 使用OpenCV获取基本信息
        cap = cv2.VideoCapture(str(video_path))

        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            duration = frame_count / fps if fps > 0 else 0
            size_mb = video_path.stat().st_size / (1024 * 1024)

            # 尝试获取编码信息
            fourcc = cap.get(cv2.CAP_PROP_FOURCC)
            codec = "".join([chr((int(fourcc) >> 8 * i) & 0xFF) for i in range(4)])

            return VideoInfo(
                path=video_path,
                duration=duration,
                fps=fps,
                resolution=(width, height),
                size_mb=size_mb,
                codec=codec,
                audio_codec="unknown",  # OpenCV无法直接获取音频编码
                bitrate=0  # 需要其他工具获取
            )

        finally:
            cap.release()

    def detect_scenes(
        self,
        video_path: Union[str, Path],
        threshold: float = 0.3,
        min_scene_length: float = 1.0
    ) -> list[SceneInfo]:
        """
        检测视频场景。

        Args:
            video_path: 视频文件路径
            threshold: 场景切换阈值
            min_scene_length: 最小场景长度(秒)

        Returns:
            场景信息列表
        """
        video_path = Path(video_path)
        self.logger.info(f"检测视频场景: {video_path}")

        cap = cv2.VideoCapture(str(video_path))
        scenes = []

        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            if fps <= 0:
                self.logger.error("无法获取视频帧率")
                return scenes

            prev_frame = None
            scene_start = 0.0
            scene_frames = []

            for frame_idx in range(0, frame_count, int(fps * 0.5)):  # 每0.5秒采样一帧
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()

                if not ret:
                    break

                current_time = frame_idx / fps

                # 转换为灰度图
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                if prev_frame is not None:
                    # 计算帧差
                    diff = cv2.absdiff(prev_frame, gray)
                    diff_score = np.mean(diff) / 255.0

                    # 检测场景切换
                    if diff_score > threshold and (current_time - scene_start) >= min_scene_length:
                        # 结束当前场景
                        scene_info = self._create_scene_info(
                            scene_start, current_time, scene_frames, fps
                        )
                        scenes.append(scene_info)

                        # 开始新场景
                        scene_start = current_time
                        scene_frames = []

                scene_frames.append((frame_idx, gray))
                prev_frame = gray

            # 添加最后一个场景
            if scene_frames:
                final_time = frame_count / fps
                scene_info = self._create_scene_info(
                    scene_start, final_time, scene_frames, fps
                )
                scenes.append(scene_info)

        finally:
            cap.release()

        self.logger.info(f"检测到 {len(scenes)} 个场景")
        return scenes

    def _create_scene_info(
        self,
        start_time: float,
        end_time: float,
        frames: list[tuple[int, np.ndarray]],
        fps: float
    ) -> SceneInfo:
        """
        创建场景信息。

        Args:
            start_time: 开始时间
            end_time: 结束时间
            frames: 帧数据列表
            fps: 帧率

        Returns:
            场景信息对象
        """
        duration = end_time - start_time

        # 计算平均亮度
        brightness_values = [np.mean(frame) for _, frame in frames]
        avg_brightness = np.mean(brightness_values) / 255.0 if brightness_values else 0.0

        # 计算运动强度
        motion_intensity = 0.0
        if len(frames) > 1:
            motion_values = []
            for i in range(1, len(frames)):
                diff = cv2.absdiff(frames[i-1][1], frames[i][1])
                motion_values.append(np.mean(diff))
            motion_intensity = np.mean(motion_values) / 255.0 if motion_values else 0.0

        # 提取关键帧
        keyframes = [start_time, end_time]
        if len(frames) > 2:
            mid_frame_idx = len(frames) // 2
            mid_time = frames[mid_frame_idx][0] / fps
            keyframes.insert(1, mid_time)

        return SceneInfo(
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            description=f"场景 {format_duration(start_time)}-{format_duration(end_time)}",
            confidence=0.8,  # 基于简单算法的固定置信度
            keyframes=keyframes,
            average_brightness=avg_brightness,
            motion_intensity=motion_intensity
        )

    def extract_audio(
        self,
        video_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None
    ) -> Path:
        """
        提取视频音频。

        Args:
            video_path: 视频文件路径
            output_path: 输出音频文件路径

        Returns:
            音频文件路径

        Raises:
            RuntimeError: 如果MoviePy不可用
            ValueError: 如果视频文件无效
        """
        if not MOVIEPY_AVAILABLE:
            raise RuntimeError("需要安装MoviePy才能提取音频")

        video_path = Path(video_path)

        if not validate_video_file(video_path):
            raise ValueError(f"无效的视频文件: {video_path}")

        if output_path is None:
            output_path = self.config.temp_dir / f"{video_path.stem}_audio.wav"
        else:
            output_path = Path(output_path)

        self.logger.info(f"提取音频: {video_path} -> {output_path}")

        try:
            with VideoFileClip(str(video_path)) as video:
                if video.audio is not None:
                    video.audio.write_audiofile(str(output_path), verbose=False, logger=None)
                else:
                    self.logger.warning("视频文件不包含音频轨道")
                    # 创建空音频文件
                    output_path.touch()

            return output_path

        except Exception as e:
            self.logger.error(f"提取音频失败: {e}")
            raise

    def create_subtitle_video(
        self,
        video_path: Union[str, Path],
        subtitles: list[SubtitleSegment],
        output_path: Optional[Union[str, Path]] = None
    ) -> Path:
        """
        为视频添加字幕。

        Args:
            video_path: 视频文件路径
            subtitles: 字幕片段列表
            output_path: 输出视频路径

        Returns:
            带字幕的视频文件路径

        Raises:
            RuntimeError: 如果MoviePy不可用
        """
        if not MOVIEPY_AVAILABLE:
            raise RuntimeError("需要安装MoviePy才能添加字幕")

        video_path = Path(video_path)

        if output_path is None:
            output_path = self.config.output_dir / f"{video_path.stem}_with_subtitles.mp4"
        else:
            output_path = Path(output_path)

        self.logger.info(f"添加字幕: {video_path} -> {output_path}")

        try:
            with VideoFileClip(str(video_path)) as video:
                # 创建字幕片段
                subtitle_clips = []

                for subtitle in subtitles:
                    # 创建文本片段
                    txt_clip = TextClip(
                        subtitle.text,
                        fontsize=subtitle.style.get("font_size", self.config.subtitle_font_size),
                        color=subtitle.style.get("color", self.config.subtitle_font_color),
                        font=subtitle.style.get("font_family", "Arial"),
                        stroke_color=subtitle.style.get("stroke_color", "black"),
                        stroke_width=subtitle.style.get("stroke_width", 1)
                    ).set_start(subtitle.start_time).set_duration(
                        subtitle.end_time - subtitle.start_time
                    ).set_position(subtitle.style.get("position", "bottom"))

                    subtitle_clips.append(txt_clip)

                # 合成视频
                if subtitle_clips:
                    final_video = CompositeVideoClip([video] + subtitle_clips)
                else:
                    final_video = video

                # 输出视频
                final_video.write_videofile(
                    str(output_path),
                    codec='libx264',
                    audio_codec='aac',
                    verbose=False,
                    logger=None
                )

            return output_path

        except Exception as e:
            self.logger.error(f"添加字幕失败: {e}")
            raise

    def merge_videos(
        self,
        video_paths: list[Union[str, Path]],
        output_path: Optional[Union[str, Path]] = None,
        transition_duration: float = 0.5
    ) -> Path:
        """
        合并多个视频。

        Args:
            video_paths: 视频文件路径列表
            output_path: 输出视频路径
            transition_duration: 转场时长(秒)

        Returns:
            合并后的视频文件路径

        Raises:
            RuntimeError: 如果MoviePy不可用
        """
        if not MOVIEPY_AVAILABLE:
            raise RuntimeError("需要安装MoviePy才能合并视频")

        if not video_paths:
            raise ValueError("视频路径列表不能为空")

        if output_path is None:
            output_path = self.config.output_dir / f"merged_video_{int(time.time())}.mp4"
        else:
            output_path = Path(output_path)

        self.logger.info(f"合并 {len(video_paths)} 个视频")

        try:
            clips = []

            for video_path in video_paths:
                video_path = Path(video_path)
                if validate_video_file(video_path):
                    clip = VideoFileClip(str(video_path))
                    clips.append(clip)
                else:
                    self.logger.warning(f"跳过无效视频文件: {video_path}")

            if not clips:
                raise ValueError("没有有效的视频文件")

            # 合并视频片段
            from moviepy.editor import concatenate_videoclips
            final_video = concatenate_videoclips(clips, method="compose")

            # 输出视频
            final_video.write_videofile(
                str(output_path),
                codec='libx264',
                audio_codec='aac',
                verbose=False,
                logger=None
            )

            # 清理资源
            for clip in clips:
                clip.close()
            final_video.close()

            return output_path

        except Exception as e:
            self.logger.error(f"合并视频失败: {e}")
            raise

    def resize_video(
        self,
        video_path: Union[str, Path],
        target_resolution: tuple[int, int],
        output_path: Optional[Union[str, Path]] = None
    ) -> Path:
        """
        调整视频分辨率。

        Args:
            video_path: 视频文件路径
            target_resolution: 目标分辨率(宽, 高)
            output_path: 输出视频路径

        Returns:
            调整后的视频文件路径
        """
        if not MOVIEPY_AVAILABLE:
            raise RuntimeError("需要安装MoviePy才能调整视频分辨率")

        video_path = Path(video_path)

        if output_path is None:
            output_path = self.config.output_dir / f"{video_path.stem}_resized.mp4"
        else:
            output_path = Path(output_path)

        self.logger.info(f"调整视频分辨率: {video_path} -> {target_resolution}")

        try:
            with VideoFileClip(str(video_path)) as video:
                resized_video = video.resize(target_resolution)

                resized_video.write_videofile(
                    str(output_path),
                    codec='libx264',
                    audio_codec='aac',
                    verbose=False,
                    logger=None
                )

            return output_path

        except Exception as e:
            self.logger.error(f"调整视频分辨率失败: {e}")
            raise

    def extract_frames(
        self,
        video_path: Union[str, Path],
        output_dir: Optional[Union[str, Path]] = None,
        interval: float = 1.0,
        max_frames: int = 100
    ) -> list[Path]:
        """
        提取视频帧。

        Args:
            video_path: 视频文件路径
            output_dir: 输出目录
            interval: 提取间隔(秒)
            max_frames: 最大帧数

        Returns:
            提取的帧文件路径列表
        """
        video_path = Path(video_path)

        if output_dir is None:
            output_dir = self.config.temp_dir / f"{video_path.stem}_frames"
        else:
            output_dir = Path(output_dir)

        ensure_directory(output_dir)

        self.logger.info(f"提取视频帧: {video_path}")

        cap = cv2.VideoCapture(str(video_path))
        frame_paths = []

        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_interval = int(fps * interval)
            frame_count = 0

            while frame_count < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break

                current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))

                if current_frame % frame_interval == 0:
                    frame_path = output_dir / f"frame_{frame_count:06d}.jpg"
                    cv2.imwrite(str(frame_path), frame)
                    frame_paths.append(frame_path)
                    frame_count += 1

        finally:
            cap.release()

        self.logger.info(f"提取了 {len(frame_paths)} 帧")
        return frame_paths

    def get_video_thumbnail(
        self,
        video_path: Union[str, Path],
        timestamp: float = 0.0,
        output_path: Optional[Union[str, Path]] = None
    ) -> Path:
        """
        获取视频缩略图。

        Args:
            video_path: 视频文件路径
            timestamp: 时间戳(秒)
            output_path: 输出图片路径

        Returns:
            缩略图文件路径
        """
        video_path = Path(video_path)

        if output_path is None:
            output_path = self.config.temp_dir / f"{video_path.stem}_thumbnail.jpg"
        else:
            output_path = Path(output_path)

        self.logger.info(f"生成视频缩略图: {video_path}")

        cap = cv2.VideoCapture(str(video_path))

        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_number = int(timestamp * fps)

            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = cap.read()

            if ret:
                cv2.imwrite(str(output_path), frame)
            else:
                self.logger.error("无法读取指定时间戳的帧")
                raise ValueError(f"无法在时间戳 {timestamp} 处读取帧")

        finally:
            cap.release()

        return output_path
