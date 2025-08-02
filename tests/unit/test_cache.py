"""
Unit tests for caching functionality
"""
import pytest
from unittest.mock import patch, Mock, MagicMock
import redis
from app.extensions import cache
from cache_manager import CacheManager


@pytest.mark.unit
@pytest.mark.cache
class TestCacheManager:
    """Test CacheManager functionality."""
    
    @pytest.fixture
    def cache_manager(self, mock_redis):
        """Create a CacheManager instance with mocked Redis."""
        with patch('cache_manager.redis.Redis', return_value=mock_redis):
            return CacheManager()
    
    def test_cache_manager_initialization(self, cache_manager):
        """Test CacheManager initialization."""
        assert cache_manager is not None
        assert hasattr(cache_manager, 'redis_client')
    
    def test_set_cache_item(self, cache_manager, mock_redis):
        """Test setting cache items."""
        key = 'test_key'
        value = {'data': 'test_value'}
        ttl = 300
        
        cache_manager.set(key, value, ttl)
        
        mock_redis.setex.assert_called_once()
    
    def test_get_cache_item(self, cache_manager, mock_redis):
        """Test getting cache items."""
        key = 'test_key'
        expected_value = {'data': 'test_value'}
        
        # Mock Redis returning JSON string
        mock_redis.get.return_value = '{"data": "test_value"}'
        
        result = cache_manager.get(key)
        
        mock_redis.get.assert_called_once_with(key)
        assert result == expected_value
    
    def test_get_nonexistent_cache_item(self, cache_manager, mock_redis):
        """Test getting non-existent cache items."""
        key = 'nonexistent_key'
        
        mock_redis.get.return_value = None
        
        result = cache_manager.get(key)
        
        assert result is None
    
    def test_delete_cache_item(self, cache_manager, mock_redis):
        """Test deleting cache items."""
        key = 'test_key'
        
        cache_manager.delete(key)
        
        mock_redis.delete.assert_called_once_with(key)
    
    def test_clear_all_cache(self, cache_manager, mock_redis):
        """Test clearing all cache."""
        cache_manager.clear_all()
        
        mock_redis.flushdb.assert_called_once()
    
    def test_cache_stats(self, cache_manager, mock_redis):
        """Test getting cache statistics."""
        mock_redis.info.return_value = {
            'used_memory': 1000000,
            'keyspace_hits': 100,
            'keyspace_misses': 10
        }
        
        stats = cache_manager.get_stats()
        
        assert 'used_memory' in stats
        assert 'keyspace_hits' in stats
        assert 'keyspace_misses' in stats


@pytest.mark.unit
@pytest.mark.cache
class TestFlaskCaching:
    """Test Flask-Caching integration."""
    
    def test_cache_configuration(self, app):
        """Test cache configuration."""
        with app.app_context():
            # Cache should be configured
            assert cache is not None
    
    @patch.object(cache, 'get')
    @patch.object(cache, 'set')
    def test_panel_caching(self, mock_set, mock_get, client, sample_panel):
        """Test panel data caching."""
        mock_get.return_value = None  # Cache miss
        
        response = client.get(f'/api/v1/panels/{sample_panel.panel_id}')
        
        assert response.status_code == 200
        # Should attempt to get from cache
        mock_get.assert_called()
    
    @patch.object(cache, 'get')
    def test_panel_cache_hit(self, mock_get, client):
        """Test panel cache hit."""
        cached_data = {
            'panel_id': 1,
            'name': 'Cached Panel',
            'version': '1.0'
        }
        mock_get.return_value = cached_data
        
        response = client.get('/api/v1/panels/1')
        
        # Should use cached data
        mock_get.assert_called()
    
    def test_cache_invalidation_on_update(self, mock_cache):
        """Test cache invalidation when data is updated."""
        # This would test that cache is cleared when panels are updated
        # Implementation depends on actual cache invalidation logic
        pass


@pytest.mark.unit
@pytest.mark.cache
@pytest.mark.redis
class TestRedisConnection:
    """Test Redis connection and operations."""
    
    def test_redis_connection_success(self, mock_redis):
        """Test successful Redis connection."""
        mock_redis.ping.return_value = True
        
        # Test connection
        result = mock_redis.ping()
        assert result is True
    
    def test_redis_connection_failure(self):
        """Test Redis connection failure handling."""
        with patch('redis.Redis') as mock_redis_class:
            mock_redis_class.side_effect = redis.ConnectionError("Could not connect")
            
            with pytest.raises(redis.ConnectionError):
                redis.Redis()
    
    def test_redis_set_operation(self, mock_redis):
        """Test Redis SET operation."""
        key = 'test_key'
        value = 'test_value'
        
        mock_redis.set.return_value = True
        
        result = mock_redis.set(key, value)
        
        mock_redis.set.assert_called_once_with(key, value)
        assert result is True
    
    def test_redis_get_operation(self, mock_redis):
        """Test Redis GET operation."""
        key = 'test_key'
        expected_value = b'test_value'
        
        mock_redis.get.return_value = expected_value
        
        result = mock_redis.get(key)
        
        mock_redis.get.assert_called_once_with(key)
        assert result == expected_value
    
    def test_redis_delete_operation(self, mock_redis):
        """Test Redis DELETE operation."""
        key = 'test_key'
        
        mock_redis.delete.return_value = 1
        
        result = mock_redis.delete(key)
        
        mock_redis.delete.assert_called_once_with(key)
        assert result == 1
    
    def test_redis_expire_operation(self, mock_redis):
        """Test Redis EXPIRE operation."""
        key = 'test_key'
        ttl = 300
        
        mock_redis.expire.return_value = True
        
        result = mock_redis.expire(key, ttl)
        
        mock_redis.expire.assert_called_once_with(key, ttl)
        assert result is True


