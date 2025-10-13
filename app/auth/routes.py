"""
Authentication routes for PanelMerge
Handles user registration, login, logout, and profile management
"""

from flask import render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
import datetime
import re
import os
from . import auth_bp
from ..models import db, User, UserRole, AuditActionType
from ..extensions import limiter
from ..audit_service import AuditService
from ..session_service import session_service

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
        privacy_consent = request.form.get('privacy_consent') == 'on'
        terms_consent = request.form.get('terms_consent') == 'on'
        
        # Validation
        errors = []
        
        # GDPR Consent Validation
        if not privacy_consent:
            errors.append("You must agree to the Privacy Policy to create an account")
        
        if not terms_consent:
            errors.append("You must agree to the Terms of Use to create an account")
        
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
                is_active=True,
                is_verified=False  # Email not verified yet
            )
            # Set initial password without adding to history (first password)
            user.set_password(password, add_to_history=False)
            
            db.session.add(user)
            db.session.commit()
            
            # Now add the first password to history after user has an ID
            from ..models import PasswordHistory
            max_history = int(os.getenv('PASSWORD_HISTORY_LENGTH', 5))
            PasswordHistory.add_password(user.id, user.password_hash, max_history)
            
            # Log successful registration with GDPR consent information
            AuditService.log_registration(username, email, success=True)
            AuditService.log_action(
                action_type=AuditActionType.COMPLIANCE_EVENT,
                action_description=f"User '{username}' provided GDPR consent during registration",
                resource_type="user",
                resource_id=username,
                details={
                    "privacy_consent": privacy_consent,
                    "terms_consent": terms_consent,
                    "consent_timestamp": datetime.datetime.now().isoformat(),
                    "ip_address": request.remote_addr
                }
            )
            
            # Send verification email
            from ..email_service import email_service
            email_sent = email_service.send_verification_email(user.email, user.get_full_name() or user.username)
            
            if email_sent:
                flash('Registration successful! Please check your email to verify your account.', 'success')
                AuditService.log_action(
                    action_type=AuditActionType.ACCOUNT_ACTION,
                    action_description=f"Verification email sent to {email}",
                    resource_type="user",
                    resource_id=username
                )
            else:
                flash('Registration successful, but we could not send verification email. Please contact support.', 'warning')
                AuditService.log_action(
                    action_type=AuditActionType.ERROR,
                    action_description=f"Failed to send verification email to {email}",
                    resource_type="user",
                    resource_id=username
                )
            
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
            
            if not user.is_verified:
                # Log failed login due to unverified email
                AuditService.log_login(username_or_email, success=False, error_message="Email not verified")
                flash('Please verify your email address before logging in. Check your inbox for the verification link.', 'warning')
                flash(f'<a href="{url_for("auth.resend_verification", email=user.email)}">Resend verification email</a>', 'info')
                return render_template('auth/login.html')
            
            # Update login statistics
            user.last_login = datetime.datetime.now()
            user.login_count = (user.login_count or 0) + 1
            db.session.commit()
            
            login_user(user, remember=remember_me)
            
            # Create enhanced secure session
            session_token = session_service.create_session(
                user_id=user.id,
                user_agent=request.headers.get('User-Agent'),
                ip_address=request.remote_addr,
                remember_me=remember_me
            )
            
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
    
    # Destroy enhanced session
    session_service.destroy_session()
    
    current_app.logger.info("🚪 LOGOUT ROUTE: logout_user() completed")
    
    flash('You have been logged out successfully.', 'info')
    current_app.logger.info("🚪 LOGOUT ROUTE: Returning redirect")
    return redirect(url_for('main.index'))

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    import time
    cache_bust = str(int(time.time()))
    return render_template('auth/profile.html', user=current_user, cache_bust=cache_bust)

