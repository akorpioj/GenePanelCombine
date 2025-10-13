"""
Cleanup old suspicious activity records
Run this script periodically (e.g., daily via cron) to maintain database size
"""

import sys
import os

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models import SuspiciousActivity

def cleanup_suspicious_activity():
    """Clean up old suspicious activity records"""
    app = create_app()
    
    with app.app_context():
        retention_days = app.config.get('SUSPICIOUS_ACTIVITY_RETENTION_DAYS', 90)
        print(f"Cleaning up suspicious activity records older than {retention_days} days...")
        
        deleted_count = SuspiciousActivity.cleanup_old_records(days=retention_days)
        
        if deleted_count > 0:
            print(f"✓ Successfully deleted {deleted_count} old suspicious activity records")
        else:
            print("✓ No old records to delete")
        
        # Get current statistics
        total_records = SuspiciousActivity.query.count()
        alert_records = SuspiciousActivity.query.filter_by(alert_triggered=True).count()
        
        print(f"\nCurrent Statistics:")
        print(f"  Total records: {total_records}")
        print(f"  Alert records: {alert_records}")

if __name__ == '__main__':
    cleanup_suspicious_activity()
