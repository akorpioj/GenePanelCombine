#!/usr/bin/env python3
"""
Cache management script for PanelMerge
Provides utilities to monitor and manage Redis cache
"""

import os
import sys
import argparse

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

def show_cache_stats():
    """Display cache statistics"""
    app = create_app('development')
    with app.app_context():
        from app.main.cache_utils import get_cache_stats
        
        print("📊 Redis Cache Statistics")
        print("=" * 40)
        stats = get_cache_stats()
        
        for key, value in stats.items():
            print(f"{key:25}: {value}")

def clear_cache():
    """Clear all cache entries"""
    app = create_app('development')
    with app.app_context():
        from app.extensions import cache
        from app.main.cache_utils import clear_panel_cache
        
        print("🧹 Clearing cache...")
        clear_panel_cache()
        
        # Also clear the entire cache for good measure
        try:
            cache.clear()
            print("✅ Cache cleared successfully!")
        except Exception as e:
            print(f"❌ Error clearing cache: {e}")

def test_cache_entry():
    """Test setting and getting a cache entry"""
    app = create_app('development')
    with app.app_context():
        from app.extensions import cache
        
        print("🧪 Testing cache entry...")
        
        # Set a test value
        cache.set('test_entry', {'timestamp': 'now', 'data': 'test'}, timeout=300)
        
        # Get it back
        result = cache.get('test_entry')
        
        if result:
            print(f"✅ Cache test successful: {result}")
        else:
            print("❌ Cache test failed")

def monitor_cache_performance():
    """Monitor cache hit/miss ratios"""
    app = create_app('development')
    with app.app_context():
        from app.main.cache_utils import get_cache_stats
        
        print("📈 Cache Performance Monitor")
        print("=" * 40)
        
        stats = get_cache_stats()
        
        hits = stats.get('cache_hits', 0)
        misses = stats.get('cache_misses', 0)
        total = hits + misses
        
        if total > 0:
            hit_ratio = (hits / total) * 100
            print(f"Cache Hits: {hits}")
            print(f"Cache Misses: {misses}")
            print(f"Hit Ratio: {hit_ratio:.2f}%")
            
            if hit_ratio > 80:
                print("🎉 Excellent cache performance!")
            elif hit_ratio > 60:
                print("👍 Good cache performance")
            elif hit_ratio > 40:
                print("⚠️  Moderate cache performance")
            else:
                print("🔥 Poor cache performance - consider tuning")
        else:
            print("No cache statistics available yet")

def main():
    parser = argparse.ArgumentParser(description='PanelMerge Cache Management')
    parser.add_argument('command', choices=['stats', 'clear', 'test', 'monitor'],
                       help='Command to execute')
    
    args = parser.parse_args()
    
    if args.command == 'stats':
        show_cache_stats()
    elif args.command == 'clear':
        clear_cache()
    elif args.command == 'test':
        test_cache_entry()
    elif args.command == 'monitor':
        monitor_cache_performance()

if __name__ == "__main__":
    main()
