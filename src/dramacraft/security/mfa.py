"""
多因素认证 (MFA) 模块

提供企业级多因素认证功能：
- TOTP (Time-based One-Time Password)
- SMS 验证码
- 邮箱验证码
- 备用恢复码
"""

import secrets
import time
import hmac
import hashlib
import base64
import qrcode
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import io


class MFAMethod(Enum):
    """MFA 方法枚举"""
    TOTP = "totp"
    SMS = "sms"
    EMAIL = "email"
    BACKUP_CODES = "backup_codes"


@dataclass
class MFADevice:
    """MFA 设备模型"""
    id: str
    user_id: str
    method: MFAMethod
    name: str
    secret: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    is_verified: bool = False
    is_primary: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None
    backup_codes: List[str] = field(default_factory=list)


@dataclass
class MFAChallenge:
    """MFA 挑战模型"""
    id: str
    user_id: str
    device_id: str
    method: MFAMethod
    code: str
    expires_at: datetime
    attempts: int = 0
    max_attempts: int = 3
    is_used: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)


class TOTPProvider:
    """TOTP 提供者"""
    
    def __init__(self, issuer: str = "DramaCraft", digits: int = 6, period: int = 30):
        """初始化 TOTP 提供者"""
        self.issuer = issuer
        self.digits = digits
        self.period = period
    
    def generate_secret(self) -> str:
        """生成 TOTP 密钥"""
        return base64.b32encode(secrets.token_bytes(20)).decode('utf-8')
    
    def generate_qr_code(self, secret: str, account_name: str) -> bytes:
        """生成 QR 码"""
        # 构建 TOTP URI
        uri = f"otpauth://totp/{self.issuer}:{account_name}?secret={secret}&issuer={self.issuer}&digits={self.digits}&period={self.period}"
        
        # 生成 QR 码
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)
        
        # 转换为图片
        img = qr.make_image(fill_color="black", back_color="white")
        
        # 转换为字节
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        return img_buffer.getvalue()
    
    def generate_totp(self, secret: str, timestamp: Optional[int] = None) -> str:
        """生成 TOTP 码"""
        if timestamp is None:
            timestamp = int(time.time())
        
        # 计算时间步长
        time_step = timestamp // self.period
        
        # 转换为字节
        time_bytes = time_step.to_bytes(8, byteorder='big')
        secret_bytes = base64.b32decode(secret)
        
        # 计算 HMAC
        hmac_hash = hmac.new(secret_bytes, time_bytes, hashlib.sha1).digest()
        
        # 动态截断
        offset = hmac_hash[-1] & 0x0f
        code = (
            (hmac_hash[offset] & 0x7f) << 24 |
            (hmac_hash[offset + 1] & 0xff) << 16 |
            (hmac_hash[offset + 2] & 0xff) << 8 |
            (hmac_hash[offset + 3] & 0xff)
        )
        
        # 生成指定位数的码
        code = code % (10 ** self.digits)
        return str(code).zfill(self.digits)
    
    def verify_totp(
        self, 
        secret: str, 
        code: str, 
        timestamp: Optional[int] = None,
        window: int = 1
    ) -> bool:
        """验证 TOTP 码"""
        if timestamp is None:
            timestamp = int(time.time())
        
        # 检查当前时间窗口和前后窗口
        for i in range(-window, window + 1):
            test_timestamp = timestamp + (i * self.period)
            expected_code = self.generate_totp(secret, test_timestamp)
            if hmac.compare_digest(expected_code, code):
                return True
        
        return False


class SMSProvider:
    """SMS 提供者（模拟实现）"""
    
    def __init__(self, api_key: str, sender_id: str):
        """初始化 SMS 提供者"""
        self.api_key = api_key
        self.sender_id = sender_id
    
    def send_sms(self, phone_number: str, message: str) -> bool:
        """发送短信"""
        # 这里应该集成真实的短信服务提供商 API
        # 例如：阿里云短信、腾讯云短信等
        
        print(f"[SMS] 发送到 {phone_number}: {message}")
        return True
    
    def generate_verification_code(self) -> str:
        """生成验证码"""
        return str(secrets.randbelow(1000000)).zfill(6)


