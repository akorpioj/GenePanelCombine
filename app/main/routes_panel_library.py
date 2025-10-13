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


@main_bp.route('/api/user/panels/<int:panel_id>/export')
@login_required
@limiter.limit("10 per minute")
def api_user_panel_export_single(panel_id):
    """Export a single panel in specified format (Excel, CSV, TSV, JSON)"""
    try:
        from .panel_excel_export import (
            generate_panel_excel, generate_panel_csv,
            generate_panel_tsv, generate_panel_json
        )
        
        # Check panel ownership (exclude deleted panels)
        panel = SavedPanel.query.filter_by(id=panel_id, owner_id=current_user.id).filter(SavedPanel.status != PanelStatus.DELETED).first()
        if not panel:
            logger.error(f"Panel {panel_id} not found or access denied for user {current_user.id}")
            return jsonify({'error': 'Panel not found or access denied'}), 404
        
        # Get export parameters
        export_format = request.args.get('format', 'excel').lower()
        filename = request.args.get('filename')
        include_metadata = request.args.get('include_metadata', 'true').lower() == 'true'
        include_versions = request.args.get('include_versions', 'true').lower() == 'true'
        include_genes = request.args.get('include_genes', 'true').lower() == 'true'
        
        # Validate format
        valid_formats = ['excel', 'csv', 'tsv', 'json']
        if export_format not in valid_formats:
            return jsonify({'error': f'Invalid format. Must be one of: {", ".join(valid_formats)}'}), 400
        
        # Log export action
        AuditService.log_action(
            action_type=AuditActionType.PANEL_DOWNLOAD,
            action_description=f"Exported panel '{panel.name}' to {export_format.upper()}",
            user_id=current_user.id,
            resource_id=panel.id,
            resource_type='panel',
            details={
                "panel_id": panel.id,
                "panel_name": panel.name,
                "format": export_format,
                "filename": filename
            }
        )
        
        # Generate and return file in requested format
        if export_format == 'excel':
            return generate_panel_excel([panel_id], filename=filename)
        elif export_format == 'csv':
            return generate_panel_csv([panel_id], filename=filename, 
                                     include_metadata=include_metadata,
                                     include_versions=include_versions)
        elif export_format == 'tsv':
            return generate_panel_tsv([panel_id], filename=filename,
                                     include_metadata=include_metadata,
                                     include_versions=include_versions)
        elif export_format == 'json':
            return generate_panel_json([panel_id], filename=filename,
                                      include_genes=include_genes,
                                      include_versions=include_versions)
        
    except Exception as e:
        logger.error(f"Error exporting panel {panel_id}: {e}")
        return jsonify({'error': f'Failed to export panel: {str(e)}'}), 500


