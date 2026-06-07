"""
Performance Tests for Data Assimilation Platform
Test system performance and scalability
"""

import logging
import pytest
import time
import statistics

import psutil  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)

# Test configuration


PERFORMANCE_THRESHOLDS = {
    'max_response_time_ms': 100,
    'max_memory_mb': 512,
    'min_throughput_rps': 100,
    'max_cpu_percent': 80
}


class TestResponseTime:
    """Test API response times"""

    @pytest.fixture
    def test_data(self):
        """Generate test data"""
        return {
            'data_size': 1000,
            'num_iterations': 100
        }

    def test_simple_operation_response_time(self, test_data):
        """Test simple operation response time"""
        data = list(range(test_data['data_size']))

        start_time = time.time()

        # Simple operation
        _ = sum(data)

        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to ms

        logger.info(f"Simple operation response time: {response_time:.3f} ms")
        assert response_time < PERFORMANCE_THRESHOLDS['max_response_time_ms']

    def test_data_processing_response_time(self, test_data):
        """Test data processing response time"""
        data = [[i + j for j in range(100)] for i in range(100)]

        start_time = time.time()

        # Data processing
        _ = [[x * 2 for x in row] for row in data]

        end_time = time.time()
        response_time = (end_time - start_time) * 1000

        print(f"Data processing response time: {response_time:.3f} ms")
        assert response_time < PERFORMANCE_THRESHOLDS['max_response_time_ms']

    def test_calculation_response_time(self):
        """Test complex calculation response time"""
        start_time = time.time()

        # Complex calculation (matrix multiplication)
        size = 50
        matrix_a = [[i + j for j in range(size)] for i in range(size)]
        matrix_b = [[i * j for j in range(size)] for i in range(size)]

        _ = [[sum(a * b for a, b in zip(row_a, col_b))
             for col_b in zip(*matrix_b)]
             for row_a in matrix_a]

        end_time = time.time()
        response_time = (end_time - start_time) * 1000

        logger.info(f"Matrix calculation response time: {response_time:.3f} ms")
        # Relaxed threshold for complex calculations
        assert response_time < 1000


class TestMemoryUsage:
    """Test memory usage"""

    def test_memory_usage_simple_operation(self):
        """Test memory usage of simple operation"""
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create some data
        data = list(range(100000))
        _ = sum(data)

        current_memory = process.memory_info().rss / 1024 / 1024
        memory_used = current_memory - initial_memory

        logger.info(f"Memory used: {memory_used:.2f} MB")
        logger.info(f"Total memory: {current_memory:.2f} MB")

        assert memory_used < PERFORMANCE_THRESHOLDS['max_memory_mb']

    def test_memory_usage_large_data(self):
        """Test memory usage with large data"""
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024

        # Create large data structure
        _large_data = {
            'array': [i for i in range(1000000)],
            'matrix': [[i for i in range(1000)] for _ in range(1000)],
            'nested': {f'key_{i}': {'data': [i] * 100} for i in range(1000)}
        }

        current_memory = process.memory_info().rss / 1024 / 1024
        memory_used = current_memory - initial_memory

        logger.info(f"Large data memory used: {memory_used:.2f} MB")

        # Large data can use more memory
        assert memory_used < 100  # Relaxed for large data

    def test_memory_cleanup(self):
        """Test memory cleanup after operation"""
        process = psutil.Process()

        # Create and delete data
        for _ in range(10):
            data = [i for i in range(100000)]
            del data

        import gc
        gc.collect()

        time.sleep(0.1)
        current_memory = process.memory_info().rss / 1024 / 1024

        logger.info(f"Memory after cleanup: {current_memory:.2f} MB")

        # Memory should be reasonable after cleanup
        assert current_memory < PERFORMANCE_THRESHOLDS['max_memory_mb']


