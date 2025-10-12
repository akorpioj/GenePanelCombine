from flask import request, jsonify
from flask_login import current_user, login_required
import datetime
from app.extensions import limiter, cache
from . import main_bp # Import the Blueprint object defined in __init__.py
from ..models import SavedPanel, PanelVersion, PanelGene, PanelStatus, PanelVisibility, db, AuditActionType
from .utils import logger
from .panel_library_utils import get_panels, create_or_update_panel, get_panel_data, update_panel_data
from ..audit_service import AuditService
from sqlalchemy import desc

@main_bp.route('/api/user/panels', methods=['GET', 'POST'])
@login_required
@limiter.limit("30 per minute")
def api_user_panels():
    """Handle user's saved panels - GET to list, POST to create/update"""
    
    if request.method == 'GET':
        """Get user's saved panels for enhanced panel library"""
        return get_panels(request)
    elif request.method == 'POST':
        """Create a new or update an existing panel"""
        return create_or_update_panel(request)


@main_bp.route('/api/user/panels/<int:panel_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
@limiter.limit("30 per minute")
def api_user_panel_detail(panel_id):
    """Handle individual panel operations - GET to retrieve, PUT to update, DELETE to remove"""
    
    # Find the panel and verify ownership (exclude deleted panels from normal operations)
    panel = SavedPanel.query.filter_by(id=panel_id, owner_id=current_user.id).filter(SavedPanel.status != PanelStatus.DELETED).first()
    if not panel:
        return jsonify({'error': 'Panel not found or access denied'}), 404
    
    if request.method == 'GET':
        """Get detailed information about a specific panel"""
        return get_panel_data(panel)
    
    elif request.method == 'PUT':
        """Update an existing panel"""
        return update_panel_data(panel, request)
    
    elif request.method == 'DELETE':
        """Delete (soft delete) a panel"""
        # For DELETE operations, we need to find the panel even if it's already deleted
        # to provide appropriate feedback
        panel_for_delete = SavedPanel.query.filter_by(id=panel_id, owner_id=current_user.id).first()
        if not panel_for_delete:
            return jsonify({'error': 'Panel not found or access denied'}), 404
        
        # Check if panel is already deleted
        if panel_for_delete.status == PanelStatus.DELETED:
            return jsonify({'message': 'Panel is already deleted'}), 200
        
        try:
            # Soft delete by setting status to DELETED
            panel_for_delete.status = PanelStatus.DELETED
            panel_for_delete.updated_at = datetime.datetime.now()
            
            # Create audit entry
            AuditService.log_action(
                action_type=AuditActionType.PANEL_DELETE,
                action_description=f"Deleted panel {panel_for_delete.name} (ID: {panel_for_delete.id})",
                user_id=current_user.id,
                resource_id=panel_for_delete.id,
                resource_type='panel',
                details={"panel_id": panel_id, "name": panel_for_delete.name}
            )
            
            db.session.commit()
            
            return jsonify({'message': 'Panel deleted successfully'})
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting panel {panel_id}: {e}")
            return jsonify({'error': 'Failed to delete panel'}), 500

@main_bp.route('/api/user/panels/<int:panel_id>/versions')
@login_required
@limiter.limit("30 per minute")
def api_user_panel_versions(panel_id):
    """Get version history for a user's saved panel"""
    try:
        # Check panel ownership (exclude deleted panels)
        panel = SavedPanel.query.filter_by(id=panel_id, owner_id=current_user.id).filter(SavedPanel.status != PanelStatus.DELETED).first()
        if not panel:
            return jsonify({'error': 'Panel not found'}), 404
        
        # Get versions
        versions = PanelVersion.query.filter_by(panel_id=panel.id).order_by(desc(PanelVersion.version_number)).all()
        
        versions_list = []
        for version in versions:
            versions_list.append({
                'id': version.id,
                'version_number': version.version_number,
                'comment': version.comment,
                'gene_count': version.gene_count,
                'changes_summary': version.changes_summary,
                'created_at': version.created_at.isoformat() if version.created_at else None,
                'created_by': {
                    'id': version.created_by.id,
                    'username': version.created_by.username
                } if version.created_by else None
            })
        
        return jsonify({
            'panel_id': panel.id,
            'panel_name': panel.name,
            'versions': versions_list
        })
        
    except Exception as e:
        logger.error(f"Error getting panel versions: {e}")
        return jsonify({'error': 'Failed to get panel versions'}), 500

@main_bp.route('/api/user/panels/<int:panel_id>/versions/<int:version_number>')
@login_required
@limiter.limit("30 per minute")
def api_user_panel_version_details(panel_id, version_number):
    """Get details for a specific version of a user's saved panel"""
    try:
        # Check panel ownership (exclude deleted panels)
        panel = SavedPanel.query.filter_by(id=panel_id, owner_id=current_user.id).filter(SavedPanel.status != PanelStatus.DELETED).first()
        if not panel:
            return jsonify({'error': 'Panel not found'}), 404
        
        # Get version
        version = PanelVersion.query.filter_by(panel_id=panel.id, version_number=version_number).first()
        if not version:
            return jsonify({'error': 'Version not found'}), 404
        
        # Get genes for this version (for now, return current panel genes)
        genes = PanelGene.query.filter_by(panel_id=panel.id).all()
        
        version_data = {
            'id': version.id,
            'version_number': version.version_number,
            'comment': version.comment,
            'gene_count': version.gene_count,
            'changes_summary': version.changes_summary,
            'created_at': version.created_at.isoformat() if version.created_at else None,
            'created_by': {
                'id': version.created_by.id,
                'username': version.created_by.username
            } if version.created_by else None,
            'genes': [{
                'gene_symbol': gene.gene_symbol,
                'gene_name': gene.gene_name,
                'confidence_level': gene.confidence_level,
                'mode_of_inheritance': gene.mode_of_inheritance,
                'phenotype': gene.phenotype
            } for gene in genes]
        }
        
        return jsonify(version_data)
        
    except Exception as e:
        logger.error(f"Error getting panel version details: {e}")
        return jsonify({'error': 'Failed to get version details'}), 500
