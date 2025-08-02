#!/usr/bin/env python3
"""
Script to create an admin user for the GenePanelCombine application.
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
        try:
            # Check if database tables exist
            db.create_all()
            
            # Collect user information
            if interactive:
                print("Creating admin user for GenePanelCombine")
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
            
            if first_name or last_name:
                print(f"Full name: {admin_user.get_full_name()}")
            if organization:
                print(f"Organization: {organization}")
            
            return True
            
        except Exception as e:
            print(f"Error creating admin user: {e}")
            db.session.rollback()
            return False

def main():
    """Main function to handle command line arguments and run the script."""
    parser = argparse.ArgumentParser(
        description="Create an admin user for GenePanelCombine application"
    )
    parser.add_argument('-u', '--username', help='Username for the admin user')
    parser.add_argument('-e', '--email', help='Email address for the admin user')
    parser.add_argument('-p', '--password', help='Password for the admin user (not recommended for security)')
    parser.add_argument('-f', '--first-name', help='First name of the admin user')
    parser.add_argument('-l', '--last-name', help='Last name of the admin user')
    parser.add_argument('-o', '--organization', help='Organization of the admin user')
    parser.add_argument('--non-interactive', action='store_true', 
                       help='Run in non-interactive mode (requires all required args)')
    
    args = parser.parse_args()
    
    # Determine if running in interactive mode
    interactive = not args.non_interactive
    
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
