"""
性能优化和监控模块。

本模块提供性能监控、资源管理、缓存优化和性能分析功能，
确保DramaCraft服务的高效运行和稳定性。
"""

import asyncio
import gc
import json
import threading
import time
import weakref
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional

import psutil

from ..utils.logging import get_logger


@dataclass
class PerformanceMetrics:
    """性能指标。"""

    timestamp: float
    """时间戳。"""

    cpu_usage: float
    """CPU使用率(%)。"""

    memory_usage: float
    """内存使用率(%)。"""

    memory_used_mb: float
    """已使用内存(MB)。"""

    disk_usage: float
    """磁盘使用率(%)。"""

    active_tasks: int
    """活跃任务数。"""

    api_calls_per_minute: int
    """每分钟API调用数。"""

    average_response_time: float
    """平均响应时间(秒)。"""

    error_rate: float
    """错误率(%)。"""

    cache_hit_rate: float
    """缓存命中率(%)。"""


@dataclass
class TaskMetrics:
    """任务性能指标。"""

    task_id: str
    """任务ID。"""

    task_type: str
    """任务类型。"""

    start_time: float
    """开始时间。"""

    end_time: Optional[float]
    """结束时间。"""

    duration: Optional[float]
    """执行时长(秒)。"""

    memory_peak: float
    """内存峰值(MB)。"""

    cpu_time: float
    """CPU时间(秒)。"""

    success: bool
    """是否成功。"""

    error_message: Optional[str]
    """错误信息。"""


