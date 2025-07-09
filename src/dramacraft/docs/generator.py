"""
文档生成器模块

提供自动化文档生成功能：
- API文档自动生成
- 代码示例提取
- 多格式输出
- 版本管理
"""

import ast
import inspect
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union
from dataclasses import dataclass, field
import markdown
from jinja2 import Environment, FileSystemLoader


@dataclass
class APIEndpoint:
    """API端点信息"""
    path: str
    method: str
    function_name: str
    description: str
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    responses: List[Dict[str, Any]] = field(default_factory=list)
    examples: List[Dict[str, Any]] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    deprecated: bool = False
    version: str = "1.0.0"


@dataclass
class CodeExample:
    """代码示例"""
    title: str
    description: str
    language: str
    code: str
    output: Optional[str] = None
    runnable: bool = False


@dataclass
class DocumentSection:
    """文档章节"""
    id: str
    title: str
    content: str
    level: int = 1
    subsections: List['DocumentSection'] = field(default_factory=list)
    examples: List[CodeExample] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class APIDocGenerator:
    """API文档生成器"""
    
    def __init__(self, project_name: str, version: str = "1.0.0"):
        """初始化API文档生成器"""
        self.project_name = project_name
        self.version = version
        self.endpoints: List[APIEndpoint] = []
        self.schemas: Dict[str, Dict[str, Any]] = {}
        
    def add_endpoint(self, endpoint: APIEndpoint):
        """添加API端点"""
        self.endpoints.append(endpoint)
    
    def add_schema(self, name: str, schema: Dict[str, Any]):
        """添加数据模式"""
        self.schemas[name] = schema
    
    def extract_from_function(self, func: callable, path: str, method: str) -> APIEndpoint:
        """从函数提取API文档"""
        # 获取函数签名
        sig = inspect.signature(func)
        
        # 解析文档字符串
        docstring = inspect.getdoc(func) or ""
        description = docstring.split('\n')[0] if docstring else func.__name__
        
        # 提取参数信息
        parameters = []
        for param_name, param in sig.parameters.items():
            if param_name in ['self', 'cls', 'request']:
                continue
                
            param_info = {
                "name": param_name,
                "type": self._get_type_name(param.annotation),
                "required": param.default == inspect.Parameter.empty,
                "default": None if param.default == inspect.Parameter.empty else param.default,
                "description": f"参数 {param_name}"
            }
            parameters.append(param_info)
        
        # 创建端点
        endpoint = APIEndpoint(
            path=path,
            method=method.upper(),
            function_name=func.__name__,
            description=description,
            parameters=parameters
        )
        
        return endpoint
    
    def _get_type_name(self, annotation) -> str:
        """获取类型名称"""
        if annotation == inspect.Parameter.empty:
            return "any"
        
        if hasattr(annotation, '__name__'):
            return annotation.__name__
        
        return str(annotation)
    
    def generate_openapi_spec(self) -> Dict[str, Any]:
        """生成OpenAPI规范"""
        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": self.project_name,
                "version": self.version,
                "description": f"{self.project_name} API文档"
            },
            "paths": {},
            "components": {
                "schemas": self.schemas
            }
        }
        
        # 添加路径
        for endpoint in self.endpoints:
            if endpoint.path not in spec["paths"]:
                spec["paths"][endpoint.path] = {}
            
            # 构建参数
            parameters = []
            for param in endpoint.parameters:
                parameters.append({
                    "name": param["name"],
                    "in": "query" if endpoint.method == "GET" else "body",
                    "required": param["required"],
                    "schema": {"type": param["type"]},
                    "description": param["description"]
                })
            
            # 构建响应
            responses = {
                "200": {
                    "description": "成功响应",
                    "content": {
                        "application/json": {
                            "schema": {"type": "object"}
                        }
                    }
                }
            }
            
            spec["paths"][endpoint.path][endpoint.method.lower()] = {
                "summary": endpoint.description,
                "parameters": parameters,
                "responses": responses,
                "tags": endpoint.tags
            }
        
        return spec
    
    def generate_markdown(self) -> str:
        """生成Markdown文档"""
        lines = [
            f"# {self.project_name} API文档",
            f"",
            f"版本: {self.version}",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"",
            f"## 概述",
            f"",
            f"本文档描述了 {self.project_name} 的API接口。",
            f"",
            f"## 端点列表",
            f""
        ]
        
        # 按标签分组
        endpoints_by_tag = {}
        for endpoint in self.endpoints:
            for tag in endpoint.tags or ["默认"]:
                if tag not in endpoints_by_tag:
                    endpoints_by_tag[tag] = []
                endpoints_by_tag[tag].append(endpoint)
        
        # 生成每个标签的文档
        for tag, endpoints in endpoints_by_tag.items():
            lines.extend([
                f"### {tag}",
                f""
            ])
            
            for endpoint in endpoints:
                lines.extend([
                    f"#### {endpoint.method} {endpoint.path}",
                    f"",
                    f"{endpoint.description}",
                    f"",
                    f"**参数:**",
                    f""
                ])
                
                if endpoint.parameters:
                    for param in endpoint.parameters:
                        required = "必需" if param["required"] else "可选"
                        lines.append(f"- `{param['name']}` ({param['type']}, {required}): {param['description']}")
                else:
                    lines.append("无参数")
                
                lines.extend([
                    f"",
                    f"**示例:**",
                    f"",
                    f"```bash",
                    f"curl -X {endpoint.method} '{endpoint.path}'",
                    f"```",
                    f"",
                    f"---",
                    f""
                ])
        
        return "\n".join(lines)


