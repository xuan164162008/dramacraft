"""
性能测试模块

测试DramaCraft的性能指标：
- API响应时间
- 并发处理能力
- 内存使用效率
- 缓存性能
- 负载测试
"""

import pytest
import asyncio
import time
import psutil
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch
from pathlib import Path

from src.dramacraft.performance.cache import MemoryCache, CacheManager, cached
from src.dramacraft.microservices.gateway import APIGateway, LoadBalancer
from src.dramacraft.microservices.registry import ServiceRegistry, ServiceInstance


class TestCachePerformance:
    """缓存性能测试"""
    
    @pytest.fixture
    def memory_cache(self):
        """创建内存缓存"""
        return MemoryCache(max_size=1000)
    
    @pytest.fixture
    def cache_manager(self):
        """创建缓存管理器"""
        manager = CacheManager()
        manager.add_cache("memory", MemoryCache(max_size=1000), is_default=True)
        return manager
    
    @pytest.mark.asyncio
    async def test_cache_write_performance(self, memory_cache):
        """测试缓存写入性能"""
        start_time = time.time()
        
        # 写入1000个缓存项
        for i in range(1000):
            await memory_cache.set(f"key_{i}", f"value_{i}")
        
        end_time = time.time()
        write_time = end_time - start_time
        
        # 性能断言：1000次写入应在1秒内完成
        assert write_time < 1.0, f"缓存写入性能不达标: {write_time:.3f}s"
        
        # 计算每秒写入次数
        writes_per_second = 1000 / write_time
        assert writes_per_second > 1000, f"写入速度过慢: {writes_per_second:.0f} ops/s"
    
    @pytest.mark.asyncio
    async def test_cache_read_performance(self, memory_cache):
        """测试缓存读取性能"""
        # 预填充缓存
        for i in range(1000):
            await memory_cache.set(f"key_{i}", f"value_{i}")
        
        start_time = time.time()
        
        # 读取1000个缓存项
        for i in range(1000):
            value = await memory_cache.get(f"key_{i}")
            assert value == f"value_{i}"
        
        end_time = time.time()
        read_time = end_time - start_time
        
        # 性能断言：1000次读取应在0.5秒内完成
        assert read_time < 0.5, f"缓存读取性能不达标: {read_time:.3f}s"
        
        # 计算每秒读取次数
        reads_per_second = 1000 / read_time
        assert reads_per_second > 2000, f"读取速度过慢: {reads_per_second:.0f} ops/s"
    
    @pytest.mark.asyncio
    async def test_concurrent_cache_access(self, memory_cache):
        """测试并发缓存访问"""
        async def cache_operation(operation_id: int):
            """缓存操作"""
            key = f"concurrent_key_{operation_id}"
            value = f"concurrent_value_{operation_id}"
            
            # 写入
            await memory_cache.set(key, value)
            
            # 读取
            retrieved_value = await memory_cache.get(key)
            assert retrieved_value == value
            
            return operation_id
        
        start_time = time.time()
        
        # 并发执行100个缓存操作
        tasks = [cache_operation(i) for i in range(100)]
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        concurrent_time = end_time - start_time
        
        # 验证所有操作都成功
        assert len(results) == 100
        assert all(isinstance(r, int) for r in results)
        
        # 性能断言：100个并发操作应在1秒内完成
        assert concurrent_time < 1.0, f"并发缓存性能不达标: {concurrent_time:.3f}s"
    
    @pytest.mark.asyncio
    async def test_cache_decorator_performance(self, cache_manager):
        """测试缓存装饰器性能"""
        call_count = 0
        
        @cached(ttl=60, cache_name="memory")
        async def expensive_function(x: int) -> int:
            """模拟耗时函数"""
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)  # 模拟100ms的计算时间
            return x * 2
        
        # 第一次调用（缓存未命中）
        start_time = time.time()
        result1 = await expensive_function(5)
        first_call_time = time.time() - start_time
        
        assert result1 == 10
        assert call_count == 1
        assert first_call_time >= 0.1  # 应该包含计算时间
        
        # 第二次调用（缓存命中）
        start_time = time.time()
        result2 = await expensive_function(5)
        second_call_time = time.time() - start_time
        
        assert result2 == 10
        assert call_count == 1  # 函数没有再次执行
        assert second_call_time < 0.01  # 缓存访问应该很快


