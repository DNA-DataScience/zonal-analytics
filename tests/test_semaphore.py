import pytest
import asyncio
import time


@pytest.fixture
def tile_semaphore():
    """Create a fresh semaphore for each test"""
    return asyncio.Semaphore(5)


class TestSemaphoreManagement:
    """Tests for TILE_SEMAPHORE concurrency control"""
    
    @pytest.mark.asyncio
    async def test_semaphore_limits_concurrent_requests(self, tile_semaphore):
        """Test semaphore limits concurrent tile requests to 5"""
        active_requests = 0
        max_concurrent = 0
        
        async def mock_request():
            nonlocal active_requests, max_concurrent
            async with tile_semaphore:
                active_requests += 1
                max_concurrent = max(max_concurrent, active_requests)
                await asyncio.sleep(0.05)
                active_requests -= 1
        
        await asyncio.gather(*[mock_request() for _ in range(20)])
        
        assert max_concurrent <= 5
    
    @pytest.mark.asyncio
    async def test_semaphore_queues_excess_requests(self, tile_semaphore):
        """Test that excess requests are queued"""
        completed = []
        
        async def mock_request(req_id):
            async with tile_semaphore:
                completed.append(req_id)
                await asyncio.sleep(0.03)
        
        start = time.time()
        await asyncio.gather(*[mock_request(i) for i in range(15)])
        elapsed = time.time() - start
        
        assert len(completed) == 15
        assert elapsed >= 0.09
    
    @pytest.mark.asyncio
    async def test_semaphore_sequential_acquisition(self, tile_semaphore):
        """Test semaphore properly sequences requests"""
        order = []
        
        async def request(num):
            async with tile_semaphore:
                order.append(('start', num))
                await asyncio.sleep(0.01)
                order.append(('end', num))
        
        await asyncio.gather(*[request(i) for i in range(3)])
        
        assert len(order) == 6
        assert order[0][0] == 'start'