"""
智能音频增强模块。

本模块实现智能背景音乐选择、音频混合和音量平衡优化功能，
根据视频内容和情绪自动选择合适的音频增强方案。
"""

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import librosa
import numpy as np
import soundfile as sf
from scipy import signal

from ..analysis.deep_analyzer import DeepAnalysisResult, SceneSegment
from ..llm.base import BaseLLMClient
from ..utils.helpers import ensure_directory
from ..utils.logging import get_logger


@dataclass
class MusicRecommendation:
    """音乐推荐。"""

    music_id: str
    """音乐ID。"""

    title: str
    """音乐标题。"""

    genre: str
    """音乐类型。"""

    mood: str
    """情绪标签。"""

    tempo: float
    """节拍(BPM)。"""

    energy_level: float
    """能量级别(0-1)。"""

    file_path: Optional[Path]
    """音乐文件路径。"""

    match_score: float
    """匹配度评分(0-1)。"""

    usage_segments: list[tuple[float, float]]
    """使用片段(开始时间, 结束时间)。"""


@dataclass
class AudioMixConfig:
    """音频混合配置。"""

    original_volume: float
    """原始音频音量(0-1)。"""

    background_volume: float
    """背景音乐音量(0-1)。"""

    commentary_volume: float
    """解说音量(0-1)。"""

    fade_in_duration: float
    """淡入时长(秒)。"""

    fade_out_duration: float
    """淡出时长(秒)。"""

    crossfade_duration: float
    """交叉淡化时长(秒)。"""

    dynamic_range_compression: bool
    """动态范围压缩。"""

    noise_reduction: bool
    """降噪处理。"""


@dataclass
class AudioEnhancementResult:
    """音频增强结果。"""

    enhanced_audio_path: Path
    """增强后的音频文件路径。"""

    music_recommendations: list[MusicRecommendation]
    """音乐推荐列表。"""

    mix_config: AudioMixConfig
    """混合配置。"""

    quality_metrics: dict[str, float]
    """质量指标。"""

    processing_time: float
    """处理时间(秒)。"""


