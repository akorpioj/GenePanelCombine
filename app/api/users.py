"""
Users API endpoints
"""

from flask import request
from flask_restx import Namespace, Resource
from flask_login import login_required, current_user
from ..models import User, UserRole
from ..extensions import limiter
from ..audit_service import AuditService
from .models import (
    user_model, user_list_model, user_update_model,
    error_response_model, success_response_model
)

ns = Namespace('users', description='User management operations')

@ns.route('')
class UserList(Resource):
    @ns.doc('get_users')
    @ns.marshal_with(user_list_model)
    @ns.response(200, 'Success')
    @ns.response(403, 'Access denied', error_response_model)
    @ns.response(500, 'Internal server error', error_response_model)
    @login_required
    @limiter.limit("10 per minute")
    def get(self):
        """Get list of all users (Admin only)"""
        try:
            if not current_user.is_admin():
                ns.abort(403, "Admin privileges required")
            
            users = User.query.all()
            
            # Convert to dict format
            user_list = []
            for user in users:
                user_dict = user.to_dict()
                user_list.append(user_dict)
            
            # Calculate statistics
            total_users = len(users)
            active_users = len([u for u in users if u.is_active])
            admin_users = len([u for u in users if u.role == UserRole.ADMIN])
            
            # Log admin action
            AuditService.log_admin_action(
                action_description="Retrieved user list via API",
                details={
                    "total_users": total_users,
                    "active_users": active_users,
                    "admin_users": admin_users
                }
            )
            
            return {
                'users': user_list,
                'total': total_users,
                'active': active_users,
                'admins': admin_users
            }
            
        except Exception as e:
            ns.abort(500, f"Failed to retrieve users: {str(e)}")

@ns.route('/<int:user_id>')
class UserDetails(Resource):
    @ns.doc('get_user')
    @ns.marshal_with(user_model)
    @ns.response(200, 'Success')
    @ns.response(403, 'Access denied', error_response_model)
    @ns.response(404, 'User not found', error_response_model)
    @ns.response(500, 'Internal server error', error_response_model)
    @login_required
    @limiter.limit("20 per minute")
    def get(self, user_id):
        """Get user details"""
        try:
            # Users can only view their own details unless they're admin
            if not current_user.is_admin() and current_user.id != user_id:
                ns.abort(403, "Access denied")
            
            user = User.query.get(user_id)
            if not user:
                ns.abort(404, "User not found")
            
            # Log user view
            AuditService.log_view(
                resource_type="user",
                resource_id=str(user_id),
                description=f"Viewed user details: {user.username}",
                details={
                    "target_user_id": user_id,
                    "target_username": user.username
                }
            )
            
            return user.to_dict()
            
        except Exception as e:
            ns.abort(500, f"Failed to get user details: {str(e)}")
    
    @ns.doc('update_user')
    @ns.expect(user_update_model)
    @ns.marshal_with(success_response_model)
    @ns.response(200, 'Success')
    @ns.response(403, 'Access denied', error_response_model)
    @ns.response(404, 'User not found', error_response_model)
    @ns.response(500, 'Internal server error', error_response_model)
    @login_required
    @limiter.limit("10 per minute")
    def put(self, user_id):
        """Update user details (Admin only)"""
        try:
            if not current_user.is_admin():
                ns.abort(403, "Admin privileges required")
            
            user = User.query.get(user_id)
            if not user:
                ns.abort(404, "User not found")
            
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
                    ns.abort(400, "Invalid role")
            
            if 'is_active' in data:
                if user.is_active != data['is_active']:
                    user.is_active = data['is_active']
                    status = 'activated' if data['is_active'] else 'deactivated'
                    changes_made.append(f"account {status}")
            
            from ..models import db
            db.session.commit()
            
            # Log user update if changes were made
            if changes_made:
                new_data = {
                    'role': user.role.value,
                    'is_active': user.is_active
                }
                AuditService.log_admin_action(
                    action_description=f"Updated user '{user.username}' via API: {', '.join(changes_made)}",
                    target_user_id=user.id,
                    details={
                        "action": "user_update",
                        "changes": changes_made,
                        "target_username": user.username,
                        "old_values": old_data,
                        "new_values": new_data
                    }
                )
            
            return {
                'success': True,
                'message': f'User updated successfully. Changes: {", ".join(changes_made)}' if changes_made else 'No changes made'
            }
            
        except Exception as e:
            from ..models import db
            db.session.rollback()
            ns.abort(500, f"Failed to update user: {str(e)}")
    
    @ns.doc('delete_user')
    @ns.marshal_with(success_response_model)
    @ns.response(200, 'Success')
    @ns.response(403, 'Access denied', error_response_model)
    @ns.response(404, 'User not found', error_response_model)
    @ns.response(500, 'Internal server error', error_response_model)
    @login_required
    @limiter.limit("5 per minute")
    def delete(self, user_id):
        """Deactivate user (Admin only)"""
        try:
            if not current_user.is_admin():
                ns.abort(403, "Admin privileges required")
            
            user = User.query.get(user_id)
            if not user:
                ns.abort(404, "User not found")
            
            # Don't allow deleting the last admin
            if user.role == UserRole.ADMIN:
                admin_count = User.query.filter_by(role=UserRole.ADMIN, is_active=True).count()
                if admin_count <= 1:
                    ns.abort(400, "Cannot deactivate the last admin user")
            
            user.is_active = False
            from ..models import db
            db.session.commit()
            
            # Log user deactivation
            AuditService.log_admin_action(
                action_description=f"Deactivated user '{user.username}' via API",
                target_user_id=user.id,
                details={
                    "action": "user_deactivation",
                    "target_username": user.username
                }
            )
            
            return {
                'success': True,
                'message': f'User {user.username} deactivated successfully'
            }
            
        except Exception as e:
            from ..models import db
            db.session.rollback()
            ns.abort(500, f"Failed to deactivate user: {str(e)}")