@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile"""
    if request.method == 'POST':
        # Get form data
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        organization = request.form.get('organization', '').strip()
        timezone_preference = request.form.get('timezone_preference', '').strip()
        time_format_preference = request.form.get('time_format_preference', '24h').strip()
        
        # Update user profile
        try:
            # Store old values for audit
            old_data = {
                'first_name': current_user.first_name,
                'last_name': current_user.last_name,
                'organization': current_user.organization,
                'timezone_preference': current_user.timezone_preference or 'Browser default',
                'time_format_preference': current_user.time_format_preference or '24h'
            }
            
            # Update user fields
            current_user.first_name = first_name
            current_user.last_name = last_name
            current_user.organization = organization
            
            # Handle timezone preference
            if timezone_preference:
                if current_user.set_timezone(timezone_preference):
                    current_app.logger.info(f"Updated timezone preference for user {current_user.id} to {timezone_preference}")
                else:
                    flash('Invalid timezone selected.', 'warning')
            else:
                # Empty string means use browser timezone (no user preference)
                current_user.timezone_preference = None
            
            # Handle time format preference
            if time_format_preference in ['12h', '24h']:
                current_user.time_format_preference = time_format_preference
                current_app.logger.info(f"Updated time format preference for user {current_user.id} to {time_format_preference}")
            else:
                current_user.time_format_preference = '24h'  # Default to 24h if invalid
            
            db.session.commit()
            
            # Prepare new values for audit
            new_data = {
                'first_name': first_name,
                'last_name': last_name,
                'organization': organization,
                'timezone_preference': timezone_preference or 'Browser default',
                'time_format_preference': time_format_preference
            }
            
            # Log profile update
            AuditService.log_profile_update(
                current_user.id,
                current_user.username,
                old_data,
                new_data
            )
            
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('auth.profile'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Profile update error: {e}")
            flash('Failed to update profile. Please try again.', 'error')
    
    return render_template('auth/edit_profile.html', user=current_user)

@auth_bp.route('/profile/sessions')
@login_required
def view_sessions():
    """View active sessions for current user"""
    try:
        current_app.logger.info(f"Retrieving sessions for user {current_user.id}")
        sessions = session_service.get_user_sessions(current_user.id)
        current_app.logger.info(f"Found {len(sessions)} sessions for user {current_user.id}")
        
        # Even if no sessions found, show the page (user might have sessions that aren't tracked)
        return render_template('auth/sessions.html', 
                             sessions=sessions, 
                             session_timeout=session_service.session_timeout)
    except Exception as e:
        current_app.logger.error(f"Error retrieving sessions for user {current_user.id}: {e}")
        import traceback
        current_app.logger.error(f"Traceback: {traceback.format_exc()}")
        flash('Unable to retrieve session information.', 'error')
        return redirect(url_for('auth.profile'))

@auth_bp.route('/profile/sessions/revoke', methods=['POST'])
@login_required
def revoke_sessions():
    """Revoke all other sessions for current user"""
    try:
        revoked_count = session_service.revoke_user_sessions(
            current_user.id, 
            except_current=True
        )
        
        flash(f'Successfully revoked {revoked_count} other sessions.', 'success')
        
        # Log session revocation
        AuditService.log_action(
            action_type=AuditActionType.SESSION_MANAGEMENT,
            user_id=current_user.id,
            action_description=f'User revoked {revoked_count} sessions',
            details={'revoked_count': revoked_count}
        )
        
    except Exception as e:
        current_app.logger.error(f"Error revoking sessions: {e}")
        flash('Failed to revoke sessions. Please try again.', 'error')
    
    return redirect(url_for('auth.view_sessions'))



@auth_bp.route('/profile/sessions/revoke/<session_id>', methods=['POST'])
@login_required
def revoke_individual_session(session_id):
    """Revoke a specific session for current user"""
    try:
        current_app.logger.info(f"Attempting to revoke session {session_id} for user {current_user.id}")
        
        # Get user's current sessions to validate the session belongs to them
        user_sessions = session_service.get_user_sessions(current_user.id)
        session_to_revoke = None
        
        # Find the session by partial ID (since we only show first 8 chars + ...)
        for sess in user_sessions:
            if sess['session_id'].startswith(session_id.replace('...', '')):
                session_to_revoke = sess
                break
        
        if not session_to_revoke:
            flash('Session not found or does not belong to you.', 'error')
            return redirect(url_for('auth.view_sessions'))
        
        # Prevent user from revoking their current session
        if session_to_revoke['is_current']:
            flash('Cannot revoke your current session. Use logout instead.', 'error')
            return redirect(url_for('auth.view_sessions'))
        
        # Get the full session token from Redis
        user_sessions_key = f"user_sessions:{current_user.id}"
        session_tokens = session_service.redis_client.smembers(user_sessions_key)
        
        full_token = None
        for token in session_tokens:
            if token.startswith(session_id.replace('...', '')):
                full_token = token
                break
        
        if not full_token:
            flash('Session not found in storage.', 'error')
            return redirect(url_for('auth.view_sessions'))
        
        # Revoke the specific session
        session_service.redis_client.delete(f"session:{full_token}")
        session_service.redis_client.srem(user_sessions_key, full_token)
        
        flash(f'Session {session_id} has been revoked successfully.', 'success')
        
        # Log session revocation
        AuditService.log_action(
            action_type=AuditActionType.SESSION_MANAGEMENT,
            user_id=current_user.id,
            action_description=f'User revoked individual session {session_id}',
            details={
                'revoked_session_id': session_id,
                'session_token': full_token[:8] + '...'
            }
        )
        
    except Exception as e:
        current_app.logger.error(f"Error revoking individual session: {e}")
        flash('Failed to revoke session. Please try again.', 'error')
    
    return redirect(url_for('auth.view_sessions'))

@auth_bp.route('/profile/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password with enhanced security"""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        errors = []
        
        if not current_password:
            errors.append("Current password is required")
        elif not current_user.check_password(current_password):
            errors.append("Current password is incorrect")
        
        if not new_password:
            errors.append("New password is required")
        else:
            valid, message = validate_password(new_password)
            if not valid:
                errors.append(message)
        
        if new_password != confirm_password:
            errors.append("New passwords do not match")
        
        # Check for password reuse
        if new_password and current_user.check_password_reuse(new_password):
            max_history = int(os.getenv('PASSWORD_HISTORY_LENGTH', 5))
            errors.append(f"You cannot reuse any of your last {max_history} passwords. Please choose a different password.")
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/change_password.html')
        
        try:
            # Update password
            current_user.set_password(new_password, add_to_history=True)
            db.session.commit()
            
            # Revoke all other sessions for security
            revoked_count = session_service.revoke_user_sessions(
                current_user.id, 
                except_current=True
            )
            
            # Rotate current session
            session_service._rotate_session_id()
            
            # Log password change
            AuditService.log_action(
                action_type=AuditActionType.PASSWORD_CHANGE,
                user_id=current_user.id,
                action_description='User changed password',
                details={
                    'sessions_revoked': revoked_count,
                    'session_rotated': True
                }
            )
            
            flash('Password changed successfully! Other sessions have been logged out for security.', 'success')
            return redirect(url_for('auth.profile'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Password change error: {e}")
            flash('Failed to change password. Please try again.', 'error')
    
    return render_template('auth/change_password.html')

@auth_bp.route('/admin/users')
@login_required
def admin_users():
    """Admin view of users (requires admin role)"""
    if current_user.role != UserRole.ADMIN:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    # Escalate privileges for this session
    session_service.escalate_privileges('admin')
    
    users = User.query.all()
    
    # Calculate user statistics for the template
   
    # Total users
    total_users = len(users)
    
    # Active users (is_active = True)
    active_users = len([u for u in users if u.is_active])
    
    # Admin users
    admin_users = len([u for u in users if u.role == UserRole.ADMIN])
    
    # Recent signups (users created in the last 30 days)
    thirty_days_ago = datetime.datetime.now() - datetime.timedelta(days=30)
    recent_signups = len([u for u in users if u.created_at >= thirty_days_ago])
    
    user_stats = {
        'total': total_users,
        'active': active_users,
        'admins': admin_users,
        'recent': recent_signups
    }
    
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


# Admin Message Management Routes
@auth_bp.route('/admin/messages')
@login_required
def admin_messages():
    """Admin view for managing site messages"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    from ..models import AdminMessage
    messages = AdminMessage.query.order_by(AdminMessage.created_at.desc()).all()
    return render_template('auth/admin_messages.html', messages=messages)


@auth_bp.route('/admin/messages/create', methods=['GET', 'POST'])
@login_required
def admin_create_message():
    """Create a new admin message"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        from ..models import AdminMessage
        
        title = request.form.get('title', '').strip()
        message = request.form.get('message', '').strip()
        message_type = request.form.get('message_type', 'info')
        expires_at_str = request.form.get('expires_at', '').strip()
        
        # Validation
        if not title or not message:
            flash('Title and message are required.', 'error')
            return render_template('auth/admin_create_message.html')
        
        # Parse expiration date if provided
        expires_at = None
        if expires_at_str:
            try:
                expires_at = datetime.strptime(expires_at_str, '%Y-%m-%dT%H:%M')
                if expires_at <= datetime.datetime.now():
                    flash('Expiration date must be in the future.', 'error')
                    return render_template('auth/admin_create_message.html')
            except ValueError:
                flash('Invalid expiration date format.', 'error')
                return render_template('auth/admin_create_message.html')
        
        # Create message
        admin_message = AdminMessage(
            title=title,
            message=message,
            message_type=message_type,
            created_by_id=current_user.id,
            expires_at=expires_at
        )
        
        try:
            db.session.add(admin_message)
            db.session.commit()
            
            # Log the action
            AuditService.log_admin_action(
                action_description=f"Created admin message: {title}",
                details={
                    "message_id": admin_message.id,
                    "message_type": message_type,
                    "expires_at": expires_at.isoformat() if expires_at else None
                }
            )
            
            flash('Message created successfully!', 'success')
            return redirect(url_for('auth.admin_messages'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating admin message: {e}")
            flash('Failed to create message. Please try again.', 'error')
    
    return render_template('auth/admin_create_message.html')


@auth_bp.route('/admin/messages/<int:message_id>/toggle', methods=['POST'])
@login_required
def admin_toggle_message(message_id):
    """Toggle message active status"""
    if not current_user.is_admin():
        return jsonify({'error': 'Access denied'}), 403
    
    from ..models import AdminMessage
    message = AdminMessage.query.get_or_404(message_id)
    
    message.is_active = not message.is_active
    
    try:
        db.session.commit()
        
        # Log the action
        action = "activated" if message.is_active else "deactivated"
        AuditService.log_admin_action(
            action_description=f"Admin message {action}: {message.title}",
            details={
                "message_id": message.id,
                "action": action,
                "new_status": message.is_active
            }
        )
        
        return jsonify({
            'success': True,
            'is_active': message.is_active,
            'status': 'Active' if message.is_active else 'Inactive'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error toggling message status: {e}")
        return jsonify({'error': 'Failed to update message'}), 500


@auth_bp.route('/admin/messages/<int:message_id>/delete', methods=['POST'])
@login_required
def admin_delete_message(message_id):
    """Delete an admin message"""
    if not current_user.is_admin():
        return jsonify({'error': 'Access denied'}), 403
    
    from ..models import AdminMessage
    message = AdminMessage.query.get_or_404(message_id)
    message_title = message.title
    
    try:
        db.session.delete(message)
        db.session.commit()
        
        # Log the action
        AuditService.log_admin_action(
            action_description=f"Deleted admin message: {message_title}",
            details={
                "message_id": message_id,
                "message_title": message_title
            }
        )
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting message: {e}")
        return jsonify({'error': 'Failed to delete message'}), 500


# ============================================================================
# EMAIL VERIFICATION ROUTES
# ============================================================================

@auth_bp.route('/verify/<token>')
@limiter.limit("10 per hour")
def verify_email(token):
    """Verify user's email address using token"""
    from ..email_service import email_service
    
    # Verify the token
    email = email_service.verify_token(token, salt='email-verification')
    
    if not email:
        flash('The verification link is invalid or has expired.', 'error')
        return redirect(url_for('auth.login'))
    
    # Find user by email
    user = User.query.filter_by(email=email.lower()).first()
    
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('auth.login'))
    
    if user.is_verified:
        flash('Email already verified. You can log in.', 'info')
        return redirect(url_for('auth.login'))
    
    # Verify the user
    try:
        user.is_verified = True
        db.session.commit()
        
        # Log verification
        AuditService.log_action(
            action_type=AuditActionType.ACCOUNT_ACTION,
            action_description=f"Email verified for user: {user.username}",
            resource_type="user",
            resource_id=user.username,
            details={
                "email": user.email,
                "verification_timestamp": datetime.datetime.now().isoformat()
            }
        )
        
        # Send confirmation email
        email_service.send_verification_success_email(user.email, user.get_full_name() or user.username)
        
        flash('Email verified successfully! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error verifying email: {e}")
        flash('An error occurred during verification. Please try again.', 'error')
        return redirect(url_for('auth.login'))


@auth_bp.route('/resend-verification', methods=['GET', 'POST'])
@limiter.limit("3 per hour")
def resend_verification():
    """Resend verification email"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Please enter your email address.', 'error')
            return render_template('auth/resend_verification.html')
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        if not user:
            # Don't reveal if email exists or not (security best practice)
            flash('If the email exists in our system, a verification link has been sent.', 'info')
            return render_template('auth/resend_verification.html')
        
        if user.is_verified:
            flash('This email is already verified. You can log in.', 'info')
            return redirect(url_for('auth.login'))
        
        # Send verification email
        from ..email_service import email_service
        email_sent = email_service.send_verification_email(user.email, user.get_full_name() or user.username)
        
        if email_sent:
            AuditService.log_action(
                action_type=AuditActionType.ACCOUNT_ACTION,
                action_description=f"Verification email resent to {email}",
                resource_type="user",
                resource_id=user.username
            )
            flash('Verification email sent! Please check your inbox.', 'success')
        else:
            flash('Failed to send verification email. Please try again later.', 'error')
        
        return render_template('auth/resend_verification.html')
    
    # GET request - check if email provided in query string
    email = request.args.get('email', '')
    return render_template('auth/resend_verification.html', email=email)


@auth_bp.route('/verify-status')
@login_required
def verify_status():
    """Show verification status for current user"""
    if current_user.is_verified:
        flash('Your email is already verified.', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/verify_status.html')


# ============================================================================
# PASSWORD RESET ROUTES
# ============================================================================

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
@limiter.limit("3 per hour")
def forgot_password():
    """Request password reset email"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Please enter your email address.', 'error')
            return render_template('auth/forgot_password.html')
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        if not user:
            # Don't reveal if email exists or not (security best practice)
            flash('If the email exists in our system, a password reset link has been sent.', 'info')
            AuditService.log_action(
                action_type=AuditActionType.ACCOUNT_ACTION,
                action_description=f"Password reset attempted for non-existent email: {email}",
                resource_type="user",
                resource_id="unknown"
            )
            return render_template('auth/forgot_password.html')
        
        # Send password reset email
        from ..email_service import email_service
        email_sent = email_service.send_password_reset_email(user.email, user.get_full_name() or user.username)
        
        if email_sent:
            AuditService.log_action(
                action_type=AuditActionType.ACCOUNT_ACTION,
                action_description=f"Password reset email sent to {email}",
                resource_type="user",
                resource_id=user.username
            )
            flash('If the email exists in our system, a password reset link has been sent.', 'info')
        else:
            flash('Failed to send password reset email. Please try again later.', 'error')
        
        return render_template('auth/forgot_password.html')
    
    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
@limiter.limit("5 per hour")
def reset_password(token):
    """Reset password using token"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    from ..email_service import email_service
    
    # Verify the token
    email = email_service.verify_token(
        token, 
        salt='password-reset',
        max_age=current_app.config.get('PASSWORD_RESET_TOKEN_MAX_AGE', 3600)
    )
    
    if not email:
        flash('The password reset link is invalid or has expired.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    # Find user by email
    user = User.query.filter_by(email=email.lower()).first()
    
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        errors = []
        
        if not password:
            errors.append("Password is required")
        else:
            valid, message = validate_password(password)
            if not valid:
                errors.append(message)
        
        if password != confirm_password:
            errors.append("Passwords do not match")
        
        # Check for password reuse
        if password and user.check_password_reuse(password):
            max_history = int(os.getenv('PASSWORD_HISTORY_LENGTH', 5))
            errors.append(f"You cannot reuse any of your last {max_history} passwords. Please choose a different password.")
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/reset_password.html', token=token)
        
        # Update password
        try:
            user.set_password(password, add_to_history=True)
            db.session.commit()
            
            # Log successful password reset
            AuditService.log_action(
                action_type=AuditActionType.ACCOUNT_ACTION,
                action_description=f"Password reset completed for user: {user.username}",
                resource_type="user",
                resource_id=user.username,
                details={
                    "email": user.email,
                    "reset_timestamp": datetime.datetime.now().isoformat()
                }
            )
            
            flash('Your password has been reset successfully! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error resetting password: {e}")
            flash('An error occurred while resetting your password. Please try again.', 'error')
            return render_template('auth/reset_password.html', token=token)
    
    return render_template('auth/reset_password.html', token=token)
