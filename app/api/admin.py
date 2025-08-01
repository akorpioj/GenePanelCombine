"""
Admin API endpoints
"""

from flask import request
from flask_restx import Namespace, Resource
from flask_login import login_required, current_user
from datetime import datetime
from ..models import AdminMessage, AuditLog, AuditActionType, db
from ..extensions import limiter
from ..audit_service import AuditService
from .models import (
    admin_message_model, admin_message_create_model,
    error_response_model, success_response_model
)

ns = Namespace('admin', description='Administrative operations')

@ns.route('/messages')
class AdminMessageList(Resource):
    @ns.doc('get_admin_messages')
    @ns.marshal_list_with(admin_message_model)
    @ns.response(200, 'Success')
    @ns.response(403, 'Access denied', error_response_model)
    @ns.response(500, 'Internal server error', error_response_model)
    @login_required
    @limiter.limit("10 per minute")
    def get(self):
        """Get all admin messages"""
        try:
            if not current_user.is_admin():
                ns.abort(403, "Admin privileges required")
            
            messages = AdminMessage.query.order_by(AdminMessage.created_at.desc()).all()
            
            # Convert to dict format with creator info
            message_list = []
            for message in messages:
                message_dict = {
                    'id': message.id,
                    'title': message.title,
                    'message': message.message,
                    'message_type': message.message_type,
                    'is_active': message.is_active,
                    'created_at': message.created_at.isoformat() if message.created_at else None,
                    'expires_at': message.expires_at.isoformat() if message.expires_at else None,
                    'created_by': {
                        'id': message.created_by.id,
                        'username': message.created_by.username,
                        'email': message.created_by.email
                    } if message.created_by else None
                }
                message_list.append(message_dict)
            
            # Log admin action
            AuditService.log_admin_action(
                action_description="Retrieved admin messages via API",
                details={
                    "message_count": len(message_list)
                }
            )
            
            return message_list
            
        except Exception as e:
            ns.abort(500, f"Failed to retrieve admin messages: {str(e)}")
    
    @ns.doc('create_admin_message')
    @ns.expect(admin_message_create_model)
    @ns.marshal_with(success_response_model)
    @ns.response(201, 'Message created successfully')
    @ns.response(400, 'Invalid input', error_response_model)
    @ns.response(403, 'Access denied', error_response_model)
    @ns.response(500, 'Internal server error', error_response_model)
    @login_required
    @limiter.limit("5 per minute")
    def post(self):
        """Create a new admin message"""
        try:
            if not current_user.is_admin():
                ns.abort(403, "Admin privileges required")
            
            data = request.get_json()
            
            # Validate required fields
            if not data.get('title') or not data.get('message'):
                ns.abort(400, "Title and message are required")
            
            title = data['title'].strip()
            message = data['message'].strip()
            message_type = data.get('message_type', 'info')
            expires_at_str = data.get('expires_at')
            
            # Validate message type
            valid_types = ['info', 'warning', 'error', 'success']
            if message_type not in valid_types:
                ns.abort(400, f"Invalid message type. Must be one of: {', '.join(valid_types)}")
            
            # Parse expiration date
            expires_at = None
            if expires_at_str:
                try:
                    expires_at = datetime.strptime(expires_at_str, '%Y-%m-%d')
                    if expires_at <= datetime.utcnow():
                        ns.abort(400, "Expiration date must be in the future")
                except ValueError:
                    ns.abort(400, "Invalid expiration date format. Use YYYY-MM-DD")
            
            # Create message
            admin_message = AdminMessage(
                title=title,
                message=message,
                message_type=message_type,
                created_by_id=current_user.id,
                expires_at=expires_at
            )
            
            db.session.add(admin_message)
            db.session.commit()
            
            # Log the action
            AuditService.log_admin_action(
                action_description=f"Created admin message via API: {title}",
                details={
                    "message_id": admin_message.id,
                    "message_type": message_type,
                    "expires_at": expires_at.isoformat() if expires_at else None
                }
            )
            
            return {
                'success': True,
                'message': 'Admin message created successfully',
                'message_id': admin_message.id
            }, 201
            
        except Exception as e:
            db.session.rollback()
            ns.abort(500, f"Failed to create admin message: {str(e)}")

