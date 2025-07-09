"""
服务注册与发现模块

实现微服务架构的核心功能：
- 服务注册
- 服务发现
- 健康检查
- 服务元数据管理
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
import json


class ServiceStatus(Enum):
    """服务状态枚举"""
    STARTING = "starting"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    STOPPING = "stopping"
    STOPPED = "stopped"


@dataclass
class ServiceInstance:
    """服务实例模型"""
    id: str
    name: str
    version: str
    host: str
    port: int
    protocol: str = "http"
    status: ServiceStatus = ServiceStatus.STARTING
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)
    health_check_url: Optional[str] = None
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    registered_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def endpoint(self) -> str:
        """获取服务端点"""
        return f"{self.protocol}://{self.host}:{self.port}"
    
    @property
    def is_healthy(self) -> bool:
        """检查服务是否健康"""
        if self.status != ServiceStatus.HEALTHY:
            return False
        
        # 检查心跳超时（默认30秒）
        timeout = timedelta(seconds=30)
        return datetime.utcnow() - self.last_heartbeat < timeout


@dataclass
class ServiceDefinition:
    """服务定义"""
    name: str
    version: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    resource_requirements: Dict[str, Any] = field(default_factory=dict)


class ServiceRegistry:
    """服务注册中心"""
    
    def __init__(self):
        """初始化服务注册中心"""
        self.services: Dict[str, ServiceInstance] = {}
        self.service_definitions: Dict[str, ServiceDefinition] = {}
        self.watchers: Dict[str, List[callable]] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """启动清理任务"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_unhealthy_services())
    
    async def _cleanup_unhealthy_services(self):
        """清理不健康的服务"""
        while True:
            try:
                await asyncio.sleep(10)  # 每10秒检查一次
                
                current_time = datetime.utcnow()
                unhealthy_services = []
                
                for service_id, service in self.services.items():
                    # 检查心跳超时
                    if current_time - service.last_heartbeat > timedelta(seconds=60):
                        unhealthy_services.append(service_id)
                        service.status = ServiceStatus.UNHEALTHY
                
                # 移除超时的服务
                for service_id in unhealthy_services:
                    if service_id in self.services:
                        service = self.services[service_id]
                        if current_time - service.last_heartbeat > timedelta(minutes=5):
                            await self.deregister_service(service_id)
                
            except Exception as e:
                print(f"清理任务错误: {e}")
    
    async def register_service(self, service: ServiceInstance) -> bool:
        """注册服务"""
        try:
            # 检查服务是否已存在
            if service.id in self.services:
                return False
            
            # 设置健康检查URL
            if not service.health_check_url:
                service.health_check_url = f"{service.endpoint}/health"
            
            # 注册服务
            self.services[service.id] = service
            
            # 通知观察者
            await self._notify_watchers(service.name, "register", service)
            
            print(f"服务注册成功: {service.name}@{service.endpoint}")
            return True
            
        except Exception as e:
            print(f"服务注册失败: {e}")
            return False
    
    async def deregister_service(self, service_id: str) -> bool:
        """注销服务"""
        try:
            if service_id not in self.services:
                return False
            
            service = self.services[service_id]
            service.status = ServiceStatus.STOPPED
            
            # 通知观察者
            await self._notify_watchers(service.name, "deregister", service)
            
            # 移除服务
            del self.services[service_id]
            
            print(f"服务注销成功: {service.name}@{service.endpoint}")
            return True
            
        except Exception as e:
            print(f"服务注销失败: {e}")
            return False
    
    async def update_service_status(self, service_id: str, status: ServiceStatus) -> bool:
        """更新服务状态"""
        if service_id not in self.services:
            return False
        
        service = self.services[service_id]
        old_status = service.status
        service.status = status
        service.last_heartbeat = datetime.utcnow()
        
        # 如果状态发生变化，通知观察者
        if old_status != status:
            await self._notify_watchers(service.name, "status_change", service)
        
        return True
    
    async def heartbeat(self, service_id: str) -> bool:
        """服务心跳"""
        if service_id not in self.services:
            return False
        
        service = self.services[service_id]
        service.last_heartbeat = datetime.utcnow()
        
        # 如果服务之前不健康，现在恢复健康
        if service.status == ServiceStatus.UNHEALTHY:
            await self.update_service_status(service_id, ServiceStatus.HEALTHY)
        
        return True
    
    def get_service(self, service_id: str) -> Optional[ServiceInstance]:
        """获取服务实例"""
        return self.services.get(service_id)
    
    def get_services_by_name(self, service_name: str) -> List[ServiceInstance]:
        """根据服务名获取服务实例列表"""
        return [
            service for service in self.services.values()
            if service.name == service_name and service.is_healthy
        ]
    
    def get_services_by_tag(self, tag: str) -> List[ServiceInstance]:
        """根据标签获取服务实例列表"""
        return [
            service for service in self.services.values()
            if tag in service.tags and service.is_healthy
        ]
    
    def list_services(self) -> List[ServiceInstance]:
        """列出所有服务"""
        return list(self.services.values())
    
    def list_healthy_services(self) -> List[ServiceInstance]:
        """列出所有健康的服务"""
        return [
            service for service in self.services.values()
            if service.is_healthy
        ]
    
    async def watch_service(self, service_name: str, callback: callable):
        """监听服务变化"""
        if service_name not in self.watchers:
            self.watchers[service_name] = []
        
        self.watchers[service_name].append(callback)
    
    async def unwatch_service(self, service_name: str, callback: callable):
        """取消监听服务变化"""
        if service_name in self.watchers:
            try:
                self.watchers[service_name].remove(callback)
            except ValueError:
                pass
    
    async def _notify_watchers(self, service_name: str, event_type: str, service: ServiceInstance):
        """通知观察者"""
        if service_name in self.watchers:
            for callback in self.watchers[service_name]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event_type, service)
                    else:
                        callback(event_type, service)
                except Exception as e:
                    print(f"通知观察者失败: {e}")
    
    def register_service_definition(self, definition: ServiceDefinition):
        """注册服务定义"""
        key = f"{definition.name}:{definition.version}"
        self.service_definitions[key] = definition
    
    def get_service_definition(self, name: str, version: str) -> Optional[ServiceDefinition]:
        """获取服务定义"""
        key = f"{name}:{version}"
        return self.service_definitions.get(key)


