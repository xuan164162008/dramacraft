"""
API网关和路由管理模块

实现微服务架构的API网关功能：
- 请求路由
- 负载均衡
- 认证授权
- 限流熔断
- 请求/响应转换
"""

import asyncio
import time
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, Pattern
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
from aiohttp import web
import json


class RouteMethod(Enum):
    """路由方法枚举"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class LoadBalanceStrategy(Enum):
    """负载均衡策略"""
    ROUND_ROBIN = "round_robin"
    RANDOM = "random"
    WEIGHTED = "weighted"
    LEAST_CONNECTIONS = "least_connections"
    IP_HASH = "ip_hash"


@dataclass
class RouteRule:
    """路由规则"""
    id: str
    path_pattern: str
    method: RouteMethod
    service_name: str
    target_path: Optional[str] = None
    load_balance_strategy: LoadBalanceStrategy = LoadBalanceStrategy.ROUND_ROBIN
    timeout: int = 30
    retry_count: int = 3
    auth_required: bool = True
    rate_limit: Optional[Dict[str, Any]] = None
    circuit_breaker: Optional[Dict[str, Any]] = None
    middleware: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后处理"""
        self.path_regex: Pattern = re.compile(self.path_pattern)


@dataclass
class RateLimitRule:
    """限流规则"""
    requests_per_minute: int
    requests_per_hour: int
    burst_size: int = 10
    key_func: Optional[Callable] = None


@dataclass
class CircuitBreakerRule:
    """熔断器规则"""
    failure_threshold: int = 5
    recovery_timeout: int = 60
    half_open_max_calls: int = 3