class TestAPIPerformance:
    """API性能测试"""
    
    @pytest.fixture
    def service_registry(self):
        """创建服务注册中心"""
        return ServiceRegistry()
    
    @pytest.fixture
    def load_balancer(self):
        """创建负载均衡器"""
        return LoadBalancer()
    
    def test_load_balancer_performance(self, load_balancer):
        """测试负载均衡器性能"""
        # 创建模拟服务实例
        services = []
        for i in range(10):
            service = Mock()
            service.host = f"server{i}.example.com"
            service.port = 8080 + i
            services.append(service)
        
        start_time = time.time()
        
        # 执行10000次负载均衡选择
        selections = []
        for _ in range(10000):
            selected = load_balancer.select_service(
                services, 
                load_balancer.LoadBalanceStrategy.ROUND_ROBIN
            )
            selections.append(selected)
        
        end_time = time.time()
        selection_time = end_time - start_time
        
        # 性能断言：10000次选择应在1秒内完成
        assert selection_time < 1.0, f"负载均衡性能不达标: {selection_time:.3f}s"
        
        # 验证负载均衡的公平性
        selection_counts = {}
        for service in selections:
            key = f"{service.host}:{service.port}"
            selection_counts[key] = selection_counts.get(key, 0) + 1
        
        # 每个服务应该被选择大约1000次（±10%）
        for count in selection_counts.values():
            assert 900 <= count <= 1100, f"负载均衡不公平: {count}"
    
    @pytest.mark.asyncio
    async def test_service_registry_performance(self, service_registry):
        """测试服务注册中心性能"""
        # 注册性能测试
        start_time = time.time()
        
        services = []
        for i in range(100):
            service = ServiceInstance(
                id=f"service_{i}",
                name="test_service",
                version="1.0.0",
                host=f"host{i}.example.com",
                port=8080 + i
            )
            await service_registry.register_service(service)
            services.append(service)
        
        registration_time = time.time() - start_time
        
        # 性能断言：100个服务注册应在2秒内完成
        assert registration_time < 2.0, f"服务注册性能不达标: {registration_time:.3f}s"
        
        # 查询性能测试
        start_time = time.time()
        
        for _ in range(1000):
            found_services = service_registry.get_services_by_name("test_service")
            assert len(found_services) == 100
        
        query_time = time.time() - start_time
        
        # 性能断言：1000次查询应在1秒内完成
        assert query_time < 1.0, f"服务查询性能不达标: {query_time:.3f}s"


class TestMemoryUsage:
    """内存使用测试"""
    
    def get_memory_usage(self) -> float:
        """获取当前内存使用量（MB）"""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    
    @pytest.mark.asyncio
    async def test_cache_memory_efficiency(self):
        """测试缓存内存效率"""
        initial_memory = self.get_memory_usage()
        
        # 创建大容量缓存
        cache = MemoryCache(max_size=10000)
        
        # 填充缓存
        for i in range(10000):
            await cache.set(f"key_{i}", f"value_{i}" * 100)  # 每个值约600字节
        
        peak_memory = self.get_memory_usage()
        memory_increase = peak_memory - initial_memory
        
        # 预期内存增长：10000 * 600字节 ≈ 6MB，加上开销应该在20MB以内
        assert memory_increase < 20, f"缓存内存使用过多: {memory_increase:.1f}MB"
        
        # 清空缓存
        await cache.clear()
        
        # 等待垃圾回收
        import gc
        gc.collect()
        
        final_memory = self.get_memory_usage()
        memory_released = peak_memory - final_memory
        
        # 应该释放大部分内存
        assert memory_released > memory_increase * 0.8, f"内存释放不充分: {memory_released:.1f}MB"
    
    def test_service_registry_memory_scaling(self):
        """测试服务注册中心内存扩展性"""
        initial_memory = self.get_memory_usage()
        
        registry = ServiceRegistry()
        
        # 注册大量服务
        for i in range(1000):
            service = ServiceInstance(
                id=f"service_{i}",
                name=f"service_type_{i % 10}",
                version="1.0.0",
                host=f"host{i}.example.com",
                port=8080 + i
            )
            # 同步调用（简化测试）
            registry.services[service.id] = service
        
        peak_memory = self.get_memory_usage()
        memory_per_service = (peak_memory - initial_memory) / 1000
        
        # 每个服务实例的内存开销应该很小（<1KB）
        assert memory_per_service < 1, f"每个服务内存开销过大: {memory_per_service:.3f}MB"