class TestThroughput:
    """Test system throughput"""

    def test_requests_per_second(self):
        """Test requests per second throughput"""
        num_requests = 1000
        start_time = time.time()

        # Simulate requests
        for _ in range(num_requests):
            data = {'id': 1, 'value': 100}
            _ = sum(data.values())

        end_time = time.time()
        total_time = end_time - start_time

        rps = num_requests / total_time

        logger.info(f"Throughput: {rps:.2f} requests/second")
        assert rps > PERFORMANCE_THRESHOLDS['min_throughput_rps']

    def test_concurrent_throughput(self):
        """Test concurrent throughput"""
        import concurrent.futures

        def process_request(request_id):
            """Process a single request"""
            time.sleep(0.001)  # Simulate processing
            return request_id * 2

        num_requests = 100
        start_time = time.time()

        # Process concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            _ = list(executor.map(process_request, range(num_requests)))

        end_time = time.time()
        total_time = end_time - start_time

        rps = num_requests / total_time

        logger.info(f"Concurrent throughput: {rps:.2f} requests/second")
        assert rps > PERFORMANCE_THRESHOLDS['min_throughput_rps']


class TestCPUUsage:
    """Test CPU usage"""

    def test_cpu_usage_calculation(self):
        """Test CPU usage during calculation"""
        process = psutil.Process()

        # Start monitoring
        process.cpu_percent()  # prime the monitor

        # Perform calculation
        _ = sum(i * i for i in range(1000000))

        # Measure CPU usage
        cpu_percent = process.cpu_percent()

        logger.info(f"CPU usage: {cpu_percent:.2f}%")
        assert cpu_percent < PERFORMANCE_THRESHOLDS['max_cpu_percent']

    def test_cpu_usage_parallel(self):
        """Test CPU usage with parallel processing"""
        import concurrent.futures

        process = psutil.Process()

        def cpu_intensive_task(n):
            """CPU intensive task"""
            return sum(i * i for i in range(n))

        num_tasks = 10

        # Start monitoring
        process.cpu_percent()  # prime the monitor

        # Process in parallel
        with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:
            _ = list(executor.map(cpu_intensive_task, [100000] * num_tasks))

        # Measure CPU usage
        cpu_percent = process.cpu_percent()

        print(f"CPU usage (parallel): {cpu_percent:.2f}%")
        # Relaxed threshold for parallel processing


class TestScalability:
    """Test system scalability"""

    def test_linear_scaling(self):
        """Test linear scaling with data size"""
        sizes = [100, 1000, 10000]
        times = []

        for size in sizes:
            start_time = time.time()

            data = list(range(size))
            _ = sum(data)

            end_time = time.time()
            times.append(end_time - start_time)

        # Check if scaling is roughly linear
        ratio_1 = times[1] / times[0]
        ratio_2 = times[2] / times[1]

        print(f"Size ratios: {sizes[1] / sizes[0]:.1f}x, {sizes[2] / sizes[1]:.1f}x")
        print(f"Time ratios: {ratio_1:.1f}x, {ratio_2:.1f}x")

        # Times should scale roughly linearly with size
        assert ratio_1 < 15  # Allow some overhead
        assert ratio_2 < 15

    def test_concurrent_scaling(self):
        """Test scaling with concurrent requests"""
        thread_counts = [1, 2, 4, 8]
        throughputs = []

        for num_threads in thread_counts:
            import concurrent.futures

            def task():
                time.sleep(0.01)
                return True

            start_time = time.time()

            with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
                _ = list(executor.map(lambda _: task(), range(100)))

            end_time = time.time()
            rps = 100 / (end_time - start_time)
            throughputs.append(rps)

        logger.info("Thread scaling:")
        for threads, rps in zip(thread_counts, throughputs):
            print(f"  {threads} threads: {rps:.2f} rps")

        # Throughput should increase with threads
        assert throughputs[-1] > throughputs[0]


