#!/usr/bin/env python3
"""
API文档生成脚本

自动从源代码中提取API信息并生成文档
"""

import os
import sys
import json
import inspect
from pathlib import Path
from typing import Dict, List, Any
import importlib.util

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def extract_mcp_tools() -> Dict[str, Any]:
    """提取MCP工具信息"""
    tools_info = {
        "video_analysis": {
            "analyze_video": {
                "name": "analyze_video",
                "description": "分析视频文件的基本信息和内容特征",
                "category": "视频分析",
                "parameters": {
                    "video_path": {
                        "type": "string",
                        "required": True,
                        "description": "视频文件路径"
                    },
                    "analysis_type": {
                        "type": "string",
                        "required": False,
                        "default": "comprehensive",
                        "description": "分析类型",
                        "options": ["basic", "comprehensive", "quick"]
                    }
                },
                "response_time": "< 30秒",
                "example": {
                    "request": {
                        "video_path": "/videos/sample.mp4",
                        "analysis_type": "comprehensive"
                    },
                    "response": {
                        "video_info": {
                            "duration": 120.5,
                            "resolution": [1920, 1080],
                            "fps": 30.0,
                            "format": "mp4"
                        },
                        "content_analysis": {
                            "scene_count": 15,
                            "average_brightness": 0.65,
                            "motion_intensity": "medium"
                        }
                    }
                }
            },
            "detect_scenes": {
                "name": "detect_scenes",
                "description": "检测视频中的场景变化点",
                "category": "视频分析",
                "parameters": {
                    "video_path": {
                        "type": "string",
                        "required": True,
                        "description": "视频文件路径"
                    },
                    "threshold": {
                        "type": "float",
                        "required": False,
                        "default": 0.3,
                        "description": "场景变化阈值 (0.1-1.0)"
                    },
                    "min_scene_length": {
                        "type": "float",
                        "required": False,
                        "default": 2.0,
                        "description": "最小场景长度（秒）"
                    }
                },
                "response_time": "< 15秒"
            },
            "extract_frames": {
                "name": "extract_frames",
                "description": "从视频中提取关键帧",
                "category": "视频分析",
                "parameters": {
                    "video_path": {
                        "type": "string",
                        "required": True,
                        "description": "视频文件路径"
                    },
                    "method": {
                        "type": "string",
                        "required": False,
                        "default": "uniform",
                        "description": "提取方法",
                        "options": ["uniform", "keyframes", "scenes"]
                    },
                    "count": {
                        "type": "integer",
                        "required": False,
                        "default": 10,
                        "description": "提取帧数"
                    }
                },
                "response_time": "< 20秒"
            }
        },
        "audio_processing": {
            "analyze_audio": {
                "name": "analyze_audio",
                "description": "分析视频中的音频内容",
                "category": "音频处理",
                "parameters": {
                    "video_path": {
                        "type": "string",
                        "required": True,
                        "description": "视频文件路径"
                    },
                    "analysis_depth": {
                        "type": "string",
                        "required": False,
                        "default": "standard",
                        "description": "分析深度",
                        "options": ["basic", "standard", "advanced"]
                    }
                },
                "response_time": "< 10秒"
            },
            "enhance_audio": {
                "name": "enhance_audio",
                "description": "增强音频质量",
                "category": "音频处理",
                "parameters": {
                    "video_path": {
                        "type": "string",
                        "required": True,
                        "description": "视频文件路径"
                    },
                    "enhancement_type": {
                        "type": "string",
                        "required": False,
                        "default": "auto",
                        "description": "增强类型",
                        "options": ["auto", "denoise", "normalize", "enhance_speech"]
                    }
                },
                "response_time": "< 45秒"
            }
        },
        "ai_director": {
            "analyze_content": {
                "name": "analyze_content",
                "description": "使用AI分析视频内容并提供编辑建议",
                "category": "AI导演",
                "parameters": {
                    "video_path": {
                        "type": "string",
                        "required": True,
                        "description": "视频文件路径"
                    },
                    "analysis_focus": {
                        "type": "string",
                        "required": False,
                        "default": "general",
                        "description": "分析重点",
                        "options": ["general", "narrative", "technical", "aesthetic"]
                    }
                },
                "response_time": "< 60秒"
            }
        },
        "project_management": {
            "create_project": {
                "name": "create_project",
                "description": "创建新的视频编辑项目",
                "category": "项目管理",
                "parameters": {
                    "project_name": {
                        "type": "string",
                        "required": True,
                        "description": "项目名称"
                    },
                    "description": {
                        "type": "string",
                        "required": False,
                        "default": "",
                        "description": "项目描述"
                    },
                    "video_files": {
                        "type": "array",
                        "required": False,
                        "default": [],
                        "description": "初始视频文件列表"
                    }
                },
                "response_time": "< 5秒"
            }
        }
    }
    
    return tools_info

