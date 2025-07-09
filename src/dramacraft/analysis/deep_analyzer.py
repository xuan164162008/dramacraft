"""
视频内容深度分析引擎。

本模块实现逐帧/逐秒的视频内容分析，识别场景、情绪、动作、对话，
确保生成的文案与视频画面内容精确匹配。
"""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional, Union

import cv2
import librosa
import numpy as np
import speech_recognition as sr

from ..llm.base import BaseLLMClient, GenerationParams
from ..utils.helpers import validate_video_file
from ..utils.logging import get_logger


@dataclass
class FrameAnalysis:
    """单帧分析结果。"""

    timestamp: float
    """时间戳(秒)。"""

    frame_number: int
    """帧编号。"""

    scene_type: str
    """场景类型(indoor, outdoor, close_up, wide_shot等)。"""

    dominant_colors: list[str]
    """主要颜色。"""

    brightness: float
    """亮度值(0-1)。"""

    motion_intensity: float
    """运动强度(0-1)。"""

    face_count: int
    """人脸数量。"""

    objects: list[str]
    """检测到的物体。"""

    composition: str
    """画面构图(center, rule_of_thirds, symmetrical等)。"""

    emotional_tone: str
    """情感基调(happy, sad, tense, calm等)。"""


@dataclass
class AudioSegment:
    """音频片段分析。"""

    start_time: float
    """开始时间(秒)。"""

    end_time: float
    """结束时间(秒)。"""

    audio_type: str
    """音频类型(speech, music, silence, noise)。"""

    volume_level: float
    """音量级别(0-1)。"""

    speech_text: Optional[str]
    """语音识别文本。"""

    speaker_emotion: Optional[str]
    """说话者情绪。"""

    background_music: bool
    """是否有背景音乐。"""

    audio_quality: float
    """音频质量评分(0-1)。"""


@dataclass
class SceneSegment:
    """场景片段。"""

    start_time: float
    """开始时间(秒)。"""

    end_time: float
    """结束时间(秒)。"""

    scene_id: str
    """场景ID。"""

    scene_description: str
    """场景描述。"""

    location: str
    """拍摄地点。"""

    characters: list[str]
    """出现的角色。"""

    actions: list[str]
    """主要动作。"""

    dialogue_summary: str
    """对话摘要。"""

    emotional_arc: list[str]
    """情感变化。"""

    visual_style: str
    """视觉风格。"""

    narrative_importance: float
    """叙事重要性(0-1)。"""


@dataclass
class DeepAnalysisResult:
    """深度分析结果。"""

    video_path: Path
    """视频文件路径。"""

    total_duration: float
    """总时长(秒)。"""

    frame_rate: float
    """帧率。"""

    resolution: tuple[int, int]
    """分辨率。"""

    frame_analyses: list[FrameAnalysis]
    """逐帧分析结果。"""

    audio_segments: list[AudioSegment]
    """音频片段分析。"""

    scene_segments: list[SceneSegment]
    """场景片段分析。"""

    overall_summary: dict[str, Any]
    """整体分析摘要。"""

    content_timeline: list[dict[str, Any]]
    """内容时间轴。"""


