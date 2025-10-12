#!/usr/bin/env python3
"""
Script to create or manage admin users for the PanelMerge application.

Features:
- Create new admin users
- Change passwords for existing admin users
- Reset failed login attempts and unlock accounts
- Interactive or command-line mode

This script can be run interactively or with command line arguments.
"""

import os
import sys
import getpass
import argparse
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app import create_app
from app.models import User, UserRole, db

def change_admin_password(username=None, new_password=None, interactive=True):
    """
    Change the password for an existing admin user.
    
    Args:
        username (str): Username of the admin user
        new_password (str): New password for the admin user
        interactive (bool): Whether to prompt for missing information
    
    Returns:
        bool: True if password was changed successfully, False otherwise
    """
    app = create_app('development')
    
    with app.app_context():
        # Initialize encryption service if not already initialized
        try:
            from app.encryption_service import encryption_service
            if not encryption_service._initialized:
                encryption_service.initialize(app)
        except Exception as e:
            # If encryption service fails, we can still change passwords
            # since password hashes don't use the encryption service
            pass
        try:
            # Collect user information
            if interactive:
                print("Change Admin User Password")
                print("=" * 40)
                
                if not username:
                    username = input("Enter username of admin user: ").strip()
                
                # Show user info before changing password
                user = User.query.filter_by(username=username).first()
                if not user:
                    print(f"Error: User '{username}' not found!")
                    return False
                
                print(f"\nUser found:")
                print(f"  Username: {user.username}")
                print(f"  Email: {user.email}")
                print(f"  Role: {user.role.value}")
                
                # Try to display full name, but handle encryption errors gracefully
                try:
                    full_name = user.get_full_name()
                    if full_name and full_name != user.username:
                        print(f"  Full name: {full_name}")
                except Exception:
                    # Silently skip if encryption fails
                    pass
                
                # Try to display organization, but handle encryption errors gracefully
                try:
                    if user.organization:
                        print(f"  Organization: {user.organization}")
                except Exception:
                    # Silently skip if encryption fails
                    pass
                
                # Confirm this is the right user
                confirm = input(f"\nChange password for this user? (yes/no): ").strip().lower()
                if confirm not in ['yes', 'y']:
                    print("Password change cancelled.")
                    return False
                
                if not new_password:
                    new_password = getpass.getpass("\nEnter new password: ")
                    confirm_password = getpass.getpass("Confirm new password: ")
                    if new_password != confirm_password:
                        print("Error: Passwords do not match!")
                        return False
            else:
                # Non-interactive mode
                if not username:
                    print("Error: Username is required!")
                    return False
                
                user = User.query.filter_by(username=username).first()
                if not user:
                    print(f"Error: User '{username}' not found!")
                    return False
            
            # Validate password
            if not new_password:
                print("Error: Password is required!")
                return False
            
            # Validate password strength
            if len(new_password) < 8:
                print("Error: Password must be at least 8 characters long!")
                return False
            
            # Update password
            user.set_password(new_password)
            
            # Reset failed login attempts
            user.failed_login_attempts = 0
            user.locked_until = None
            
            db.session.commit()
            
            print(f"\n✓ Password changed successfully for user '{username}'!")
            print(f"  - Failed login attempts reset to 0")
            print(f"  - Account unlocked (if it was locked)")
            
            return True
            
        except Exception as e:
            print(f"Error changing password: {e}")
            db.session.rollback()
            return False