class RateLimiter:
    """限流器"""
    
    def __init__(self):
        """初始化限流器"""
        self.counters: Dict[str, Dict[str, Any]] = {}
    
    def is_allowed(self, key: str, rule: RateLimitRule) -> bool:
        """检查是否允许请求"""
        current_time = time.time()
        current_minute = int(current_time // 60)
        current_hour = int(current_time // 3600)
        
        if key not in self.counters:
            self.counters[key] = {
                "minute": current_minute,
                "hour": current_hour,
                "minute_count": 0,
                "hour_count": 0,
                "burst_tokens": rule.burst_size,
                "last_refill": current_time
            }
        
        counter = self.counters[key]
        
        # 重置计数器
        if counter["minute"] != current_minute:
            counter["minute"] = current_minute
            counter["minute_count"] = 0
        
        if counter["hour"] != current_hour:
            counter["hour"] = current_hour
            counter["hour_count"] = 0
        
        # 令牌桶算法处理突发请求
        time_passed = current_time - counter["last_refill"]
        tokens_to_add = time_passed * (rule.requests_per_minute / 60.0)
        counter["burst_tokens"] = min(
            rule.burst_size,
            counter["burst_tokens"] + tokens_to_add
        )
        counter["last_refill"] = current_time
        
        # 检查限流
        if (counter["minute_count"] >= rule.requests_per_minute or
            counter["hour_count"] >= rule.requests_per_hour or
            counter["burst_tokens"] < 1):
            return False
        
        # 消费令牌和计数
        counter["burst_tokens"] -= 1
        counter["minute_count"] += 1
        counter["hour_count"] += 1
        
        return True


class CircuitBreaker:
    """熔断器"""
    
    def __init__(self, rule: CircuitBreakerRule):
        """初始化熔断器"""
        self.rule = rule
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.half_open_calls = 0
    
    def can_execute(self) -> bool:
        """检查是否可以执行请求"""
        current_time = time.time()
        
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            if current_time - self.last_failure_time > self.rule.recovery_timeout:
                self.state = "HALF_OPEN"
                self.half_open_calls = 0
                return True
            return False
        elif self.state == "HALF_OPEN":
            return self.half_open_calls < self.rule.half_open_max_calls
        
        return False
    
    def record_success(self):
        """记录成功"""
        if self.state == "HALF_OPEN":
            self.half_open_calls += 1
            if self.half_open_calls >= self.rule.half_open_max_calls:
                self.state = "CLOSED"
                self.failure_count = 0
        elif self.state == "CLOSED":
            self.failure_count = max(0, self.failure_count - 1)
    
    def record_failure(self):
        """记录失败"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == "CLOSED" and self.failure_count >= self.rule.failure_threshold:
            self.state = "OPEN"
        elif self.state == "HALF_OPEN":
            self.state = "OPEN"


class LoadBalancer:
    """负载均衡器"""
    
    def __init__(self):
        """初始化负载均衡器"""
        self.round_robin_counters: Dict[str, int] = {}
        self.connection_counts: Dict[str, int] = {}
    
    def select_service(
        self, 
        services: List[Any], 
        strategy: LoadBalanceStrategy,
        client_ip: str = None
    ) -> Optional[Any]:
        """选择服务实例"""
        if not services:
            return None
        
        if strategy == LoadBalanceStrategy.ROUND_ROBIN:
            return self._round_robin(services)
        elif strategy == LoadBalanceStrategy.RANDOM:
            return self._random(services)
        elif strategy == LoadBalanceStrategy.WEIGHTED:
            return self._weighted(services)
        elif strategy == LoadBalanceStrategy.LEAST_CONNECTIONS:
            return self._least_connections(services)
        elif strategy == LoadBalanceStrategy.IP_HASH:
            return self._ip_hash(services, client_ip)
        else:
            return services[0]
    
    def _round_robin(self, services: List[Any]) -> Any:
        """轮询算法"""
        service_key = f"rr_{id(services)}"
        if service_key not in self.round_robin_counters:
            self.round_robin_counters[service_key] = 0
        
        index = self.round_robin_counters[service_key] % len(services)
        self.round_robin_counters[service_key] += 1
        
        return services[index]
    
    def _random(self, services: List[Any]) -> Any:
        """随机算法"""
        import random
        return random.choice(services)
    
    def _weighted(self, services: List[Any]) -> Any:
        """加权算法"""
        # 简化实现，假设所有服务权重相等
        return self._round_robin(services)
    
    def _least_connections(self, services: List[Any]) -> Any:
        """最少连接算法"""
        min_connections = float('inf')
        selected_service = services[0]
        
        for service in services:
            service_key = f"{service.host}:{service.port}"
            connections = self.connection_counts.get(service_key, 0)
            
            if connections < min_connections:
                min_connections = connections
                selected_service = service
        
        return selected_service
    
    def _ip_hash(self, services: List[Any], client_ip: str) -> Any:
        """IP哈希算法"""
        if not client_ip:
            return self._round_robin(services)
        
        import hashlib
        hash_value = int(hashlib.md5(client_ip.encode()).hexdigest(), 16)
        index = hash_value % len(services)
        
        return services[index]
    
    def increment_connections(self, service: Any):
        """增加连接计数"""
        service_key = f"{service.host}:{service.port}"
        self.connection_counts[service_key] = self.connection_counts.get(service_key, 0) + 1
    
    def decrement_connections(self, service: Any):
        """减少连接计数"""
        service_key = f"{service.host}:{service.port}"
        if service_key in self.connection_counts:
            self.connection_counts[service_key] = max(0, self.connection_counts[service_key] - 1)


class RouteManager:
    """路由管理器"""
    
    def __init__(self):
        """初始化路由管理器"""
        self.routes: Dict[str, RouteRule] = {}
        self.rate_limiters: Dict[str, RateLimiter] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
    
    def add_route(self, route: RouteRule):
        """添加路由规则"""
        self.routes[route.id] = route
        
        # 初始化限流器
        if route.rate_limit:
            self.rate_limiters[route.id] = RateLimiter()
        
        # 初始化熔断器
        if route.circuit_breaker:
            cb_rule = CircuitBreakerRule(**route.circuit_breaker)
            self.circuit_breakers[route.id] = CircuitBreaker(cb_rule)
    
    def remove_route(self, route_id: str):
        """移除路由规则"""
        self.routes.pop(route_id, None)
        self.rate_limiters.pop(route_id, None)
        self.circuit_breakers.pop(route_id, None)
    
    def find_route(self, path: str, method: str) -> Optional[RouteRule]:
        """查找匹配的路由"""
        for route in self.routes.values():
            if (route.method.value == method and 
                route.path_regex.match(path)):
                return route
        return None
    
    def check_rate_limit(self, route_id: str, client_key: str) -> bool:
        """检查限流"""
        if route_id not in self.rate_limiters:
            return True
        
        route = self.routes[route_id]
        if not route.rate_limit:
            return True
        
        rate_limit_rule = RateLimitRule(**route.rate_limit)
        return self.rate_limiters[route_id].is_allowed(client_key, rate_limit_rule)
    
    def check_circuit_breaker(self, route_id: str) -> bool:
        """检查熔断器"""
        if route_id not in self.circuit_breakers:
            return True
        
        return self.circuit_breakers[route_id].can_execute()
    
    def record_success(self, route_id: str):
        """记录成功"""
        if route_id in self.circuit_breakers:
            self.circuit_breakers[route_id].record_success()
    
    def record_failure(self, route_id: str):
        """记录失败"""
        if route_id in self.circuit_breakers:
            self.circuit_breakers[route_id].record_failure()


class APIGateway:
    """API网关"""
    
    def __init__(self, service_discovery, auth_manager=None):
        """初始化API网关"""
        self.service_discovery = service_discovery
        self.auth_manager = auth_manager
        self.route_manager = RouteManager()
        self.load_balancer = LoadBalancer()
        self.middleware_stack: List[Callable] = []
        
        # 创建web应用
        self.app = web.Application()
        self.app.router.add_route('*', '/{path:.*}', self.handle_request)
    
    def add_middleware(self, middleware: Callable):
        """添加中间件"""
        self.middleware_stack.append(middleware)
    
    async def handle_request(self, request: web.Request) -> web.Response:
        """处理请求"""
        start_time = time.time()
        
        try:
            # 查找路由
            route = self.route_manager.find_route(request.path, request.method)
            if not route:
                return web.json_response(
                    {"error": "Route not found"}, 
                    status=404
                )
            
            # 获取客户端IP
            client_ip = request.remote or request.headers.get('X-Forwarded-For', '').split(',')[0].strip()
            client_key = f"{client_ip}:{route.id}"
            
            # 检查限流
            if not self.route_manager.check_rate_limit(route.id, client_key):
                return web.json_response(
                    {"error": "Rate limit exceeded"}, 
                    status=429
                )
            
            # 检查熔断器
            if not self.route_manager.check_circuit_breaker(route.id):
                return web.json_response(
                    {"error": "Service temporarily unavailable"}, 
                    status=503
                )
            
            # 认证检查
            if route.auth_required and self.auth_manager:
                auth_result = await self._authenticate_request(request)
                if not auth_result:
                    return web.json_response(
                        {"error": "Authentication required"}, 
                        status=401
                    )
            
            # 执行中间件
            for middleware in self.middleware_stack:
                result = await middleware(request, route)
                if isinstance(result, web.Response):
                    return result
            
            # 转发请求
            response = await self._forward_request(request, route, client_ip)
            
            # 记录成功
            self.route_manager.record_success(route.id)
            
            # 添加响应头
            response.headers['X-Gateway-Time'] = str(time.time() - start_time)
            
            return response
            
        except Exception as e:
            # 记录失败
            if 'route' in locals():
                self.route_manager.record_failure(route.id)
            
            return web.json_response(
                {"error": f"Internal server error: {str(e)}"}, 
                status=500
            )
    
    async def _authenticate_request(self, request: web.Request) -> bool:
        """认证请求"""
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return False
        
        try:
            # 提取token
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
                payload = self.auth_manager.verify_access_token(token)
                if payload:
                    # 将用户信息添加到请求中
                    request['user'] = payload
                    return True
        except Exception:
            pass
        
        return False
    
    async def _forward_request(
        self, 
        request: web.Request, 
        route: RouteRule,
        client_ip: str
    ) -> web.Response:
        """转发请求"""
        # 发现服务
        services = await self.service_discovery.discover_service(route.service_name)
        if not services:
            raise Exception(f"Service {route.service_name} not available")
        
        # 负载均衡选择服务
        selected_service = self.load_balancer.select_service(
            services, 
            route.load_balance_strategy,
            client_ip
        )
        
        if not selected_service:
            raise Exception("No available service instance")
        
        # 构建目标URL
        target_path = route.target_path or request.path
        target_url = f"{selected_service.endpoint}{target_path}"
        
        # 添加查询参数
        if request.query_string:
            target_url += f"?{request.query_string}"
        
        # 准备请求头
        headers = dict(request.headers)
        headers.pop('Host', None)  # 移除原始Host头
        headers['X-Forwarded-For'] = client_ip
        headers['X-Forwarded-Proto'] = request.scheme
        
        # 增加连接计数
        self.load_balancer.increment_connections(selected_service)
        
        try:
            # 转发请求
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=route.timeout)
            ) as session:
                
                # 读取请求体
                body = None
                if request.method in ['POST', 'PUT', 'PATCH']:
                    body = await request.read()
                
                async with session.request(
                    method=request.method,
                    url=target_url,
                    headers=headers,
                    data=body
                ) as response:
                    
                    # 读取响应
                    response_body = await response.read()
                    response_headers = dict(response.headers)
                    
                    # 移除不需要的响应头
                    response_headers.pop('Transfer-Encoding', None)
                    response_headers.pop('Content-Encoding', None)
                    
                    return web.Response(
                        body=response_body,
                        status=response.status,
                        headers=response_headers
                    )
        
        finally:
            # 减少连接计数
            self.load_balancer.decrement_connections(selected_service)
    
    def add_route(self, route: RouteRule):
        """添加路由"""
        self.route_manager.add_route(route)
    
    def remove_route(self, route_id: str):
        """移除路由"""
        self.route_manager.remove_route(route_id)
    
    async def start(self, host: str = '0.0.0.0', port: int = 8080):
        """启动网关"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, host, port)
        await site.start()
        
        print(f"API Gateway started on {host}:{port}")
        
        return runner