class PerformanceCache:
    """高性能缓存系统。"""

    def __init__(self, max_size: int = 1000, ttl: float = 3600):
        """
        初始化缓存。

        Args:
            max_size: 最大缓存条目数
            ttl: 生存时间(秒)
        """
        self.max_size = max_size
        self.ttl = ttl
        self.cache: dict[str, dict[str, Any]] = {}
        self.access_times: dict[str, float] = {}
        self.hit_count = 0
        self.miss_count = 0
        self.logger = get_logger("monitoring.cache")

        # 启动清理线程
        self._cleanup_thread = threading.Thread(target=self._cleanup_expired, daemon=True)
        self._cleanup_thread.start()

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值。"""
        current_time = time.time()

        if key in self.cache:
            entry = self.cache[key]

            # 检查是否过期
            if current_time - entry["timestamp"] < self.ttl:
                self.access_times[key] = current_time
                self.hit_count += 1
                return entry["value"]
            else:
                # 过期，删除
                del self.cache[key]
                del self.access_times[key]

        self.miss_count += 1
        return None

    def set(self, key: str, value: Any) -> None:
        """设置缓存值。"""
        current_time = time.time()

        # 如果缓存已满，删除最久未访问的条目
        if len(self.cache) >= self.max_size and key not in self.cache:
            self._evict_lru()

        self.cache[key] = {
            "value": value,
            "timestamp": current_time
        }
        self.access_times[key] = current_time

    def delete(self, key: str) -> bool:
        """删除缓存条目。"""
        if key in self.cache:
            del self.cache[key]
            del self.access_times[key]
            return True
        return False

    def clear(self) -> None:
        """清空缓存。"""
        self.cache.clear()
        self.access_times.clear()
        self.hit_count = 0
        self.miss_count = 0

    def get_hit_rate(self) -> float:
        """获取缓存命中率。"""
        total = self.hit_count + self.miss_count
        return self.hit_count / total if total > 0 else 0.0

    def get_stats(self) -> dict[str, Any]:
        """获取缓存统计信息。"""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_rate": self.get_hit_rate(),
            "memory_usage_mb": self._estimate_memory_usage()
        }

    def _evict_lru(self) -> None:
        """删除最久未访问的条目。"""
        if not self.access_times:
            return

        lru_key = min(self.access_times.items(), key=lambda x: x[1])[0]
        del self.cache[lru_key]
        del self.access_times[lru_key]

    def _cleanup_expired(self) -> None:
        """清理过期条目。"""
        while True:
            try:
                current_time = time.time()
                expired_keys = []

                for key, entry in self.cache.items():
                    if current_time - entry["timestamp"] >= self.ttl:
                        expired_keys.append(key)

                for key in expired_keys:
                    del self.cache[key]
                    del self.access_times[key]

                if expired_keys:
                    self.logger.debug(f"清理了 {len(expired_keys)} 个过期缓存条目")

                # 每分钟清理一次
                time.sleep(60)

            except Exception as e:
                self.logger.error(f"缓存清理失败: {e}")
                time.sleep(60)

    def _estimate_memory_usage(self) -> float:
        """估算内存使用量(MB)。"""
        try:
            import sys
            total_size = 0

            for key, entry in self.cache.items():
                total_size += sys.getsizeof(key)
                total_size += sys.getsizeof(entry)
                total_size += sys.getsizeof(entry["value"])

            return total_size / (1024 * 1024)  # 转换为MB
        except Exception:
            return 0.0


class PerformanceMonitor:
    """性能监控器。"""

    def __init__(self, metrics_retention: int = 1000):
        """
        初始化性能监控器。

        Args:
            metrics_retention: 保留的指标数量
        """
        self.metrics_retention = metrics_retention
        self.metrics_history: deque = deque(maxlen=metrics_retention)
        self.task_metrics: dict[str, TaskMetrics] = {}
        self.api_call_times: deque = deque(maxlen=1000)
        self.error_count = 0
        self.total_requests = 0
        self.cache = PerformanceCache()
        self.logger = get_logger("monitoring.performance")

        # 监控线程
        self._monitoring_active = True
        self._monitoring_thread = threading.Thread(target=self._collect_metrics, daemon=True)
        self._monitoring_thread.start()

        # 弱引用集合，用于跟踪活跃任务
        self._active_tasks = weakref.WeakSet()

    def start_task(self, task_id: str, task_type: str) -> None:
        """开始任务监控。"""
        current_time = time.time()

        task_metrics = TaskMetrics(
            task_id=task_id,
            task_type=task_type,
            start_time=current_time,
            end_time=None,
            duration=None,
            memory_peak=self._get_memory_usage(),
            cpu_time=0.0,
            success=False,
            error_message=None
        )

        self.task_metrics[task_id] = task_metrics
        self._active_tasks.add(task_metrics)

        self.logger.debug(f"开始监控任务: {task_id} ({task_type})")

    def end_task(self, task_id: str, success: bool = True, error_message: Optional[str] = None) -> None:
        """结束任务监控。"""
        if task_id not in self.task_metrics:
            return

        current_time = time.time()
        task_metrics = self.task_metrics[task_id]

        task_metrics.end_time = current_time
        task_metrics.duration = current_time - task_metrics.start_time
        task_metrics.success = success
        task_metrics.error_message = error_message
        task_metrics.memory_peak = max(task_metrics.memory_peak, self._get_memory_usage())

        if not success:
            self.error_count += 1

        self.total_requests += 1

        self.logger.debug(f"任务完成: {task_id}, 耗时: {task_metrics.duration:.2f}s, 成功: {success}")

    def record_api_call(self, response_time: float) -> None:
        """记录API调用。"""
        current_time = time.time()
        self.api_call_times.append((current_time, response_time))

    def get_current_metrics(self) -> PerformanceMetrics:
        """获取当前性能指标。"""
        current_time = time.time()

        # 计算每分钟API调用数
        minute_ago = current_time - 60
        recent_calls = [t for t, _ in self.api_call_times if t > minute_ago]
        api_calls_per_minute = len(recent_calls)

        # 计算平均响应时间
        recent_response_times = [rt for t, rt in self.api_call_times if t > minute_ago]
        avg_response_time = sum(recent_response_times) / len(recent_response_times) if recent_response_times else 0.0

        # 计算错误率
        error_rate = (self.error_count / self.total_requests * 100) if self.total_requests > 0 else 0.0

        # 获取系统资源使用情况
        cpu_usage = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        metrics = PerformanceMetrics(
            timestamp=current_time,
            cpu_usage=cpu_usage,
            memory_usage=memory.percent,
            memory_used_mb=memory.used / (1024 * 1024),
            disk_usage=disk.percent,
            active_tasks=len(self._active_tasks),
            api_calls_per_minute=api_calls_per_minute,
            average_response_time=avg_response_time,
            error_rate=error_rate,
            cache_hit_rate=self.cache.get_hit_rate() * 100
        )

        return metrics

    def get_metrics_history(self, minutes: int = 60) -> list[PerformanceMetrics]:
        """获取历史指标。"""
        cutoff_time = time.time() - (minutes * 60)
        return [m for m in self.metrics_history if m.timestamp > cutoff_time]

    def get_task_statistics(self) -> dict[str, Any]:
        """获取任务统计信息。"""
        completed_tasks = [t for t in self.task_metrics.values() if t.end_time is not None]

        if not completed_tasks:
            return {"total_tasks": 0}

        # 按任务类型分组
        by_type = defaultdict(list)
        for task in completed_tasks:
            by_type[task.task_type].append(task)

        statistics = {
            "total_tasks": len(completed_tasks),
            "success_rate": sum(1 for t in completed_tasks if t.success) / len(completed_tasks) * 100,
            "average_duration": sum(t.duration for t in completed_tasks) / len(completed_tasks),
            "by_type": {}
        }

        for task_type, tasks in by_type.items():
            statistics["by_type"][task_type] = {
                "count": len(tasks),
                "success_rate": sum(1 for t in tasks if t.success) / len(tasks) * 100,
                "average_duration": sum(t.duration for t in tasks) / len(tasks),
                "total_duration": sum(t.duration for t in tasks)
            }

        return statistics

    def export_metrics(self, file_path: Path) -> None:
        """导出性能指标到文件。"""
        data = {
            "current_metrics": asdict(self.get_current_metrics()),
            "metrics_history": [asdict(m) for m in self.metrics_history],
            "task_statistics": self.get_task_statistics(),
            "cache_stats": self.cache.get_stats(),
            "export_time": time.time()
        }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        self.logger.info(f"性能指标已导出到: {file_path}")

    def cleanup_old_tasks(self, max_age_hours: int = 24) -> None:
        """清理旧的任务记录。"""
        cutoff_time = time.time() - (max_age_hours * 3600)
        old_task_ids = [
            task_id for task_id, task in self.task_metrics.items()
            if task.end_time and task.end_time < cutoff_time
        ]

        for task_id in old_task_ids:
            del self.task_metrics[task_id]

        if old_task_ids:
            self.logger.debug(f"清理了 {len(old_task_ids)} 个旧任务记录")

    def stop_monitoring(self) -> None:
        """停止监控。"""
        self._monitoring_active = False
        if self._monitoring_thread.is_alive():
            self._monitoring_thread.join(timeout=5)

    def _collect_metrics(self) -> None:
        """收集性能指标。"""
        while self._monitoring_active:
            try:
                metrics = self.get_current_metrics()
                self.metrics_history.append(metrics)

                # 定期清理
                if len(self.metrics_history) % 100 == 0:
                    self.cleanup_old_tasks()
                    gc.collect()  # 强制垃圾回收

                time.sleep(30)  # 每30秒收集一次

            except Exception as e:
                self.logger.error(f"指标收集失败: {e}")
                time.sleep(30)

    def _get_memory_usage(self) -> float:
        """获取当前内存使用量(MB)。"""
        return psutil.virtual_memory().used / (1024 * 1024)


# 全局性能监控器实例
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """获取全局性能监控器实例。"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def performance_monitor(task_type: str = "unknown"):
    """性能监控装饰器。"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            task_id = f"{func.__name__}_{int(time.time() * 1000)}"

            monitor.start_task(task_id, task_type)
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                monitor.end_task(task_id, success=True)
                return result
            except Exception as e:
                monitor.end_task(task_id, success=False, error_message=str(e))
                raise
            finally:
                response_time = time.time() - start_time
                monitor.record_api_call(response_time)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            task_id = f"{func.__name__}_{int(time.time() * 1000)}"

            monitor.start_task(task_id, task_type)
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                monitor.end_task(task_id, success=True)
                return result
            except Exception as e:
                monitor.end_task(task_id, success=False, error_message=str(e))
                raise
            finally:
                response_time = time.time() - start_time
                monitor.record_api_call(response_time)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


def cache_result(ttl: float = 3600, key_func: Optional[Callable] = None):
    """结果缓存装饰器。"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache = get_performance_monitor().cache

            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}_{hash(str(args) + str(sorted(kwargs.items())))}"

            # 尝试从缓存获取
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # 执行函数并缓存结果
            result = await func(*args, **kwargs)
            cache.set(cache_key, result)
            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache = get_performance_monitor().cache

            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}_{hash(str(args) + str(sorted(kwargs.items())))}"

            # 尝试从缓存获取
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache.set(cache_key, result)
            return result

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator
