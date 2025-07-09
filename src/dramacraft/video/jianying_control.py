"""
剪映控制系统。

本模块实现对剪映应用程序的自动化控制，包括项目导入、
编辑操作执行和状态监控等功能。
"""

import asyncio
import json
import platform
import subprocess
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from ..utils.logging import get_logger
from .jianying_format import JianYingProjectManager


class JianYingOperation(Enum):
    """剪映操作类型。"""
    IMPORT_PROJECT = "import_project"
    EXPORT_VIDEO = "export_video"
    ADD_SUBTITLE = "add_subtitle"
    ADD_MUSIC = "add_music"
    ADD_EFFECT = "add_effect"
    CUT_VIDEO = "cut_video"
    MERGE_VIDEO = "merge_video"
    ADJUST_SPEED = "adjust_speed"
    COLOR_CORRECTION = "color_correction"
    SAVE_PROJECT = "save_project"


@dataclass
class JianYingCommand:
    """剪映命令。"""

    operation: JianYingOperation
    """操作类型。"""

    parameters: dict[str, Any]
    """操作参数。"""

    target: Optional[str] = None
    """目标对象。"""

    wait_time: float = 1.0
    """等待时间(秒)。"""

    retry_count: int = 3
    """重试次数。"""


@dataclass
class JianYingStatus:
    """剪映状态。"""

    is_running: bool
    """是否运行中。"""

    current_project: Optional[str]
    """当前项目。"""

    last_operation: Optional[str]
    """最后操作。"""

    operation_success: bool
    """操作是否成功。"""

    error_message: Optional[str]
    """错误信息。"""

    timestamp: float
    """时间戳。"""