class DocumentationGenerator:
    """文档生成器"""
    
    def __init__(self, project_root: Path, output_dir: Path):
        """初始化文档生成器"""
        self.project_root = Path(project_root)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置Jinja2环境
        template_dir = Path(__file__).parent / "templates"
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=True
        )
        
        self.sections: List[DocumentSection] = []
        self.api_generator = APIDocGenerator("DramaCraft")
    
    def add_section(self, section: DocumentSection):
        """添加文档章节"""
        self.sections.append(section)
    
    def extract_docstrings(self, module_path: Path) -> List[DocumentSection]:
        """从模块提取文档字符串"""
        sections = []
        
        if module_path.is_file() and module_path.suffix == '.py':
            try:
                with open(module_path, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())
                
                # 提取模块文档
                if (ast.get_docstring(tree)):
                    module_doc = ast.get_docstring(tree)
                    section = DocumentSection(
                        id=f"module_{module_path.stem}",
                        title=f"模块: {module_path.stem}",
                        content=module_doc,
                        level=2
                    )
                    sections.append(section)
                
                # 提取类和函数文档
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        class_doc = ast.get_docstring(node)
                        if class_doc:
                            section = DocumentSection(
                                id=f"class_{node.name}",
                                title=f"类: {node.name}",
                                content=class_doc,
                                level=3
                            )
                            sections.append(section)
                    
                    elif isinstance(node, ast.FunctionDef):
                        func_doc = ast.get_docstring(node)
                        if func_doc:
                            section = DocumentSection(
                                id=f"function_{node.name}",
                                title=f"函数: {node.name}",
                                content=func_doc,
                                level=4
                            )
                            sections.append(section)
            
            except Exception as e:
                print(f"解析文件失败 {module_path}: {e}")
        
        return sections
    
    def scan_project(self):
        """扫描项目文件"""
        for py_file in self.project_root.rglob("*.py"):
            if "test" not in str(py_file) and "__pycache__" not in str(py_file):
                sections = self.extract_docstrings(py_file)
                self.sections.extend(sections)
    
    def generate_html(self, template_name: str = "documentation.html") -> str:
        """生成HTML文档"""
        template = self.jinja_env.get_template(template_name)
        
        # 构建导航
        navigation = self._build_navigation()
        
        # 渲染模板
        html_content = template.render(
            title="DramaCraft 文档",
            version="1.0.0",
            sections=self.sections,
            navigation=navigation,
            generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
        return html_content
    
    def _build_navigation(self) -> List[Dict[str, Any]]:
        """构建导航结构"""
        navigation = []
        
        for section in self.sections:
            nav_item = {
                "id": section.id,
                "title": section.title,
                "level": section.level,
                "children": []
            }
            
            for subsection in section.subsections:
                nav_item["children"].append({
                    "id": subsection.id,
                    "title": subsection.title,
                    "level": subsection.level
                })
            
            navigation.append(nav_item)
        
        return navigation
    
    def generate_search_index(self) -> Dict[str, Any]:
        """生成搜索索引"""
        index = {
            "documents": [],
            "index": {}
        }
        
        for section in self.sections:
            doc = {
                "id": section.id,
                "title": section.title,
                "content": section.content,
                "url": f"#{section.id}"
            }
            index["documents"].append(doc)
            
            # 简单的关键词索引
            words = section.content.lower().split()
            for word in words:
                if len(word) > 2:  # 忽略太短的词
                    if word not in index["index"]:
                        index["index"][word] = []
                    if section.id not in index["index"][word]:
                        index["index"][word].append(section.id)
        
        return index
    
    def build_documentation(self):
        """构建完整文档"""
        # 扫描项目
        self.scan_project()
        
        # 生成HTML
        html_content = self.generate_html()
        html_file = self.output_dir / "index.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # 生成API文档
        api_spec = self.api_generator.generate_openapi_spec()
        api_file = self.output_dir / "api.json"
        with open(api_file, 'w', encoding='utf-8') as f:
            json.dump(api_spec, f, ensure_ascii=False, indent=2)
        
        # 生成搜索索引
        search_index = self.generate_search_index()
        search_file = self.output_dir / "search.json"
        with open(search_file, 'w', encoding='utf-8') as f:
            json.dump(search_index, f, ensure_ascii=False, indent=2)
        
        # 复制静态资源
        self._copy_static_files()
        
        print(f"文档已生成到: {self.output_dir}")
    
    def _copy_static_files(self):
        """复制静态文件"""
        static_dir = Path(__file__).parent / "static"
        if static_dir.exists():
            import shutil
            target_static = self.output_dir / "static"
            if target_static.exists():
                shutil.rmtree(target_static)
            shutil.copytree(static_dir, target_static)
