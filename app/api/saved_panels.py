"""
Saved Panels API endpoints
"""

from flask import request, jsonify, current_app
from flask_restx import Namespace, Resource
from flask_login import current_user
from sqlalchemy import desc, asc
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import json
import os
import secrets

from ..models import (
    SavedPanel, PanelVersion, PanelGene, PanelShare, PanelChange,
    PanelStatus, PanelVisibility, ChangeType, SharePermission, AuditActionType, db
)
from ..extensions import limiter
from ..audit_service import AuditService
from .auth_decorators import api_login_required
from .models import (
    saved_panel_model, saved_panel_list_model, saved_panel_create_model,
    saved_panel_update_model, panel_version_model, panel_version_list_model,
    panel_share_model, panel_share_create_model, saved_panel_gene_model,
    error_response_model, success_response_model
)

ns = Namespace('saved-panels', description='Saved panel management operations')

@ns.route('/test')
class SavedPanelTest(Resource):
    @ns.doc('test_auth')
    @api_login_required
    def get(self):
        """Test authentication for saved panels namespace"""
        return {'message': 'Authentication working', 'user': current_user.username}

@ns.route('/')
class SavedPanelList(Resource):
    @ns.doc('get_saved_panels')
    @ns.response(200, 'Success')
    @ns.response(401, 'Authentication required', error_response_model)
    @ns.response(500, 'Internal server error', error_response_model)
    @api_login_required
    @limiter.limit("30 per minute")
    def get(self):
        """Get list of user's saved panels"""
        try:
            # Get query parameters
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 10, type=int), 100)
            status = request.args.get('status')
            visibility = request.args.get('visibility')
            search = request.args.get('search', '').strip()
            sort_by = request.args.get('sort_by', 'updated_at')
            sort_order = request.args.get('sort_order', 'desc')
            
            # Build query
            query = SavedPanel.query.filter_by(owner_id=current_user.id)
            
            # Apply filters
            if status:
                try:
                    status_enum = PanelStatus(status.upper())
                    query = query.filter_by(status=status_enum)
                except ValueError:
                    ns.abort(400, f"Invalid status: {status}")
            
            if visibility:
                try:
                    visibility_enum = PanelVisibility(visibility.upper())
                    query = query.filter_by(visibility=visibility_enum)
                except ValueError:
                    ns.abort(400, f"Invalid visibility: {visibility}")
            
            if search:
                query = query.filter(
                    db.or_(
                        SavedPanel.name.ilike(f'%{search}%'),
                        SavedPanel.description.ilike(f'%{search}%'),
                        SavedPanel.tags.ilike(f'%{search}%')
                    )
                )
            
            # Apply sorting
            if sort_by == 'name':
                order_column = SavedPanel.name
            elif sort_by == 'created_at':
                order_column = SavedPanel.created_at
            elif sort_by == 'gene_count':
                order_column = SavedPanel.gene_count
            else:
                order_column = SavedPanel.updated_at
            
            if sort_order == 'asc':
                query = query.order_by(asc(order_column))
            else:
                query = query.order_by(desc(order_column))
            
            # Paginate
            panels_pagination = query.paginate(
                page=page, 
                per_page=per_page, 
                error_out=False
            )
            
            # Convert to dict format
            panels_list = []
            for panel in panels_pagination.items:
                panel_dict = {
                    'id': panel.id,
                    'name': panel.name,
                    'description': panel.description,
                    'tags': panel.tags,
                    'status': panel.status.value,
                    'visibility': panel.visibility.value,
                    'gene_count': panel.gene_count,
                    'version_count': panel.version_count,
                    'created_at': panel.created_at.isoformat(),
                    'updated_at': panel.updated_at.isoformat(),
                    'last_accessed_at': panel.last_accessed_at.isoformat() if panel.last_accessed_at else None,
                    'source_type': panel.source_type,
                    'source_reference': panel.source_reference,
                    'storage_backend': panel.storage_backend,
                    'current_version_id': panel.current_version_id
                }
                panels_list.append(panel_dict)
            
            # Log access
            AuditService.log_action(
                action_type=AuditActionType.PANEL_LIST,
                action_description=f"Retrieved saved panels list via API (page {page})",
                details={
                    "page": page,
                    "per_page": per_page,
                    "total_panels": panels_pagination.total,
                    "search": search,
                    "status_filter": status,
                    "visibility_filter": visibility
                }
            )
            
            return {
                'panels': panels_list,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': panels_pagination.total,
                    'pages': panels_pagination.pages,
                    'has_next': panels_pagination.has_next,
                    'has_prev': panels_pagination.has_prev
                },
                'total': panels_pagination.total
            }
            
        except Exception as e:
            current_app.logger.error(f"Error retrieving saved panels: {str(e)}")
            ns.abort(500, "Internal server error")
    
    @ns.doc('create_saved_panel')
    @ns.expect(saved_panel_create_model)
    @ns.marshal_with(saved_panel_model)
    @ns.response(201, 'Panel created successfully')
    @ns.response(400, 'Invalid input', error_response_model)
    @ns.response(401, 'Authentication required', error_response_model)
    @ns.response(500, 'Internal server error', error_response_model)
    @api_login_required
    @limiter.limit("5 per minute")
    def post(self):
        """Create a new saved panel"""
        try:
            data = request.get_json()
            
            # Validate required fields
            if not data.get('name'):
                ns.abort(400, "Panel name is required")
            
            if not data.get('genes') or not isinstance(data['genes'], list):
                ns.abort(400, "Genes list is required")
            
            # Check for duplicate panel name for this user
            existing_panel = SavedPanel.query.filter_by(
                owner_id=current_user.id,
                name=data['name']
            ).first()
            
            if existing_panel:
                ns.abort(400, f"Panel with name '{data['name']}' already exists")
            
            # Create saved panel
            panel = SavedPanel(
                name=data['name'],
                description=data.get('description', ''),
                tags=data.get('tags', ''),
                owner_id=current_user.id,
                status=PanelStatus(data.get('status', 'ACTIVE').upper()),
                visibility=PanelVisibility(data.get('visibility', 'PRIVATE').upper()),
                gene_count=len(data['genes']),
                source_type=data.get('source_type', 'manual'),
                source_reference=data.get('source_reference', ''),
                storage_backend='gcs'  # Default to Google Cloud Storage
            )
            
            db.session.add(panel)
            db.session.flush()  # Get the panel ID
            
            # Create initial version
            version = PanelVersion(
                panel_id=panel.id,
                version_number=1,
                comment=data.get('version_comment', 'Initial version'),
                created_by_id=current_user.id,
                gene_count=len(data['genes']),
                changes_summary=f"Created panel with {len(data['genes'])} genes"
            )
            
            db.session.add(version)
            db.session.flush()  # Get the version ID
            
            # Set current version
            panel.current_version_id = version.id
            
            # Add genes
            for gene_data in data['genes']:
                gene = PanelGene(
                    panel_id=panel.id,
                    gene_symbol=gene_data.get('gene_symbol', ''),
                    gene_name=gene_data.get('gene_name', ''),
                    ensembl_id=gene_data.get('ensembl_id', ''),
                    hgnc_id=gene_data.get('hgnc_id', ''),
                    confidence_level=gene_data.get('confidence_level', ''),
                    mode_of_inheritance=gene_data.get('mode_of_inheritance', ''),
                    phenotype=gene_data.get('phenotype', ''),
                    evidence_level=gene_data.get('evidence_level', ''),
                    source_panel_id=gene_data.get('source_panel_id', ''),
                    source_list_type=gene_data.get('source_list_type', ''),
                    added_by_id=current_user.id,
                    user_notes=gene_data.get('user_notes', ''),
                    custom_confidence=gene_data.get('custom_confidence', '')
                )
                db.session.add(gene)
            
            # Record creation change
            change = PanelChange(
                panel_id=panel.id,
                version_id=version.id,
                change_type=ChangeType.PANEL_CREATED,
                target_type='panel',
                target_id=str(panel.id),
                changed_by_id=current_user.id,
                change_reason=data.get('version_comment', 'Panel created')
            )
            change.new_value = {
                'panel_name': panel.name,
                'gene_count': panel.gene_count,
                'description': panel.description
            }
            db.session.add(change)
            
            db.session.commit()
            
            # Log creation
            AuditService.log_action(
                action_type=AuditActionType.PANEL_CREATE,
                action_description=f"Created saved panel '{panel.name}' via API",
                details={
                    "panel_id": panel.id,
                    "panel_name": panel.name,
                    "gene_count": panel.gene_count,
                    "status": panel.status.value,
                    "visibility": panel.visibility.value
                }
            )
            
            # Return created panel
            return {
                'id': panel.id,
                'name': panel.name,
                'description': panel.description,
                'tags': panel.tags,
                'status': panel.status.value,
                'visibility': panel.visibility.value,
                'gene_count': panel.gene_count,
                'version_count': panel.version_count,
                'created_at': panel.created_at.isoformat(),
                'updated_at': panel.updated_at.isoformat(),
                'source_type': panel.source_type,
                'source_reference': panel.source_reference,
                'storage_backend': panel.storage_backend,
                'current_version_id': panel.current_version_id
            }, 201
            
        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Database integrity error creating panel: {str(e)}")
            ns.abort(400, "Database constraint violation")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating saved panel: {str(e)}")
            ns.abort(500, "Internal server error")


