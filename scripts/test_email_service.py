"""
Email Service Test Script
Tests email verification functionality
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import User
from app.email_service import email_service

def test_email_configuration():
    """Test email configuration"""
    app = create_app()
    
    with app.app_context():
        print("=" * 70)
        print("EMAIL CONFIGURATION TEST")
        print("=" * 70)
        print()
        
        # Check configuration
        config = {
            'MAIL_SERVER': app.config.get('MAIL_SERVER'),
            'MAIL_PORT': app.config.get('MAIL_PORT'),
            'MAIL_USE_TLS': app.config.get('MAIL_USE_TLS'),
            'MAIL_USE_SSL': app.config.get('MAIL_USE_SSL'),
            'MAIL_USERNAME': app.config.get('MAIL_USERNAME'),
            'MAIL_DEFAULT_SENDER': app.config.get('MAIL_DEFAULT_SENDER'),
            'MAIL_SUPPRESS_SEND': app.config.get('MAIL_SUPPRESS_SEND'),
            'VERIFICATION_TOKEN_MAX_AGE': app.config.get('VERIFICATION_TOKEN_MAX_AGE'),
        }
        
        print("Configuration:")
        print("-" * 70)
        for key, value in config.items():
            # Hide password
            if key == 'MAIL_PASSWORD':
                display_value = '***hidden***' if value else 'Not set'
            else:
                display_value = value
            
            status = '✓' if value else '✗'
            print(f"  {status} {key}: {display_value}")
        
        print()
        
        # Check if configuration is complete
        required = ['MAIL_SERVER', 'MAIL_PORT', 'MAIL_USERNAME', 'MAIL_DEFAULT_SENDER']
        missing = [key for key in required if not app.config.get(key)]
        
        if missing:
            print("❌ CONFIGURATION INCOMPLETE")
            print(f"   Missing required settings: {', '.join(missing)}")
            print()
            print("   Please configure email settings in your .env file.")
            print("   See .env.email.example for reference.")
            return False
        else:
            print("✅ CONFIGURATION COMPLETE")
            print()
        
        return True


def test_token_generation():
    """Test token generation and verification"""
    app = create_app()
    
    with app.app_context():
        print("=" * 70)
        print("TOKEN GENERATION TEST")
        print("=" * 70)
        print()
        
        test_email = "test@example.com"
        
        try:
            # Generate token
            print(f"Generating verification token for: {test_email}")
            token = email_service.generate_verification_token(test_email)
            print(f"✓ Token generated: {token[:50]}...")
            print()
            
            # Verify token
            print("Verifying token...")
            verified_email = email_service.verify_token(token, salt='email-verification')
            
            if verified_email == test_email:
                print(f"✅ TOKEN VERIFICATION SUCCESS")
                print(f"   Email extracted from token: {verified_email}")
                print()
                return True
            else:
                print(f"❌ TOKEN VERIFICATION FAILED")
                print(f"   Expected: {test_email}")
                print(f"   Got: {verified_email}")
                print()
                return False
                
        except Exception as e:
            print(f"❌ TOKEN TEST FAILED")
            print(f"   Error: {e}")
            print()
            return False


def test_send_verification_email():
    """Test sending verification email"""
    app = create_app()
    
    with app.app_context():
        print("=" * 70)
        print("EMAIL SENDING TEST")
        print("=" * 70)
        print()
        
        # Get test user or create one
        test_user = User.query.filter_by(username='testuser').first()
        
        if not test_user:
            print("No test user found. Creating one...")
            test_user = User(
                username='testuser',
                email='test@example.com',
                first_name='Test',
                last_name='User',
                is_verified=False
            )
            test_user.set_password('TestPass123!')
            db.session.add(test_user)
            db.session.commit()
            print(f"✓ Test user created: {test_user.username}")
        else:
            print(f"Using existing test user: {test_user.username}")
        
        print()
        print(f"Test user email: {test_user.email}")
        print()
        
        # Check suppress mode
        if app.config.get('MAIL_SUPPRESS_SEND'):
            print("⚠️  EMAIL SUPPRESSION IS ENABLED (Development Mode)")
            print("   Emails will not actually be sent.")
            print("   Check console output for verification link.")
        else:
            print("📧 EMAIL SUPPRESSION IS DISABLED (Production Mode)")
            print("   Email will be sent to: " + test_user.email)
        
        print()
        print("Sending verification email...")
        
        try:
            success = email_service.send_verification_email(
                test_user.email,
                test_user.get_full_name() or test_user.username
            )
            
            if success:
                print("✅ EMAIL SENT SUCCESSFULLY")
                if app.config.get('MAIL_SUPPRESS_SEND'):
                    print()
                    print("   Check the console output above for the verification link.")
                    print("   Copy the link and open it in your browser to test verification.")
                else:
                    print()
                    print("   Check your email inbox for the verification message.")
                print()
                return True
            else:
                print("❌ EMAIL SENDING FAILED")
                print()
                return False
                
        except Exception as e:
            print(f"❌ EMAIL SENDING ERROR")
            print(f"   Error: {e}")
            print()
            return False


def test_full_verification_flow():
    """Test complete verification flow"""
    app = create_app()
    
    with app.app_context():
        print("=" * 70)
        print("FULL VERIFICATION FLOW TEST")
        print("=" * 70)
        print()
        
        # Find unverified user
        user = User.query.filter_by(is_verified=False).first()
        
        if not user:
            print("No unverified users found. Creating test user...")
            user = User(
                username=f'testuser_{os.urandom(4).hex()}',
                email=f'test_{os.urandom(4).hex()}@example.com',
                first_name='Test',
                last_name='User',
                is_verified=False
            )
            user.set_password('TestPass123!')
            db.session.add(user)
            db.session.commit()
            print(f"✓ Created test user: {user.username} ({user.email})")
        else:
            print(f"Using existing unverified user: {user.username} ({user.email})")
        
        print()
        print("Step 1: Generate verification token")
        token = email_service.generate_verification_token(user.email)
        print(f"✓ Token: {token[:30]}...")
        
        print()
        print("Step 2: Verify token")
        verified_email = email_service.verify_token(token, salt='email-verification')
        
        if verified_email != user.email:
            print("❌ Token verification failed")
            return False
        print(f"✓ Token verified: {verified_email}")
        
        print()
        print("Step 3: Update user verification status")
        user.is_verified = True
        db.session.commit()
        print(f"✓ User marked as verified")
        
        print()
        print("Step 4: Verify database update")
        updated_user = User.query.get(user.id)
        
        if updated_user.is_verified:
            print("✅ VERIFICATION FLOW COMPLETE")
            print(f"   User {user.username} is now verified")
            print()
            return True
        else:
            print("❌ VERIFICATION FAILED")
            print("   Database update did not persist")
            print()
            return False


def run_all_tests():
    """Run all tests"""
    print()
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "EMAIL VERIFICATION SYSTEM TESTS" + " " * 22 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    results = {
        'Configuration': test_email_configuration(),
        'Token Generation': test_token_generation(),
        'Email Sending': test_send_verification_email(),
        'Full Flow': test_full_verification_flow(),
    }
    
    print()
    print("=" * 70)
    print("TEST RESULTS SUMMARY")
    print("=" * 70)
    print()
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_name:.<40} {status}")
    
    print()
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print()
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️  SOME TESTS FAILED")
        print()
        print("Troubleshooting:")
        print("  1. Check your .env file has all required email settings")
        print("  2. Verify SMTP credentials are correct")
        print("  3. For Gmail, use App Password (not regular password)")
        print("  4. Check firewall/network allows SMTP connections")
        print("  5. Review application logs for detailed errors")
    
    print()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Email Verification System')
    parser.add_argument('--test', choices=['config', 'token', 'email', 'flow', 'all'], 
                       default='all', help='Which test to run')
    
    args = parser.parse_args()
    
    if args.test == 'config':
        test_email_configuration()
    elif args.test == 'token':
        test_token_generation()
    elif args.test == 'email':
        test_send_verification_email()
    elif args.test == 'flow':
        test_full_verification_flow()
    else:
        run_all_tests()
