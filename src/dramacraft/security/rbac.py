"""
基于角色的访问控制 (RBAC) 模块

实现企业级权限管理：
- 角色管理
- 权限控制
- 资源访问控制
- 动态权限检查
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum


class PermissionType(Enum):
    """权限类型枚举"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    ADMIN = "admin"


class ResourceType(Enum):
    """资源类型枚举"""
    VIDEO = "video"
    AUDIO = "audio"
    PROJECT = "project"
    USER = "user"
    SYSTEM = "system"
    API = "api"


@dataclass
class Permission:
    """权限模型"""
    id: str
    name: str
    description: str
    resource_type: ResourceType
    permission_type: PermissionType
    conditions: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Role:
    """角色模型"""
    id: str
    name: str
    description: str
    permissions: Set[str] = field(default_factory=set)
    parent_roles: Set[str] = field(default_factory=set)
    is_system_role: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class UserRole:
    """用户角色关联"""
    user_id: str
    role_id: str
    granted_by: str
    granted_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    conditions: Dict[str, Any] = field(default_factory=dict)


class PermissionManager:
    """权限管理器"""
    
    def __init__(self):
        self.permissions: Dict[str, Permission] = {}
        self._initialize_default_permissions()
    
    def _initialize_default_permissions(self):
        """初始化默认权限"""
        default_permissions = [
            # 视频权限
            Permission("video:read", "读取视频", "查看视频信息和内容", 
                      ResourceType.VIDEO, PermissionType.READ),
            Permission("video:write", "编辑视频", "创建和修改视频", 
                      ResourceType.VIDEO, PermissionType.WRITE),
            Permission("video:delete", "删除视频", "删除视频文件", 
                      ResourceType.VIDEO, PermissionType.DELETE),
            Permission("video:process", "处理视频", "执行视频处理任务", 
                      ResourceType.VIDEO, PermissionType.EXECUTE),
            
            # 音频权限
            Permission("audio:read", "读取音频", "查看音频信息", 
                      ResourceType.AUDIO, PermissionType.READ),
            Permission("audio:write", "编辑音频", "创建和修改音频", 
                      ResourceType.AUDIO, PermissionType.WRITE),
            Permission("audio:delete", "删除音频", "删除音频文件", 
                      ResourceType.AUDIO, PermissionType.DELETE),
            
            # 项目权限
            Permission("project:read", "读取项目", "查看项目信息", 
                      ResourceType.PROJECT, PermissionType.READ),
            Permission("project:write", "编辑项目", "创建和修改项目", 
                      ResourceType.PROJECT, PermissionType.WRITE),
            Permission("project:delete", "删除项目", "删除项目", 
                      ResourceType.PROJECT, PermissionType.DELETE),
            Permission("project:share", "分享项目", "分享项目给其他用户", 
                      ResourceType.PROJECT, PermissionType.EXECUTE),
            
            # 用户权限
            Permission("user:read", "读取用户", "查看用户信息", 
                      ResourceType.USER, PermissionType.READ),
            Permission("user:write", "编辑用户", "创建和修改用户", 
                      ResourceType.USER, PermissionType.WRITE),
            Permission("user:delete", "删除用户", "删除用户账户", 
                      ResourceType.USER, PermissionType.DELETE),
            
            # 系统权限
            Permission("system:read", "系统监控", "查看系统状态", 
                      ResourceType.SYSTEM, PermissionType.READ),
            Permission("system:write", "系统配置", "修改系统配置", 
                      ResourceType.SYSTEM, PermissionType.WRITE),
            Permission("system:admin", "系统管理", "完全系统管理权限", 
                      ResourceType.SYSTEM, PermissionType.ADMIN),
            
            # API权限
            Permission("api:read", "API读取", "调用只读API", 
                      ResourceType.API, PermissionType.READ),
            Permission("api:write", "API写入", "调用写入API", 
                      ResourceType.API, PermissionType.WRITE),
            Permission("api:admin", "API管理", "管理API配置", 
                      ResourceType.API, PermissionType.ADMIN),
        ]
        
        for permission in default_permissions:
            self.permissions[permission.id] = permission
    
    def create_permission(
        self, 
        permission_id: str,
        name: str,
        description: str,
        resource_type: ResourceType,
        permission_type: PermissionType,
        conditions: Dict[str, Any] = None
    ) -> Permission:
        """创建权限"""
        if permission_id in self.permissions:
            raise ValueError(f"Permission {permission_id} already exists")
        
        permission = Permission(
            id=permission_id,
            name=name,
            description=description,
            resource_type=resource_type,
            permission_type=permission_type,
            conditions=conditions or {}
        )
        
        self.permissions[permission_id] = permission
        return permission
    
    def get_permission(self, permission_id: str) -> Optional[Permission]:
        """获取权限"""
        return self.permissions.get(permission_id)
    
    def list_permissions(
        self, 
        resource_type: Optional[ResourceType] = None,
        permission_type: Optional[PermissionType] = None
    ) -> List[Permission]:
        """列出权限"""
        permissions = list(self.permissions.values())
        
        if resource_type:
            permissions = [p for p in permissions if p.resource_type == resource_type]
        
        if permission_type:
            permissions = [p for p in permissions if p.permission_type == permission_type]
        
        return permissions
    
    def delete_permission(self, permission_id: str) -> bool:
        """删除权限"""
        if permission_id in self.permissions:
            del self.permissions[permission_id]
            return True
        return False