class DeepVideoAnalyzer:
    """深度视频分析器。"""

    def __init__(self, llm_client: BaseLLMClient):
        """
        初始化深度分析器。

        Args:
            llm_client: 大模型客户端
        """
        self.llm_client = llm_client
        self.logger = get_logger("analysis.deep_analyzer")

        # 初始化计算机视觉模型
        self._init_cv_models()

        # 初始化语音识别
        self.speech_recognizer = sr.Recognizer()

        self.logger.info("深度视频分析器已初始化")

    def _init_cv_models(self):
        """初始化计算机视觉模型。"""
        try:
            # 人脸检测器
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )

            # 物体检测模型 (使用预训练的COCO模型)
            self.object_detector = None  # 可以集成YOLO或其他模型

            self.logger.info("计算机视觉模型初始化完成")

        except Exception as e:
            self.logger.warning(f"CV模型初始化失败: {e}")

    async def analyze_video_deeply(
        self,
        video_path: Union[str, Path],
        analysis_interval: float = 1.0,
        include_audio: bool = True,
        max_frames: Optional[int] = None
    ) -> DeepAnalysisResult:
        """
        对视频进行深度分析。

        Args:
            video_path: 视频文件路径
            analysis_interval: 分析间隔(秒)
            include_audio: 是否包含音频分析
            max_frames: 最大分析帧数

        Returns:
            深度分析结果
        """
        video_path = Path(video_path)

        if not validate_video_file(video_path):
            raise ValueError(f"无效的视频文件: {video_path}")

        self.logger.info(f"开始深度分析视频: {video_path}")

        # 获取视频基本信息
        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0

        # 逐帧分析
        frame_analyses = await self._analyze_frames(
            cap, fps, analysis_interval, max_frames
        )

        cap.release()

        # 音频分析
        audio_segments = []
        if include_audio:
            audio_segments = await self._analyze_audio(video_path)

        # 场景分割和分析
        scene_segments = await self._analyze_scenes(
            frame_analyses, audio_segments, video_path
        )

        # 生成整体摘要
        overall_summary = await self._generate_overall_summary(
            frame_analyses, audio_segments, scene_segments
        )

        # 构建内容时间轴
        content_timeline = self._build_content_timeline(
            frame_analyses, audio_segments, scene_segments
        )

        result = DeepAnalysisResult(
            video_path=video_path,
            total_duration=duration,
            frame_rate=fps,
            resolution=(width, height),
            frame_analyses=frame_analyses,
            audio_segments=audio_segments,
            scene_segments=scene_segments,
            overall_summary=overall_summary,
            content_timeline=content_timeline
        )

        self.logger.info(f"深度分析完成: {len(frame_analyses)}帧, {len(scene_segments)}个场景")
        return result

    async def _analyze_frames(
        self,
        cap: cv2.VideoCapture,
        fps: float,
        interval: float,
        max_frames: Optional[int]
    ) -> list[FrameAnalysis]:
        """分析视频帧。"""
        frame_analyses = []
        frame_interval = int(fps * interval)
        frame_number = 0
        analyzed_count = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_number % frame_interval == 0:
                timestamp = frame_number / fps

                # 分析当前帧
                analysis = await self._analyze_single_frame(frame, timestamp, frame_number)
                frame_analyses.append(analysis)

                analyzed_count += 1
                if max_frames and analyzed_count >= max_frames:
                    break

            frame_number += 1

        return frame_analyses

    async def _analyze_single_frame(
        self,
        frame: np.ndarray,
        timestamp: float,
        frame_number: int
    ) -> FrameAnalysis:
        """分析单个帧。"""
        # 基础图像分析
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 亮度计算
        brightness = np.mean(gray) / 255.0

        # 主要颜色提取
        dominant_colors = self._extract_dominant_colors(frame)

        # 人脸检测
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        face_count = len(faces)

        # 运动强度计算 (简化版本)
        motion_intensity = self._calculate_motion_intensity(frame)

        # 场景类型识别
        scene_type = self._classify_scene_type(frame, face_count)

        # 画面构图分析
        composition = self._analyze_composition(frame, faces)

        # 情感基调分析
        emotional_tone = self._analyze_emotional_tone(frame, brightness, dominant_colors)

        return FrameAnalysis(
            timestamp=timestamp,
            frame_number=frame_number,
            scene_type=scene_type,
            dominant_colors=dominant_colors,
            brightness=brightness,
            motion_intensity=motion_intensity,
            face_count=face_count,
            objects=[],  # 需要物体检测模型
            composition=composition,
            emotional_tone=emotional_tone
        )

    def _extract_dominant_colors(self, frame: np.ndarray, k: int = 3) -> list[str]:
        """提取主要颜色。"""
        # 重塑图像数据
        data = frame.reshape((-1, 3))
        data = np.float32(data)

        # K-means聚类
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
        _, labels, centers = cv2.kmeans(data, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

        # 转换为颜色名称
        colors = []
        for center in centers:
            b, g, r = center.astype(int)
            color_name = self._rgb_to_color_name(r, g, b)
            colors.append(color_name)

        return colors

    def _rgb_to_color_name(self, r: int, g: int, b: int) -> str:
        """将RGB值转换为颜色名称。"""
        # 简化的颜色映射
        if r > 200 and g > 200 and b > 200:
            return "白色"
        elif r < 50 and g < 50 and b < 50:
            return "黑色"
        elif r > g and r > b:
            return "红色"
        elif g > r and g > b:
            return "绿色"
        elif b > r and b > g:
            return "蓝色"
        elif r > 150 and g > 150:
            return "黄色"
        elif r > 150 and b > 150:
            return "紫色"
        elif g > 150 and b > 150:
            return "青色"
        else:
            return "灰色"

    def _calculate_motion_intensity(self, frame: np.ndarray) -> float:
        """计算运动强度。"""
        # 简化版本：基于边缘检测
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        motion_intensity = np.sum(edges) / (frame.shape[0] * frame.shape[1] * 255)
        return min(motion_intensity, 1.0)

    def _classify_scene_type(self, frame: np.ndarray, face_count: int) -> str:
        """分类场景类型。"""
        if face_count == 0:
            return "wide_shot"
        elif face_count == 1:
            return "close_up"
        elif face_count >= 2:
            return "group_shot"
        else:
            return "unknown"

    def _analyze_composition(self, frame: np.ndarray, faces: np.ndarray) -> str:
        """分析画面构图。"""
        height, width = frame.shape[:2]

        if len(faces) > 0:
            # 计算人脸中心
            face_centers = []
            for (x, y, w, h) in faces:
                center_x = x + w // 2
                center_y = y + h // 2
                face_centers.append((center_x, center_y))

            # 判断是否居中
            center_x = width // 2
            center_y = height // 2

            for fx, fy in face_centers:
                if abs(fx - center_x) < width * 0.1 and abs(fy - center_y) < height * 0.1:
                    return "center"

            # 判断三分法则
            third_x = width // 3
            third_y = height // 3

            for fx, fy in face_centers:
                if (abs(fx - third_x) < width * 0.1 or abs(fx - 2 * third_x) < width * 0.1) and \
                   (abs(fy - third_y) < height * 0.1 or abs(fy - 2 * third_y) < height * 0.1):
                    return "rule_of_thirds"

        return "balanced"

    def _analyze_emotional_tone(
        self,
        frame: np.ndarray,
        brightness: float,
        colors: list[str]
    ) -> str:
        """分析情感基调。"""
        # 基于亮度和颜色的简单情感分析
        if brightness > 0.7:
            if "黄色" in colors or "白色" in colors:
                return "happy"
            else:
                return "calm"
        elif brightness < 0.3:
            if "黑色" in colors or "灰色" in colors:
                return "sad"
            else:
                return "tense"
        else:
            if "红色" in colors:
                return "passionate"
            elif "蓝色" in colors:
                return "calm"
            else:
                return "neutral"

    async def _analyze_audio(self, video_path: Path) -> list[AudioSegment]:
        """分析音频内容。"""
        try:
            # 使用librosa加载音频
            y, sr = librosa.load(str(video_path), sr=None)
            duration = len(y) / sr

            # 分段分析音频
            segment_length = 5.0  # 5秒一段
            segments = []

            for i in range(0, int(duration), int(segment_length)):
                start_time = i
                end_time = min(i + segment_length, duration)

                # 提取音频片段
                start_sample = int(start_time * sr)
                end_sample = int(end_time * sr)
                segment_audio = y[start_sample:end_sample]

                # 分析音频特征
                volume_level = np.mean(np.abs(segment_audio))

                # 简单的音频类型分类
                audio_type = self._classify_audio_type(segment_audio, sr)

                # 语音识别 (简化版本)
                speech_text = None
                if audio_type == "speech":
                    speech_text = await self._recognize_speech(segment_audio, sr)

                segment = AudioSegment(
                    start_time=start_time,
                    end_time=end_time,
                    audio_type=audio_type,
                    volume_level=min(volume_level, 1.0),
                    speech_text=speech_text,
                    speaker_emotion=None,  # 需要情感识别模型
                    background_music=audio_type == "music",
                    audio_quality=0.8  # 简化评分
                )

                segments.append(segment)

            return segments

        except Exception as e:
            self.logger.warning(f"音频分析失败: {e}")
            return []

    def _classify_audio_type(self, audio: np.ndarray, sr: int) -> str:
        """分类音频类型。"""
        # 简化的音频分类
        if np.max(np.abs(audio)) < 0.01:
            return "silence"

        # 计算频谱特征
        stft = librosa.stft(audio)
        magnitude = np.abs(stft)

        # 基于频谱特征的简单分类
        low_freq_energy = np.mean(magnitude[:magnitude.shape[0]//4])
        high_freq_energy = np.mean(magnitude[3*magnitude.shape[0]//4:])

        if high_freq_energy > low_freq_energy * 2:
            return "speech"
        elif low_freq_energy > high_freq_energy * 1.5:
            return "music"
        else:
            return "noise"

    async def _recognize_speech(self, audio: np.ndarray, sr: int) -> Optional[str]:
        """语音识别。"""
        try:
            # 这里可以集成更好的语音识别服务
            # 目前返回占位符
            return "语音内容"
        except Exception as e:
            self.logger.debug(f"语音识别失败: {e}")
            return None

    async def _analyze_scenes(
        self,
        frame_analyses: list[FrameAnalysis],
        audio_segments: list[AudioSegment],
        video_path: Path
    ) -> list[SceneSegment]:
        """分析场景片段。"""
        # 基于帧分析结果进行场景分割
        scenes = []
        current_scene_start = 0.0
        current_scene_type = frame_analyses[0].scene_type if frame_analyses else "unknown"

        for i, frame_analysis in enumerate(frame_analyses):
            # 检测场景变化
            if (frame_analysis.scene_type != current_scene_type or
                i == len(frame_analyses) - 1):

                # 结束当前场景
                scene_end = frame_analysis.timestamp

                # 使用AI生成场景描述
                scene_description = await self._generate_scene_description(
                    frame_analyses[max(0, i-5):i+1],  # 使用周围的帧
                    audio_segments,
                    current_scene_start,
                    scene_end
                )

                scene = SceneSegment(
                    start_time=current_scene_start,
                    end_time=scene_end,
                    scene_id=f"scene_{len(scenes)+1}",
                    scene_description=scene_description,
                    location="未知",
                    characters=[],
                    actions=[],
                    dialogue_summary="",
                    emotional_arc=[],
                    visual_style=current_scene_type,
                    narrative_importance=0.5
                )

                scenes.append(scene)

                # 开始新场景
                current_scene_start = scene_end
                current_scene_type = frame_analysis.scene_type

        return scenes

    async def _generate_scene_description(
        self,
        frame_analyses: list[FrameAnalysis],
        audio_segments: list[AudioSegment],
        start_time: float,
        end_time: float
    ) -> str:
        """生成场景描述。"""
        # 构建场景分析提示词
        prompt = f"""
请基于以下视频分析数据，生成简洁的场景描述：

时间段: {start_time:.1f}s - {end_time:.1f}s

视觉特征:
"""

        for frame in frame_analyses[-3:]:  # 使用最后3帧
            prompt += f"- {frame.timestamp:.1f}s: {frame.scene_type}, 亮度{frame.brightness:.2f}, 人脸{frame.face_count}个, 情感{frame.emotional_tone}\n"

        # 添加音频信息
        relevant_audio = [seg for seg in audio_segments
                         if seg.start_time <= end_time and seg.end_time >= start_time]

        if relevant_audio:
            prompt += "\n音频特征:\n"
            for audio in relevant_audio:
                prompt += f"- {audio.audio_type}, 音量{audio.volume_level:.2f}\n"

        prompt += "\n请用一句话描述这个场景的主要内容："

        try:
            params = GenerationParams(max_tokens=100, temperature=0.3)
            response = await self.llm_client.generate(prompt, params)
            return response.text.strip()
        except Exception as e:
            self.logger.warning(f"场景描述生成失败: {e}")
            return f"场景片段 {start_time:.1f}s-{end_time:.1f}s"

    async def _generate_overall_summary(
        self,
        frame_analyses: list[FrameAnalysis],
        audio_segments: list[AudioSegment],
        scene_segments: list[SceneSegment]
    ) -> dict[str, Any]:
        """生成整体分析摘要。"""
        # 统计分析
        total_frames = len(frame_analyses)
        avg_brightness = np.mean([f.brightness for f in frame_analyses])
        dominant_emotions = {}

        for frame in frame_analyses:
            emotion = frame.emotional_tone
            dominant_emotions[emotion] = dominant_emotions.get(emotion, 0) + 1

        most_common_emotion = max(dominant_emotions.items(), key=lambda x: x[1])[0]

        # 音频统计
        speech_segments = [seg for seg in audio_segments if seg.audio_type == "speech"]
        music_segments = [seg for seg in audio_segments if seg.audio_type == "music"]

        return {
            "total_frames_analyzed": total_frames,
            "total_scenes": len(scene_segments),
            "average_brightness": avg_brightness,
            "dominant_emotion": most_common_emotion,
            "emotion_distribution": dominant_emotions,
            "speech_segments_count": len(speech_segments),
            "music_segments_count": len(music_segments),
            "analysis_quality": "high" if total_frames > 10 else "medium"
        }

    def _build_content_timeline(
        self,
        frame_analyses: list[FrameAnalysis],
        audio_segments: list[AudioSegment],
        scene_segments: list[SceneSegment]
    ) -> list[dict[str, Any]]:
        """构建内容时间轴。"""
        timeline = []

        # 合并所有时间点事件
        events = []

        # 添加场景事件
        for scene in scene_segments:
            events.append({
                "timestamp": scene.start_time,
                "type": "scene_start",
                "data": scene
            })

        # 添加关键帧事件
        for frame in frame_analyses[::5]:  # 每5帧取一个
            events.append({
                "timestamp": frame.timestamp,
                "type": "frame_analysis",
                "data": frame
            })

        # 添加音频事件
        for audio in audio_segments:
            if audio.audio_type == "speech" and audio.speech_text:
                events.append({
                    "timestamp": audio.start_time,
                    "type": "speech",
                    "data": audio
                })

        # 按时间排序
        events.sort(key=lambda x: x["timestamp"])

        # 构建时间轴
        for event in events:
            timeline_item = {
                "timestamp": event["timestamp"],
                "type": event["type"],
                "description": self._get_event_description(event),
                "data": asdict(event["data"]) if hasattr(event["data"], '__dict__') else event["data"]
            }
            timeline.append(timeline_item)

        return timeline

    def _get_event_description(self, event: dict[str, Any]) -> str:
        """获取事件描述。"""
        if event["type"] == "scene_start":
            return f"场景开始: {event['data'].scene_description}"
        elif event["type"] == "frame_analysis":
            frame = event["data"]
            return f"画面: {frame.scene_type}, {frame.emotional_tone}情绪"
        elif event["type"] == "speech":
            return f"语音: {event['data'].speech_text}"
        else:
            return "未知事件"