class EmailProvider:
    """邮箱提供者（模拟实现）"""
    
    def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str):
        """初始化邮箱提供者"""
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
    
    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """发送邮件"""
        # 这里应该集成真实的邮件发送服务
        # 例如：SMTP、SendGrid、阿里云邮件推送等
        
        print(f"[EMAIL] 发送到 {to_email}: {subject}")
        print(f"内容: {body}")
        return True
    
    def generate_verification_code(self) -> str:
        """生成验证码"""
        return str(secrets.randbelow(1000000)).zfill(6)


class BackupCodeManager:
    """备用码管理器"""
    
    @staticmethod
    def generate_backup_codes(count: int = 10) -> List[str]:
        """生成备用恢复码"""
        codes = []
        for _ in range(count):
            # 生成 8 位备用码
            code = ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(8))
            codes.append(code)
        return codes
    
    @staticmethod
    def hash_backup_code(code: str) -> str:
        """哈希备用码"""
        return hashlib.sha256(code.encode()).hexdigest()
    
    @staticmethod
    def verify_backup_code(code: str, hashed_code: str) -> bool:
        """验证备用码"""
        return hmac.compare_digest(
            hashlib.sha256(code.encode()).hexdigest(),
            hashed_code
        )


class MFAManager:
    """MFA 管理器"""
    
    def __init__(
        self,
        totp_provider: TOTPProvider,
        sms_provider: Optional[SMSProvider] = None,
        email_provider: Optional[EmailProvider] = None
    ):
        """初始化 MFA 管理器"""
        self.totp_provider = totp_provider
        self.sms_provider = sms_provider
        self.email_provider = email_provider
        self.backup_code_manager = BackupCodeManager()
        
        # 存储（实际应用中应使用数据库）
        self.devices: Dict[str, MFADevice] = {}
        self.challenges: Dict[str, MFAChallenge] = {}
    
    def setup_totp(self, user_id: str, device_name: str) -> Tuple[str, bytes]:
        """设置 TOTP"""
        import uuid
        
        device_id = str(uuid.uuid4())
        secret = self.totp_provider.generate_secret()
        
        device = MFADevice(
            id=device_id,
            user_id=user_id,
            method=MFAMethod.TOTP,
            name=device_name,
            secret=secret
        )
        
        self.devices[device_id] = device
        
        # 生成 QR 码
        qr_code = self.totp_provider.generate_qr_code(secret, user_id)
        
        return device_id, qr_code
    
    def verify_totp_setup(self, device_id: str, code: str) -> bool:
        """验证 TOTP 设置"""
        device = self.devices.get(device_id)
        if not device or device.method != MFAMethod.TOTP:
            return False
        
        if self.totp_provider.verify_totp(device.secret, code):
            device.is_verified = True
            device.last_used = datetime.utcnow()
            return True
        
        return False
    
    def setup_sms(self, user_id: str, phone_number: str, device_name: str) -> str:
        """设置短信 MFA"""
        import uuid
        
        device_id = str(uuid.uuid4())
        device = MFADevice(
            id=device_id,
            user_id=user_id,
            method=MFAMethod.SMS,
            name=device_name,
            phone_number=phone_number
        )
        
        self.devices[device_id] = device
        
        # 发送验证短信
        self.send_sms_challenge(device_id)
        
        return device_id
    
    def setup_email(self, user_id: str, email: str, device_name: str) -> str:
        """设置邮箱 MFA"""
        import uuid
        
        device_id = str(uuid.uuid4())
        device = MFADevice(
            id=device_id,
            user_id=user_id,
            method=MFAMethod.EMAIL,
            name=device_name,
            email=email
        )
        
        self.devices[device_id] = device
        
        # 发送验证邮件
        self.send_email_challenge(device_id)
        
        return device_id
    
    def generate_backup_codes(self, user_id: str) -> Tuple[str, List[str]]:
        """生成备用码"""
        import uuid
        
        device_id = str(uuid.uuid4())
        codes = self.backup_code_manager.generate_backup_codes()
        
        # 哈希存储备用码
        hashed_codes = [
            self.backup_code_manager.hash_backup_code(code) 
            for code in codes
        ]
        
        device = MFADevice(
            id=device_id,
            user_id=user_id,
            method=MFAMethod.BACKUP_CODES,
            name="备用恢复码",
            backup_codes=hashed_codes,
            is_verified=True
        )
        
        self.devices[device_id] = device
        
        return device_id, codes
    
    def send_sms_challenge(self, device_id: str) -> Optional[str]:
        """发送短信挑战"""
        device = self.devices.get(device_id)
        if not device or device.method != MFAMethod.SMS or not self.sms_provider:
            return None
        
        import uuid
        
        challenge_id = str(uuid.uuid4())
        code = self.sms_provider.generate_verification_code()
        
        challenge = MFAChallenge(
            id=challenge_id,
            user_id=device.user_id,
            device_id=device_id,
            method=MFAMethod.SMS,
            code=code,
            expires_at=datetime.utcnow() + timedelta(minutes=5)
        )
        
        self.challenges[challenge_id] = challenge
        
        # 发送短信
        message = f"您的 DramaCraft 验证码是: {code}，5分钟内有效。"
        if self.sms_provider.send_sms(device.phone_number, message):
            return challenge_id
        
        return None
    
    def send_email_challenge(self, device_id: str) -> Optional[str]:
        """发送邮箱挑战"""
        device = self.devices.get(device_id)
        if not device or device.method != MFAMethod.EMAIL or not self.email_provider:
            return None
        
        import uuid
        
        challenge_id = str(uuid.uuid4())
        code = self.email_provider.generate_verification_code()
        
        challenge = MFAChallenge(
            id=challenge_id,
            user_id=device.user_id,
            device_id=device_id,
            method=MFAMethod.EMAIL,
            code=code,
            expires_at=datetime.utcnow() + timedelta(minutes=10)
        )
        
        self.challenges[challenge_id] = challenge
        
        # 发送邮件
        subject = "DramaCraft 验证码"
        body = f"""
        您好，
        
        您的 DramaCraft 验证码是: {code}
        
        此验证码将在 10 分钟后过期。
        
        如果这不是您的操作，请忽略此邮件。
        
        DramaCraft 团队
        """
        
        if self.email_provider.send_email(device.email, subject, body):
            return challenge_id
        
        return None
    
    def verify_challenge(self, challenge_id: str, code: str) -> bool:
        """验证挑战"""
        challenge = self.challenges.get(challenge_id)
        if not challenge:
            return False
        
        # 检查是否过期
        if datetime.utcnow() > challenge.expires_at:
            return False
        
        # 检查是否已使用
        if challenge.is_used:
            return False
        
        # 检查尝试次数
        if challenge.attempts >= challenge.max_attempts:
            return False
        
        challenge.attempts += 1
        
        # 验证码
        if hmac.compare_digest(challenge.code, code):
            challenge.is_used = True
            
            # 更新设备状态
            device = self.devices.get(challenge.device_id)
            if device:
                device.is_verified = True
                device.last_used = datetime.utcnow()
            
            return True
        
        return False
    
    def verify_totp(self, device_id: str, code: str) -> bool:
        """验证 TOTP"""
        device = self.devices.get(device_id)
        if not device or device.method != MFAMethod.TOTP or not device.is_verified:
            return False
        
        if self.totp_provider.verify_totp(device.secret, code):
            device.last_used = datetime.utcnow()
            return True
        
        return False
    
    def verify_backup_code(self, user_id: str, code: str) -> bool:
        """验证备用码"""
        # 查找用户的备用码设备
        backup_device = None
        for device in self.devices.values():
            if (device.user_id == user_id and 
                device.method == MFAMethod.BACKUP_CODES and 
                device.is_verified):
                backup_device = device
                break
        
        if not backup_device:
            return False
        
        # 验证备用码
        for i, hashed_code in enumerate(backup_device.backup_codes):
            if self.backup_code_manager.verify_backup_code(code, hashed_code):
                # 移除已使用的备用码
                backup_device.backup_codes.pop(i)
                backup_device.last_used = datetime.utcnow()
                return True
        
        return False
    
    def get_user_devices(self, user_id: str) -> List[MFADevice]:
        """获取用户的 MFA 设备"""
        return [
            device for device in self.devices.values()
            if device.user_id == user_id
        ]
    
    def remove_device(self, device_id: str) -> bool:
        """移除 MFA 设备"""
        if device_id in self.devices:
            del self.devices[device_id]
            return True
        return False
    
    def set_primary_device(self, user_id: str, device_id: str) -> bool:
        """设置主要设备"""
        device = self.devices.get(device_id)
        if not device or device.user_id != user_id:
            return False
        
        # 取消其他设备的主要状态
        for d in self.devices.values():
            if d.user_id == user_id:
                d.is_primary = False
        
        # 设置新的主要设备
        device.is_primary = True
        return True