class RoleManager:
    """角色管理器"""
    
    def __init__(self, permission_manager: PermissionManager):
        self.permission_manager = permission_manager
        self.roles: Dict[str, Role] = {}
        self.user_roles: Dict[str, List[UserRole]] = {}
        self._initialize_default_roles()
    
    def _initialize_default_roles(self):
        """初始化默认角色"""
        # 超级管理员角色
        admin_permissions = {p.id for p in self.permission_manager.permissions.values()}
        self.create_role(
            "admin",
            "超级管理员",
            "拥有所有权限的系统管理员",
            permissions=admin_permissions,
            is_system_role=True
        )
        
        # 编辑者角色
        editor_permissions = {
            "video:read", "video:write", "video:process",
            "audio:read", "audio:write",
            "project:read", "project:write", "project:share",
            "api:read", "api:write"
        }
        self.create_role(
            "editor",
            "编辑者",
            "可以创建和编辑视频项目",
            permissions=editor_permissions,
            is_system_role=True
        )
        
        # 查看者角色
        viewer_permissions = {
            "video:read", "audio:read", "project:read", "api:read"
        }
        self.create_role(
            "viewer",
            "查看者",
            "只能查看内容，不能修改",
            permissions=viewer_permissions,
            is_system_role=True
        )
        
        # 普通用户角色
        user_permissions = {
            "video:read", "video:write", "video:process",
            "audio:read", "audio:write",
            "project:read", "project:write",
            "api:read", "api:write"
        }
        self.create_role(
            "user",
            "普通用户",
            "标准用户权限",
            permissions=user_permissions,
            is_system_role=True
        )
    
    def create_role(
        self,
        role_id: str,
        name: str,
        description: str,
        permissions: Set[str] = None,
        parent_roles: Set[str] = None,
        is_system_role: bool = False
    ) -> Role:
        """创建角色"""
        if role_id in self.roles:
            raise ValueError(f"Role {role_id} already exists")
        
        # 验证权限是否存在
        if permissions:
            for perm_id in permissions:
                if perm_id not in self.permission_manager.permissions:
                    raise ValueError(f"Permission {perm_id} does not exist")
        
        # 验证父角色是否存在
        if parent_roles:
            for parent_id in parent_roles:
                if parent_id not in self.roles:
                    raise ValueError(f"Parent role {parent_id} does not exist")
        
        role = Role(
            id=role_id,
            name=name,
            description=description,
            permissions=permissions or set(),
            parent_roles=parent_roles or set(),
            is_system_role=is_system_role
        )
        
        self.roles[role_id] = role
        return role
    
    def get_role(self, role_id: str) -> Optional[Role]:
        """获取角色"""
        return self.roles.get(role_id)
    
    def update_role(
        self,
        role_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        permissions: Optional[Set[str]] = None,
        parent_roles: Optional[Set[str]] = None
    ) -> bool:
        """更新角色"""
        role = self.roles.get(role_id)
        if not role:
            return False
        
        if role.is_system_role:
            raise ValueError("Cannot modify system role")
        
        if name:
            role.name = name
        if description:
            role.description = description
        if permissions is not None:
            # 验证权限
            for perm_id in permissions:
                if perm_id not in self.permission_manager.permissions:
                    raise ValueError(f"Permission {perm_id} does not exist")
            role.permissions = permissions
        if parent_roles is not None:
            # 验证父角色
            for parent_id in parent_roles:
                if parent_id not in self.roles:
                    raise ValueError(f"Parent role {parent_id} does not exist")
            role.parent_roles = parent_roles
        
        role.updated_at = datetime.utcnow()
        return True
    
    def delete_role(self, role_id: str) -> bool:
        """删除角色"""
        role = self.roles.get(role_id)
        if not role:
            return False
        
        if role.is_system_role:
            raise ValueError("Cannot delete system role")
        
        # 检查是否有用户使用此角色
        for user_roles in self.user_roles.values():
            if any(ur.role_id == role_id for ur in user_roles):
                raise ValueError(f"Role {role_id} is still assigned to users")
        
        del self.roles[role_id]
        return True
    
    def assign_role_to_user(
        self,
        user_id: str,
        role_id: str,
        granted_by: str,
        expires_at: Optional[datetime] = None,
        conditions: Dict[str, Any] = None
    ) -> bool:
        """为用户分配角色"""
        if role_id not in self.roles:
            raise ValueError(f"Role {role_id} does not exist")
        
        # 检查用户是否已有此角色
        user_roles = self.user_roles.get(user_id, [])
        for user_role in user_roles:
            if user_role.role_id == role_id:
                return False  # 已有此角色
        
        user_role = UserRole(
            user_id=user_id,
            role_id=role_id,
            granted_by=granted_by,
            expires_at=expires_at,
            conditions=conditions or {}
        )
        
        if user_id not in self.user_roles:
            self.user_roles[user_id] = []
        
        self.user_roles[user_id].append(user_role)
        return True
    
    def revoke_role_from_user(self, user_id: str, role_id: str) -> bool:
        """撤销用户角色"""
        if user_id not in self.user_roles:
            return False
        
        user_roles = self.user_roles[user_id]
        for i, user_role in enumerate(user_roles):
            if user_role.role_id == role_id:
                del user_roles[i]
                return True
        
        return False
    
    def get_user_roles(self, user_id: str) -> List[Role]:
        """获取用户角色"""
        if user_id not in self.user_roles:
            return []
        
        roles = []
        current_time = datetime.utcnow()
        
        for user_role in self.user_roles[user_id]:
            # 检查角色是否过期
            if user_role.expires_at and current_time > user_role.expires_at:
                continue
            
            role = self.roles.get(user_role.role_id)
            if role:
                roles.append(role)
        
        return roles
    
    def get_user_permissions(self, user_id: str) -> Set[str]:
        """获取用户所有权限"""
        permissions = set()
        roles = self.get_user_roles(user_id)
        
        for role in roles:
            # 添加角色直接权限
            permissions.update(role.permissions)
            
            # 添加父角色权限
            self._add_parent_role_permissions(role, permissions)
        
        return permissions
    
    def _add_parent_role_permissions(self, role: Role, permissions: Set[str]):
        """递归添加父角色权限"""
        for parent_role_id in role.parent_roles:
            parent_role = self.roles.get(parent_role_id)
            if parent_role:
                permissions.update(parent_role.permissions)
                self._add_parent_role_permissions(parent_role, permissions)
    
    def check_permission(self, user_id: str, permission_id: str) -> bool:
        """检查用户是否有指定权限"""
        user_permissions = self.get_user_permissions(user_id)
        return permission_id in user_permissions
    
    def check_resource_access(
        self,
        user_id: str,
        resource_type: ResourceType,
        permission_type: PermissionType,
        resource_id: Optional[str] = None,
        context: Dict[str, Any] = None
    ) -> bool:
        """检查用户对资源的访问权限"""
        # 构建权限ID
        permission_id = f"{resource_type.value}:{permission_type.value}"
        
        if not self.check_permission(user_id, permission_id):
            return False
        
        # 检查条件权限
        permission = self.permission_manager.get_permission(permission_id)
        if permission and permission.conditions:
            return self._check_permission_conditions(
                user_id, permission, resource_id, context
            )
        
        return True
    
    def _check_permission_conditions(
        self,
        user_id: str,
        permission: Permission,
        resource_id: Optional[str],
        context: Dict[str, Any]
    ) -> bool:
        """检查权限条件"""
        # 这里可以实现复杂的条件检查逻辑
        # 例如：时间限制、IP限制、资源所有者检查等
        
        conditions = permission.conditions
        
        # 示例：检查资源所有者
        if "owner_only" in conditions and conditions["owner_only"]:
            if not context or context.get("owner_id") != user_id:
                return False
        
        # 示例：检查时间限制
        if "time_restriction" in conditions:
            time_restriction = conditions["time_restriction"]
            current_hour = datetime.utcnow().hour
            if not (time_restriction["start"] <= current_hour <= time_restriction["end"]):
                return False
        
        return True