class AudioEnhancer:
    """智能音频增强器。"""

    def __init__(self, llm_client: BaseLLMClient, music_library_path: Optional[Path] = None):
        """
        初始化音频增强器。

        Args:
            llm_client: 大模型客户端
            music_library_path: 音乐库路径
        """
        self.llm_client = llm_client
        self.music_library_path = music_library_path or Path("assets/music")
        self.logger = get_logger("audio.enhancer")

        # 确保音乐库目录存在
        ensure_directory(self.music_library_path)

        # 音频处理参数
        self.sample_rate = 44100
        self.bit_depth = 16

        # 音乐库索引
        self.music_index = self._build_music_index()

        self.logger.info("智能音频增强器已初始化")

    def _build_music_index(self) -> dict[str, dict[str, Any]]:
        """构建音乐库索引。"""
        index = {}

        # 预定义音乐库（实际应用中可以从文件系统扫描）
        default_music = [
            {
                "id": "happy_upbeat_01",
                "title": "快乐时光",
                "genre": "pop",
                "mood": "happy",
                "tempo": 120.0,
                "energy_level": 0.8,
                "tags": ["轻快", "积极", "日常"]
            },
            {
                "id": "romantic_soft_01",
                "title": "浪漫旋律",
                "genre": "romantic",
                "mood": "romantic",
                "tempo": 80.0,
                "energy_level": 0.4,
                "tags": ["浪漫", "温柔", "爱情"]
            },
            {
                "id": "tense_dramatic_01",
                "title": "紧张时刻",
                "genre": "dramatic",
                "mood": "tense",
                "tempo": 140.0,
                "energy_level": 0.9,
                "tags": ["紧张", "戏剧", "冲突"]
            },
            {
                "id": "sad_emotional_01",
                "title": "忧伤回忆",
                "genre": "emotional",
                "mood": "sad",
                "tempo": 60.0,
                "energy_level": 0.3,
                "tags": ["忧伤", "情感", "回忆"]
            },
            {
                "id": "calm_ambient_01",
                "title": "宁静时光",
                "genre": "ambient",
                "mood": "calm",
                "tempo": 70.0,
                "energy_level": 0.2,
                "tags": ["宁静", "放松", "环境"]
            }
        ]

        for music in default_music:
            index[music["id"]] = music

        return index

    async def enhance_audio(
        self,
        video_path: Path,
        analysis_result: DeepAnalysisResult,
        enhancement_options: Optional[dict[str, Any]] = None
    ) -> AudioEnhancementResult:
        """
        增强视频音频。

        Args:
            video_path: 视频文件路径
            analysis_result: 深度分析结果
            enhancement_options: 增强选项

        Returns:
            音频增强结果
        """
        import time
        start_time = time.time()

        self.logger.info(f"开始音频增强: {video_path}")

        # 提取原始音频
        original_audio_path = await self._extract_audio(video_path)

        # 分析音频特征
        audio_features = await self._analyze_audio_features(original_audio_path)

        # 生成音乐推荐
        music_recommendations = await self._recommend_music(
            analysis_result, audio_features, enhancement_options
        )

        # 生成混合配置
        mix_config = await self._generate_mix_config(
            analysis_result, audio_features, music_recommendations
        )

        # 执行音频混合
        enhanced_audio_path = await self._mix_audio(
            original_audio_path, music_recommendations, mix_config
        )

        # 计算质量指标
        quality_metrics = await self._calculate_quality_metrics(
            original_audio_path, enhanced_audio_path
        )

        processing_time = time.time() - start_time

        result = AudioEnhancementResult(
            enhanced_audio_path=enhanced_audio_path,
            music_recommendations=music_recommendations,
            mix_config=mix_config,
            quality_metrics=quality_metrics,
            processing_time=processing_time
        )

        self.logger.info(f"音频增强完成，耗时: {processing_time:.2f}秒")
        return result

    async def _extract_audio(self, video_path: Path) -> Path:
        """从视频中提取音频。"""
        import subprocess

        # 创建临时音频文件
        temp_dir = Path(tempfile.gettempdir()) / "dramacraft_audio"
        ensure_directory(temp_dir)

        audio_path = temp_dir / f"{video_path.stem}_audio.wav"

        try:
            # 使用ffmpeg提取音频
            cmd = [
                "ffmpeg", "-i", str(video_path),
                "-vn", "-acodec", "pcm_s16le",
                "-ar", str(self.sample_rate),
                "-ac", "2",  # 立体声
                "-y",  # 覆盖输出文件
                str(audio_path)
            ]

            subprocess.run(cmd, check=True, capture_output=True)

            self.logger.info(f"音频提取完成: {audio_path}")
            return audio_path

        except subprocess.CalledProcessError as e:
            self.logger.error(f"音频提取失败: {e}")
            raise

    async def _analyze_audio_features(self, audio_path: Path) -> dict[str, Any]:
        """分析音频特征。"""
        # 加载音频
        y, sr = librosa.load(str(audio_path), sr=self.sample_rate)

        # 提取音频特征
        features = {}

        # 基础特征
        features["duration"] = len(y) / sr
        features["rms_energy"] = float(np.mean(librosa.feature.rms(y=y)))
        features["zero_crossing_rate"] = float(np.mean(librosa.feature.zero_crossing_rate(y)))

        # 频谱特征
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)
        features["spectral_centroid"] = float(np.mean(spectral_centroids))

        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
        features["spectral_rolloff"] = float(np.mean(spectral_rolloff))

        # MFCC特征
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        features["mfcc_mean"] = np.mean(mfccs, axis=1).tolist()

        # 节拍检测
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        features["tempo"] = float(tempo)
        features["beat_count"] = len(beats)

        # 音调特征
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        features["chroma_mean"] = np.mean(chroma, axis=1).tolist()

        # 音量分析
        features["loudness_range"] = float(np.max(y) - np.min(y))
        features["dynamic_range"] = float(20 * np.log10(np.max(np.abs(y)) / (np.mean(np.abs(y)) + 1e-10)))

        return features

    async def _recommend_music(
        self,
        analysis_result: DeepAnalysisResult,
        audio_features: dict[str, Any],
        enhancement_options: Optional[dict[str, Any]]
    ) -> list[MusicRecommendation]:
        """推荐背景音乐。"""
        recommendations = []

        # 分析视频情绪和节奏
        scene_emotions = [scene.emotional_arc for scene in analysis_result.scene_segments if scene.emotional_arc]
        dominant_emotions = self._analyze_dominant_emotions(scene_emotions)

        # 为每个场景推荐音乐
        for scene in analysis_result.scene_segments:
            scene_mood = self._determine_scene_mood(scene, dominant_emotions)
            scene_energy = self._calculate_scene_energy(scene, analysis_result.frame_analyses)

            # 从音乐库中匹配
            best_match = self._find_best_music_match(scene_mood, scene_energy, audio_features)

            if best_match:
                recommendation = MusicRecommendation(
                    music_id=best_match["id"],
                    title=best_match["title"],
                    genre=best_match["genre"],
                    mood=best_match["mood"],
                    tempo=best_match["tempo"],
                    energy_level=best_match["energy_level"],
                    file_path=self._get_music_file_path(best_match["id"]),
                    match_score=self._calculate_match_score(best_match, scene_mood, scene_energy),
                    usage_segments=[(scene.start_time, scene.end_time)]
                )

                recommendations.append(recommendation)

        # 合并相邻的相同音乐推荐
        merged_recommendations = self._merge_similar_recommendations(recommendations)

        return merged_recommendations

    def _analyze_dominant_emotions(self, scene_emotions: list[list[str]]) -> dict[str, int]:
        """分析主导情绪。"""
        emotion_count = {}

        for emotions in scene_emotions:
            for emotion in emotions:
                emotion_count[emotion] = emotion_count.get(emotion, 0) + 1

        return emotion_count

    def _determine_scene_mood(self, scene: SceneSegment, dominant_emotions: dict[str, int]) -> str:
        """确定场景情绪。"""
        if scene.emotional_arc:
            # 使用场景的情绪变化
            return scene.emotional_arc[-1]  # 使用最后的情绪状态
        else:
            # 使用全局主导情绪
            if dominant_emotions:
                return max(dominant_emotions.items(), key=lambda x: x[1])[0]
            else:
                return "neutral"

    def _calculate_scene_energy(self, scene: SceneSegment, frame_analyses: list) -> float:
        """计算场景能量级别。"""
        scene_frames = [
            frame for frame in frame_analyses
            if scene.start_time <= frame.timestamp <= scene.end_time
        ]

        if not scene_frames:
            return 0.5

        # 基于运动强度和亮度变化计算能量
        motion_energy = np.mean([frame.motion_intensity for frame in scene_frames])
        brightness_variance = np.var([frame.brightness for frame in scene_frames])

        energy = (motion_energy + brightness_variance) / 2
        return min(max(energy, 0.0), 1.0)

    def _find_best_music_match(
        self,
        scene_mood: str,
        scene_energy: float,
        audio_features: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """找到最佳音乐匹配。"""
        best_match = None
        best_score = 0.0

        for _music_id, music_info in self.music_index.items():
            # 计算匹配分数
            mood_match = 1.0 if music_info["mood"] == scene_mood else 0.3
            energy_match = 1.0 - abs(music_info["energy_level"] - scene_energy)

            # 节拍匹配
            tempo_diff = abs(music_info["tempo"] - audio_features.get("tempo", 120))
            tempo_match = max(0.0, 1.0 - tempo_diff / 60.0)  # 60 BPM容差

            total_score = (mood_match * 0.5 + energy_match * 0.3 + tempo_match * 0.2)

            if total_score > best_score:
                best_score = total_score
                best_match = music_info

        return best_match

    def _calculate_match_score(
        self,
        music_info: dict[str, Any],
        scene_mood: str,
        scene_energy: float
    ) -> float:
        """计算匹配分数。"""
        mood_match = 1.0 if music_info["mood"] == scene_mood else 0.3
        energy_match = 1.0 - abs(music_info["energy_level"] - scene_energy)

        return (mood_match + energy_match) / 2

    def _get_music_file_path(self, music_id: str) -> Optional[Path]:
        """获取音乐文件路径。"""
        # 在实际应用中，这里应该返回真实的音乐文件路径
        music_file = self.music_library_path / f"{music_id}.mp3"
        return music_file if music_file.exists() else None

    def _merge_similar_recommendations(
        self,
        recommendations: list[MusicRecommendation]
    ) -> list[MusicRecommendation]:
        """合并相似的音乐推荐。"""
        if not recommendations:
            return []

        merged = []
        current_group = [recommendations[0]]

        for i in range(1, len(recommendations)):
            current = recommendations[i]
            previous = recommendations[i-1]

            # 如果是相同音乐且时间连续，则合并
            if (current.music_id == previous.music_id and
                current.usage_segments[0][0] - previous.usage_segments[-1][1] < 5.0):  # 5秒容差
                current_group.append(current)
            else:
                # 创建合并的推荐
                merged_recommendation = self._create_merged_recommendation(current_group)
                merged.append(merged_recommendation)
                current_group = [current]

        # 处理最后一组
        if current_group:
            merged_recommendation = self._create_merged_recommendation(current_group)
            merged.append(merged_recommendation)

        return merged

    def _create_merged_recommendation(
        self,
        recommendation_group: list[MusicRecommendation]
    ) -> MusicRecommendation:
        """创建合并的推荐。"""
        first = recommendation_group[0]

        # 合并使用片段
        all_segments = []
        for rec in recommendation_group:
            all_segments.extend(rec.usage_segments)

        # 计算平均匹配分数
        avg_match_score = np.mean([rec.match_score for rec in recommendation_group])

        return MusicRecommendation(
            music_id=first.music_id,
            title=first.title,
            genre=first.genre,
            mood=first.mood,
            tempo=first.tempo,
            energy_level=first.energy_level,
            file_path=first.file_path,
            match_score=avg_match_score,
            usage_segments=all_segments
        )

    async def _generate_mix_config(
        self,
        analysis_result: DeepAnalysisResult,
        audio_features: dict[str, Any],
        music_recommendations: list[MusicRecommendation]
    ) -> AudioMixConfig:
        """生成音频混合配置。"""
        # 基于音频特征和内容分析生成配置

        # 原始音频音量：基于动态范围
        dynamic_range = audio_features.get("dynamic_range", 20)
        original_volume = min(max(0.3, 1.0 - dynamic_range / 40), 0.8)

        # 背景音乐音量：基于场景情绪
        avg_energy = np.mean([rec.energy_level for rec in music_recommendations]) if music_recommendations else 0.5
        background_volume = 0.2 + avg_energy * 0.3  # 0.2-0.5范围

        # 解说音量：确保清晰度
        commentary_volume = 0.8

        # 淡入淡出时长：基于音乐节拍
        avg_tempo = np.mean([rec.tempo for rec in music_recommendations]) if music_recommendations else 120
        fade_duration = max(1.0, 60.0 / avg_tempo)  # 一个节拍的时长

        config = AudioMixConfig(
            original_volume=original_volume,
            background_volume=background_volume,
            commentary_volume=commentary_volume,
            fade_in_duration=fade_duration,
            fade_out_duration=fade_duration,
            crossfade_duration=fade_duration * 2,
            dynamic_range_compression=dynamic_range > 30,  # 动态范围过大时启用压缩
            noise_reduction=audio_features.get("rms_energy", 0) < 0.01  # 低能量时启用降噪
        )

        return config

    async def _mix_audio(
        self,
        original_audio_path: Path,
        music_recommendations: list[MusicRecommendation],
        mix_config: AudioMixConfig
    ) -> Path:
        """混合音频。"""
        # 加载原始音频
        original_audio, sr = librosa.load(str(original_audio_path), sr=self.sample_rate)

        # 应用音量调整
        mixed_audio = original_audio * mix_config.original_volume

        # 添加背景音乐
        for recommendation in music_recommendations:
            if recommendation.file_path and recommendation.file_path.exists():
                music_audio = await self._prepare_background_music(
                    recommendation, mix_config, len(mixed_audio) / sr
                )

                if music_audio is not None and len(music_audio) == len(mixed_audio):
                    mixed_audio += music_audio * mix_config.background_volume

        # 应用音频处理
        if mix_config.dynamic_range_compression:
            mixed_audio = self._apply_compression(mixed_audio)

        if mix_config.noise_reduction:
            mixed_audio = self._apply_noise_reduction(mixed_audio)

        # 标准化音频
        mixed_audio = self._normalize_audio(mixed_audio)

        # 保存混合音频
        output_path = original_audio_path.parent / f"{original_audio_path.stem}_enhanced.wav"
        sf.write(str(output_path), mixed_audio, self.sample_rate)

        return output_path

    async def _prepare_background_music(
        self,
        recommendation: MusicRecommendation,
        mix_config: AudioMixConfig,
        target_duration: float
    ) -> Optional[np.ndarray]:
        """准备背景音乐。"""
        try:
            # 加载音乐文件
            music_audio, sr = librosa.load(str(recommendation.file_path), sr=self.sample_rate)

            # 调整长度以匹配目标时长
            target_samples = int(target_duration * self.sample_rate)

            if len(music_audio) < target_samples:
                # 循环播放
                repeat_count = int(np.ceil(target_samples / len(music_audio)))
                music_audio = np.tile(music_audio, repeat_count)

            # 截取到目标长度
            music_audio = music_audio[:target_samples]

            # 应用淡入淡出
            fade_samples = int(mix_config.fade_in_duration * self.sample_rate)

            if len(music_audio) > 2 * fade_samples:
                # 淡入
                fade_in = np.linspace(0, 1, fade_samples)
                music_audio[:fade_samples] *= fade_in

                # 淡出
                fade_out = np.linspace(1, 0, fade_samples)
                music_audio[-fade_samples:] *= fade_out

            return music_audio

        except Exception as e:
            self.logger.warning(f"背景音乐处理失败: {e}")
            return None

    def _apply_compression(self, audio: np.ndarray, threshold: float = 0.5, ratio: float = 4.0) -> np.ndarray:
        """应用动态范围压缩。"""
        # 简单的压缩器实现
        compressed = audio.copy()

        # 计算音频包络
        envelope = np.abs(audio)

        # 应用压缩
        mask = envelope > threshold
        compressed[mask] = threshold + (envelope[mask] - threshold) / ratio
        compressed[mask] *= np.sign(audio[mask])

        return compressed

    def _apply_noise_reduction(self, audio: np.ndarray, noise_factor: float = 0.1) -> np.ndarray:
        """应用降噪处理。"""
        # 简单的噪声门限
        threshold = np.max(np.abs(audio)) * noise_factor
        mask = np.abs(audio) < threshold

        denoised = audio.copy()
        denoised[mask] *= 0.1  # 降低低于阈值的信号

        return denoised

    def _normalize_audio(self, audio: np.ndarray, target_level: float = 0.8) -> np.ndarray:
        """标准化音频。"""
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            return audio * (target_level / max_val)
        return audio

    async def _calculate_quality_metrics(
        self,
        original_path: Path,
        enhanced_path: Path
    ) -> dict[str, float]:
        """计算音频质量指标。"""
        # 加载音频
        original, sr1 = librosa.load(str(original_path), sr=self.sample_rate)
        enhanced, sr2 = librosa.load(str(enhanced_path), sr=self.sample_rate)

        metrics = {}

        # 信噪比改善
        original_snr = self._calculate_snr(original)
        enhanced_snr = self._calculate_snr(enhanced)
        metrics["snr_improvement"] = enhanced_snr - original_snr

        # 动态范围
        original_dr = 20 * np.log10(np.max(np.abs(original)) / (np.mean(np.abs(original)) + 1e-10))
        enhanced_dr = 20 * np.log10(np.max(np.abs(enhanced)) / (np.mean(np.abs(enhanced)) + 1e-10))
        metrics["dynamic_range_original"] = original_dr
        metrics["dynamic_range_enhanced"] = enhanced_dr

        # 频谱平衡
        original_spectrum = np.abs(np.fft.fft(original))
        enhanced_spectrum = np.abs(np.fft.fft(enhanced))

        # 计算频谱相似度
        correlation = np.corrcoef(original_spectrum[:len(original_spectrum)//2],
                                enhanced_spectrum[:len(enhanced_spectrum)//2])[0, 1]
        metrics["spectral_similarity"] = correlation if not np.isnan(correlation) else 0.0

        # 整体质量评分
        metrics["overall_quality"] = (
            min(max(metrics["snr_improvement"] / 10 + 0.5, 0), 1) * 0.4 +
            min(max(metrics["spectral_similarity"], 0), 1) * 0.3 +
            min(max((30 - abs(enhanced_dr - 20)) / 30, 0), 1) * 0.3
        )

        return metrics

    def _calculate_snr(self, audio: np.ndarray) -> float:
        """计算信噪比。"""
        # 简化的SNR计算
        signal_power = np.mean(audio ** 2)
        noise_power = np.var(audio - signal.medfilt(audio, kernel_size=5))

        if noise_power > 0:
            snr = 10 * np.log10(signal_power / noise_power)
        else:
            snr = 60  # 假设很高的SNR

        return snr
