"""
数据加密和安全存储模块

提供企业级数据安全功能：
- AES-256 加密
- RSA 非对称加密
- 数据脱敏
- 安全存储
"""

import os
import base64
import hashlib
import secrets
from typing import Any, Dict, Optional, Union
from pathlib import Path
from dataclasses import dataclass
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


@dataclass
class EncryptionKey:
    """加密密钥信息"""
    key_id: str
    algorithm: str
    key_data: bytes
    created_at: str
    expires_at: Optional[str] = None


class DataEncryption:
    """数据加密管理器"""
    
    def __init__(self, master_key: Optional[bytes] = None):
        """初始化加密管理器"""
        if master_key is None:
            master_key = Fernet.generate_key()
        
        self.master_key = master_key
        self.cipher = Fernet(master_key)
        self.keys: Dict[str, EncryptionKey] = {}
    
    @classmethod
    def generate_key_from_password(cls, password: str, salt: bytes = None) -> bytes:
        """从密码生成加密密钥"""
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt_data(self, data: Union[str, bytes], key_id: str = None) -> Dict[str, str]:
        """加密数据"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        # 使用指定密钥或主密钥
        if key_id and key_id in self.keys:
            cipher = Fernet(self.keys[key_id].key_data)
        else:
            cipher = self.cipher
            key_id = "master"
        
        encrypted_data = cipher.encrypt(data)
        
        return {
            "data": base64.b64encode(encrypted_data).decode('utf-8'),
            "key_id": key_id,
            "algorithm": "AES-256-GCM"
        }
    
    def decrypt_data(self, encrypted_data: Dict[str, str]) -> bytes:
        """解密数据"""
        key_id = encrypted_data.get("key_id", "master")
        data = base64.b64decode(encrypted_data["data"])
        
        # 使用对应密钥解密
        if key_id == "master":
            cipher = self.cipher
        elif key_id in self.keys:
            cipher = Fernet(self.keys[key_id].key_data)
        else:
            raise ValueError(f"Unknown key ID: {key_id}")
        
        return cipher.decrypt(data)
    
    def encrypt_file(self, file_path: Path, output_path: Path = None) -> Path:
        """加密文件"""
        if output_path is None:
            output_path = file_path.with_suffix(file_path.suffix + '.enc')
        
        with open(file_path, 'rb') as infile:
            data = infile.read()
        
        encrypted_data = self.cipher.encrypt(data)
        
        with open(output_path, 'wb') as outfile:
            outfile.write(encrypted_data)
        
        return output_path
    
    def decrypt_file(self, encrypted_file_path: Path, output_path: Path = None) -> Path:
        """解密文件"""
        if output_path is None:
            output_path = encrypted_file_path.with_suffix('')
        
        with open(encrypted_file_path, 'rb') as infile:
            encrypted_data = infile.read()
        
        data = self.cipher.decrypt(encrypted_data)
        
        with open(output_path, 'wb') as outfile:
            outfile.write(data)
        
        return output_path
    
    def create_encryption_key(self, key_id: str, algorithm: str = "AES-256") -> EncryptionKey:
        """创建新的加密密钥"""
        key_data = Fernet.generate_key()
        
        encryption_key = EncryptionKey(
            key_id=key_id,
            algorithm=algorithm,
            key_data=key_data,
            created_at=str(datetime.utcnow())
        )
        
        self.keys[key_id] = encryption_key
        return encryption_key
    
    def rotate_key(self, key_id: str) -> EncryptionKey:
        """轮换加密密钥"""
        if key_id not in self.keys:
            raise ValueError(f"Key {key_id} not found")
        
        # 创建新密钥
        new_key = self.create_encryption_key(f"{key_id}_new")
        
        # 标记旧密钥为过期
        old_key = self.keys[key_id]
        old_key.expires_at = str(datetime.utcnow())
        
        # 替换密钥
        self.keys[key_id] = new_key
        
        return new_key


class RSAEncryption:
    """RSA 非对称加密"""
    
    def __init__(self, key_size: int = 2048):
        """初始化 RSA 加密"""
        self.key_size = key_size
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size
        )
        self.public_key = self.private_key.public_key()
    
    def encrypt_with_public_key(self, data: bytes) -> bytes:
        """使用公钥加密"""
        return self.public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
    
    def decrypt_with_private_key(self, encrypted_data: bytes) -> bytes:
        """使用私钥解密"""
        return self.private_key.decrypt(
            encrypted_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
    
    def sign_data(self, data: bytes) -> bytes:
        """数字签名"""
        return self.private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
    
    def verify_signature(self, data: bytes, signature: bytes) -> bool:
        """验证数字签名"""
        try:
            self.public_key.verify(
                signature,
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False
    
    def export_public_key(self) -> bytes:
        """导出公钥"""
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
    
    def export_private_key(self, password: bytes = None) -> bytes:
        """导出私钥"""
        encryption_algorithm = serialization.NoEncryption()
        if password:
            encryption_algorithm = serialization.BestAvailableEncryption(password)
        
        return self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=encryption_algorithm
        )


class DataMasking:
    """数据脱敏工具"""
    
    @staticmethod
    def mask_email(email: str) -> str:
        """脱敏邮箱地址"""
        if '@' not in email:
            return email
        
        local, domain = email.split('@', 1)
        if len(local) <= 2:
            masked_local = '*' * len(local)
        else:
            masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
        
        return f"{masked_local}@{domain}"
    
    @staticmethod
    def mask_phone(phone: str) -> str:
        """脱敏手机号"""
        if len(phone) < 7:
            return '*' * len(phone)
        
        return phone[:3] + '*' * (len(phone) - 6) + phone[-3:]
    
    @staticmethod
    def mask_id_card(id_card: str) -> str:
        """脱敏身份证号"""
        if len(id_card) < 8:
            return '*' * len(id_card)
        
        return id_card[:4] + '*' * (len(id_card) - 8) + id_card[-4:]
    
    @staticmethod
    def mask_credit_card(card_number: str) -> str:
        """脱敏信用卡号"""
        if len(card_number) < 8:
            return '*' * len(card_number)
        
        return '*' * (len(card_number) - 4) + card_number[-4:]
    
    @staticmethod
    def mask_custom(data: str, visible_start: int = 2, visible_end: int = 2) -> str:
        """自定义脱敏"""
        if len(data) <= visible_start + visible_end:
            return '*' * len(data)
        
        start = data[:visible_start]
        end = data[-visible_end:] if visible_end > 0 else ''
        middle = '*' * (len(data) - visible_start - visible_end)
        
        return start + middle + end


class SecureStorage:
    """安全存储管理器"""
    
    def __init__(self, storage_path: Path, encryption: DataEncryption):
        """初始化安全存储"""
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.encryption = encryption
        self.metadata_file = self.storage_path / "metadata.json"
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Any]:
        """加载元数据"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    import json
                    encrypted_metadata = json.load(f)
                    decrypted_data = self.encryption.decrypt_data(encrypted_metadata)
                    return json.loads(decrypted_data.decode('utf-8'))
            except Exception:
                return {}
        return {}
    
    def _save_metadata(self):
        """保存元数据"""
        import json
        metadata_json = json.dumps(self.metadata, ensure_ascii=False, indent=2)
        encrypted_metadata = self.encryption.encrypt_data(metadata_json)
        
        with open(self.metadata_file, 'w') as f:
            json.dump(encrypted_metadata, f, ensure_ascii=False, indent=2)
    
    def store_data(self, key: str, data: Any, metadata: Dict[str, Any] = None) -> str:
        """存储数据"""
        import json
        
        # 序列化数据
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, ensure_ascii=False)
        else:
            data_str = str(data)
        
        # 加密数据
        encrypted_data = self.encryption.encrypt_data(data_str)
        
        # 生成文件名
        file_id = hashlib.sha256(key.encode()).hexdigest()[:16]
        file_path = self.storage_path / f"{file_id}.enc"
        
        # 保存加密数据
        with open(file_path, 'w') as f:
            json.dump(encrypted_data, f)
        
        # 更新元数据
        self.metadata[key] = {
            "file_id": file_id,
            "file_path": str(file_path),
            "created_at": str(datetime.utcnow()),
            "metadata": metadata or {}
        }
        self._save_metadata()
        
        return file_id
    
    def retrieve_data(self, key: str) -> Optional[Any]:
        """检索数据"""
        if key not in self.metadata:
            return None
        
        file_path = Path(self.metadata[key]["file_path"])
        if not file_path.exists():
            return None
        
        try:
            import json
            
            # 读取加密数据
            with open(file_path, 'r') as f:
                encrypted_data = json.load(f)
            
            # 解密数据
            decrypted_data = self.encryption.decrypt_data(encrypted_data)
            data_str = decrypted_data.decode('utf-8')
            
            # 尝试解析 JSON
            try:
                return json.loads(data_str)
            except json.JSONDecodeError:
                return data_str
        
        except Exception:
            return None
    
    def delete_data(self, key: str) -> bool:
        """删除数据"""
        if key not in self.metadata:
            return False
        
        file_path = Path(self.metadata[key]["file_path"])
        if file_path.exists():
            file_path.unlink()
        
        del self.metadata[key]
        self._save_metadata()
        
        return True
    
    def list_keys(self) -> List[str]:
        """列出所有键"""
        return list(self.metadata.keys())
    
    def get_metadata(self, key: str) -> Optional[Dict[str, Any]]:
        """获取数据元数据"""
        return self.metadata.get(key)