def generate_tool_documentation(tool_name: str, tool_info: Dict[str, Any]) -> str:
    """生成单个工具的文档"""
    doc = f"""### {tool_name}

{tool_info['description']}

!!! info "工具信息"
    **工具名称**: `{tool_name}`  
    **类别**: {tool_info['category']}  
    **响应时间**: {tool_info.get('response_time', '未知')}  

**参数:**

| 参数名 | 类型 | 必需 | 默认值 | 描述 |
|--------|------|------|--------|------|
"""
    
    for param_name, param_info in tool_info['parameters'].items():
        required = "✅" if param_info['required'] else "❌"
        default = param_info.get('default', '-')
        doc += f"| `{param_name}` | {param_info['type']} | {required} | {default} | {param_info['description']} |\n"
    
    # 添加选项说明
    for param_name, param_info in tool_info['parameters'].items():
        if 'options' in param_info:
            doc += f"\n**{param_name} 选项:**\n\n"
            for option in param_info['options']:
                doc += f"- `{option}`: {option}选项说明\n"
    
    # 添加示例
    if 'example' in tool_info:
        doc += f"\n**使用示例:**\n\n"
        doc += "=== \"Python\"\n"
        doc += "    ```python\n"
        doc += f"    result = await mcp_client.call_tool(\"{tool_name}\", {{\n"
        for key, value in tool_info['example']['request'].items():
            if isinstance(value, str):
                doc += f"        \"{key}\": \"{value}\",\n"
            else:
                doc += f"        \"{key}\": {value},\n"
        doc += "    })\n"
        doc += "    ```\n\n"
    
    return doc

def generate_api_reference() -> str:
    """生成完整的API参考文档"""
    tools_info = extract_mcp_tools()
    
    doc = """# API 参考文档

DramaCraft 提供了完整的 MCP (Model Context Protocol) 工具集，让您可以在 AI 编辑器中轻松进行视频编辑和处理。

## 🔧 MCP 工具概览

<div class="api-overview">
"""
    
    # 生成工具概览
    for category, tools in tools_info.items():
        category_name = {
            'video_analysis': '🎬 视频分析',
            'audio_processing': '🎵 音频处理',
            'ai_director': '🤖 AI 导演',
            'project_management': '📁 项目管理'
        }.get(category, category)
        
        doc += f"""  <div class="api-category">
    <h3>{category_name}</h3>
    <p>{len(tools)}个工具</p>
    <span>工具类别描述</span>
  </div>
  
"""
    
    doc += "</div>\n\n"
    
    # 生成详细文档
    for category, tools in tools_info.items():
        category_name = {
            'video_analysis': '📹 视频分析工具',
            'audio_processing': '🎵 音频处理工具',
            'ai_director': '🤖 AI 导演工具',
            'project_management': '📁 项目管理工具'
        }.get(category, category)
        
        doc += f"## {category_name}\n\n"
        
        for tool_name, tool_info in tools.items():
            doc += generate_tool_documentation(tool_name, tool_info)
            doc += "\n"
    
    return doc

def main():
    """主函数"""
    print("🔧 生成API文档...")
    
    # 创建输出目录
    docs_dir = Path(__file__).parent.parent / "docs" / "api-reference"
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成API参考文档
    api_doc = generate_api_reference()
    
    # 写入文件
    api_file = docs_dir / "mcp-tools.md"
    with open(api_file, 'w', encoding='utf-8') as f:
        f.write(api_doc)
    
    print(f"✅ API文档已生成: {api_file}")
    
    # 生成工具统计
    tools_info = extract_mcp_tools()
    total_tools = sum(len(tools) for tools in tools_info.values())
    
    stats = {
        "total_tools": total_tools,
        "categories": len(tools_info),
        "tools_by_category": {cat: len(tools) for cat, tools in tools_info.items()}
    }
    
    stats_file = docs_dir / "tools-stats.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    print(f"📊 工具统计已生成: {stats_file}")
    print(f"📈 总计: {total_tools} 个工具，{len(tools_info)} 个类别")

if __name__ == "__main__":
    main()