def create_admin_user(username=None, email=None, password=None, first_name=None, 
                     last_name=None, organization=None, interactive=True):
    """
    Create an admin user with the provided details.
    
    Args:
        username (str): Username for the admin user
        email (str): Email address for the admin user
        password (str): Password for the admin user
        first_name (str): First name (optional)
        last_name (str): Last name (optional)
        organization (str): Organization name (optional)
        interactive (bool): Whether to prompt for missing information
    
    Returns:
        bool: True if user was created successfully, False otherwise
    """
    app = create_app('development')
    
    with app.app_context():
        # Initialize encryption service for encrypted fields
        try:
            from app.encryption_service import encryption_service
            if not encryption_service._initialized:
                encryption_service.initialize(app)
        except Exception as e:
            # If encryption service fails, log but continue
            # Password hashes don't use encryption service
            print(f"Warning: Encryption service initialization failed: {e}")
        
        try:
            # Check if database tables exist
            db.create_all()
            
            # Collect user information
            if interactive:
                print("Creating admin user for PanelMerge")
                print("=" * 40)
                
                if not username:
                    username = input("Enter username: ").strip()
                if not email:
                    email = input("Enter email address: ").strip()
                if not password:
                    password = getpass.getpass("Enter password: ")
                    confirm_password = getpass.getpass("Confirm password: ")
                    if password != confirm_password:
                        print("Error: Passwords do not match!")
                        return False
                
                # Optional fields
                if not first_name:
                    first_name = input("Enter first name (optional): ").strip() or None
                if not last_name:
                    last_name = input("Enter last name (optional): ").strip() or None
                if not organization:
                    organization = input("Enter organization (optional): ").strip() or None
            
            # Validate required fields
            if not username or not email or not password:
                print("Error: Username, email, and password are required!")
                return False
            
            # Check if user already exists
            existing_user = User.query.filter(
                (User.username == username) | (User.email == email)
            ).first()
            
            if existing_user:
                if existing_user.username == username:
                    print(f"Error: User with username '{username}' already exists!")
                else:
                    print(f"Error: User with email '{email}' already exists!")
                return False
            
            # Create the admin user
            admin_user = User(
                username=username,
                email=email,
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True,
                created_at=datetime.now(),
                login_count=0,
                failed_login_attempts=0
            )
            
            # Set password
            admin_user.set_password(password)
            
            # Set optional fields if provided
            if first_name:
                admin_user.first_name = first_name
            if last_name:
                admin_user.last_name = last_name
            if organization:
                admin_user.organization = organization
            
            # Add to database
            db.session.add(admin_user)
            db.session.commit()
            
            print(f"\nAdmin user created successfully!")
            print(f"Username: {username}")
            print(f"Email: {email}")
            print(f"Role: {UserRole.ADMIN.value}")
            print(f"Active: {admin_user.is_active}")
            print(f"Verified: {admin_user.is_verified}")
            
            # Display optional fields with encryption error handling
            if first_name or last_name:
                try:
                    full_name = admin_user.get_full_name()
                    if full_name:
                        print(f"Full name: {full_name}")
                except Exception:
                    # If encryption fails, show what we have
                    if first_name and last_name:
                        print(f"Full name: {first_name} {last_name}")
                    elif first_name:
                        print(f"First name: {first_name}")
                    elif last_name:
                        print(f"Last name: {last_name}")
            
            if organization:
                try:
                    org = admin_user.organization
                    if org:
                        print(f"Organization: {org}")
                except Exception:
                    print(f"Organization: {organization}")
            
            return True
            
        except Exception as e:
            print(f"Error creating admin user: {e}")
            db.session.rollback()
            return False

def main():
    """Main function to handle command line arguments and run the script."""
    parser = argparse.ArgumentParser(
        description="Create or manage admin users for PanelMerge application",
        epilog="""
Examples:
  # Create admin user interactively
  python create_admin_user.py
  
  # Create admin user with arguments
  python create_admin_user.py -u admin -e admin@example.com -p MyPassword123!
  
  # Change admin password interactively
  python create_admin_user.py --change-password
  
  # Change admin password with arguments
  python create_admin_user.py --change-password -u admin -p NewPassword123!
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Operation mode
    parser.add_argument('--change-password', action='store_true',
                       help='Change password for an existing admin user instead of creating new one')
    
    # User details
    parser.add_argument('-u', '--username', help='Username for the admin user')
    parser.add_argument('-e', '--email', help='Email address for the admin user (create only)')
    parser.add_argument('-p', '--password', help='Password for the admin user (not recommended for security)')
    parser.add_argument('-f', '--first-name', help='First name of the admin user (create only)')
    parser.add_argument('-l', '--last-name', help='Last name of the admin user (create only)')
    parser.add_argument('-o', '--organization', help='Organization of the admin user (create only)')
    parser.add_argument('--non-interactive', action='store_true', 
                       help='Run in non-interactive mode (requires all required args)')
    
    args = parser.parse_args()
    
    # Determine if running in interactive mode
    interactive = not args.non_interactive
    
    # Change password mode
    if args.change_password:
        if args.non_interactive:
            # In non-interactive mode, username and password must be provided
            if not all([args.username, args.password]):
                print("Error: In non-interactive mode with --change-password, username and password must be provided!")
                print("Use --help for more information.")
                sys.exit(1)
        
        success = change_admin_password(
            username=args.username,
            new_password=args.password,
            interactive=interactive
        )
        
        if success:
            print("\nPassword change completed successfully!")
            sys.exit(0)
        else:
            print("\nPassword change failed!")
            sys.exit(1)
    
    # Create user mode (default)
    else:
        if args.non_interactive:
            # In non-interactive mode, all required fields must be provided
            if not all([args.username, args.email, args.password]):
                print("Error: In non-interactive mode, username, email, and password must be provided!")
                print("Use --help for more information.")
                sys.exit(1)
        
        # Create the admin user
        success = create_admin_user(
            username=args.username,
            email=args.email,
            password=args.password,
            first_name=args.first_name,
            last_name=args.last_name,
            organization=args.organization,
            interactive=interactive
        )
        
        if success:
            print("\nAdmin user creation completed successfully!")
            sys.exit(0)
        else:
            print("\nAdmin user creation failed!")
            sys.exit(1)

if __name__ == '__main__':
    main()
