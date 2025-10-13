"""
Database Cleanup Tasks
Run periodically to maintain database health
"""

from app import create_app
from app.models import PasswordResetToken

def cleanup_expired_tokens():
    """Remove expired password reset tokens"""
    app = create_app()
    with app.app_context():
        count = PasswordResetToken.cleanup_expired_tokens()
        print(f"✅ Cleaned up {count} expired password reset tokens")

def cleanup_old_tokens(days=30):
    """Remove old password reset tokens (default: 30 days)"""
    app = create_app()
    with app.app_context():
        count = PasswordResetToken.cleanup_old_tokens(days)
        print(f"✅ Cleaned up {count} old password reset tokens (>{days} days)")

if __name__ == '__main__':
    print("Running database cleanup tasks...")
    cleanup_expired_tokens()
    cleanup_old_tokens()
    print("✅ Cleanup complete!")