@ns.route('/<int:panel_id>')
class SavedPanelResource(Resource):
    @ns.doc('get_saved_panel')
    @ns.marshal_with(saved_panel_model)
    @ns.response(200, 'Success')
    @ns.response(401, 'Authentication required', error_response_model)
    @ns.response(403, 'Access denied', error_response_model)
    @ns.response(404, 'Panel not found', error_response_model)
    @ns.response(500, 'Internal server error', error_response_model)
    @api_login_required
    @limiter.limit("30 per minute")
    def get(self, panel_id):
        """Get a specific saved panel with its genes"""
        try:
            # Get panel with ownership or sharing check
            panel = self._get_accessible_panel(panel_id, SharePermission.VIEW)
            
            # Update last accessed time if owner
            if panel.owner_id == current_user.id:
                panel.last_accessed_at = datetime.utcnow()
                db.session.commit()
            
            # Get genes
            genes = PanelGene.query.filter_by(
                panel_id=panel.id,
                is_active=True
            ).all()
            
            genes_list = []
            for gene in genes:
                gene_dict = {
                    'id': gene.id,
                    'gene_symbol': gene.gene_symbol,
                    'gene_name': gene.gene_name,
                    'ensembl_id': gene.ensembl_id,
                    'hgnc_id': gene.hgnc_id,
                    'confidence_level': gene.confidence_level,
                    'mode_of_inheritance': gene.mode_of_inheritance,
                    'phenotype': gene.phenotype,
                    'evidence_level': gene.evidence_level,
                    'source_panel_id': gene.source_panel_id,
                    'source_list_type': gene.source_list_type,
                    'user_notes': gene.user_notes,
                    'custom_confidence': gene.custom_confidence,
                    'is_modified': gene.is_modified,
                    'added_at': gene.added_at.isoformat()
                }
                genes_list.append(gene_dict)
            
            # Log access
            AuditService.log_action(
                action_type=AuditActionType.VIEW,
                action_description=f"Retrieved saved panel '{panel.name}' via API",
                details={
                    "panel_id": panel.id,
                    "panel_name": panel.name,
                    "gene_count": len(genes_list)
                }
            )
            
            return {
                'id': panel.id,
                'name': panel.name,
                'description': panel.description,
                'tags': panel.tags,
                'status': panel.status.value,
                'visibility': panel.visibility.value,
                'gene_count': panel.gene_count,
                'version_count': panel.version_count,
                'created_at': panel.created_at.isoformat(),
                'updated_at': panel.updated_at.isoformat(),
                'last_accessed_at': panel.last_accessed_at.isoformat() if panel.last_accessed_at else None,
                'source_type': panel.source_type,
                'source_reference': panel.source_reference,
                'storage_backend': panel.storage_backend,
                'current_version_id': panel.current_version_id,
                'owner': {
                    'id': panel.owner.id,
                    'username': panel.owner.username
                },
                'genes': genes_list
            }
            
        except Exception as e:
            current_app.logger.error(f"Error retrieving saved panel {panel_id}: {str(e)}")
            ns.abort(500, "Internal server error")
    
    @ns.doc('update_saved_panel')
    @ns.expect(saved_panel_update_model)
    @ns.marshal_with(saved_panel_model)
    @ns.response(200, 'Panel updated successfully')
    @ns.response(400, 'Invalid input', error_response_model)
    @ns.response(401, 'Authentication required', error_response_model)
    @ns.response(403, 'Access denied', error_response_model)
    @ns.response(404, 'Panel not found', error_response_model)
    @ns.response(500, 'Internal server error', error_response_model)
    @api_login_required
    @limiter.limit("10 per minute")
    def put(self, panel_id):
        """Update a saved panel"""
        try:
            # Get panel with edit access
            panel = self._get_accessible_panel(panel_id, SharePermission.EDIT)
            
            data = request.get_json()
            old_values = {}
            new_values = {}
            
            # Track changes for version history
            if 'name' in data and data['name'] != panel.name:
                old_values['name'] = panel.name
                new_values['name'] = data['name']
                panel.name = data['name']
            
            if 'description' in data and data['description'] != panel.description:
                old_values['description'] = panel.description
                new_values['description'] = data['description']
                panel.description = data['description']
            
            if 'tags' in data and data['tags'] != panel.tags:
                old_values['tags'] = panel.tags
                new_values['tags'] = data['tags']
                panel.tags = data['tags']
            
            if 'status' in data:
                try:
                    new_status = PanelStatus(data['status'].upper())
                    if new_status != panel.status:
                        old_values['status'] = panel.status.value
                        new_values['status'] = new_status.value
                        panel.status = new_status
                except ValueError:
                    ns.abort(400, f"Invalid status: {data['status']}")
            
            if 'visibility' in data:
                try:
                    new_visibility = PanelVisibility(data['visibility'].upper())
                    if new_visibility != panel.visibility:
                        old_values['visibility'] = panel.visibility.value
                        new_values['visibility'] = new_visibility.value
                        panel.visibility = new_visibility
                except ValueError:
                    ns.abort(400, f"Invalid visibility: {data['visibility']}")
            
            # Update timestamp
            panel.updated_at = datetime.utcnow()
            
            # Create new version if significant changes
            if old_values:
                version_number = panel.version_count + 1
                version = PanelVersion(
                    panel_id=panel.id,
                    version_number=version_number,
                    comment=data.get('version_comment', 'Panel metadata updated'),
                    created_by_id=current_user.id,
                    gene_count=panel.gene_count,
                    changes_summary=f"Updated: {', '.join(old_values.keys())}"
                )
                
                db.session.add(version)
                db.session.flush()
                
                # Update panel version info
                panel.version_count = version_number
                panel.current_version_id = version.id
                
                # Record change
                change = PanelChange(
                    panel_id=panel.id,
                    version_id=version.id,
                    change_type=ChangeType.METADATA_CHANGED,
                    target_type='panel',
                    target_id=str(panel.id),
                    changed_by_id=current_user.id,
                    change_reason=data.get('version_comment', 'Panel metadata updated')
                )
                change.old_value = old_values
                change.new_value = new_values
                db.session.add(change)
            
            db.session.commit()
            
            # Log update
            AuditService.log_action(
                action_type=AuditActionType.PANEL_UPDATE,
                action_description=f"Updated saved panel '{panel.name}' via API",
                details={
                    "panel_id": panel.id,
                    "panel_name": panel.name,
                    "changes": list(old_values.keys())
                }
            )
            
            return {
                'id': panel.id,
                'name': panel.name,
                'description': panel.description,
                'tags': panel.tags,
                'status': panel.status.value,
                'visibility': panel.visibility.value,
                'gene_count': panel.gene_count,
                'version_count': panel.version_count,
                'created_at': panel.created_at.isoformat(),
                'updated_at': panel.updated_at.isoformat(),
                'source_type': panel.source_type,
                'source_reference': panel.source_reference,
                'storage_backend': panel.storage_backend,
                'current_version_id': panel.current_version_id
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating saved panel {panel_id}: {str(e)}")
            ns.abort(500, "Internal server error")
    
    @ns.doc('delete_saved_panel')
    @ns.marshal_with(success_response_model)
    @ns.response(200, 'Panel deleted successfully')
    @ns.response(401, 'Authentication required', error_response_model)
    @ns.response(403, 'Access denied', error_response_model)
    @ns.response(404, 'Panel not found', error_response_model)
    @ns.response(500, 'Internal server error', error_response_model)
    @api_login_required
    @limiter.limit("5 per minute")
    def delete(self, panel_id):
        """Delete a saved panel (owner only)"""
        try:
            # Only owner can delete
            panel = SavedPanel.query.filter_by(
                id=panel_id,
                owner_id=current_user.id
            ).first()
            
            if not panel:
                ns.abort(404, "Panel not found or access denied")
            
            panel_name = panel.name
            
            # Clear the current_version_id first to avoid foreign key constraint issues
            panel.current_version_id = None
            db.session.flush()
            
            # Delete related records (cascade should handle this, but being explicit)
            PanelChange.query.filter_by(panel_id=panel.id).delete()
            PanelShare.query.filter_by(panel_id=panel.id).delete()
            PanelGene.query.filter_by(panel_id=panel.id).delete()
            PanelVersion.query.filter_by(panel_id=panel.id).delete()
            
            # Delete the panel
            db.session.delete(panel)
            db.session.commit()
            
            # Log deletion
            AuditService.log_action(
                action_type=AuditActionType.PANEL_DELETE,
                action_description=f"Deleted saved panel '{panel_name}' via API",
                details={
                    "panel_id": panel_id,
                    "panel_name": panel_name
                }
            )
            
            return {
                'success': True,
                'message': f"Panel '{panel_name}' deleted successfully"
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error deleting saved panel {panel_id}: {str(e)}")
            ns.abort(500, "Internal server error")
    
    def _get_accessible_panel(self, panel_id, required_permission):
        """Get a panel that the current user can access with the required permission"""
        # First check if user owns the panel
        panel = SavedPanel.query.filter_by(
            id=panel_id,
            owner_id=current_user.id
        ).first()
        
        if panel:
            return panel  # Owner has all permissions
        
        # Check if panel is shared with user
        share = PanelShare.query.join(SavedPanel).filter(
            SavedPanel.id == panel_id,
            PanelShare.shared_with_user_id == current_user.id,
            PanelShare.is_active == True
        ).first()
        
        if not share:
            ns.abort(404, "Panel not found or access denied")
        
        # Check if share has expired
        if share.expires_at and share.expires_at < datetime.utcnow():
            ns.abort(403, "Access to this panel has expired")
        
        # Check permission level
        if required_permission == SharePermission.ADMIN and share.permission_level != SharePermission.ADMIN:
            ns.abort(403, "Admin permission required")
        elif required_permission == SharePermission.EDIT and share.permission_level == SharePermission.VIEW:
            ns.abort(403, "Edit permission required")
        
        return share.panel


@ns.route('/<int:panel_id>/versions')
class PanelVersionList(Resource):
    @ns.doc('get_panel_versions')
    @ns.marshal_with(panel_version_list_model)
    @ns.response(200, 'Success')
    @ns.response(401, 'Authentication required', error_response_model)
    @ns.response(403, 'Access denied', error_response_model)
    @ns.response(404, 'Panel not found', error_response_model)
    @ns.response(500, 'Internal server error', error_response_model)
    @api_login_required
    @limiter.limit("30 per minute")
    def get(self, panel_id):
        """Get version history for a saved panel"""
        try:
            # Check access
            panel = SavedPanelResource()._get_accessible_panel(panel_id, SharePermission.VIEW)
            
            # Get versions
            versions = PanelVersion.query.filter_by(panel_id=panel.id).order_by(desc(PanelVersion.version_number)).all()
            
            versions_list = []
            for version in versions:
                version_dict = {
                    'id': version.id,
                    'version_number': version.version_number,
                    'comment': version.comment,
                    'gene_count': version.gene_count,
                    'changes_summary': version.changes_summary,
                    'storage_path': version.storage_path,
                    'created_at': version.created_at.isoformat(),
                    'created_by': {
                        'id': version.created_by.id,
                        'username': version.created_by.username
                    }
                }
                versions_list.append(version_dict)
            
            return {
                'panel_id': panel.id,
                'panel_name': panel.name,
                'versions': versions_list,
                'total': len(versions_list)
            }
            
        except Exception as e:
            current_app.logger.error(f"Error retrieving panel versions: {str(e)}")
            ns.abort(500, "Internal server error")


@ns.route('/<int:panel_id>/share')
class PanelShareResource(Resource):
    @ns.doc('share_panel')
    @ns.expect(panel_share_create_model)
    @ns.marshal_with(panel_share_model)
    @ns.response(201, 'Panel shared successfully')
    @ns.response(400, 'Invalid input', error_response_model)
    @ns.response(401, 'Authentication required', error_response_model)
    @ns.response(403, 'Access denied', error_response_model)
    @ns.response(404, 'Panel not found', error_response_model)
    @ns.response(500, 'Internal server error', error_response_model)
    @api_login_required
    @limiter.limit("10 per minute")
    def post(self, panel_id):
        """Share a panel with another user"""
        try:
            # Check access (only owner or admin can share)
            panel = SavedPanelResource()._get_accessible_panel(panel_id, SharePermission.ADMIN)
            
            data = request.get_json()
            
            # Validate required fields
            if not data.get('shared_with_user_id') and not data.get('create_public_link'):
                ns.abort(400, "Either shared_with_user_id or create_public_link must be provided")
            
            # Create share
            share = PanelShare(
                panel_id=panel.id,
                shared_by_id=current_user.id,
                permission_level=SharePermission(data.get('permission_level', 'VIEW').upper()),
                can_reshare=data.get('can_reshare', False)
            )
            
            # Set expiration if provided
            if data.get('expires_in_days'):
                share.expires_at = datetime.utcnow() + timedelta(days=data['expires_in_days'])
            
            # Handle specific user sharing
            if data.get('shared_with_user_id'):
                from ..models import User
                target_user = User.query.get(data['shared_with_user_id'])
                if not target_user:
                    ns.abort(400, "Target user not found")
                
                # Check for existing share
                existing_share = PanelShare.query.filter_by(
                    panel_id=panel.id,
                    shared_with_user_id=target_user.id,
                    is_active=True
                ).first()
                
                if existing_share:
                    ns.abort(400, "Panel already shared with this user")
                
                share.shared_with_user_id = target_user.id
            
            # Generate share token for public links or as backup
            share.share_token = secrets.token_urlsafe(32)
            
            db.session.add(share)
            db.session.commit()
            
            # Log sharing
            target_info = f"user {data.get('shared_with_user_id')}" if data.get('shared_with_user_id') else "public link"
            AuditService.log_action(
                action_type=AuditActionType.PANEL_SHARE,
                action_description=f"Shared panel '{panel.name}' with {target_info} via API",
                details={
                    "panel_id": panel.id,
                    "panel_name": panel.name,
                    "shared_with_user_id": data.get('shared_with_user_id'),
                    "permission_level": share.permission_level.value,
                    "expires_at": share.expires_at.isoformat() if share.expires_at else None
                }
            )
            
            return {
                'id': share.id,
                'panel_id': share.panel_id,
                'shared_with_user_id': share.shared_with_user_id,
                'permission_level': share.permission_level.value,
                'can_reshare': share.can_reshare,
                'is_active': share.is_active,
                'expires_at': share.expires_at.isoformat() if share.expires_at else None,
                'created_at': share.created_at.isoformat(),
                'share_token': share.share_token
            }, 201
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error sharing panel {panel_id}: {str(e)}")
            ns.abort(500, "Internal server error")


@ns.route('/shared')
class SharedPanelList(Resource):
    @ns.doc('get_shared_panels')
    @ns.marshal_with(saved_panel_list_model)
    @ns.response(200, 'Success')
    @ns.response(401, 'Authentication required', error_response_model)
    @ns.response(500, 'Internal server error', error_response_model)
    @api_login_required
    @limiter.limit("30 per minute")
    def get(self):
        """Get list of panels shared with the current user"""
        try:
            # Get panels shared with current user
            shared_panels = db.session.query(SavedPanel).join(PanelShare).filter(
                PanelShare.shared_with_user_id == current_user.id,
                PanelShare.is_active == True,
                db.or_(
                    PanelShare.expires_at.is_(None),
                    PanelShare.expires_at > datetime.utcnow()
                )
            ).all()
            
            panels_list = []
            for panel in shared_panels:
                # Get the share info
                share = PanelShare.query.filter_by(
                    panel_id=panel.id,
                    shared_with_user_id=current_user.id,
                    is_active=True
                ).first()
                
                panel_dict = {
                    'id': panel.id,
                    'name': panel.name,
                    'description': panel.description,
                    'tags': panel.tags,
                    'status': panel.status.value,
                    'visibility': panel.visibility.value,
                    'gene_count': panel.gene_count,
                    'version_count': panel.version_count,
                    'created_at': panel.created_at.isoformat(),
                    'updated_at': panel.updated_at.isoformat(),
                    'source_type': panel.source_type,
                    'source_reference': panel.source_reference,
                    'owner': {
                        'id': panel.owner.id,
                        'username': panel.owner.username
                    },
                    'shared_permission': share.permission_level.value,
                    'shared_at': share.created_at.isoformat(),
                    'expires_at': share.expires_at.isoformat() if share.expires_at else None
                }
                panels_list.append(panel_dict)
            
            return {
                'panels': panels_list,
                'total': len(panels_list)
            }
            
        except Exception as e:
            current_app.logger.error(f"Error retrieving shared panels: {str(e)}")
            ns.abort(500, "Internal server error")