@ns.route('/messages/<int:message_id>')
class AdminMessageDetails(Resource):
    @ns.doc('get_admin_message')
    @ns.marshal_with(admin_message_model)
    @ns.response(200, 'Success')
    @ns.response(403, 'Access denied', error_response_model)
    @ns.response(404, 'Message not found', error_response_model)
    @ns.response(500, 'Internal server error', error_response_model)
    @login_required
    @limiter.limit("20 per minute")
    def get(self, message_id):
        """Get specific admin message"""
        try:
            if not current_user.is_admin():
                ns.abort(403, "Admin privileges required")
            
            message = AdminMessage.query.get(message_id)
            if not message:
                ns.abort(404, "Message not found")
            
            return {
                'id': message.id,
                'title': message.title,
                'message': message.message,
                'message_type': message.message_type,
                'is_active': message.is_active,
                'created_at': message.created_at.isoformat() if message.created_at else None,
                'expires_at': message.expires_at.isoformat() if message.expires_at else None,
                'created_by': {
                    'id': message.created_by.id,
                    'username': message.created_by.username,
                    'email': message.created_by.email
                } if message.created_by else None
            }
            
        except Exception as e:
            ns.abort(500, f"Failed to get admin message: {str(e)}")
    
    @ns.doc('delete_admin_message')
    @ns.marshal_with(success_response_model)
    @ns.response(200, 'Message deleted successfully')
    @ns.response(403, 'Access denied', error_response_model)
    @ns.response(404, 'Message not found', error_response_model)
    @ns.response(500, 'Internal server error', error_response_model)
    @login_required
    @limiter.limit("5 per minute")
    def delete(self, message_id):
        """Delete an admin message"""
        try:
            if not current_user.is_admin():
                ns.abort(403, "Admin privileges required")
            
            message = AdminMessage.query.get(message_id)
            if not message:
                ns.abort(404, "Message not found")
            
            title = message.title
            db.session.delete(message)
            db.session.commit()
            
            # Log the action
            AuditService.log_admin_action(
                action_description=f"Deleted admin message via API: {title}",
                details={
                    "message_id": message_id,
                    "message_title": title
                }
            )
            
            return {
                'success': True,
                'message': f'Admin message "{title}" deleted successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            ns.abort(500, f"Failed to delete admin message: {str(e)}")

@ns.route('/messages/<int:message_id>/toggle')
class AdminMessageToggle(Resource):
    @ns.doc('toggle_admin_message')
    @ns.marshal_with(success_response_model)
    @ns.response(200, 'Message toggled successfully')
    @ns.response(403, 'Access denied', error_response_model)
    @ns.response(404, 'Message not found', error_response_model)
    @ns.response(500, 'Internal server error', error_response_model)
    @login_required
    @limiter.limit("10 per minute")
    def post(self, message_id):
        """Toggle admin message active status"""
        try:
            if not current_user.is_admin():
                ns.abort(403, "Admin privileges required")
            
            message = AdminMessage.query.get(message_id)
            if not message:
                ns.abort(404, "Message not found")
            
            old_status = message.is_active
            message.is_active = not message.is_active
            db.session.commit()
            
            status_text = "activated" if message.is_active else "deactivated"
            
            # Log the action
            AuditService.log_admin_action(
                action_description=f"Toggled admin message via API: {message.title} ({status_text})",
                details={
                    "message_id": message_id,
                    "message_title": message.title,
                    "old_status": old_status,
                    "new_status": message.is_active
                }
            )
            
            return {
                'success': True,
                'message': f'Message "{message.title}" {status_text} successfully',
                'is_active': message.is_active
            }
            
        except Exception as e:
            db.session.rollback()
            ns.abort(500, f"Failed to toggle admin message: {str(e)}")

@ns.route('/audit-logs')
class AuditLogList(Resource):
    @ns.doc('get_audit_logs')
    @ns.param('page', 'Page number', type='int', default=1)
    @ns.param('per_page', 'Items per page (max 100)', type='int', default=50)
    @ns.param('action_type', 'Filter by action type')
    @ns.param('username', 'Filter by username')
    @ns.param('date_from', 'Filter from date (YYYY-MM-DD)')
    @ns.param('date_to', 'Filter to date (YYYY-MM-DD)')
    @ns.param('success', 'Filter by success status (true/false)')
    @ns.response(200, 'Success')
    @ns.response(403, 'Access denied', error_response_model)
    @ns.response(500, 'Internal server error', error_response_model)
    @login_required
    @limiter.limit("10 per minute")
    def get(self):
        """Get audit logs with filtering and pagination"""
        try:
            if not current_user.is_admin():
                ns.abort(403, "Admin privileges required")
            
            # Get pagination parameters
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 50, type=int), 100)
            
            # Get filter parameters
            action_type = request.args.get('action_type', '')
            username = request.args.get('username', '')
            date_from = request.args.get('date_from', '')
            date_to = request.args.get('date_to', '')
            success_filter = request.args.get('success', '')
            
            # Build query
            query = AuditLog.query
            
            # Apply filters
            if action_type:
                try:
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
            
            # Order by timestamp (newest first)
            query = query.order_by(AuditLog.timestamp.desc())
            
            # Paginate
            audit_logs_paginated = query.paginate(
                page=page, 
                per_page=per_page, 
                error_out=False
            )
            
            # Convert to dict format
            logs = []
            for log in audit_logs_paginated.items:
                log_dict = {
                    'id': log.id,
                    'timestamp': log.timestamp.isoformat() if log.timestamp else None,
                    'user_id': log.user_id,
                    'username': log.username,
                    'action_type': log.action_type.value if log.action_type else None,
                    'description': log.description,
                    'ip_address': log.ip_address,
                    'user_agent': log.user_agent,
                    'success': log.success,
                    'error_message': log.error_message,
                    'details': log.details
                }
                logs.append(log_dict)
            
            # Log admin action
            AuditService.log_admin_action(
                action_description="Retrieved audit logs via API",
                details={
                    "filters": {
                        "action_type": action_type,
                        "username": username,
                        "date_from": date_from,
                        "date_to": date_to,
                        "success": success_filter
                    },
                    "page": page,
                    "per_page": per_page,
                    "total_results": audit_logs_paginated.total
                }
            )
            
            return {
                'logs': logs,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': audit_logs_paginated.total,
                    'pages': audit_logs_paginated.pages,
                    'has_next': audit_logs_paginated.has_next,
                    'has_prev': audit_logs_paginated.has_prev,
                    'next_num': audit_logs_paginated.next_num,
                    'prev_num': audit_logs_paginated.prev_num
                },
                'filters': {
                    'action_type': action_type,
                    'username': username,
                    'date_from': date_from,
                    'date_to': date_to,
                    'success': success_filter
                }
            }
            
        except Exception as e:
            ns.abort(500, f"Failed to retrieve audit logs: {str(e)}")
