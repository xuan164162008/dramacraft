"""
安全审计和日志记录模块

提供企业级安全审计功能：
- 操作日志记录
- 安全事件监控
- 审计报告生成
- 异常行为检测
"""

import json
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging


class AuditEventType(Enum):
    """审计事件类型"""
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    PERMISSION_DENIED = "permission_denied"
    DATA_ACCESS = "data_access"
    DATA_MODIFY = "data_modify"
    DATA_DELETE = "data_delete"
    CONFIG_CHANGE = "config_change"
    SECURITY_VIOLATION = "security_violation"
    SYSTEM_ERROR = "system_error"
    API_CALL = "api_call"
    FILE_UPLOAD = "file_upload"
    FILE_DOWNLOAD = "file_download"


class RiskLevel(Enum):
    """风险级别"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """审计事件模型"""
    id: str
    event_type: AuditEventType
    user_id: Optional[str]
    session_id: Optional[str]
    timestamp: datetime
    source_ip: str
    user_agent: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[str]
    action: str
    result: str  # success, failure, error
    risk_level: RiskLevel
    details: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityAlert:
    """安全告警模型"""
    id: str
    alert_type: str
    severity: RiskLevel
    title: str
    description: str
    user_id: Optional[str]
    source_ip: str
    timestamp: datetime
    events: List[str]  # 相关事件ID列表
    status: str = "open"  # open, investigating, resolved, false_positive
    assigned_to: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None


class AuditLogger:
    """审计日志记录器"""
    
    def __init__(self, log_file: Path, encryption_key: Optional[bytes] = None):
        """初始化审计日志记录器"""
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 设置日志记录器
        self.logger = logging.getLogger("dramacraft.audit")
        self.logger.setLevel(logging.INFO)
        
        # 文件处理器
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.INFO)
        
        # 日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
        
        # 加密支持
        self.encryption_key = encryption_key
        if encryption_key:
            from .encryption import DataEncryption
            self.encryption = DataEncryption(encryption_key)
        else:
            self.encryption = None
    
    def log_event(self, event: AuditEvent):
        """记录审计事件"""
        # 序列化事件
        event_data = {
            "id": event.id,
            "event_type": event.event_type.value,
            "user_id": event.user_id,
            "session_id": event.session_id,
            "timestamp": event.timestamp.isoformat(),
            "source_ip": event.source_ip,
            "user_agent": event.user_agent,
            "resource_type": event.resource_type,
            "resource_id": event.resource_id,
            "action": event.action,
            "result": event.result,
            "risk_level": event.risk_level.value,
            "details": event.details,
            "metadata": event.metadata
        }
        
        # 加密敏感数据
        if self.encryption:
            sensitive_fields = ["user_id", "session_id", "details", "metadata"]
            for field in sensitive_fields:
                if event_data[field]:
                    encrypted_data = self.encryption.encrypt_data(
                        json.dumps(event_data[field])
                    )
                    event_data[f"{field}_encrypted"] = encrypted_data
                    event_data[field] = "[ENCRYPTED]"
        
        # 记录到日志文件
        log_message = json.dumps(event_data, ensure_ascii=False)
        self.logger.info(log_message)
        
        # 高风险事件立即刷新
        if event.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            for handler in self.logger.handlers:
                handler.flush()
    
    def search_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_types: Optional[List[AuditEventType]] = None,
        user_id: Optional[str] = None,
        risk_level: Optional[RiskLevel] = None,
        limit: int = 1000
    ) -> List[AuditEvent]:
        """搜索审计事件"""
        events = []
        
        if not self.log_file.exists():
            return events
        
        with open(self.log_file, 'r') as f:
            for line in f:
                try:
                    event_data = json.loads(line.strip())
                    
                    # 解析时间戳
                    timestamp = datetime.fromisoformat(
                        event_data["timestamp"].replace("Z", "+00:00")
                    )
                    
                    # 时间过滤
                    if start_time and timestamp < start_time:
                        continue
                    if end_time and timestamp > end_time:
                        continue
                    
                    # 事件类型过滤
                    if event_types:
                        event_type = AuditEventType(event_data["event_type"])
                        if event_type not in event_types:
                            continue
                    
                    # 用户过滤
                    if user_id and event_data.get("user_id") != user_id:
                        continue
                    
                    # 风险级别过滤
                    if risk_level:
                        event_risk = RiskLevel(event_data["risk_level"])
                        if event_risk != risk_level:
                            continue
                    
                    # 构建事件对象
                    event = AuditEvent(
                        id=event_data["id"],
                        event_type=AuditEventType(event_data["event_type"]),
                        user_id=event_data.get("user_id"),
                        session_id=event_data.get("session_id"),
                        timestamp=timestamp,
                        source_ip=event_data["source_ip"],
                        user_agent=event_data.get("user_agent"),
                        resource_type=event_data.get("resource_type"),
                        resource_id=event_data.get("resource_id"),
                        action=event_data["action"],
                        result=event_data["result"],
                        risk_level=RiskLevel(event_data["risk_level"]),
                        details=event_data.get("details", {}),
                        metadata=event_data.get("metadata", {})
                    )
                    
                    events.append(event)
                    
                    if len(events) >= limit:
                        break
                
                except (json.JSONDecodeError, KeyError, ValueError):
                    continue
        
        return events


class SecurityAudit:
    """安全审计管理器"""
    
    def __init__(self, audit_logger: AuditLogger):
        """初始化安全审计管理器"""
        self.audit_logger = audit_logger
        self.alerts: Dict[str, SecurityAlert] = {}
        self.alert_rules = self._initialize_alert_rules()
    
    def _initialize_alert_rules(self) -> Dict[str, Dict[str, Any]]:
        """初始化告警规则"""
        return {
            "multiple_failed_logins": {
                "description": "多次登录失败",
                "threshold": 5,
                "time_window": timedelta(minutes=15),
                "severity": RiskLevel.HIGH
            },
            "privilege_escalation": {
                "description": "权限提升尝试",
                "threshold": 3,
                "time_window": timedelta(minutes=5),
                "severity": RiskLevel.CRITICAL
            },
            "unusual_access_pattern": {
                "description": "异常访问模式",
                "threshold": 10,
                "time_window": timedelta(hours=1),
                "severity": RiskLevel.MEDIUM
            },
            "data_exfiltration": {
                "description": "数据泄露风险",
                "threshold": 100,
                "time_window": timedelta(hours=1),
                "severity": RiskLevel.HIGH
            }
        }
    
    def record_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[str],
        session_id: Optional[str],
        source_ip: str,
        action: str,
        result: str,
        user_agent: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        risk_level: RiskLevel = RiskLevel.LOW,
        details: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """记录审计事件"""
        import uuid
        
        event_id = str(uuid.uuid4())
        event = AuditEvent(
            id=event_id,
            event_type=event_type,
            user_id=user_id,
            session_id=session_id,
            timestamp=datetime.utcnow(),
            source_ip=source_ip,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            result=result,
            risk_level=risk_level,
            details=details or {},
            metadata=metadata or {}
        )
        
        # 记录事件
        self.audit_logger.log_event(event)
        
        # 检查告警规则
        self._check_alert_rules(event)
        
        return event_id
    
    def _check_alert_rules(self, event: AuditEvent):
        """检查告警规则"""
        current_time = datetime.utcnow()
        
        # 检查多次登录失败
        if event.event_type == AuditEventType.LOGIN_FAILED:
            self._check_multiple_failed_logins(event, current_time)
        
        # 检查权限拒绝
        if event.event_type == AuditEventType.PERMISSION_DENIED:
            self._check_privilege_escalation(event, current_time)
        
        # 检查数据访问模式
        if event.event_type in [AuditEventType.DATA_ACCESS, AuditEventType.FILE_DOWNLOAD]:
            self._check_data_access_pattern(event, current_time)
    
    def _check_multiple_failed_logins(self, event: AuditEvent, current_time: datetime):
        """检查多次登录失败"""
        rule = self.alert_rules["multiple_failed_logins"]
        time_window = current_time - rule["time_window"]
        
        # 搜索相关事件
        failed_logins = self.audit_logger.search_events(
            start_time=time_window,
            end_time=current_time,
            event_types=[AuditEventType.LOGIN_FAILED],
            user_id=event.user_id
        )
        
        if len(failed_logins) >= rule["threshold"]:
            self._create_alert(
                "multiple_failed_logins",
                rule["severity"],
                f"用户 {event.user_id} 在 {rule['time_window']} 内登录失败 {len(failed_logins)} 次",
                rule["description"],
                event.user_id,
                event.source_ip,
                [e.id for e in failed_logins]
            )
    
    def _check_privilege_escalation(self, event: AuditEvent, current_time: datetime):
        """检查权限提升尝试"""
        rule = self.alert_rules["privilege_escalation"]
        time_window = current_time - rule["time_window"]
        
        # 搜索权限拒绝事件
        permission_denials = self.audit_logger.search_events(
            start_time=time_window,
            end_time=current_time,
            event_types=[AuditEventType.PERMISSION_DENIED],
            user_id=event.user_id
        )
        
        if len(permission_denials) >= rule["threshold"]:
            self._create_alert(
                "privilege_escalation",
                rule["severity"],
                f"用户 {event.user_id} 疑似尝试权限提升",
                rule["description"],
                event.user_id,
                event.source_ip,
                [e.id for e in permission_denials]
            )
    
    def _check_data_access_pattern(self, event: AuditEvent, current_time: datetime):
        """检查数据访问模式"""
        rule = self.alert_rules["data_exfiltration"]
        time_window = current_time - rule["time_window"]
        
        # 搜索数据访问事件
        data_access_events = self.audit_logger.search_events(
            start_time=time_window,
            end_time=current_time,
            event_types=[AuditEventType.DATA_ACCESS, AuditEventType.FILE_DOWNLOAD],
            user_id=event.user_id
        )
        
        if len(data_access_events) >= rule["threshold"]:
            self._create_alert(
                "data_exfiltration",
                rule["severity"],
                f"用户 {event.user_id} 在短时间内大量访问数据",
                rule["description"],
                event.user_id,
                event.source_ip,
                [e.id for e in data_access_events]
            )
    
    def _create_alert(
        self,
        alert_type: str,
        severity: RiskLevel,
        title: str,
        description: str,
        user_id: Optional[str],
        source_ip: str,
        event_ids: List[str]
    ):
        """创建安全告警"""
        import uuid
        
        alert_id = str(uuid.uuid4())
        alert = SecurityAlert(
            id=alert_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            description=description,
            user_id=user_id,
            source_ip=source_ip,
            timestamp=datetime.utcnow(),
            events=event_ids
        )
        
        self.alerts[alert_id] = alert
        
        # 记录告警事件
        self.record_event(
            AuditEventType.SECURITY_VIOLATION,
            user_id,
            None,
            source_ip,
            f"security_alert_{alert_type}",
            "alert_created",
            risk_level=severity,
            details={
                "alert_id": alert_id,
                "alert_type": alert_type,
                "title": title
            }
        )
    
    def get_alerts(
        self,
        status: Optional[str] = None,
        severity: Optional[RiskLevel] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[SecurityAlert]:
        """获取安全告警"""
        alerts = list(self.alerts.values())
        
        if status:
            alerts = [a for a in alerts if a.status == status]
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        if start_time:
            alerts = [a for a in alerts if a.timestamp >= start_time]
        
        if end_time:
            alerts = [a for a in alerts if a.timestamp <= end_time]
        
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)
    
    def resolve_alert(
        self,
        alert_id: str,
        resolved_by: str,
        resolution_notes: str
    ) -> bool:
        """解决告警"""
        if alert_id not in self.alerts:
            return False
        
        alert = self.alerts[alert_id]
        alert.status = "resolved"
        alert.assigned_to = resolved_by
        alert.resolved_at = datetime.utcnow()
        alert.resolution_notes = resolution_notes
        
        return True
    
    def generate_audit_report(
        self,
        start_time: datetime,
        end_time: datetime,
        include_details: bool = False
    ) -> Dict[str, Any]:
        """生成审计报告"""
        events = self.audit_logger.search_events(
            start_time=start_time,
            end_time=end_time
        )
        
        # 统计分析
        event_counts = {}
        risk_counts = {}
        user_activity = {}
        
        for event in events:
            # 事件类型统计
            event_type = event.event_type.value
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
            
            # 风险级别统计
            risk_level = event.risk_level.value
            risk_counts[risk_level] = risk_counts.get(risk_level, 0) + 1
            
            # 用户活动统计
            if event.user_id:
                if event.user_id not in user_activity:
                    user_activity[event.user_id] = {
                        "total_events": 0,
                        "login_count": 0,
                        "failed_logins": 0,
                        "data_access": 0
                    }
                
                user_activity[event.user_id]["total_events"] += 1
                
                if event.event_type == AuditEventType.LOGIN:
                    user_activity[event.user_id]["login_count"] += 1
                elif event.event_type == AuditEventType.LOGIN_FAILED:
                    user_activity[event.user_id]["failed_logins"] += 1
                elif event.event_type == AuditEventType.DATA_ACCESS:
                    user_activity[event.user_id]["data_access"] += 1
        
        # 获取告警
        alerts = self.get_alerts(start_time=start_time, end_time=end_time)
        
        report = {
            "report_period": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            },
            "summary": {
                "total_events": len(events),
                "total_alerts": len(alerts),
                "unique_users": len(user_activity),
                "event_types": event_counts,
                "risk_levels": risk_counts
            },
            "alerts": [
                {
                    "id": alert.id,
                    "type": alert.alert_type,
                    "severity": alert.severity.value,
                    "title": alert.title,
                    "timestamp": alert.timestamp.isoformat(),
                    "status": alert.status
                }
                for alert in alerts
            ],
            "user_activity": user_activity
        }
        
        if include_details:
            report["events"] = [
                {
                    "id": event.id,
                    "type": event.event_type.value,
                    "timestamp": event.timestamp.isoformat(),
                    "user_id": event.user_id,
                    "action": event.action,
                    "result": event.result,
                    "risk_level": event.risk_level.value
                }
                for event in events
            ]
        
        return report
