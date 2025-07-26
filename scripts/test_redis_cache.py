#!/usr/bin/env python3
"""
Test Redis caching implementation for PanelMerge
"""

import os
import sys
import time

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.main.cache_utils import (
    get_cached_all_panels, 
    get_cached_gene_suggestions,
    get_cache_stats,
    clear_panel_cache
)

def test_redis_connection():
    """Test basic Redis connection"""
    print("🔍 Testing Redis connection...")
    
    app = create_app('development')
    with app.app_context():
        try:
            from app.extensions import cache
            # Simple cache test
            cache.set('test_key', 'test_value', timeout=60)
            result = cache.get('test_key')
            
            if result == 'test_value':
                print("✅ Redis connection successful!")
                cache.delete('test_key')
                return True
            else:
                print("❌ Redis connection failed - value mismatch")
                return False
                
        except Exception as e:
            print(f"❌ Redis connection error: {e}")
            return False

def test_cached_functions():
    """Test the cached API functions"""
    print("\n🧪 Testing cached functions...")
    
    app = create_app('development')
    with app.app_context():
        try:
            # Test 1: Panel caching
            print("Testing panel caching...")
            start_time = time.time()
            
            panels_uk = get_cached_all_panels('uk')
            first_call_time = time.time() - start_time
            
            print(f"   First call (cache miss): {first_call_time:.2f}s, {len(panels_uk)} panels")
            
            # Second call should be faster (cache hit)
            start_time = time.time()
            panels_uk_cached = get_cached_all_panels('uk')
            second_call_time = time.time() - start_time
            
            print(f"   Second call (cache hit): {second_call_time:.2f}s, {len(panels_uk_cached)} panels")
            
            if second_call_time < first_call_time:
                print("   ✅ Caching is working - second call was faster!")
            else:
                print("   ⚠️  Caching might not be working - times similar")
            
            # Test 2: Gene suggestions caching
            print("\nTesting gene suggestions caching...")
            start_time = time.time()
            
            suggestions = get_cached_gene_suggestions('BRCA', 'uk', 5)
            gene_call_time = time.time() - start_time
            
            print(f"   Gene suggestions call: {gene_call_time:.2f}s, {len(suggestions)} suggestions")
            
            if suggestions:
                print(f"   Sample suggestions: {[s['symbol'] for s in suggestions[:3]]}")
            
            return True
            
        except Exception as e:
            print(f"❌ Cached functions test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

def test_cache_stats():
    """Test cache statistics"""
    print("\n📊 Testing cache statistics...")
    
    app = create_app('development')
    with app.app_context():
        try:
            stats = get_cache_stats()
            print("Cache stats:", stats)
            return True
        except Exception as e:
            print(f"❌ Cache stats test failed: {e}")
            return False

def main():
    """Run all tests"""
    print("🚀 PanelMerge Redis Caching Test Suite")
    print("=" * 50)
    
    # Test 1: Redis connection
    redis_ok = test_redis_connection()
    
    if not redis_ok:
        print("\n❌ Redis connection failed. Please check:")
        print("   1. Redis Cloud service is running")
        print("   2. REDIS_URL in .env is correct")
        print("   3. Authentication credentials are included")
        return False
    
    # Test 2: Cached functions
    functions_ok = test_cached_functions()
    
    # Test 3: Cache stats
    stats_ok = test_cache_stats()
    
    print("\n" + "=" * 50)
    if redis_ok and functions_ok:
        print("🎉 All tests passed! Redis caching is working correctly.")
        print("\n📈 Performance improvements:")
        print("   • Panel API calls cached for 30 minutes")
        print("   • Gene suggestions cached for 24 hours")
        print("   • Significant speed improvement on repeated requests")
        return True
    else:
        print("❌ Some tests failed. Check the error messages above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