class JianYingController:
    """剪映控制器。"""

    def __init__(self, jianying_path: Optional[Path] = None):
        """
        初始化剪映控制器。

        Args:
            jianying_path: 剪映安装路径
        """
        self.project_manager = JianYingProjectManager(jianying_path)
        self.logger = get_logger("video.jianying_controller")
        self.current_status = JianYingStatus(
            is_running=False,
            current_project=None,
            last_operation=None,
            operation_success=False,
            error_message=None,
            timestamp=time.time()
        )

        # 操作历史
        self.operation_history: list[dict[str, Any]] = []

        # 系统信息
        self.system = platform.system()

        self.logger.info("剪映控制器已初始化")

    async def execute_command(self, command: JianYingCommand) -> bool:
        """
        执行剪映命令。

        Args:
            command: 剪映命令

        Returns:
            是否执行成功
        """
        self.logger.info(f"执行剪映命令: {command.operation.value}")

        start_time = time.time()
        success = False
        error_message = None

        try:
            # 根据操作类型执行相应命令
            if command.operation == JianYingOperation.IMPORT_PROJECT:
                success = await self._import_project(command.parameters)
            elif command.operation == JianYingOperation.EXPORT_VIDEO:
                success = await self._export_video(command.parameters)
            elif command.operation == JianYingOperation.ADD_SUBTITLE:
                success = await self._add_subtitle(command.parameters)
            elif command.operation == JianYingOperation.ADD_MUSIC:
                success = await self._add_music(command.parameters)
            elif command.operation == JianYingOperation.ADD_EFFECT:
                success = await self._add_effect(command.parameters)
            elif command.operation == JianYingOperation.SAVE_PROJECT:
                success = await self._save_project(command.parameters)
            else:
                error_message = f"不支持的操作: {command.operation.value}"
                success = False

        except Exception as e:
            error_message = str(e)
            success = False
            self.logger.error(f"命令执行失败: {e}")

        # 更新状态
        self.current_status.last_operation = command.operation.value
        self.current_status.operation_success = success
        self.current_status.error_message = error_message
        self.current_status.timestamp = time.time()

        # 记录操作历史
        self.operation_history.append({
            "operation": command.operation.value,
            "parameters": command.parameters,
            "success": success,
            "error": error_message,
            "duration": time.time() - start_time,
            "timestamp": time.time()
        })

        # 限制历史记录数量
        if len(self.operation_history) > 100:
            self.operation_history = self.operation_history[-100:]

        return success

    async def execute_batch_commands(self, commands: list[JianYingCommand]) -> list[bool]:
        """
        批量执行剪映命令。

        Args:
            commands: 命令列表

        Returns:
            执行结果列表
        """
        results = []

        for i, command in enumerate(commands):
            self.logger.info(f"执行批量命令 {i+1}/{len(commands)}")

            result = await self.execute_command(command)
            results.append(result)

            # 如果命令失败且不允许继续，则停止
            if not result and command.parameters.get("stop_on_error", False):
                self.logger.error("命令失败，停止批量执行")
                break

            # 等待指定时间
            if command.wait_time > 0:
                await asyncio.sleep(command.wait_time)

        return results

    async def _import_project(self, parameters: dict[str, Any]) -> bool:
        """导入项目。"""
        draft_file = Path(parameters["draft_file"])
        project_name = parameters.get("project_name")
        auto_open = parameters.get("auto_open", True)

        # 使用项目管理器导入
        success = self.project_manager.import_project(draft_file, project_name)

        if success:
            self.current_status.current_project = project_name or draft_file.stem
            self.current_status.is_running = auto_open

        return success

    async def _export_video(self, parameters: dict[str, Any]) -> bool:
        """导出视频。"""
        # 这里需要实现具体的导出逻辑
        # 由于剪映没有公开的API，这里使用模拟实现

        output_path = parameters.get("output_path")
        parameters.get("quality", "high")
        parameters.get("format", "mp4")

        self.logger.info(f"模拟导出视频到: {output_path}")

        # 模拟导出过程
        await asyncio.sleep(2)

        return True

    async def _add_subtitle(self, parameters: dict[str, Any]) -> bool:
        """添加字幕。"""
        subtitle_text = parameters.get("text", "")
        parameters.get("start_time", 0)
        parameters.get("end_time", 5)
        parameters.get("style", {})

        self.logger.info(f"模拟添加字幕: {subtitle_text}")

        # 模拟添加字幕
        await asyncio.sleep(1)

        return True

    async def _add_music(self, parameters: dict[str, Any]) -> bool:
        """添加音乐。"""
        music_file = parameters.get("music_file")
        parameters.get("start_time", 0)
        parameters.get("volume", 0.5)

        self.logger.info(f"模拟添加音乐: {music_file}")

        # 模拟添加音乐
        await asyncio.sleep(1)

        return True

    async def _add_effect(self, parameters: dict[str, Any]) -> bool:
        """添加特效。"""
        effect_type = parameters.get("effect_type")
        parameters.get("target_clip")
        parameters.get("effect_parameters", {})

        self.logger.info(f"模拟添加特效: {effect_type}")

        # 模拟添加特效
        await asyncio.sleep(1)

        return True

    async def _save_project(self, parameters: dict[str, Any]) -> bool:
        """保存项目。"""
        project_name = parameters.get("project_name")

        self.logger.info(f"模拟保存项目: {project_name}")

        # 模拟保存项目
        await asyncio.sleep(0.5)

        return True

    def get_status(self) -> JianYingStatus:
        """获取当前状态。"""
        return self.current_status

    def get_operation_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """获取操作历史。"""
        return self.operation_history[-limit:]

    def is_jianying_running(self) -> bool:
        """检查剪映是否运行。"""
        try:
            if self.system == "Darwin":  # macOS
                cmd = ["pgrep", "-f", "JianyingPro"]
            elif self.system == "Windows":
                cmd = ["tasklist", "/FI", "IMAGENAME eq JianyingPro.exe"]
            else:
                return False

            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0

        except Exception as e:
            self.logger.warning(f"检查剪映运行状态失败: {e}")
            return False

    async def wait_for_jianying(self, timeout: float = 30.0) -> bool:
        """等待剪映启动。"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            if self.is_jianying_running():
                self.current_status.is_running = True
                return True

            await asyncio.sleep(1)

        return False

    def create_automation_script(self, commands: list[JianYingCommand]) -> str:
        """创建自动化脚本。"""
        script_data = {
            "version": "1.0",
            "description": "DramaCraft 自动化脚本",
            "commands": [
                {
                    "operation": cmd.operation.value,
                    "parameters": cmd.parameters,
                    "target": cmd.target,
                    "wait_time": cmd.wait_time,
                    "retry_count": cmd.retry_count
                }
                for cmd in commands
            ],
            "created_time": time.time()
        }

        return json.dumps(script_data, ensure_ascii=False, indent=2)

    def load_automation_script(self, script_content: str) -> list[JianYingCommand]:
        """加载自动化脚本。"""
        try:
            script_data = json.loads(script_content)
            commands = []

            for cmd_data in script_data.get("commands", []):
                command = JianYingCommand(
                    operation=JianYingOperation(cmd_data["operation"]),
                    parameters=cmd_data["parameters"],
                    target=cmd_data.get("target"),
                    wait_time=cmd_data.get("wait_time", 1.0),
                    retry_count=cmd_data.get("retry_count", 3)
                )
                commands.append(command)

            return commands

        except Exception as e:
            self.logger.error(f"加载自动化脚本失败: {e}")
            return []