@ns.route('/current')
class CurrentUser(Resource):
    @ns.doc('get_current_user')
    @ns.marshal_with(user_model)
    @ns.response(200, 'Success')
    @ns.response(401, 'Not authenticated', error_response_model)
    @ns.response(500, 'Internal server error', error_response_model)
    @login_required
    @limiter.limit("30 per minute")
    def get(self):
        """Get current authenticated user information"""
        try:
            return current_user.to_dict()
        except Exception as e:
            ns.abort(500, f"Failed to get current user: {str(e)}")

@ns.route('/check-username')
class CheckUsername(Resource):
    @ns.doc('check_username')
    @ns.param('username', 'Username to check', required=True)
    @ns.response(200, 'Success')
    @ns.response(400, 'Missing username parameter', error_response_model)
    @ns.response(500, 'Internal server error', error_response_model)
    @limiter.limit("20 per minute")
    def get(self):
        """Check if username is available"""
        try:
            username = request.args.get('username', '').strip()
            if not username:
                ns.abort(400, "Username parameter is required")
            
            exists = User.query.filter_by(username=username).first() is not None
            
            return {
                'available': not exists,
                'message': 'Username is available' if not exists else 'Username already taken'
            }
            
        except Exception as e:
            ns.abort(500, f"Failed to check username: {str(e)}")

@ns.route('/check-email')
class CheckEmail(Resource):
    @ns.doc('check_email')
    @ns.param('email', 'Email to check', required=True)
    @ns.response(200, 'Success')
    @ns.response(400, 'Missing email parameter', error_response_model)
    @ns.response(500, 'Internal server error', error_response_model)
    @limiter.limit("20 per minute")
    def get(self):
        """Check if email is available"""
        try:
            email = request.args.get('email', '').strip().lower()
            if not email:
                ns.abort(400, "Email parameter is required")
            
            # Basic email validation
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                return {
                    'available': False,
                    'message': 'Invalid email format'
                }
            
            exists = User.query.filter_by(email=email).first() is not None
            
            return {
                'available': not exists,
                'message': 'Email is available' if not exists else 'Email already registered'
            }
            
        except Exception as e:
            ns.abort(500, f"Failed to check email: {str(e)}")
