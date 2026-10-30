import time
from typing import Callable, Any

class PerformanceProfiler:
    """Measures tick duration and throughput performance."""

    @staticmethod
    def measure_execution_time(func: Callable[..., Any], *args, **kwargs) -> tuple[Any, float]:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return result, elapsed_ms
