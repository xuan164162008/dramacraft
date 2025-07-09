"""
MCP服务器测试模块。

测试Model Context Protocol服务器的实现和工具功能。
"""

import pytest
import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from src.dramacraft.server import DramaCraftServer
from src.dramacraft.config import DramaCraftConfig
from src.dramacraft.llm.base import BaseLLMClient, GenerationResult


class MockLLMClient(BaseLLMClient):
    """模拟LLM客户端。"""
    
    def __init__(self):
        super().__init__()
        self.call_count = 0
        self.responses = {}
    
    async def generate(self, prompt: str, params=None) -> GenerationResult:
        """模拟生成响应。"""
        self.call_count += 1
        
        # 根据提示词返回不同响应
        if "解说" in prompt or "commentary" in prompt.lower():
            response = {
                "title": "测试解说标题",
                "style": "humorous",
                "segments": [
                    {
                        "start_time": 0,
                        "end_time": 10,
                        "content": "这是一个搞笑的测试解说",
                        "key_points": ["重点1", "重点2"]
                    }
                ]
            }
        elif "混剪" in prompt or "remix" in prompt.lower():
            response = {
                "clips": [
                    {
                        "start_time": 0,
                        "end_time": 5,
                        "reason": "精彩片段",
                        "importance": 0.9
                    }
                ],
                "transitions": ["fade_in", "cut"],
                "music_style": "upbeat"
            }
        elif "叙述" in prompt or "narrative" in prompt.lower():
            response = {
                "character": "主角",
                "perspective": "first_person",
                "narrative_segments": [
                    {
                        "start_time": 0,
                        "end_time": 10,
                        "content": "我是主角，这是我的故事...",
                        "emotion": "excited"
                    }
                ]
            }
        else:
            response = "通用测试响应"
        
        return GenerationResult(
            text=json.dumps(response) if isinstance(response, dict) else response,
            usage={"prompt_tokens": 50, "completion_tokens": 100, "total_tokens": 150}
        )


class TestDramaCraftServer:
    """DramaCraft服务器测试。"""
    
    @pytest.fixture
    def test_config(self):
        """测试配置。"""
        return DramaCraftConfig(
            llm={"provider": "mock", "api_key": "test_key"},
            video={"temp_dir": "/tmp/dramacraft_test"},
            jianying={"installation_path": "/Applications/JianyingPro.app"}
        )
    
    @pytest.fixture
    def mock_llm_client(self):
        """模拟LLM客户端。"""
        return MockLLMClient()
    
    @pytest.fixture
    def server(self, test_config, mock_llm_client):
        """服务器实例。"""
        with patch('src.dramacraft.llm.factory.create_llm_client', return_value=mock_llm_client):
            return DramaCraftServer(test_config)
    
    def test_server_initialization(self, server):
        """测试服务器初始化。"""
        assert server.config is not None
        assert server.llm_client is not None
        assert server.commentary_generator is not None
        assert server.remix_generator is not None
        assert server.narrative_generator is not None
    
    @pytest.mark.asyncio
    async def test_list_tools(self, server):
        """测试列出工具。"""
        tools = await server.list_tools()
        
        # 验证工具数量和名称
        tool_names = [tool.name for tool in tools.tools]
        expected_tools = [
            "smart_video_edit",
            "generate_commentary",
            "create_remix",
            "generate_narrative",
            "analyze_video",
            "create_jianying_draft",
            "control_jianying",
            "batch_process"
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names
    
    @pytest.mark.asyncio
    async def test_generate_commentary_tool(self, server):
        """测试生成解说工具。"""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            video_path = Path(f.name)
            f.write(b"fake video data")
        
        try:
            result = await server.call_tool(
                "generate_commentary",
                {
                    "video_path": str(video_path),
                    "style": "humorous",
                    "target_audience": "年轻人"
                }
            )
            
            assert len(result) > 0
            assert result[0].type == "text"
            
            # 验证返回内容包含解说信息
            content = result[0].text
            assert "解说" in content or "commentary" in content.lower()
            
        finally:
            video_path.unlink()
    
    @pytest.mark.asyncio
    async def test_create_remix_tool(self, server):
        """测试创建混剪工具。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 创建多个测试视频文件
            video_paths = []
            for i in range(3):
                video_file = temp_path / f"video_{i}.mp4"
                video_file.write_bytes(b"fake video data")
                video_paths.append(str(video_file))
            
            result = await server.call_tool(
                "create_remix",
                {
                    "video_paths": video_paths,
                    "theme": "搞笑合集",
                    "target_duration": 60
                }
            )
            
            assert len(result) > 0
            assert result[0].type == "text"
            
            # 验证返回内容包含混剪信息
            content = result[0].text
            assert "混剪" in content or "remix" in content.lower()
    
    @pytest.mark.asyncio
    async def test_generate_narrative_tool(self, server):
        """测试生成叙述工具。"""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            video_path = Path(f.name)
            f.write(b"fake video data")
        
        try:
            result = await server.call_tool(
                "generate_narrative",
                {
                    "video_path": str(video_path),
                    "character_name": "小明",
                    "narrative_style": "第一人称"
                }
            )
            
            assert len(result) > 0
            assert result[0].type == "text"
            
            # 验证返回内容包含叙述信息
            content = result[0].text
            assert "叙述" in content or "narrative" in content.lower()
            
        finally:
            video_path.unlink()
    
    @pytest.mark.asyncio
    async def test_smart_video_edit_tool(self, server):
        """测试智能视频编辑工具。"""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            video_path = Path(f.name)
            f.write(b"fake video data")
        
        try:
            # 模拟工作流执行
            with patch.object(server, '_handle_smart_video_edit') as mock_handle:
                mock_handle.return_value = [
                    Mock(type="text", text="智能编辑完成，已生成剪映草稿文件")
                ]
                
                result = await server.call_tool(
                    "smart_video_edit",
                    {
                        "video_paths": [str(video_path)],
                        "editing_objective": "制作搞笑短视频",
                        "style_preferences": {"humor": True, "fast_paced": True}
                    }
                )
                
                assert len(result) > 0
                mock_handle.assert_called_once()
                
        finally:
            video_path.unlink()
    
    @pytest.mark.asyncio
    async def test_analyze_video_tool(self, server):
        """测试视频分析工具。"""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            video_path = Path(f.name)
            f.write(b"fake video data")
        
        try:
            # 模拟分析过程
            with patch.object(server, '_handle_analyze_video') as mock_handle:
                mock_handle.return_value = [
                    Mock(type="text", text="视频分析完成")
                ]
                
                result = await server.call_tool(
                    "analyze_video",
                    {
                        "video_path": str(video_path),
                        "analysis_depth": "deep"
                    }
                )
                
                assert len(result) > 0
                mock_handle.assert_called_once()
                
        finally:
            video_path.unlink()
    
    @pytest.mark.asyncio
    async def test_create_jianying_draft_tool(self, server):
        """测试创建剪映草稿工具。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            video_file = temp_path / "test.mp4"
            video_file.write_bytes(b"fake video data")
            
            # 模拟草稿创建
            with patch.object(server, '_handle_create_jianying_draft') as mock_handle:
                mock_handle.return_value = [
                    Mock(type="text", text="剪映草稿已创建")
                ]
                
                result = await server.call_tool(
                    "create_jianying_draft",
                    {
                        "video_path": str(video_file),
                        "project_name": "测试项目",
                        "output_dir": str(temp_path)
                    }
                )
                
                assert len(result) > 0
                mock_handle.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_control_jianying_tool(self, server):
        """测试控制剪映工具。"""
        # 模拟剪映控制
        with patch.object(server, '_handle_control_jianying') as mock_handle:
            mock_handle.return_value = [
                Mock(type="text", text="剪映操作执行完成")
            ]
            
            result = await server.call_tool(
                "control_jianying",
                {
                    "operation": "import_project",
                    "parameters": {"draft_file": "test.draft"}
                }
            )
            
            assert len(result) > 0
            mock_handle.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_batch_process_tool(self, server):
        """测试批量处理工具。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 创建多个测试视频
            video_paths = []
            for i in range(3):
                video_file = temp_path / f"video_{i}.mp4"
                video_file.write_bytes(b"fake video data")
                video_paths.append(str(video_file))
            
            # 模拟批量处理
            with patch.object(server, '_handle_batch_process') as mock_handle:
                mock_handle.return_value = [
                    Mock(type="text", text="批量处理完成")
                ]
                
                result = await server.call_tool(
                    "batch_process",
                    {
                        "video_paths": video_paths,
                        "operation": "generate_commentary",
                        "batch_settings": {"parallel": True}
                    }
                )
                
                assert len(result) > 0
                mock_handle.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_invalid_tool_call(self, server):
        """测试无效工具调用。"""
        with pytest.raises(ValueError, match="未知工具"):
            await server.call_tool("invalid_tool", {})
    
    @pytest.mark.asyncio
    async def test_tool_call_with_missing_parameters(self, server):
        """测试缺少参数的工具调用。"""
        # 测试缺少必需参数
        with pytest.raises(Exception):
            await server.call_tool("generate_commentary", {})
    
    @pytest.mark.asyncio
    async def test_tool_call_with_invalid_parameters(self, server):
        """测试无效参数的工具调用。"""
        # 测试无效的视频路径
        result = await server.call_tool(
            "generate_commentary",
            {
                "video_path": "/nonexistent/video.mp4",
                "style": "humorous"
            }
        )
        
        # 应该返回错误信息
        assert len(result) > 0
        assert "错误" in result[0].text or "error" in result[0].text.lower()


class TestMCPProtocolCompliance:
    """MCP协议合规性测试。"""
    
    @pytest.fixture
    def server(self):
        """服务器实例。"""
        config = DramaCraftConfig()
        with patch('src.dramacraft.llm.factory.create_llm_client', return_value=MockLLMClient()):
            return DramaCraftServer(config)
    
    @pytest.mark.asyncio
    async def test_list_tools_response_format(self, server):
        """测试列出工具的响应格式。"""
        tools = await server.list_tools()
        
        # 验证响应格式符合MCP标准
        assert hasattr(tools, 'tools')
        assert isinstance(tools.tools, list)
        
        for tool in tools.tools:
            assert hasattr(tool, 'name')
            assert hasattr(tool, 'description')
            assert hasattr(tool, 'inputSchema')
            assert isinstance(tool.name, str)
            assert isinstance(tool.description, str)
    
    @pytest.mark.asyncio
    async def test_tool_input_schema_validation(self, server):
        """测试工具输入模式验证。"""
        tools = await server.list_tools()
        
        for tool in tools.tools:
            schema = tool.inputSchema
            
            # 验证模式包含必要字段
            assert "type" in schema
            assert schema["type"] == "object"
            
            if "properties" in schema:
                assert isinstance(schema["properties"], dict)
            
            if "required" in schema:
                assert isinstance(schema["required"], list)
    
    @pytest.mark.asyncio
    async def test_tool_response_format(self, server):
        """测试工具响应格式。"""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            video_path = Path(f.name)
            f.write(b"fake video data")
        
        try:
            result = await server.call_tool(
                "generate_commentary",
                {
                    "video_path": str(video_path),
                    "style": "humorous"
                }
            )
            
            # 验证响应格式符合MCP标准
            assert isinstance(result, list)
            
            for item in result:
                assert hasattr(item, 'type')
                assert hasattr(item, 'text')
                assert item.type in ["text", "image", "resource"]
                
        finally:
            video_path.unlink()


class TestServerErrorHandling:
    """服务器错误处理测试。"""
    
    @pytest.fixture
    def server_with_failing_llm(self):
        """带有失败LLM的服务器。"""
        config = DramaCraftConfig()
        
        # 创建会失败的LLM客户端
        failing_client = Mock()
        failing_client.generate = AsyncMock(side_effect=Exception("LLM调用失败"))
        
        with patch('src.dramacraft.llm.factory.create_llm_client', return_value=failing_client):
            return DramaCraftServer(config)
    
    @pytest.mark.asyncio
    async def test_llm_failure_handling(self, server_with_failing_llm):
        """测试LLM失败处理。"""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            video_path = Path(f.name)
            f.write(b"fake video data")
        
        try:
            result = await server_with_failing_llm.call_tool(
                "generate_commentary",
                {
                    "video_path": str(video_path),
                    "style": "humorous"
                }
            )
            
            # 应该返回错误信息而不是抛出异常
            assert len(result) > 0
            assert "错误" in result[0].text or "失败" in result[0].text
            
        finally:
            video_path.unlink()
    
    @pytest.mark.asyncio
    async def test_concurrent_tool_calls(self, server):
        """测试并发工具调用。"""
        config = DramaCraftConfig()
        with patch('src.dramacraft.llm.factory.create_llm_client', return_value=MockLLMClient()):
            server = DramaCraftServer(config)
        
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            video_path = Path(f.name)
            f.write(b"fake video data")
        
        try:
            # 并发调用多个工具
            tasks = [
                server.call_tool("generate_commentary", {
                    "video_path": str(video_path),
                    "style": "humorous"
                }),
                server.call_tool("generate_commentary", {
                    "video_path": str(video_path),
                    "style": "professional"
                }),
                server.call_tool("generate_commentary", {
                    "video_path": str(video_path),
                    "style": "emotional"
                })
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 验证所有调用都成功
            for result in results:
                assert not isinstance(result, Exception)
                assert len(result) > 0
                
        finally:
            video_path.unlink()