class ServiceDiscovery:
    """服务发现客户端"""
    
    def __init__(self, registry: ServiceRegistry):
        """初始化服务发现客户端"""
        self.registry = registry
        self.cache: Dict[str, List[ServiceInstance]] = {}
        self.cache_ttl = timedelta(seconds=30)
        self.cache_timestamps: Dict[str, datetime] = {}
    
    async def discover_service(self, service_name: str, use_cache: bool = True) -> List[ServiceInstance]:
        """发现服务"""
        # 检查缓存
        if use_cache and self._is_cache_valid(service_name):
            return self.cache[service_name]
        
        # 从注册中心获取服务
        services = self.registry.get_services_by_name(service_name)
        
        # 更新缓存
        self.cache[service_name] = services
        self.cache_timestamps[service_name] = datetime.utcnow()
        
        return services
    
    async def discover_service_by_tag(self, tag: str, use_cache: bool = True) -> List[ServiceInstance]:
        """根据标签发现服务"""
        cache_key = f"tag:{tag}"
        
        # 检查缓存
        if use_cache and self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        # 从注册中心获取服务
        services = self.registry.get_services_by_tag(tag)
        
        # 更新缓存
        self.cache[cache_key] = services
        self.cache_timestamps[cache_key] = datetime.utcnow()
        
        return services
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """检查缓存是否有效"""
        if cache_key not in self.cache or cache_key not in self.cache_timestamps:
            return False
        
        return datetime.utcnow() - self.cache_timestamps[cache_key] < self.cache_ttl
    
    def invalidate_cache(self, service_name: str = None):
        """使缓存失效"""
        if service_name:
            self.cache.pop(service_name, None)
            self.cache_timestamps.pop(service_name, None)
        else:
            self.cache.clear()
            self.cache_timestamps.clear()
    
    async def get_service_endpoint(self, service_name: str) -> Optional[str]:
        """获取服务端点（负载均衡）"""
        services = await self.discover_service(service_name)
        
        if not services:
            return None
        
        # 简单的轮询负载均衡
        import random
        service = random.choice(services)
        return service.endpoint
    
    async def call_service(
        self, 
        service_name: str, 
        path: str, 
        method: str = "GET",
        data: Any = None,
        headers: Dict[str, str] = None,
        timeout: int = 30
    ) -> Optional[Dict[str, Any]]:
        """调用服务"""
        endpoint = await self.get_service_endpoint(service_name)
        if not endpoint:
            raise Exception(f"Service {service_name} not found")
        
        url = f"{endpoint}{path}"
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            try:
                if method.upper() == "GET":
                    async with session.get(url, headers=headers) as response:
                        return await response.json()
                elif method.upper() == "POST":
                    async with session.post(url, json=data, headers=headers) as response:
                        return await response.json()
                elif method.upper() == "PUT":
                    async with session.put(url, json=data, headers=headers) as response:
                        return await response.json()
                elif method.upper() == "DELETE":
                    async with session.delete(url, headers=headers) as response:
                        return await response.json()
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                    
            except Exception as e:
                print(f"调用服务失败 {service_name}: {e}")
                return None


class HealthChecker:
    """健康检查器"""
    
    def __init__(self, registry: ServiceRegistry):
        """初始化健康检查器"""
        self.registry = registry
        self.check_interval = 30  # 30秒检查一次
        self.timeout = 5  # 5秒超时
        self._check_task: Optional[asyncio.Task] = None
        self._start_health_check()
    
    def _start_health_check(self):
        """启动健康检查任务"""
        if self._check_task is None or self._check_task.done():
            self._check_task = asyncio.create_task(self._health_check_loop())
    
    async def _health_check_loop(self):
        """健康检查循环"""
        while True:
            try:
                await asyncio.sleep(self.check_interval)
                
                services = self.registry.list_services()
                tasks = []
                
                for service in services:
                    if service.health_check_url:
                        task = asyncio.create_task(
                            self._check_service_health(service)
                        )
                        tasks.append(task)
                
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                    
            except Exception as e:
                print(f"健康检查循环错误: {e}")
    
    async def _check_service_health(self, service: ServiceInstance):
        """检查单个服务健康状态"""
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as session:
                async with session.get(service.health_check_url) as response:
                    if response.status == 200:
                        # 服务健康
                        if service.status != ServiceStatus.HEALTHY:
                            await self.registry.update_service_status(
                                service.id, ServiceStatus.HEALTHY
                            )
                    else:
                        # 服务不健康
                        await self.registry.update_service_status(
                            service.id, ServiceStatus.UNHEALTHY
                        )
                        
        except Exception as e:
            # 健康检查失败，标记为不健康
            await self.registry.update_service_status(
                service.id, ServiceStatus.UNHEALTHY
            )
            print(f"健康检查失败 {service.name}: {e}")
    
    def stop(self):
        """停止健康检查"""
        if self._check_task and not self._check_task.done():
            self._check_task.cancel()
