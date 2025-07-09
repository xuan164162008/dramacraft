"""
安全测试模块

测试DramaCraft的安全功能：
- 认证和授权
- 数据加密
- 权限控制
- 安全审计
- 多因素认证
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.dramacraft.security.auth import AuthManager, JWTManager, PasswordManager
from src.dramacraft.security.encryption import DataEncryption, RSAEncryption
from src.dramacraft.security.rbac import RoleManager, PermissionManager, ResourceType, PermissionType
from src.dramacraft.security.audit import SecurityAudit, AuditLogger, AuditEventType, RiskLevel
from src.dramacraft.security.mfa import MFAManager, TOTPProvider
from src.dramacraft.config import DramaCraftConfig


class TestAuthentication:
    """认证系统测试"""
    
    @pytest.fixture
    def auth_manager(self):
        """创建认证管理器"""
        config = Mock(spec=DramaCraftConfig)
        config.security.jwt_secret_key = "test-secret-key"
        config.security.jwt_algorithm = "HS256"
        config.security.session_encryption_key = "test-session-key-32-bytes-long"
        
        return AuthManager(config)
    
    @pytest.fixture
    def jwt_manager(self):
        """创建JWT管理器"""
        return JWTManager("test-secret-key")
    
    def test_password_hashing(self):
        """测试密码哈希"""
        password = "test_password_123"
        
        # 测试密码哈希
        hashed = PasswordManager.hash_password(password)
        assert hashed != password
        assert len(hashed) > 50  # bcrypt哈希长度
        
        # 测试密码验证
        assert PasswordManager.verify_password(password, hashed)
        assert not PasswordManager.verify_password("wrong_password", hashed)
    
    def test_secure_password_generation(self):
        """测试安全密码生成"""
        password = PasswordManager.generate_secure_password(16)
        
        assert len(password) == 16
        assert any(c.isupper() for c in password)  # 包含大写字母
        assert any(c.islower() for c in password)  # 包含小写字母
        assert any(c.isdigit() for c in password)  # 包含数字
        assert any(c in "!@#$%^&*" for c in password)  # 包含特殊字符
    
    def test_jwt_token_creation_and_verification(self, jwt_manager):
        """测试JWT令牌创建和验证"""
        user_id = "test_user_123"
        permissions = ["video:read", "video:write"]
        
        # 创建访问令牌
        access_token = jwt_manager.create_access_token(user_id, permissions)
        assert access_token is not None
        assert len(access_token) > 100  # JWT令牌长度
        
        # 验证令牌
        payload = jwt_manager.verify_token(access_token)
        assert payload["sub"] == user_id
        assert payload["permissions"] == permissions
        assert payload["type"] == "access"
        
        # 创建刷新令牌
        refresh_token = jwt_manager.create_refresh_token(user_id)
        refresh_payload = jwt_manager.verify_token(refresh_token)
        assert refresh_payload["sub"] == user_id
        assert refresh_payload["type"] == "refresh"
    
    def test_expired_token_rejection(self, jwt_manager):
        """测试过期令牌拒绝"""
        user_id = "test_user"
        permissions = ["video:read"]
        
        # 创建立即过期的令牌
        expired_token = jwt_manager.create_access_token(
            user_id, permissions, expires_delta=timedelta(seconds=-1)
        )
        
        # 验证过期令牌应该失败
        with pytest.raises(ValueError, match="Token has expired"):
            jwt_manager.verify_token(expired_token)
    
    def test_user_registration_and_authentication(self, auth_manager):
        """测试用户注册和认证"""
        username = "test_user"
        email = "test@example.com"
        password = "secure_password_123"
        
        # 注册用户
        user = auth_manager.register_user(username, email, password)
        assert user.username == username
        assert user.email == email
        assert user.id is not None
        
        # 认证用户
        authenticated_user = auth_manager.authenticate_user(username, password)
        assert authenticated_user is not None
        assert authenticated_user.username == username
        
        # 错误密码认证失败
        failed_auth = auth_manager.authenticate_user(username, "wrong_password")
        assert failed_auth is None
    
    def test_duplicate_user_registration(self, auth_manager):
        """测试重复用户注册"""
        username = "duplicate_user"
        email = "duplicate@example.com"
        password = "password123"
        
        # 第一次注册成功
        auth_manager.register_user(username, email, password)
        
        # 第二次注册应该失败
        with pytest.raises(ValueError, match="Username already exists"):
            auth_manager.register_user(username, email, password)


class TestEncryption:
    """加密系统测试"""
    
    @pytest.fixture
    def data_encryption(self):
        """创建数据加密器"""
        return DataEncryption()
    
    @pytest.fixture
    def rsa_encryption(self):
        """创建RSA加密器"""
        return RSAEncryption()
    
    def test_symmetric_encryption(self, data_encryption):
        """测试对称加密"""
        original_data = "这是需要加密的敏感数据"
        
        # 加密数据
        encrypted_result = data_encryption.encrypt_data(original_data)
        assert "data" in encrypted_result
        assert "key_id" in encrypted_result
        assert "algorithm" in encrypted_result
        
        # 解密数据
        decrypted_data = data_encryption.decrypt_data(encrypted_result)
        assert decrypted_data.decode('utf-8') == original_data
    
    def test_file_encryption(self, data_encryption, temp_dir):
        """测试文件加密"""
        # 创建测试文件
        test_file = temp_dir / "test_file.txt"
        test_content = "这是测试文件内容"
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        # 加密文件
        encrypted_file = data_encryption.encrypt_file(test_file)
        assert encrypted_file.exists()
        assert encrypted_file.suffix == ".enc"
        
        # 解密文件
        decrypted_file = data_encryption.decrypt_file(encrypted_file)
        
        with open(decrypted_file, 'r', encoding='utf-8') as f:
            decrypted_content = f.read()
        
        assert decrypted_content == test_content
    
    def test_rsa_encryption(self, rsa_encryption):
        """测试RSA非对称加密"""
        original_data = b"RSA encryption test data"
        
        # 使用公钥加密
        encrypted_data = rsa_encryption.encrypt_with_public_key(original_data)
        assert encrypted_data != original_data
        assert len(encrypted_data) > len(original_data)
        
        # 使用私钥解密
        decrypted_data = rsa_encryption.decrypt_with_private_key(encrypted_data)
        assert decrypted_data == original_data
    
    def test_digital_signature(self, rsa_encryption):
        """测试数字签名"""
        data = b"Data to be signed"
        
        # 创建数字签名
        signature = rsa_encryption.sign_data(data)
        assert signature is not None
        assert len(signature) > 0
        
        # 验证签名
        is_valid = rsa_encryption.verify_signature(data, signature)
        assert is_valid
        
        # 验证篡改数据的签名
        tampered_data = b"Tampered data"
        is_invalid = rsa_encryption.verify_signature(tampered_data, signature)
        assert not is_invalid


class TestRBAC:
    """RBAC权限控制测试"""
    
    @pytest.fixture
    def permission_manager(self):
        """创建权限管理器"""
        return PermissionManager()
    
    @pytest.fixture
    def role_manager(self, permission_manager):
        """创建角色管理器"""
        return RoleManager(permission_manager)
    
    def test_permission_creation(self, permission_manager):
        """测试权限创建"""
        permission_id = "test:permission"
        name = "测试权限"
        description = "这是一个测试权限"
        
        permission = permission_manager.create_permission(
            permission_id, name, description,
            ResourceType.VIDEO, PermissionType.READ
        )
        
        assert permission.id == permission_id
        assert permission.name == name
        assert permission.resource_type == ResourceType.VIDEO
        assert permission.permission_type == PermissionType.READ
    
    def test_role_creation_and_management(self, role_manager):
        """测试角色创建和管理"""
        role_id = "test_role"
        role_name = "测试角色"
        permissions = {"video:read", "video:write"}
        
        # 创建角色
        role = role_manager.create_role(
            role_id, role_name, "测试角色描述", permissions
        )
        
        assert role.id == role_id
        assert role.name == role_name
        assert role.permissions == permissions
    
    def test_user_role_assignment(self, role_manager):
        """测试用户角色分配"""
        user_id = "test_user"
        role_id = "editor"  # 使用默认角色
        granted_by = "admin"
        
        # 分配角色
        success = role_manager.assign_role_to_user(user_id, role_id, granted_by)
        assert success
        
        # 获取用户角色
        user_roles = role_manager.get_user_roles(user_id)
        assert len(user_roles) == 1
        assert user_roles[0].id == role_id
    
    def test_permission_checking(self, role_manager):
        """测试权限检查"""
        user_id = "test_user"
        role_id = "editor"  # 编辑者角色
        granted_by = "admin"
        
        # 分配角色
        role_manager.assign_role_to_user(user_id, role_id, granted_by)
        
        # 检查权限
        has_read = role_manager.check_permission(user_id, "video:read")
        has_write = role_manager.check_permission(user_id, "video:write")
        has_delete = role_manager.check_permission(user_id, "video:delete")
        
        assert has_read  # 编辑者有读权限
        assert has_write  # 编辑者有写权限
        assert not has_delete  # 编辑者没有删除权限


class TestSecurityAudit:
    """安全审计测试"""
    
    @pytest.fixture
    def audit_logger(self, temp_dir):
        """创建审计日志记录器"""
        log_file = temp_dir / "audit.log"
        return AuditLogger(log_file)
    
    @pytest.fixture
    def security_audit(self, audit_logger):
        """创建安全审计管理器"""
        return SecurityAudit(audit_logger)
    
    def test_audit_event_recording(self, security_audit):
        """测试审计事件记录"""
        event_id = security_audit.record_event(
            event_type=AuditEventType.LOGIN,
            user_id="test_user",
            session_id="session_123",
            source_ip="192.168.1.100",
            action="user_login",
            result="success",
            risk_level=RiskLevel.LOW
        )
        
        assert event_id is not None
        assert len(event_id) > 0
    
    def test_failed_login_detection(self, security_audit):
        """测试登录失败检测"""
        user_id = "test_user"
        source_ip = "192.168.1.100"
        
        # 模拟多次登录失败
        for i in range(6):  # 超过阈值(5次)
            security_audit.record_event(
                event_type=AuditEventType.LOGIN_FAILED,
                user_id=user_id,
                session_id=None,
                source_ip=source_ip,
                action="login_attempt",
                result="failure",
                risk_level=RiskLevel.MEDIUM
            )
        
        # 检查是否生成了告警
        alerts = security_audit.get_alerts(severity=RiskLevel.HIGH)
        assert len(alerts) > 0
        
        # 验证告警类型
        login_alerts = [a for a in alerts if a.alert_type == "multiple_failed_logins"]
        assert len(login_alerts) > 0


class TestMFA:
    """多因素认证测试"""
    
    @pytest.fixture
    def totp_provider(self):
        """创建TOTP提供者"""
        return TOTPProvider()
    
    @pytest.fixture
    def mfa_manager(self, totp_provider):
        """创建MFA管理器"""
        return MFAManager(totp_provider)
    
    def test_totp_generation_and_verification(self, totp_provider):
        """测试TOTP生成和验证"""
        secret = totp_provider.generate_secret()
        assert len(secret) == 32  # Base32编码的20字节
        
        # 生成TOTP码
        current_time = int(time.time())
        totp_code = totp_provider.generate_totp(secret, current_time)
        assert len(totp_code) == 6  # 6位数字
        assert totp_code.isdigit()
        
        # 验证TOTP码
        is_valid = totp_provider.verify_totp(secret, totp_code, current_time)
        assert is_valid
        
        # 验证错误的TOTP码
        wrong_code = "123456"
        is_invalid = totp_provider.verify_totp(secret, wrong_code, current_time)
        assert not is_invalid
    
    def test_mfa_device_setup(self, mfa_manager):
        """测试MFA设备设置"""
        user_id = "test_user"
        device_name = "Test Device"
        
        # 设置TOTP设备
        device_id, qr_code = mfa_manager.setup_totp(user_id, device_name)
        assert device_id is not None
        assert qr_code is not None
        assert len(qr_code) > 0  # QR码数据
        
        # 获取设备
        device = mfa_manager.devices.get(device_id)
        assert device is not None
        assert device.user_id == user_id
        assert device.name == device_name
    
    def test_backup_codes_generation(self, mfa_manager):
        """测试备用码生成"""
        user_id = "test_user"
        
        device_id, codes = mfa_manager.generate_backup_codes(user_id)
        assert device_id is not None
        assert len(codes) == 10  # 默认生成10个备用码
        
        # 验证备用码格式
        for code in codes:
            assert len(code) == 8  # 8位备用码
            assert code.isupper()  # 大写字母和数字
        
        # 测试备用码验证
        test_code = codes[0]
        is_valid = mfa_manager.verify_backup_code(user_id, test_code)
        assert is_valid
        
        # 同一备用码不能重复使用
        is_invalid = mfa_manager.verify_backup_code(user_id, test_code)
        assert not is_invalid


@pytest.mark.asyncio
class TestSecurityIntegration:
    """安全系统集成测试"""
    
    async def test_complete_authentication_flow(self):
        """测试完整的认证流程"""
        # 创建配置
        config = Mock(spec=DramaCraftConfig)
        config.security.jwt_secret_key = "test-secret-key"
        config.security.jwt_algorithm = "HS256"
        config.security.session_encryption_key = "test-session-key-32-bytes-long"
        
        # 创建管理器
        auth_manager = AuthManager(config)
        permission_manager = PermissionManager()
        role_manager = RoleManager(permission_manager)
        
        # 1. 注册用户
        user = auth_manager.register_user(
            "integration_user", 
            "integration@test.com", 
            "secure_password_123"
        )
        
        # 2. 分配角色
        role_manager.assign_role_to_user(user.id, "editor", "admin")
        
        # 3. 认证用户
        authenticated_user = auth_manager.authenticate_user(
            "integration_user", 
            "secure_password_123"
        )
        assert authenticated_user is not None
        
        # 4. 创建令牌
        tokens = auth_manager.create_auth_tokens(authenticated_user)
        assert tokens.access_token is not None
        assert tokens.refresh_token is not None
        
        # 5. 验证令牌
        payload = auth_manager.verify_access_token(tokens.access_token)
        assert payload is not None
        assert payload["sub"] == user.id
        
        # 6. 检查权限
        has_permission = role_manager.check_permission(user.id, "video:read")
        assert has_permission
    
    async def test_security_violation_detection(self):
        """测试安全违规检测"""
        # 创建审计系统
        audit_logger = AuditLogger(Path("/tmp/test_audit.log"))
        security_audit = SecurityAudit(audit_logger)
        
        user_id = "suspicious_user"
        source_ip = "192.168.1.200"
        
        # 模拟可疑活动：快速连续的权限拒绝
        for i in range(5):
            security_audit.record_event(
                event_type=AuditEventType.PERMISSION_DENIED,
                user_id=user_id,
                session_id=f"session_{i}",
                source_ip=source_ip,
                action="access_restricted_resource",
                result="denied",
                risk_level=RiskLevel.MEDIUM
            )
        
        # 检查是否触发了安全告警
        alerts = security_audit.get_alerts(severity=RiskLevel.CRITICAL)
        privilege_alerts = [
            a for a in alerts 
            if a.alert_type == "privilege_escalation"
        ]
        
        assert len(privilege_alerts) > 0