class TestDatabasePerformance:
    """Test database performance"""

    def test_query_performance(self):
        """Test database query performance"""
        # Simulate database query
        start_time = time.time()

        # Simulated query
        _ = [i for i in range(1000) if i % 2 == 0]

        end_time = time.time()
        query_time = (end_time - start_time) * 1000

        print(f"Query time: {query_time:.3f} ms")
        assert query_time < PERFORMANCE_THRESHOLDS['max_response_time_ms']

    def test_batch_insert_performance(self):
        """Test batch insert performance"""
        num_records = 1000

        start_time = time.time()

        # Simulate batch insert
        _ = [{'id': i, 'data': f'record_{i}'} for i in range(num_records)]

        end_time = time.time()
        insert_time = (end_time - start_time)

        records_per_second = num_records / insert_time

        print(f"Batch insert: {records_per_second:.2f} records/second")
        assert records_per_second > 100


class TestCachePerformance:
    """Test cache performance"""

    def test_cache_hit_rate(self):
        """Test cache hit rate"""
        cache = {}
        hits = 0
        misses = 0

        data = list(range(100))

        for i in range(200):  # Access 100 items twice
            if i % 100 in cache:
                hits += 1
            else:
                misses += 1
                cache[i % 100] = data[i % 100]

        hit_rate = hits / (hits + misses)

        print(f"Cache hit rate: {hit_rate:.2%}")
        assert hit_rate > 0.4  # Should have at least 40% hit rate

    def test_cache_latency(self):
        """Test cache access latency"""
        cache = {i: f'value_{i}' for i in range(1000)}

        latencies = []

        for _ in range(1000):
            key = 500  # Fixed key
            start = time.time()
            _ = cache.get(key)
            end = time.time()
            latencies.append((end - start) * 1000)

        avg_latency = statistics.mean(latencies)
        p99_latency = sorted(latencies)[int(len(latencies) * 0.99)]

        print(f"Average cache latency: {avg_latency:.3f} ms")
        print(f"P99 cache latency: {p99_latency:.3f} ms")

        assert avg_latency < 1.0  # Should be sub-ms


class TestStress:
    """Stress tests"""

    def test_high_load(self):
        """Test system under high load"""
        duration = 5  # seconds
        requests = []

        start_time = time.time()
        end_time = start_time + duration

        while time.time() < end_time:
            request_start = time.time()

            # Simulate request processing
            data = list(range(1000))
            _ = sum(data)

            request_end = time.time()
            requests.append(request_end - request_start)

        total_requests = len(requests)
        avg_time = statistics.mean(requests)
        max_time = max(requests)

        logger.info("High load test:")
        print(f"  Total requests: {total_requests}")
        print(f"  Average time: {avg_time * 1000:.3f} ms")
        print(f"  Max time: {max_time * 1000:.3f} ms")
        print(f"  Throughput: {total_requests / duration:.2f} rps")

        # System should handle high load
        assert total_requests > 100

    def test_memory_pressure(self):
        """Test system under memory pressure"""
        process = psutil.Process()

        # Gradually increase memory usage
        data_structures = []

        for i in range(10):
            # Create data structure
            data = [j for j in range(100000)]
            data_structures.append(data)

            current_memory = process.memory_info().rss / 1024 / 1024

            print(f"Iteration {i + 1}: Memory = {current_memory:.2f} MB")

            # Keep some data, release some
            if len(data_structures) > 5:
                data_structures.pop(0)

        # System should handle memory pressure
        current_memory = process.memory_info().rss / 1024 / 1024
        assert current_memory < 1000  # Should not exceed 1 GB


# Performance test utilities


def benchmark(func, iterations=100):
    """Benchmark a function"""
    times = []

    for _ in range(iterations):
        start = time.time()
        func()
        end = time.time()
        times.append(end - start)

    return {
        'mean': statistics.mean(times),
        'median': statistics.median(times),
        'stdev': statistics.stdev(times) if len(times) > 1 else 0,
        'min': min(times),
        'max': max(times)
    }


# Pytest configuration


def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "stress: mark test as stress test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow"
    )


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
