"""
认证和授权管理模块

实现企业级身份认证：
- JWT Token 管理
- OAuth 2.0 集成
- 会话管理
- 安全策略
"""

import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List
from dataclasses import dataclass
from pathlib import Path
import jwt
import bcrypt
from cryptography.fernet import Fernet

from ..config import DramaCraftConfig


@dataclass
class User:
    """用户信息模型"""
    id: str
    username: str
    email: str
    roles: List[str]
    permissions: List[str]
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True
    mfa_enabled: bool = False


@dataclass
class AuthToken:
    """认证令牌模型"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    scope: List[str] = None


class JWTManager:
    """JWT 令牌管理器"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire = timedelta(hours=1)
        self.refresh_token_expire = timedelta(days=30)
    
    def create_access_token(
        self, 
        user_id: str, 
        permissions: List[str],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """创建访问令牌"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + self.access_token_expire
        
        payload = {
            "sub": user_id,
            "permissions": permissions,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(self, user_id: str) -> str:
        """创建刷新令牌"""
        expire = datetime.utcnow() + self.refresh_token_expire
        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """验证令牌"""
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")


class PasswordManager:
    """密码管理器"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """哈希密码"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """验证密码"""
        return bcrypt.checkpw(
            password.encode('utf-8'), 
            hashed.encode('utf-8')
        )
    
    @staticmethod
    def generate_secure_password(length: int = 16) -> str:
        """生成安全密码"""
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))


class SessionManager:
    """会话管理器"""
    
    def __init__(self, encryption_key: bytes):
        self.cipher = Fernet(encryption_key)
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = timedelta(hours=24)
    
    def create_session(self, user_id: str, metadata: Dict[str, Any]) -> str:
        """创建会话"""
        session_id = secrets.token_urlsafe(32)
        session_data = {
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "metadata": metadata
        }
        
        # 加密会话数据
        encrypted_data = self.cipher.encrypt(
            str(session_data).encode('utf-8')
        )
        self.sessions[session_id] = {
            "data": encrypted_data,
            "expires_at": datetime.utcnow() + self.session_timeout
        }
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        if datetime.utcnow() > session["expires_at"]:
            del self.sessions[session_id]
            return None
        
        # 解密会话数据
        try:
            decrypted_data = self.cipher.decrypt(session["data"])
            return eval(decrypted_data.decode('utf-8'))
        except Exception:
            return None
    
    def update_session_activity(self, session_id: str) -> bool:
        """更新会话活动时间"""
        session_data = self.get_session(session_id)
        if session_data:
            session_data["last_activity"] = datetime.utcnow()
            encrypted_data = self.cipher.encrypt(
                str(session_data).encode('utf-8')
            )
            self.sessions[session_id]["data"] = encrypted_data
            return True
        return False
    
    def revoke_session(self, session_id: str) -> bool:
        """撤销会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False


class AuthManager:
    """认证管理器"""
    
    def __init__(self, config: DramaCraftConfig):
        self.config = config
        self.jwt_manager = JWTManager(
            secret_key=config.security.jwt_secret_key,
            algorithm=config.security.jwt_algorithm
        )
        self.password_manager = PasswordManager()
        self.session_manager = SessionManager(
            encryption_key=config.security.session_encryption_key.encode()
        )
        
        # 用户存储 (实际应用中应使用数据库)
        self.users: Dict[str, User] = {}
        self.user_credentials: Dict[str, str] = {}  # username -> hashed_password
    
    def register_user(
        self, 
        username: str, 
        email: str, 
        password: str,
        roles: List[str] = None
    ) -> User:
        """注册用户"""
        if username in self.user_credentials:
            raise ValueError("Username already exists")
        
        user_id = secrets.token_urlsafe(16)
        hashed_password = self.password_manager.hash_password(password)
        
        user = User(
            id=user_id,
            username=username,
            email=email,
            roles=roles or ["user"],
            permissions=self._get_permissions_for_roles(roles or ["user"]),
            created_at=datetime.utcnow()
        )
        
        self.users[user_id] = user
        self.user_credentials[username] = hashed_password
        
        return user
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """认证用户"""
        if username not in self.user_credentials:
            return None
        
        hashed_password = self.user_credentials[username]
        if not self.password_manager.verify_password(password, hashed_password):
            return None
        
        # 查找用户
        for user in self.users.values():
            if user.username == username:
                user.last_login = datetime.utcnow()
                return user
        
        return None
    
    def create_auth_tokens(self, user: User) -> AuthToken:
        """创建认证令牌"""
        access_token = self.jwt_manager.create_access_token(
            user_id=user.id,
            permissions=user.permissions
        )
        refresh_token = self.jwt_manager.create_refresh_token(user.id)
        
        return AuthToken(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=3600,
            scope=user.permissions
        )
    
    def verify_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证访问令牌"""
        try:
            payload = self.jwt_manager.verify_token(token)
            if payload.get("type") != "access":
                return None
            return payload
        except ValueError:
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """刷新访问令牌"""
        try:
            payload = self.jwt_manager.verify_token(refresh_token)
            if payload.get("type") != "refresh":
                return None
            
            user_id = payload.get("sub")
            user = self.users.get(user_id)
            if not user or not user.is_active:
                return None
            
            return self.jwt_manager.create_access_token(
                user_id=user.id,
                permissions=user.permissions
            )
        except ValueError:
            return None
    
    def _get_permissions_for_roles(self, roles: List[str]) -> List[str]:
        """根据角色获取权限"""
        role_permissions = {
            "admin": [
                "video:read", "video:write", "video:delete",
                "user:read", "user:write", "user:delete",
                "system:read", "system:write"
            ],
            "editor": [
                "video:read", "video:write",
                "user:read"
            ],
            "user": [
                "video:read"
            ]
        }
        
        permissions = set()
        for role in roles:
            permissions.update(role_permissions.get(role, []))
        
        return list(permissions)


class OAuthProvider:
    """OAuth 2.0 提供者"""
    
    def __init__(self, auth_manager: AuthManager):
        self.auth_manager = auth_manager
        self.authorization_codes: Dict[str, Dict[str, Any]] = {}
        self.code_expire_time = timedelta(minutes=10)
    
    def generate_authorization_code(
        self, 
        user_id: str, 
        client_id: str,
        scope: List[str],
        redirect_uri: str
    ) -> str:
        """生成授权码"""
        code = secrets.token_urlsafe(32)
        self.authorization_codes[code] = {
            "user_id": user_id,
            "client_id": client_id,
            "scope": scope,
            "redirect_uri": redirect_uri,
            "expires_at": datetime.utcnow() + self.code_expire_time
        }
        return code
    
    def exchange_code_for_token(
        self, 
        code: str, 
        client_id: str,
        redirect_uri: str
    ) -> Optional[AuthToken]:
        """用授权码换取令牌"""
        if code not in self.authorization_codes:
            return None
        
        code_data = self.authorization_codes[code]
        
        # 验证授权码
        if (datetime.utcnow() > code_data["expires_at"] or
            code_data["client_id"] != client_id or
            code_data["redirect_uri"] != redirect_uri):
            del self.authorization_codes[code]
            return None
        
        # 获取用户信息
        user = self.auth_manager.users.get(code_data["user_id"])
        if not user:
            del self.authorization_codes[code]
            return None
        
        # 创建令牌
        tokens = self.auth_manager.create_auth_tokens(user)
        
        # 删除已使用的授权码
        del self.authorization_codes[code]
        
        return tokens
