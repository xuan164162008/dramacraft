"""
DramaCraft 命令行接口。

提供启动MCP服务器、配置管理、工具测试等功能。
"""

import asyncio
import json
from pathlib import Path
from typing import Any, Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .config import DramaCraftConfig
from .monitoring.performance import get_performance_monitor
from .server import DramaCraftServer
from .utils.logging import get_logger, setup_logging

app = typer.Typer(
    name="dramacraft",
    help="🎬 DramaCraft - 专业短剧视频编辑MCP服务",
    add_completion=False,
    rich_markup_mode="rich"
)
console = Console()


@app.command()
def start(
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="配置文件路径",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="启用调试模式",
    ),
    log_level: str = typer.Option(
        "INFO",
        "--log-level",
        help="日志级别",
        case_sensitive=False,
    ),
    production: bool = typer.Option(
        False,
        "--production",
        help="生产模式",
    ),
) -> None:
    """🚀 启动 DramaCraft MCP 服务器"""

    # 设置日志
    if debug:
        log_level = "DEBUG"
    setup_logging(level=log_level.upper())
    get_logger("cli.start")

    try:
        # 加载配置
        if config_file:
            config = DramaCraftConfig.from_file(config_file)
        else:
            config = DramaCraftConfig()

        # 应用命令行参数
        if production:
            config.performance.monitoring_enabled = True
            config.performance.cache_enabled = True

        console.print("[green]🎬 启动 DramaCraft MCP 服务器...[/green]")
        console.print(f"[blue]📋 LLM提供商:[/blue] {config.llm.provider}")
        console.print(f"[blue]🎥 临时目录:[/blue] {config.video.temp_dir}")
        console.print(f"[blue]🔧 模式:[/blue] {'生产' if production else '开发'}")

        # 启动性能监控
        if config.performance.monitoring_enabled:
            get_performance_monitor()
            console.print("[blue]📊 性能监控已启用[/blue]")

        # 创建并启动服务器
        server = DramaCraftServer(config)
        asyncio.run(server.run())

    except KeyboardInterrupt:
        console.print("\n[yellow]⏹️  用户中断服务[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ 服务器启动失败: {e}[/red]")
        if debug:
            raise
        raise typer.Exit(1)


@app.command()
def config(
    show: bool = typer.Option(
        False,
        "--show",
        "-s",
        help="显示当前配置",
    ),
    validate: bool = typer.Option(
        False,
        "--validate",
        "-v",
        help="验证配置",
    ),
    init: bool = typer.Option(
        False,
        "--init",
        help="初始化配置文件",
    ),
    export: Optional[Path] = typer.Option(
        None,
        "--export",
        help="导出配置到文件",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--file",
        "-f",
        help="配置文件路径",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
) -> None:
    """⚙️ 配置管理"""

    get_logger("cli.config")

    try:
        if init:
            init_config()
            return

        if config_file:
            config = DramaCraftConfig.from_file(config_file)
        else:
            config = DramaCraftConfig()

        if validate:
            console.print("[green]✅ 配置验证通过![/green]")
            console.print(f"[blue]LLM提供商:[/blue] {config.llm.provider}")
            console.print(f"[blue]API密钥:[/blue] {'已配置' if config.llm.api_key else '未配置'}")
            console.print(f"[blue]剪映路径:[/blue] {'已配置' if config.jianying.installation_path else '未配置'}")
            return

        if export:
            export_config(config, export)
            return

        if show:
            table = Table(title="📋 DramaCraft 配置")
            table.add_column("设置项", style="cyan")
            table.add_column("值", style="magenta")

            # LLM 设置
            table.add_row("🤖 LLM提供商", config.llm.provider)
            table.add_row("🎯 模型", config.llm.model)
            table.add_row("🌡️ 温度", str(config.llm.temperature))
            table.add_row("📏 最大令牌", str(config.llm.max_tokens))

            # 视频设置
            table.add_row("📁 临时目录", str(config.video.temp_dir))
            table.add_row("📤 输出目录", str(config.video.output_dir))
            table.add_row("📊 最大文件大小", f"{config.video.max_file_size_mb}MB")

            # 剪映设置
            table.add_row("🎬 剪映路径", str(config.jianying.installation_path))
            table.add_row("💾 自动备份", str(config.jianying.auto_backup))

            # 性能设置
            table.add_row("⚡ 最大并发", str(config.performance.max_concurrent_tasks))
            table.add_row("💾 缓存启用", str(config.performance.cache_enabled))
            table.add_row("📊 监控启用", str(config.performance.monitoring_enabled))

            console.print(table)
            return

        console.print("[yellow]请指定操作: --show, --validate, --init, 或 --export[/yellow]")

    except Exception as e:
        console.print(f"[red]❌ 配置操作失败: {e}[/red]")
        raise typer.Exit(1)


def init_config():
    """初始化配置文件。"""
    config_content = '''# DramaCraft 配置文件
# 复制此文件为 .env 并填入您的配置

# LLM 配置
LLM__PROVIDER=baidu
LLM__API_KEY=your_api_key_here
LLM__SECRET_KEY=your_secret_key_here
LLM__MODEL=ernie-bot-turbo
LLM__TEMPERATURE=0.7
LLM__MAX_TOKENS=2000

# 视频处理配置
VIDEO__TEMP_DIR=./temp
VIDEO__OUTPUT_DIR=./output
VIDEO__MAX_FILE_SIZE_MB=500

# 剪映配置
JIANYING__INSTALLATION_PATH=/Applications/JianyingPro.app
JIANYING__PROJECTS_DIR=~/Movies/JianyingPro
JIANYING__AUTO_BACKUP=true

# 性能配置
PERFORMANCE__MAX_CONCURRENT_TASKS=5
PERFORMANCE__CACHE_ENABLED=true
PERFORMANCE__MONITORING_ENABLED=true
'''

    config_file = Path(".env.example")
    config_file.write_text(config_content, encoding='utf-8')

    console.print(f"[green]✅ 配置模板已创建: {config_file}[/green]")
    console.print("[blue]请复制为 .env 文件并填入您的配置[/blue]")


def export_config(config: DramaCraftConfig, file_path: Path):
    """导出配置到文件。"""
    try:
        config_dict = config.model_dump()

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, ensure_ascii=False, indent=2)

        console.print(f"[green]✅ 配置已导出到: {file_path}[/green]")
    except Exception as e:
        console.print(f"[red]❌ 导出配置失败: {e}[/red]")