@main_bp.route('/api/user/panels/export', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
def api_user_panels_export_multiple():
    """Export multiple panels in specified format (Excel, CSV, TSV, JSON)"""
    try:
        from .panel_excel_export import (
            generate_panel_excel, generate_panel_csv,
            generate_panel_tsv, generate_panel_json
        )
        
        data = request.get_json()
        
        # Validate input
        if not data or 'panel_ids' not in data:
            logger.error(f"Panel IDs not provided in request")
            return jsonify({'error': 'panel_ids required'}), 400
        
        panel_ids = data['panel_ids']
        if not isinstance(panel_ids, list) or len(panel_ids) == 0:
            logger.error(f"Invalid panel_ids format: {panel_ids}")
            return jsonify({'error': 'panel_ids must be a non-empty list'}), 400
        
        # Get export parameters
        export_format = data.get('format', 'excel').lower()
        filename = data.get('filename')
        include_metadata = data.get('include_metadata', True)
        include_versions = data.get('include_versions', True)
        include_genes = data.get('include_genes', True)
        
        # Validate format
        valid_formats = ['excel', 'csv', 'tsv', 'json']
        if export_format not in valid_formats:
            return jsonify({'error': f'Invalid format. Must be one of: {", ".join(valid_formats)}'}), 400
        
        # Validate access to all panels
        accessible_panels = []
        for panel_id in panel_ids:
            panel = SavedPanel.query.filter_by(id=panel_id, owner_id=current_user.id).filter(SavedPanel.status != PanelStatus.DELETED).first()
            if not panel:
                logger.error(f"Panel {panel_id} not found or access denied for user {current_user.id}")
                return jsonify({'error': f'Panel ID {panel_id} not found or access denied'}), 403
            accessible_panels.append(panel)
        
        if not accessible_panels:
            logger.error(f"No accessible panels found for user {current_user.id}")
            return jsonify({'error': 'No accessible panels found'}), 404
        
        # Log export action
        AuditService.log_action(
            action_type=AuditActionType.PANEL_DOWNLOAD,
            action_description=f"Exported {len(panel_ids)} panels to {export_format.upper()}",
            user_id=current_user.id,
            resource_type='panel',
            details={
                "panel_ids": panel_ids,
                "panel_names": [p.name for p in accessible_panels],
                "format": export_format,
                "filename": filename
            }
        )
        
        # Generate and return file in requested format
        if export_format == 'excel':
            return generate_panel_excel(panel_ids, filename=filename)
        elif export_format == 'csv':
            return generate_panel_csv(panel_ids, filename=filename,
                                     include_metadata=include_metadata,
                                     include_versions=include_versions)
        elif export_format == 'tsv':
            return generate_panel_tsv(panel_ids, filename=filename,
                                     include_metadata=include_metadata,
                                     include_versions=include_versions)
        elif export_format == 'json':
            return generate_panel_json(panel_ids, filename=filename,
                                      include_genes=include_genes,
                                      include_versions=include_versions)
        
    except Exception as e:
        logger.error(f"Error exporting panels: {e}")
        return jsonify({'error': f'Failed to export panels: {str(e)}'}), 500


# ============================================================================
# Export Templates API
# ============================================================================

@main_bp.route('/api/user/export-templates', methods=['GET', 'POST'])
@login_required
@limiter.limit("30 per minute")
def api_user_export_templates():
    """Manage export templates - GET to list, POST to create"""
    from ..models import ExportTemplate
    
    if request.method == 'GET':
        """Get user's export templates"""
        try:
            templates = ExportTemplate.query.filter_by(user_id=current_user.id)\
                .order_by(ExportTemplate.is_default.desc(), ExportTemplate.usage_count.desc()).all()
            
            return jsonify({
                'templates': [t.to_dict() for t in templates],
                'count': len(templates)
            }), 200
            
        except Exception as e:
            logger.error(f"Error fetching export templates: {e}")
            return jsonify({'error': 'Failed to fetch export templates'}), 500
    
    elif request.method == 'POST':
        """Create a new export template"""
        try:
            data = request.get_json()
            
            # Validate required fields
            if not data or 'name' not in data or 'format' not in data:
                return jsonify({'error': 'name and format are required'}), 400
            
            # Validate format
            valid_formats = ['excel', 'csv', 'tsv', 'json']
            if data['format'].lower() not in valid_formats:
                return jsonify({'error': f'Invalid format. Must be one of: {", ".join(valid_formats)}'}), 400
            
            # Check for duplicate name
            existing = ExportTemplate.query.filter_by(
                user_id=current_user.id,
                name=data['name']
            ).first()
            
            if existing:
                return jsonify({'error': 'A template with this name already exists'}), 409
            
            # If setting as default, unset other defaults
            if data.get('is_default', False):
                ExportTemplate.query.filter_by(
                    user_id=current_user.id,
                    is_default=True
                ).update({'is_default': False})
            
            # Create new template
            template = ExportTemplate(
                user_id=current_user.id,
                name=data['name'],
                description=data.get('description'),
                is_default=data.get('is_default', False),
                format=data['format'].lower(),
                include_metadata=data.get('include_metadata', True),
                include_versions=data.get('include_versions', True),
                include_genes=data.get('include_genes', True),
                filename_pattern=data.get('filename_pattern')
            )
            
            db.session.add(template)
            db.session.commit()
            
            # Log audit action
            AuditService.log_action(
                action_type=AuditActionType.PANEL_EXPORT_TEMPLATE_CREATE,
                action_description=f"Created export template '{template.name}'",
                user_id=current_user.id,
                resource_type='export_template',
                resource_id=template.id,
                details={
                    'template_name': template.name,
                    'format': template.format
                }
            )
            
            logger.info(f"Export template created: {template.name} by user {current_user.id}")
            
            return jsonify({
                'message': 'Export template created successfully',
                'template': template.to_dict()
            }), 201
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating export template: {e}")
            return jsonify({'error': f'Failed to create export template: {str(e)}'}), 500


@main_bp.route('/api/user/export-templates/<int:template_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
@limiter.limit("30 per minute")
def api_user_export_template_detail(template_id):
    """Manage individual export template - GET to retrieve, PUT to update, DELETE to remove"""
    from ..models import ExportTemplate
    
    try:
        # Get template and verify ownership
        template = ExportTemplate.query.filter_by(
            id=template_id,
            user_id=current_user.id
        ).first()
        
        if not template:
            return jsonify({'error': 'Export template not found or access denied'}), 404
        
        if request.method == 'GET':
            """Get export template details"""
            return jsonify({'template': template.to_dict()}), 200
        
        elif request.method == 'PUT':
            """Update export template"""
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            # Update fields if provided
            if 'name' in data:
                # Check for duplicate name (excluding current template)
                existing = ExportTemplate.query.filter(
                    ExportTemplate.user_id == current_user.id,
                    ExportTemplate.name == data['name'],
                    ExportTemplate.id != template_id
                ).first()
                
                if existing:
                    return jsonify({'error': 'A template with this name already exists'}), 409
                
                template.name = data['name']
            
            if 'description' in data:
                template.description = data['description']
            
            if 'format' in data:
                valid_formats = ['excel', 'csv', 'tsv', 'json']
                if data['format'].lower() not in valid_formats:
                    return jsonify({'error': f'Invalid format. Must be one of: {", ".join(valid_formats)}'}), 400
                template.format = data['format'].lower()
            
            if 'include_metadata' in data:
                template.include_metadata = data['include_metadata']
            
            if 'include_versions' in data:
                template.include_versions = data['include_versions']
            
            if 'include_genes' in data:
                template.include_genes = data['include_genes']
            
            if 'filename_pattern' in data:
                template.filename_pattern = data['filename_pattern']
            
            # Handle default flag
            if 'is_default' in data and data['is_default']:
                # Unset other defaults
                ExportTemplate.query.filter_by(
                    user_id=current_user.id,
                    is_default=True
                ).update({'is_default': False})
                template.is_default = True
            elif 'is_default' in data:
                template.is_default = False
            
            template.updated_at = datetime.datetime.now()
            db.session.commit()
            
            # Log audit action
            AuditService.log_action(
                action_type=AuditActionType.PANEL_EXPORT_TEMPLATE_UPDATE,
                action_description=f"Updated export template '{template.name}'",
                user_id=current_user.id,
                resource_type='export_template',
                resource_id=template.id
            )
            
            logger.info(f"Export template updated: {template.name} by user {current_user.id}")
            
            return jsonify({
                'message': 'Export template updated successfully',
                'template': template.to_dict()
            }), 200
        
        elif request.method == 'DELETE':
            """Delete export template"""
            template_name = template.name
            
            db.session.delete(template)
            db.session.commit()
            
            # Log audit action
            AuditService.log_action(
                action_type=AuditActionType.PANEL_EXPORT_TEMPLATE_DELETE,
                action_description=f"Deleted export template '{template_name}'",
                user_id=current_user.id,
                resource_type='export_template',
                resource_id=template_id
            )
            
            logger.info(f"Export template deleted: {template_name} by user {current_user.id}")
            
            return jsonify({'message': 'Export template deleted successfully'}), 200
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error managing export template: {e}")
        return jsonify({'error': f'Failed to manage export template: {str(e)}'}), 500


@main_bp.route('/api/user/export-templates/<int:template_id>/use', methods=['POST'])
@login_required
@limiter.limit("30 per minute")
def api_use_export_template(template_id):
    """Mark template as used and return its settings"""
    from ..models import ExportTemplate
    
    try:
        # Get template and verify ownership
        template = ExportTemplate.query.filter_by(
            id=template_id,
            user_id=current_user.id
        ).first()
        
        if not template:
            return jsonify({'error': 'Export template not found or access denied'}), 404
        
        # Mark as used
        template.mark_as_used()
        db.session.commit()
        
        return jsonify({
            'message': 'Template usage recorded',
            'template': template.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error using export template: {e}")
        return jsonify({'error': f'Failed to use export template: {str(e)}'}), 500


@main_bp.route('/api/user/export-templates/<int:template_id>/set-default', methods=['POST'])
@login_required
@limiter.limit("30 per minute")
def api_set_default_export_template(template_id):
    """Set a template as the default"""
    from ..models import ExportTemplate
    
    try:
        # Get template and verify ownership
        template = ExportTemplate.query.filter_by(
            id=template_id,
            user_id=current_user.id
        ).first()
        
        if not template:
            return jsonify({'error': 'Export template not found or access denied'}), 404
        
        # Unset other defaults
        ExportTemplate.query.filter_by(
            user_id=current_user.id,
            is_default=True
        ).update({'is_default': False})
        
        # Set this as default
        template.is_default = True
        template.updated_at = datetime.datetime.now()
        db.session.commit()
        
        # Log audit action
        AuditService.log_action(
            action_type=AuditActionType.PANEL_EXPORT_TEMPLATE_UPDATE,
            action_description=f"Set export template '{template.name}' as default",
            user_id=current_user.id,
            resource_type='export_template',
            resource_id=template.id
        )
        
        return jsonify({
            'message': 'Default template set successfully',
            'template': template.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error setting default template: {e}")
        return jsonify({'error': f'Failed to set default template: {str(e)}'}), 500
