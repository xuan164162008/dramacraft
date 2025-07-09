"""
剪映自动化引擎。

本模块提供剪映应用的自动化控制功能，通过API调用和草稿文件操控
实现智能视频编辑自动化。
"""

import asyncio
import json
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import cv2
import numpy as np
import pyautogui

from ..config import JianYingConfig
from ..llm.base import BaseLLMClient, GenerationParams
from ..utils.logging import get_logger
from ..video.draft import JianYingDraftManager


@dataclass
class AutomationTask:
    """自动化任务。"""

    id: str
    """任务ID。"""

    name: str
    """任务名称。"""

    type: str
    """任务类型。"""

    parameters: dict[str, Any]
    """任务参数。"""

    status: str
    """任务状态(pending, running, completed, failed)。"""

    progress: float
    """任务进度(0-1)。"""

    result: Optional[dict[str, Any]]
    """任务结果。"""

    error: Optional[str]
    """错误信息。"""


@dataclass
class AutomationStep:
    """自动化步骤。"""

    action: str
    """操作类型。"""

    target: str
    """目标元素。"""

    parameters: dict[str, Any]
    """操作参数。"""

    wait_time: float
    """等待时间。"""

    retry_count: int
    """重试次数。"""


class JianYingAutomationEngine:
    """剪映自动化引擎。"""

    def __init__(
        self,
        config: JianYingConfig,
        llm_client: BaseLLMClient,
        draft_manager: JianYingDraftManager
    ):
        """
        初始化自动化引擎。

        Args:
            config: 剪映配置
            llm_client: 大模型客户端
            draft_manager: 草稿管理器
        """
        self.config = config
        self.llm_client = llm_client
        self.draft_manager = draft_manager
        self.logger = get_logger("automation.engine")

        # 自动化设置
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = config.automation_delay

        # 任务队列
        self.task_queue: list[AutomationTask] = []
        self.running_tasks: dict[str, AutomationTask] = {}

        # 界面元素识别模板
        self.ui_templates = self._load_ui_templates()

        self.logger.info("剪映自动化引擎已初始化")

    def _load_ui_templates(self) -> dict[str, Any]:
        """加载界面元素识别模板。"""
        templates_dir = self.config.project_template_dir / "ui_templates"
        templates = {}

        if templates_dir.exists():
            for template_file in templates_dir.glob("*.json"):
                try:
                    with open(template_file, encoding='utf-8') as f:
                        template_data = json.load(f)
                        templates[template_file.stem] = template_data
                except Exception as e:
                    self.logger.warning(f"加载UI模板失败 {template_file}: {e}")

        return templates

    async def create_automation_plan(
        self,
        objective: str,
        draft_file: Optional[Path] = None,
        custom_requirements: Optional[list[str]] = None
    ) -> list[AutomationStep]:
        """
        创建自动化计划。

        Args:
            objective: 自动化目标
            draft_file: 草稿文件路径
            custom_requirements: 自定义需求

        Returns:
            自动化步骤列表
        """
        self.logger.info(f"创建自动化计划: {objective}")

        # 构建自动化计划提示词
        plan_prompt = self._build_automation_plan_prompt(
            objective, draft_file, custom_requirements
        )

        params = GenerationParams(max_tokens=2000, temperature=0.3)
        response = await self.llm_client.generate(plan_prompt, params)

        # 解析自动化步骤
        steps = self._parse_automation_plan(response.text)

        return steps

    def _build_automation_plan_prompt(
        self,
        objective: str,
        draft_file: Optional[Path],
        custom_requirements: Optional[list[str]]
    ) -> str:
        """构建自动化计划提示词。"""
        prompt = f"""
作为剪映自动化专家，请为以下目标制定详细的自动化操作计划：

## 自动化目标
{objective}

## 草稿文件信息
"""

        if draft_file:
            prompt += f"草稿文件: {draft_file}\n"
        else:
            prompt += "无草稿文件，需要从头创建项目\n"

        if custom_requirements:
            prompt += "\n## 自定义需求\n"
            for req in custom_requirements:
                prompt += f"- {req}\n"

        prompt += """
## 可用操作类型
1. **应用控制**
   - open_app: 打开剪映应用
   - close_app: 关闭应用
   - wait: 等待指定时间

2. **项目操作**
   - create_project: 创建新项目
   - import_draft: 导入草稿文件
   - save_project: 保存项目
   - export_video: 导出视频

3. **编辑操作**
   - add_media: 添加媒体文件
   - cut_clip: 剪切片段
   - add_effect: 添加特效
   - add_subtitle: 添加字幕
   - adjust_audio: 调整音频

4. **界面操作**
   - click: 点击元素
   - drag: 拖拽操作
   - type_text: 输入文本
   - scroll: 滚动操作

## 输出格式
请按以下JSON格式输出自动化步骤：

```json
{
    "steps": [
        {
            "action": "操作类型",
            "target": "目标元素",
            "parameters": {
                "参数名": "参数值"
            },
            "wait_time": 等待时间秒数,
            "retry_count": 重试次数
        }
    ]
}
```

请确保步骤具有可执行性，考虑界面响应时间和用户体验。
"""

        return prompt.strip()

    def _parse_automation_plan(self, response_text: str) -> list[AutomationStep]:
        """解析自动化计划响应。"""
        try:
            # 提取JSON
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start != -1 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                plan_data = json.loads(json_text)
            else:
                # 创建基础计划
                plan_data = {"steps": []}

            steps = []
            for step_data in plan_data.get("steps", []):
                step = AutomationStep(
                    action=step_data.get("action", "wait"),
                    target=step_data.get("target", ""),
                    parameters=step_data.get("parameters", {}),
                    wait_time=step_data.get("wait_time", 1.0),
                    retry_count=step_data.get("retry_count", 3)
                )
                steps.append(step)

            return steps

        except json.JSONDecodeError as e:
            self.logger.warning(f"解析自动化计划失败: {e}")
            return []

    async def execute_automation_plan(
        self,
        steps: list[AutomationStep],
        task_id: Optional[str] = None
    ) -> dict[str, Any]:
        """
        执行自动化计划。

        Args:
            steps: 自动化步骤列表
            task_id: 任务ID

        Returns:
            执行结果
        """
        if not task_id:
            task_id = f"auto_{int(time.time())}"

        self.logger.info(f"执行自动化计划: {task_id}, {len(steps)}个步骤")

        # 创建任务
        task = AutomationTask(
            id=task_id,
            name="自动化执行",
            type="automation",
            parameters={"steps_count": len(steps)},
            status="running",
            progress=0.0,
            result=None,
            error=None
        )

        self.running_tasks[task_id] = task

        try:
            # 执行步骤
            for i, step in enumerate(steps):
                self.logger.info(f"执行步骤 {i+1}/{len(steps)}: {step.action}")

                success = await self._execute_step(step)

                if not success:
                    task.status = "failed"
                    task.error = f"步骤 {i+1} 执行失败: {step.action}"
                    break

                # 更新进度
                task.progress = (i + 1) / len(steps)

                # 等待
                if step.wait_time > 0:
                    await asyncio.sleep(step.wait_time)

            if task.status == "running":
                task.status = "completed"
                task.result = {"steps_executed": len(steps)}

        except Exception as e:
            self.logger.error(f"自动化执行失败: {e}")
            task.status = "failed"
            task.error = str(e)

        finally:
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]

        return {
            "task_id": task_id,
            "status": task.status,
            "progress": task.progress,
            "result": task.result,
            "error": task.error
        }

    async def _execute_step(self, step: AutomationStep) -> bool:
        """
        执行单个自动化步骤。

        Args:
            step: 自动化步骤

        Returns:
            是否执行成功
        """
        try:
            if step.action == "open_app":
                return await self._open_jianying()

            elif step.action == "close_app":
                return await self._close_jianying()

            elif step.action == "wait":
                wait_time = step.parameters.get("time", 1.0)
                await asyncio.sleep(wait_time)
                return True

            elif step.action == "import_draft":
                draft_path = step.parameters.get("path")
                if draft_path:
                    return self.draft_manager.import_to_jianying(Path(draft_path))
                return False

            elif step.action == "click":
                return await self._click_element(step.target, step.parameters)

            elif step.action == "type_text":
                text = step.parameters.get("text", "")
                pyautogui.typewrite(text)
                return True

            elif step.action == "drag":
                return await self._drag_element(step.parameters)

            else:
                self.logger.warning(f"未知操作类型: {step.action}")
                return False

        except Exception as e:
            self.logger.error(f"执行步骤失败 {step.action}: {e}")
            return False

    async def _open_jianying(self) -> bool:
        """打开剪映应用。"""
        try:
            if self.config.installation_path:
                if self.config.installation_path.suffix == '.app':
                    # macOS
                    subprocess.run(['open', str(self.config.installation_path)], check=True)
                else:
                    # Windows/Linux
                    subprocess.run([str(self.config.installation_path)], check=True)

                # 等待应用启动
                await asyncio.sleep(5)
                return True

            return False

        except Exception as e:
            self.logger.error(f"打开剪映失败: {e}")
            return False

    async def _close_jianying(self) -> bool:
        """关闭剪映应用。"""
        try:
            # 尝试通过快捷键关闭
            pyautogui.hotkey('cmd', 'q')  # macOS
            await asyncio.sleep(2)
            return True

        except Exception as e:
            self.logger.error(f"关闭剪映失败: {e}")
            return False

    async def _click_element(self, target: str, parameters: dict[str, Any]) -> bool:
        """点击界面元素。"""
        try:
            # 尝试通过坐标点击
            if "x" in parameters and "y" in parameters:
                x, y = parameters["x"], parameters["y"]
                pyautogui.click(x, y)
                return True

            # 尝试通过模板匹配点击
            if target in self.ui_templates:
                template_info = self.ui_templates[target]
                location = self._find_element_by_template(template_info)
                if location:
                    pyautogui.click(location)
                    return True

            # 尝试通过文本查找点击
            if "text" in parameters:
                # 这里可以实现OCR文本识别点击
                pass

            return False

        except Exception as e:
            self.logger.error(f"点击元素失败 {target}: {e}")
            return False

    async def _drag_element(self, parameters: dict[str, Any]) -> bool:
        """拖拽操作。"""
        try:
            start_x = parameters.get("start_x")
            start_y = parameters.get("start_y")
            end_x = parameters.get("end_x")
            end_y = parameters.get("end_y")

            if all(coord is not None for coord in [start_x, start_y, end_x, end_y]):
                pyautogui.drag(start_x, start_y, end_x, end_y, duration=1.0)
                return True

            return False

        except Exception as e:
            self.logger.error(f"拖拽操作失败: {e}")
            return False

    def _find_element_by_template(self, template_info: dict[str, Any]) -> Optional[tuple]:
        """通过模板匹配查找界面元素。"""
        try:
            template_path = template_info.get("image_path")
            if not template_path or not Path(template_path).exists():
                return None

            # 截取当前屏幕
            screenshot = pyautogui.screenshot()
            screenshot_np = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            # 加载模板图像
            template = cv2.imread(template_path)
            if template is None:
                return None

            # 模板匹配
            result = cv2.matchTemplate(screenshot_np, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            # 检查匹配度
            threshold = template_info.get("threshold", 0.8)
            if max_val >= threshold:
                # 计算点击位置（模板中心）
                h, w = template.shape[:2]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                return (center_x, center_y)

            return None

        except Exception as e:
            self.logger.error(f"模板匹配失败: {e}")
            return None

    def get_task_status(self, task_id: str) -> Optional[dict[str, Any]]:
        """获取任务状态。"""
        if task_id in self.running_tasks:
            task = self.running_tasks[task_id]
            return {
                "id": task.id,
                "name": task.name,
                "status": task.status,
                "progress": task.progress,
                "result": task.result,
                "error": task.error
            }
        return None

    def list_running_tasks(self) -> list[dict[str, Any]]:
        """列出正在运行的任务。"""
        return [
            {
                "id": task.id,
                "name": task.name,
                "status": task.status,
                "progress": task.progress
            }
            for task in self.running_tasks.values()
        ]