@app.command()
def test(
    tool: Optional[str] = typer.Option(
        None,
        "--tool",
        help="测试指定工具",
    ),
    all_tools: bool = typer.Option(
        False,
        "--all",
        help="测试所有工具",
    ),
    video: Optional[Path] = typer.Option(
        None,
        "--video",
        help="测试视频文件路径",
        exists=True,
        file_okay=True,
    ),
) -> None:
    """🧪 测试工具功能"""

    get_logger("cli.test")

    try:
        config = DramaCraftConfig()
        server = DramaCraftServer(config)

        if tool:
            asyncio.run(test_single_tool(server, tool, video))
        elif all_tools:
            asyncio.run(test_all_tools(server, video))
        else:
            console.print("[yellow]请指定要测试的工具: --tool <工具名> 或 --all[/yellow]")

    except Exception as e:
        console.print(f"[red]❌ 工具测试失败: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def status() -> None:
    """📊 查看服务状态"""

    try:
        monitor = get_performance_monitor()
        metrics = monitor.get_current_metrics()

        table = Table(title="📊 DramaCraft 服务状态")
        table.add_column("指标", style="cyan")
        table.add_column("值", style="magenta")

        table.add_row("🖥️ CPU使用率", f"{metrics.cpu_usage:.1f}%")
        table.add_row("💾 内存使用率", f"{metrics.memory_usage:.1f}%")
        table.add_row("📊 活跃任务", str(metrics.active_tasks))
        table.add_row("🚀 API调用/分钟", str(metrics.api_calls_per_minute))
        table.add_row("⏱️ 平均响应时间", f"{metrics.average_response_time:.2f}s")
        table.add_row("💾 缓存命中率", f"{metrics.cache_hit_rate:.1f}%")
        table.add_row("❌ 错误率", f"{metrics.error_rate:.1f}%")

        console.print(table)

        # 显示任务统计
        stats = monitor.get_task_statistics()
        if stats.get("total_tasks", 0) > 0:
            console.print("\n[blue]📈 任务统计:[/blue]")
            console.print(f"  总任务数: {stats['total_tasks']}")
            console.print(f"  成功率: {stats['success_rate']:.1f}%")
            console.print(f"  平均耗时: {stats['average_duration']:.2f}s")

    except Exception as e:
        console.print(f"[red]❌ 获取状态失败: {e}[/red]")


@app.command()
def monitor(
    export: Optional[Path] = typer.Option(
        None,
        "--export",
        help="导出监控数据",
    ),
    realtime: bool = typer.Option(
        False,
        "--realtime",
        help="实时监控",
    ),
) -> None:
    """📊 性能监控"""

    try:
        monitor = get_performance_monitor()

        if export:
            monitor.export_metrics(export)
            console.print(f"[green]✅ 监控数据已导出到: {export}[/green]")
            return

        if realtime:
            console.print("[blue]🔄 实时监控模式 (按 Ctrl+C 退出)[/blue]")
            try:
                import time
                while True:
                    metrics = monitor.get_current_metrics()
                    console.clear()
                    console.print(f"[green]📊 实时监控 - {time.strftime('%H:%M:%S')}[/green]")
                    console.print(f"CPU: {metrics.cpu_usage:.1f}% | 内存: {metrics.memory_usage:.1f}% | 任务: {metrics.active_tasks}")
                    time.sleep(1)
            except KeyboardInterrupt:
                console.print("\n[yellow]⏹️  监控已停止[/yellow]")
            return

        # 显示历史数据
        history = monitor.get_metrics_history(minutes=60)
        if history:
            console.print(f"[blue]📈 过去1小时监控数据 ({len(history)} 个数据点)[/blue]")

            avg_cpu = sum(m.cpu_usage for m in history) / len(history)
            avg_memory = sum(m.memory_usage for m in history) / len(history)
            avg_response = sum(m.average_response_time for m in history) / len(history)

            console.print(f"  平均CPU: {avg_cpu:.1f}%")
            console.print(f"  平均内存: {avg_memory:.1f}%")
            console.print(f"  平均响应: {avg_response:.2f}s")
        else:
            console.print("[yellow]⚠️  暂无监控数据[/yellow]")

    except Exception as e:
        console.print(f"[red]❌ 监控操作失败: {e}[/red]")


@app.command()
def version() -> None:
    """📋 显示版本信息"""
    try:
        from importlib.metadata import version
        pkg_version = version("dramacraft")
    except Exception:
        pkg_version = "开发版本"

    console.print(f"""
[green]🎬 DramaCraft v{pkg_version}[/green]
[blue]专业短剧视频编辑 MCP 服务[/blue]

[cyan]特性:[/cyan]
  ✅ 智能解说生成
  ✅ 视频混剪制作
  ✅ 第一人称叙述
  ✅ 剪映深度集成
  ✅ 端到端自动化

[cyan]链接:[/cyan]
  🔗 GitHub: https://github.com/dramacraft/dramacraft
  📖 文档: https://dramacraft.readthedocs.io
""")


@app.command()
def doctor() -> None:
    """🩺 系统诊断"""

    console.print("[blue]🩺 运行系统诊断...[/blue]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:

        # 检查Python版本
        task = progress.add_task("检查Python版本...", total=None)
        import sys
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        console.print(f"[green]✅ Python版本: {python_version}[/green]")
        progress.remove_task(task)

        # 检查依赖
        task = progress.add_task("检查依赖包...", total=None)
        try:
            import cv2
            console.print("[green]✅ OpenCV 已安装[/green]")
        except ImportError:
            console.print("[red]❌ OpenCV 未安装[/red]")

        try:
            import numpy
            console.print("[green]✅ NumPy 已安装[/green]")
        except ImportError:
            console.print("[red]❌ NumPy 未安装[/red]")
        progress.remove_task(task)

        # 检查配置
        task = progress.add_task("检查配置...", total=None)
        try:
            config = DramaCraftConfig()
            console.print("[green]✅ 配置加载成功[/green]")

            if config.llm.api_key:
                console.print("[green]✅ LLM API密钥已配置[/green]")
            else:
                console.print("[yellow]⚠️  LLM API密钥未配置[/yellow]")

        except Exception as e:
            console.print(f"[red]❌ 配置加载失败: {e}[/red]")
        progress.remove_task(task)

        # 检查剪映
        task = progress.add_task("检查剪映安装...", total=None)
        try:
            config = DramaCraftConfig()
            jianying_path = Path(config.jianying.installation_path)
            if jianying_path.exists():
                console.print(f"[green]✅ 剪映已安装: {jianying_path}[/green]")
            else:
                console.print(f"[yellow]⚠️  剪映路径不存在: {jianying_path}[/yellow]")
        except Exception as e:
            console.print(f"[red]❌ 剪映检查失败: {e}[/red]")
        progress.remove_task(task)

    console.print("\n[blue]🎉 诊断完成![/blue]")


async def test_single_tool(server, tool_name: str, video_path: Optional[Path] = None):
    """测试单个工具。"""
    console.print(f"[blue]🧪 测试工具: {tool_name}[/blue]")

    # 获取工具列表
    tools_result = await server.list_tools()
    tool_names = [tool.name for tool in tools_result.tools]

    if tool_name not in tool_names:
        console.print(f"[red]❌ 未找到工具: {tool_name}[/red]")
        console.print(f"[yellow]可用工具: {', '.join(tool_names)}[/yellow]")
        return

    # 创建测试参数
    test_params = get_test_params(tool_name, video_path)

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"执行 {tool_name}...", total=None)
            result = await server.call_tool(tool_name, test_params)
            progress.remove_task(task)

        console.print(f"[green]✅ 工具 {tool_name} 测试成功[/green]")
        for item in result:
            console.print(f"[dim]📄 {item.text[:100]}...[/dim]")
    except Exception as e:
        console.print(f"[red]❌ 工具 {tool_name} 测试失败: {e}[/red]")


async def test_all_tools(server, video_path: Optional[Path] = None):
    """测试所有工具。"""
    console.print("[blue]🧪 测试所有工具...[/blue]")

    tools_result = await server.list_tools()

    for tool in tools_result.tools:
        await test_single_tool(server, tool.name, video_path)


def get_test_params(tool_name: str, video_path: Optional[Path] = None) -> dict[str, Any]:
    """获取工具测试参数。"""
    default_video = str(video_path) if video_path else "test_video.mp4"

    test_params = {
        "generate_commentary": {
            "video_path": default_video,
            "style": "humorous",
            "target_audience": "年轻人"
        },
        "create_remix": {
            "video_paths": [default_video],
            "theme": "测试混剪",
            "target_duration": 60
        },
        "generate_narrative": {
            "video_path": default_video,
            "character_name": "主角",
            "narrative_style": "first_person"
        },
        "analyze_video": {
            "video_path": default_video,
            "analysis_depth": "basic"
        },
        "smart_video_edit": {
            "video_paths": [default_video],
            "editing_objective": "测试编辑",
            "auto_import": False
        },
        "create_jianying_draft": {
            "video_path": default_video,
            "project_name": "测试项目"
        },
        "control_jianying": {
            "operation": "save_project",
            "parameters": {"project_name": "测试"}
        },
        "batch_process": {
            "video_paths": [default_video],
            "operation": "analyze"
        }
    }

    return test_params.get(tool_name, {})


def main() -> None:
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