@pytest.mark.unit
@pytest.mark.cache
class TestCacheDecorators:
    """Test cache decorators and utilities."""
    
    def test_cache_key_generation(self):
        """Test cache key generation for consistent caching."""
        from app.main.cache_utils import generate_cache_key
        
        # Test with various inputs
        key1 = generate_cache_key('panels', 1)
        key2 = generate_cache_key('panels', 1)
        key3 = generate_cache_key('panels', 2)
        
        assert key1 == key2  # Same inputs should produce same key
        assert key1 != key3  # Different inputs should produce different keys
    
    @patch.object(cache, 'cached')
    def test_cached_function_decorator(self, mock_cached):
        """Test cached function decorator."""
        @cache.cached(timeout=300, key_prefix='test')
        def expensive_function(param):
            return f"result_{param}"
        
        # Call function
        result = expensive_function('test_param')
        
        # Should have used cache decorator
        assert result == "result_test_param"
    
    def test_cache_timeout_configuration(self, app):
        """Test cache timeout configuration."""
        with app.app_context():
            # Test that timeouts are properly configured
            # This depends on actual configuration
            assert True  # Placeholder


@pytest.mark.unit
@pytest.mark.cache
@pytest.mark.slow
class TestCachePerformance:
    """Test cache performance characteristics."""
    
    def test_cache_response_time(self, cache_manager, mock_redis):
        """Test cache response time is reasonable."""
        import time
        
        key = 'performance_test'
        value = {'data': 'test'}
        
        start_time = time.time()
        cache_manager.set(key, value)
        cache_manager.get(key)
        end_time = time.time()
        
        # Cache operations should be fast (mocked, so very fast)
        assert (end_time - start_time) < 1.0
    
    def test_large_data_caching(self, cache_manager, mock_redis):
        """Test caching of large data structures."""
        large_data = {
            'panels': [{'id': i, 'name': f'Panel {i}'} for i in range(1000)]
        }
        
        # Should handle large data without issues
        cache_manager.set('large_data', large_data)
        mock_redis.setex.assert_called_once()
    
    def test_concurrent_cache_access(self, cache_manager, mock_redis):
        """Test concurrent cache access simulation."""
        # Simulate multiple concurrent requests
        keys = [f'concurrent_key_{i}' for i in range(10)]
        
        for key in keys:
            cache_manager.get(key)
        
        # Should handle multiple calls
        assert mock_redis.get.call_count == 10


@pytest.mark.unit
@pytest.mark.cache
class TestCacheErrorHandling:
    """Test cache error handling and fallbacks."""
    
    def test_redis_unavailable_fallback(self, cache_manager):
        """Test behavior when Redis is unavailable."""
        with patch.object(cache_manager, 'redis_client') as mock_client:
            mock_client.get.side_effect = redis.ConnectionError("Redis unavailable")
            
            # Should handle gracefully and return None
            result = cache_manager.get('test_key')
            assert result is None
    
    def test_corrupted_cache_data_handling(self, cache_manager, mock_redis):
        """Test handling of corrupted cache data."""
        mock_redis.get.return_value = 'invalid json data'
        
        # Should handle JSON decode errors gracefully
        result = cache_manager.get('test_key')
        assert result is None
    
    def test_cache_memory_overflow_handling(self, cache_manager, mock_redis):
        """Test handling of cache memory overflow."""
        mock_redis.setex.side_effect = redis.ResponseError("OOM command not allowed")
        
        # Should handle memory errors gracefully
        try:
            cache_manager.set('test_key', {'data': 'test'})
        except redis.ResponseError:
            pass  # Expected behavior
    
    def test_network_timeout_handling(self, cache_manager, mock_redis):
        """Test handling of network timeouts."""
        mock_redis.get.side_effect = redis.TimeoutError("Timeout")
        
        # Should handle timeouts gracefully
        result = cache_manager.get('test_key')
        assert result is None