class TestConcurrencyPerformance:
    """并发性能测试"""
    
    @pytest.mark.asyncio
    async def test_concurrent_api_requests(self):
        """测试并发API请求处理"""
        async def mock_api_call(request_id: int) -> dict:
            """模拟API调用"""
            # 模拟一些处理时间
            await asyncio.sleep(0.01)
            return {
                "request_id": request_id,
                "status": "success",
                "timestamp": time.time()
            }
        
        start_time = time.time()
        
        # 并发执行1000个API请求
        tasks = [mock_api_call(i) for i in range(1000)]
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 验证所有请求都成功
        assert len(results) == 1000
        assert all(r["status"] == "success" for r in results)
        
        # 性能断言：1000个并发请求应在2秒内完成
        # （如果是串行执行需要10秒，并发应该大大减少时间）
        assert total_time < 2.0, f"并发API性能不达标: {total_time:.3f}s"
        
        # 计算吞吐量
        throughput = 1000 / total_time
        assert throughput > 500, f"API吞吐量过低: {throughput:.0f} req/s"
    
    def test_thread_pool_performance(self):
        """测试线程池性能"""
        def cpu_intensive_task(n: int) -> int:
            """CPU密集型任务"""
            result = 0
            for i in range(n):
                result += i * i
            return result
        
        # 串行执行基准测试
        start_time = time.time()
        serial_results = []
        for i in range(100):
            result = cpu_intensive_task(10000)
            serial_results.append(result)
        serial_time = time.time() - start_time
        
        # 并行执行测试
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(cpu_intensive_task, 10000) for _ in range(100)]
            parallel_results = [future.result() for future in as_completed(futures)]
        parallel_time = time.time() - start_time
        
        # 验证结果一致性
        assert len(parallel_results) == 100
        assert all(r == serial_results[0] for r in parallel_results)
        
        # 性能提升应该显著（至少2倍）
        speedup = serial_time / parallel_time
        assert speedup > 2.0, f"并行化效果不明显: {speedup:.2f}x"


class TestResponseTimeDistribution:
    """响应时间分布测试"""
    
    @pytest.mark.asyncio
    async def test_response_time_consistency(self):
        """测试响应时间一致性"""
        async def api_endpoint() -> str:
            """模拟API端点"""
            # 模拟变化的处理时间
            import random
            processing_time = random.uniform(0.01, 0.05)
            await asyncio.sleep(processing_time)
            return "success"
        
        response_times = []
        
        # 执行100次请求并记录响应时间
        for _ in range(100):
            start_time = time.time()
            result = await api_endpoint()
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # 转换为毫秒
            response_times.append(response_time)
            
            assert result == "success"
        
        # 计算统计指标
        avg_response_time = statistics.mean(response_times)
        median_response_time = statistics.median(response_times)
        p95_response_time = sorted(response_times)[94]  # 95th percentile
        p99_response_time = sorted(response_times)[98]  # 99th percentile
        
        # 性能断言
        assert avg_response_time < 100, f"平均响应时间过长: {avg_response_time:.1f}ms"
        assert median_response_time < 80, f"中位响应时间过长: {median_response_time:.1f}ms"
        assert p95_response_time < 150, f"95%响应时间过长: {p95_response_time:.1f}ms"
        assert p99_response_time < 200, f"99%响应时间过长: {p99_response_time:.1f}ms"
        
        # 响应时间变异系数应该较小（稳定性）
        std_dev = statistics.stdev(response_times)
        coefficient_of_variation = std_dev / avg_response_time
        assert coefficient_of_variation < 0.5, f"响应时间不稳定: CV={coefficient_of_variation:.2f}"


@pytest.mark.slow
class TestLoadTesting:
    """负载测试（标记为慢速测试）"""
    
    @pytest.mark.asyncio
    async def test_sustained_load(self):
        """测试持续负载"""
        async def sustained_api_call(call_id: int) -> dict:
            """持续API调用"""
            await asyncio.sleep(0.001)  # 1ms处理时间
            return {"call_id": call_id, "timestamp": time.time()}
        
        # 持续5秒的负载测试
        start_time = time.time()
        end_time = start_time + 5.0
        
        completed_calls = 0
        error_count = 0
        
        while time.time() < end_time:
            try:
                # 批量并发请求
                batch_size = 50
                tasks = [sustained_api_call(completed_calls + i) for i in range(batch_size)]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 统计成功和失败
                for result in results:
                    if isinstance(result, Exception):
                        error_count += 1
                    else:
                        completed_calls += 1
                
            except Exception:
                error_count += batch_size
        
        total_time = time.time() - start_time
        
        # 计算性能指标
        throughput = completed_calls / total_time
        error_rate = error_count / (completed_calls + error_count) if (completed_calls + error_count) > 0 else 0
        
        # 性能断言
        assert throughput > 1000, f"持续负载吞吐量不足: {throughput:.0f} req/s"
        assert error_rate < 0.01, f"错误率过高: {error_rate:.2%}"
        assert completed_calls > 5000, f"完成请求数不足: {completed_calls}"


if __name__ == "__main__":
    # 运行性能测试
    pytest.main([__file__, "-v", "--tb=short"])
