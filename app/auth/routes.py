"""
Authentication routes for PanelMerge
Handles user registration, login, logout, and profile management
"""

from flask import render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from datetime import datetime
import re
from . import auth_bp
from ..models import db, User, UserRole
from ..extensions import limiter
from ..audit_service import AuditService

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"

@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        # Get form data
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        organization = request.form.get('organization', '').strip()
        
        # Validation
        errors = []
        
        if not username or len(username) < 3:
            errors.append("Username must be at least 3 characters long")
        elif User.query.filter_by(username=username).first():
            errors.append("Username already exists")
        
        if not email:
            errors.append("Email is required")
        elif not validate_email(email):
            errors.append("Invalid email format")
        elif User.query.filter_by(email=email).first():
            errors.append("Email already registered")
        
        if not password:
            errors.append("Password is required")
        else:
            valid, message = validate_password(password)
            if not valid:
                errors.append(message)
        
        if password != confirm_password:
            errors.append("Passwords do not match")
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html')
        
        # Create new user
        try:
            user = User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                organization=organization,
                role=UserRole.USER,  # Default role
                is_active=True
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            # Log successful registration
            AuditService.log_registration(username, email, success=True)
            
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            # Log failed registration
            AuditService.log_registration(username, email, success=False, error_message=str(e))
            current_app.logger.error(f"Registration error: {e}")
            flash('Registration failed. Please try again.', 'error')
    
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username_or_email = request.form.get('username_or_email', '').strip()
        password = request.form.get('password', '')
        remember_me = request.form.get('remember_me') == 'on'
        
        if not username_or_email or not password:
            flash('Please enter both username/email and password', 'error')
            return render_template('auth/login.html')
        
        # Find user by username or email
        user = User.query.filter(
            (User.username == username_or_email) | 
            (User.email == username_or_email.lower())
        ).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                # Log failed login due to inactive account
                AuditService.log_login(username_or_email, success=False, error_message="Account deactivated")
                flash('Your account has been deactivated. Please contact an administrator.', 'error')
                return render_template('auth/login.html')
            
            # Update login statistics
            user.last_login = datetime.utcnow()
            user.login_count = (user.login_count or 0) + 1
            db.session.commit()
            
            login_user(user, remember=remember_me)
            
            # Log successful login
            AuditService.log_login(user.username, success=True)
            
            flash(f'Welcome back, {user.get_full_name()}!', 'success')
            
            # Redirect to next page or home
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('main.index')
            return redirect(next_page)
        else:
            # Log failed login
            AuditService.log_login(username_or_email, success=False, error_message="Invalid credentials")
            flash('Invalid username/email or password', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    current_app.logger.info("🚪 LOGOUT ROUTE: Starting logout function")
    
    # Capture username before logout_user() is called
    username = current_user.username if current_user.is_authenticated else "Unknown"
    user_id = current_user.id if current_user.is_authenticated else None
    
    current_app.logger.info(f"🚪 LOGOUT ROUTE: User details - username: {username}, user_id: {user_id}, authenticated: {current_user.is_authenticated}")
    
    # Log logout action BEFORE calling logout_user()
    try:
        current_app.logger.info(f"🚪 LOGOUT ROUTE: Attempting to log logout for user: {username}")
        audit_result = AuditService.log_logout(username)
        current_app.logger.info(f"🚪 LOGOUT ROUTE: Logout audit result: {audit_result}")
    except Exception as e:
        current_app.logger.error(f"🚪 LOGOUT ROUTE: Failed to log logout audit: {e}")
        import traceback
        current_app.logger.error(f"🚪 LOGOUT ROUTE: Traceback: {traceback.format_exc()}")
    
    current_app.logger.info("🚪 LOGOUT ROUTE: Calling logout_user()")
    logout_user()
    current_app.logger.info("🚪 LOGOUT ROUTE: logout_user() completed")
    
    flash('You have been logged out successfully.', 'info')
    current_app.logger.info("🚪 LOGOUT ROUTE: Returning redirect")
    return redirect(url_for('main.index'))

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('auth/profile.html', user=current_user)

@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile"""
    if request.method == 'POST':
        # Get form data
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        organization = request.form.get('organization', '').strip()
        
        # Store old values for audit
        old_data = {
            'first_name': current_user.first_name,
            'last_name': current_user.last_name,
            'organization': current_user.organization
        }
        
        # Update user
        current_user.first_name = first_name
        current_user.last_name = last_name
        current_user.organization = organization
        
        try:
            db.session.commit()
            
            # Log profile update
            new_data = {
                'first_name': first_name,
                'last_name': last_name,
                'organization': organization
            }
            AuditService.log_profile_update(current_user.id, current_user.username, old_data, new_data)
            
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('auth.profile'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Profile update error: {e}")
            flash('Failed to update profile. Please try again.', 'error')
    
    return render_template('auth/edit_profile.html', user=current_user)

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
@limiter.limit("5 per hour")
def change_password():
    """Change user password"""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not current_user.check_password(current_password):
            flash('Current password is incorrect', 'error')
            return render_template('auth/change_password.html')
        
        valid, message = validate_password(new_password)
        if not valid:
            flash(message, 'error')
            return render_template('auth/change_password.html')
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return render_template('auth/change_password.html')
        
        # Update password
        try:
            current_user.set_password(new_password)
            db.session.commit()
            
            # Log password change
            AuditService.log_password_change(current_user.username, success=True)
            
            flash('Password changed successfully!', 'success')
            return redirect(url_for('auth.profile'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Password change error: {e}")
            
            # Log failed password change
            AuditService.log_password_change(current_user.username, success=False)
            
            flash('Failed to change password. Please try again.', 'error')
    
    return render_template('auth/change_password.html')

# Admin routes
@auth_bp.route('/admin/users')
@login_required
def admin_users():
    """Admin: List all users"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    # Get user statistics
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    admin_users = User.query.filter_by(role=UserRole.ADMIN).count()
    recent_users = User.query.filter(User.created_at >= datetime.utcnow().replace(day=1)).count()
    
    user_stats = {
        'total': total_users,
        'active': active_users,
        'admins': admin_users,
        'recent': recent_users
    }
    
    users = User.query.order_by(User.created_at.desc()).all()
    
    return render_template('auth/admin_users.html', users=users, user_stats=user_stats)

@auth_bp.route('/admin/users/<int:user_id>/toggle-active', methods=['POST'])
@login_required
def admin_toggle_user_active(user_id):
    """Admin: Toggle user active status"""
    if not current_user.is_admin():
        return jsonify({'error': 'Access denied'}), 403
    
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        return jsonify({'error': 'Cannot deactivate your own account'}), 400
    
    user.is_active = not user.is_active
    try:
        db.session.commit()
        status = 'activated' if user.is_active else 'deactivated'
        
        # Log user status change
        AuditService.log_admin_action(
            action_description=f"User '{user.username}' {status}",
            target_user_id=user.id,
            details={
                "action": "toggle_active_status",
                "new_status": user.is_active,
                "target_username": user.username
            }
        )
        
        return jsonify({
            'success': True, 
            'message': f'User {user.username} has been {status}',
            'is_active': user.is_active
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Toggle user active error: {e}")
        return jsonify({'error': 'Failed to update user status'}), 500

@auth_bp.route('/api/user/<int:user_id>/toggle-status', methods=['POST'])
@login_required
def api_toggle_user_status(user_id):
    """API: Toggle user active status (alternative endpoint)"""
    return admin_toggle_user_active(user_id)

@auth_bp.route('/api/user/<int:user_id>', methods=['GET', 'PUT'])
@login_required
def api_user_details(user_id):
    """API: Get or update user details"""
    if not current_user.is_admin():
        return jsonify({'error': 'Access denied'}), 403
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'GET':
        return jsonify({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role.value,
            'is_active': user.is_active
        })
    
    elif request.method == 'PUT':
        data = request.get_json()
        
        # Store old values for audit
        old_data = {
            'role': user.role.value,
            'is_active': user.is_active
        }
        
        changes_made = []
        
        if 'role' in data:
            try:
                new_role = UserRole(data['role'])
                if user.role != new_role:
                    user.role = new_role
                    changes_made.append(f"role changed to {new_role.value}")
            except ValueError:
                return jsonify({'error': 'Invalid role'}), 400
        
        if 'is_active' in data:
            if user.is_active != data['is_active']:
                user.is_active = data['is_active']
                status = 'activated' if data['is_active'] else 'deactivated'
                changes_made.append(f"account {status}")
        
        try:
            db.session.commit()
            
            # Log user update if changes were made
            if changes_made:
                new_data = {
                    'role': user.role.value,
                    'is_active': user.is_active
                }
                AuditService.log_admin_action(
                    action_description=f"Updated user '{user.username}': {', '.join(changes_made)}",
                    target_user_id=user.id,
                    details={
                        "action": "user_update",
                        "changes": changes_made,
                        "target_username": user.username,
                        "old_values": old_data,
                        "new_values": new_data
                    }
                )
            
            return jsonify({'success': True, 'message': 'User updated successfully'})
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Update user error: {e}")
            return jsonify({'error': 'Failed to update user'}), 500

# API endpoints
@auth_bp.route('/api/current-user')
@login_required
def api_current_user():
    """API: Get current user information"""
    return jsonify(current_user.to_dict())

@auth_bp.route('/api/check-username')
def api_check_username():
    """API: Check if username is available"""
    username = request.args.get('username', '').strip()
    if not username:
        return jsonify({'available': False, 'message': 'Username is required'})
    
    exists = User.query.filter_by(username=username).first() is not None
    return jsonify({
        'available': not exists,
        'message': 'Username is available' if not exists else 'Username already taken'
    })

@auth_bp.route('/api/check-email')
def api_check_email():
    """API: Check if email is available"""
    email = request.args.get('email', '').strip().lower()
    if not email:
        return jsonify({'available': False, 'message': 'Email is required'})
    
    if not validate_email(email):
        return jsonify({'available': False, 'message': 'Invalid email format'})
    
    exists = User.query.filter_by(email=email).first() is not None
    return jsonify({
        'available': not exists,
        'message': 'Email is available' if not exists else 'Email already registered'
    })

@auth_bp.route('/admin/audit-logs')
@login_required
def audit_logs():
    """Admin page to view audit logs"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 100)  # Max 100 per page
    
    # Get filter parameters
    action_type = request.args.get('action_type', '')
    username = request.args.get('username', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    success_filter = request.args.get('success', '')
    
    # Build query
    from ..models import AuditLog, AuditActionType
    query = AuditLog.query
    
    # Apply filters
    if action_type:
        try:
            action_enum = AuditActionType(action_type)
            query = query.filter(AuditLog.action_type == action_enum)
        except ValueError:
            pass  # Invalid action type, ignore filter
    
    if username:
        query = query.filter(AuditLog.username.ilike(f'%{username}%'))
    
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(AuditLog.timestamp >= from_date)
        except ValueError:
            pass  # Invalid date format, ignore filter
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d')
            # Add one day to include the entire day
            to_date = to_date.replace(hour=23, minute=59, second=59)
            query = query.filter(AuditLog.timestamp <= to_date)
        except ValueError:
            pass  # Invalid date format, ignore filter
    
    if success_filter:
        if success_filter.lower() == 'true':
            query = query.filter(AuditLog.success == True)
        elif success_filter.lower() == 'false':
            query = query.filter(AuditLog.success == False)
    
    # Order by timestamp (newest first)
    query = query.order_by(AuditLog.timestamp.desc())
    
    # Paginate
    audit_logs_paginated = query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    # Log admin action
    AuditService.log_admin_action(
        action_description="Viewed audit logs",
        details={
            "filters": {
                "action_type": action_type,
                "username": username,
                "date_from": date_from,
                "date_to": date_to,
                "success": success_filter
            },
            "page": page,
            "per_page": per_page
        }
    )
    
    return render_template('auth/audit_logs.html', 
                         audit_logs=audit_logs_paginated,
                         action_types=[action.value for action in AuditActionType],
                         filters={
                             'action_type': action_type,
                             'username': username,
                             'date_from': date_from,
                             'date_to': date_to,
                             'success': success_filter
                         })

@auth_bp.route('/admin/audit-logs/export')
@login_required
def export_audit_logs():
    """Export audit logs as CSV"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    import csv
    import io
    from flask import make_response
    from ..models import AuditLog
    
    # Get filter parameters (same as audit_logs route)
    action_type = request.args.get('action_type', '')
    username = request.args.get('username', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    success_filter = request.args.get('success', '')
    
    # Build query (same logic as audit_logs route)
    query = AuditLog.query
    
    # Apply same filters as the view
    if action_type:
        try:
            from ..models import AuditActionType
            action_enum = AuditActionType(action_type)
            query = query.filter(AuditLog.action_type == action_enum)
        except ValueError:
            pass
    
    if username:
        query = query.filter(AuditLog.username.ilike(f'%{username}%'))
    
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(AuditLog.timestamp >= from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d')
            to_date = to_date.replace(hour=23, minute=59, second=59)
            query = query.filter(AuditLog.timestamp <= to_date)
        except ValueError:
            pass
    
    if success_filter:
        if success_filter.lower() == 'true':
            query = query.filter(AuditLog.success == True)
        elif success_filter.lower() == 'false':
            query = query.filter(AuditLog.success == False)
    
    # Order by timestamp
    query = query.order_by(AuditLog.timestamp.desc())
    
    # Limit to prevent memory issues
    audit_logs = query.limit(10000).all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'ID', 'Timestamp', 'Username', 'Action Type', 'Description', 
        'IP Address', 'Resource Type', 'Resource ID', 'Success', 
        'Error Message', 'Duration (ms)'
    ])
    
    # Write data
    for log in audit_logs:
        writer.writerow([
            log.id,
            log.timestamp.isoformat() if log.timestamp else '',
            log.username or '',
            log.action_type.value if log.action_type else '',
            log.action_description or '',
            log.ip_address or '',
            log.resource_type or '',
            log.resource_id or '',
            'Yes' if log.success else 'No',
            log.error_message or '',
            log.duration_ms or ''
        ])
    
    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=audit_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    # Log export action
    AuditService.log_data_export(
        export_type="audit_logs",
        record_count=len(audit_logs),
        file_name=f"audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    )
    
    return response
