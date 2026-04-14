import secrets
from flask import request, jsonify, render_template, abort, session
from flask_login import current_user, login_required
import datetime
import re
from app.extensions import limiter, cache
from . import main_bp # Import the Blueprint object defined in __init__.py
from ..models import (
    SavedPanel, PanelVersion, PanelGene, PanelStatus, PanelVisibility, db, AuditActionType,
    PanelVersionTag, PanelVersionBranch, PanelVersionMetadata, PanelRetentionPolicy,
    TagType, VersionType
)
from .utils import logger
from .panel_library_utils import get_panels, create_or_update_panel, get_panel_data, update_panel_data
from ..audit_service import AuditService
from ..version_control_service import (
    VersionControlService, VersionControlError, BranchConflictError,
    MergeStrategy
)
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError

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


# ===========================
# VERSION CONTROL ENDPOINTS
# ===========================

@main_bp.route('/api/user/panels/<int:panel_id>/versions/<int:version_id>/tags', methods=['GET', 'POST'])
@login_required
@limiter.limit("30 per minute")
def api_version_tags(panel_id, version_id):
    """Get or create tags for a specific version"""
    
    # Verify panel ownership
    panel = SavedPanel.query.filter_by(id=panel_id, owner_id=current_user.id).first()
    if not panel:
        return jsonify({'error': 'Panel not found or access denied'}), 404
    
    # Verify version exists
    version = PanelVersion.query.filter_by(id=version_id, panel_id=panel_id).first()
    if not version:
        return jsonify({'error': 'Version not found'}), 404
    
    if request.method == 'GET':
        """Get all tags for a version"""
        try:
            tags = PanelVersionTag.query.filter_by(version_id=version_id).all()
            return jsonify({
                'tags': [tag.to_dict() for tag in tags]
            }), 200
        except Exception as e:
            logger.error(f"Error getting tags for version {version_id}: {e}")
            return jsonify({'error': 'Failed to retrieve tags'}), 500
    
    elif request.method == 'POST':
        """Create a new tag for a version"""
        try:
            data = request.get_json()
            
            if not data or 'tag_name' not in data or 'tag_type' not in data:
                return jsonify({'error': 'tag_name and tag_type are required'}), 400
            
            # Validate tag type
            try:
                tag_type = TagType(data['tag_type'].upper())
            except ValueError:
                return jsonify({'error': f'Invalid tag type: {data["tag_type"]}'}), 400
            
            # Check for duplicate tag name
            existing_tag = PanelVersionTag.query.filter_by(
                version_id=version_id,
                tag_name=data['tag_name']
            ).first()
            if existing_tag:
                return jsonify({'error': f'Tag "{data["tag_name"]}" already exists for this version'}), 409
            
            # Create tag
            tag = PanelVersionTag(
                version_id=version_id,
                tag_name=data['tag_name'],
                tag_type=tag_type,
                description=data.get('description'),
                created_by_id=current_user.id,
                is_protected=(tag_type in [TagType.PRODUCTION, TagType.STAGING])
            )
            
            db.session.add(tag)
            
            # Update version protection if needed
            if tag.is_protected:
                version.is_protected = True
                version.retention_priority = 10
            
            db.session.commit()
            
            # Log tag creation
            AuditService.log_action(
                action_type=AuditActionType.PANEL_UPDATE,
                action_description=f"Created tag '{data['tag_name']}' ({tag_type.value}) for version {version.version_number}",
                user_id=current_user.id,
                resource_type='panel_version_tag',
                resource_id=tag.id,
                details={
                    'panel_id': panel_id,
                    'version_id': version_id,
                    'tag_name': data['tag_name'],
                    'tag_type': tag_type.value,
                    'is_protected': tag.is_protected
                }
            )
            
            return jsonify({
                'message': 'Tag created successfully',
                'tag': tag.to_dict()
            }), 201
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating tag: {e}")
            return jsonify({'error': f'Failed to create tag: {str(e)}'}), 500


@main_bp.route('/api/user/panels/<int:panel_id>/branches', methods=['GET', 'POST'])
@login_required
@limiter.limit("30 per minute")
def api_panel_branches(panel_id):
    """Get or create branches for a panel"""
    
    # Verify panel ownership
    panel = SavedPanel.query.filter_by(id=panel_id, owner_id=current_user.id).first()
    if not panel:
        return jsonify({'error': 'Panel not found or access denied'}), 404
    
    if request.method == 'GET':
        """Get all branches for a panel"""
        try:
            branches = PanelVersionBranch.query.filter_by(panel_id=panel_id)\
                .order_by(desc(PanelVersionBranch.created_at)).all()
            
            return jsonify({
                'branches': [branch.to_dict() for branch in branches]
            }), 200
        except Exception as e:
            logger.error(f"Error getting branches for panel {panel_id}: {e}")
            return jsonify({'error': 'Failed to retrieve branches'}), 500
    
    elif request.method == 'POST':
        """Create a new branch"""
        try:
            data = request.get_json()
            
            if not data or 'branch_name' not in data or 'from_version_id' not in data:
                return jsonify({'error': 'branch_name and from_version_id are required'}), 400
            
            # Verify source version
            from_version = PanelVersion.query.get(data['from_version_id'])
            if not from_version or from_version.panel_id != panel_id:
                return jsonify({'error': 'Invalid source version'}), 400
            
            # Check for duplicate branch name
            existing_branch = PanelVersionBranch.query.filter_by(
                panel_id=panel_id,
                branch_name=data['branch_name']
            ).first()
            if existing_branch:
                return jsonify({'error': f'Branch "{data["branch_name"]}" already exists'}), 409
            
            # Use version control service to create branch
            vc_service = VersionControlService()
            branch_version = vc_service.create_branch(
                panel_id=panel_id,
                from_version_id=data['from_version_id'],
                branch_name=data['branch_name'],
                user_id=current_user.id,
                description=data.get('description')
            )
            
            # Get the created branch
            branch = PanelVersionBranch.query.filter_by(
                panel_id=panel_id,
                branch_name=data['branch_name']
            ).first()
            
            return jsonify({
                'message': 'Branch created successfully',
                'branch': branch.to_dict(),
                'branch_version': branch_version.to_dict()
            }), 201
            
        except VersionControlError as e:
            logger.error(f"Version control error creating branch: {e}")
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating branch: {e}")
            return jsonify({'error': f'Failed to create branch: {str(e)}'}), 500


@main_bp.route('/api/user/panels/<int:panel_id>/versions/<int:version_id>/diff/<int:other_version_id>')
@login_required
@limiter.limit("20 per minute")
def api_version_diff(panel_id, version_id, other_version_id):
    """Get differences between two versions"""
    
    # Verify panel ownership
    panel = SavedPanel.query.filter_by(id=panel_id, owner_id=current_user.id).first()
    if not panel:
        return jsonify({'error': 'Panel not found or access denied'}), 404
    
    try:
        # Verify both versions exist
        version1 = PanelVersion.query.filter_by(id=version_id, panel_id=panel_id).first()
        version2 = PanelVersion.query.filter_by(id=other_version_id, panel_id=panel_id).first()
        
        if not version1 or not version2:
            return jsonify({'error': 'One or both versions not found'}), 404
        
        # Use version control service to get diff
        vc_service = VersionControlService()
        diff = vc_service.get_version_diff(version_id, other_version_id)
        
        return jsonify(diff), 200
        
    except VersionControlError as e:
        logger.error(f"Version control error getting diff: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting version diff: {e}")
        return jsonify({'error': 'Failed to get version diff'}), 500


@main_bp.route('/api/user/panels/<int:panel_id>/merge', methods=['POST'])
@login_required
@limiter.limit("3 per minute")
def api_merge_versions(panel_id):
    """Merge two versions"""
    
    # Verify panel ownership
    panel = SavedPanel.query.filter_by(id=panel_id, owner_id=current_user.id).first()
    if not panel:
        return jsonify({'error': 'Panel not found or access denied'}), 404
    
    try:
        data = request.get_json()
        
        if not data or 'source_version_id' not in data or 'target_version_id' not in data:
            return jsonify({'error': 'source_version_id and target_version_id are required'}), 400
        
        # Validate merge strategy
        strategy_str = data.get('strategy', 'auto').upper()
        try:
            strategy = MergeStrategy(strategy_str)
        except ValueError:
            return jsonify({'error': f'Invalid merge strategy: {strategy_str}'}), 400
        
        # Use version control service to perform merge
        vc_service = VersionControlService()
        
        try:
            merged_version = vc_service.merge_versions(
                panel_id=panel_id,
                source_version_id=data['source_version_id'],
                target_version_id=data['target_version_id'],
                user_id=current_user.id,
                strategy=strategy,
                conflict_resolutions=data.get('conflict_resolutions'),
                comment=data.get('comment')
            )
            
            return jsonify({
                'success': True,
                'merged_version': merged_version.to_dict(),
                'message': f'Successfully merged versions {data["source_version_id"]} and {data["target_version_id"]}'
            }), 200
            
        except BranchConflictError as e:
            return jsonify({'error': str(e), 'conflicts': True}), 409
            
    except VersionControlError as e:
        logger.error(f"Version control error during merge: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error merging versions: {e}")
        return jsonify({'error': 'Failed to merge versions'}), 500


@main_bp.route('/api/user/panels/<int:panel_id>/retention-policy', methods=['GET', 'PUT'])
@login_required
@limiter.limit("30 per minute")
def api_retention_policy(panel_id):
    """Get or update retention policy for a panel"""
    
    # Verify panel ownership
    panel = SavedPanel.query.filter_by(id=panel_id, owner_id=current_user.id).first()
    if not panel:
        return jsonify({'error': 'Panel not found or access denied'}), 404
    
    if request.method == 'GET':
        """Get retention policy"""
        try:
            policy = PanelRetentionPolicy.query.filter_by(panel_id=panel_id).first()
            if not policy:
                # Create default policy
                policy = PanelRetentionPolicy(
                    panel_id=panel_id,
                    created_by_id=current_user.id
                )
                db.session.add(policy)
                db.session.commit()
            
            return jsonify({'policy': policy.to_dict()}), 200
            
        except Exception as e:
            logger.error(f"Error getting retention policy for panel {panel_id}: {e}")
            return jsonify({'error': 'Failed to retrieve retention policy'}), 500
    
    elif request.method == 'PUT':
        """Update retention policy"""
        try:
            data = request.get_json()
            
            policy = PanelRetentionPolicy.query.filter_by(panel_id=panel_id).first()
            if not policy:
                # Create new policy
                policy = PanelRetentionPolicy(
                    panel_id=panel_id,
                    created_by_id=current_user.id
                )
                db.session.add(policy)
            
            # Update policy fields
            if 'max_versions' in data:
                policy.max_versions = data['max_versions']
            if 'backup_retention_days' in data:
                policy.backup_retention_days = data['backup_retention_days']
            if 'keep_tagged_versions' in data:
                policy.keep_tagged_versions = data['keep_tagged_versions']
            if 'keep_production_tags' in data:
                policy.keep_production_tags = data['keep_production_tags']
            if 'auto_cleanup_enabled' in data:
                policy.auto_cleanup_enabled = data['auto_cleanup_enabled']
            if 'cleanup_frequency_hours' in data:
                policy.cleanup_frequency_hours = data['cleanup_frequency_hours']
            
            policy.updated_at = datetime.datetime.now()
            db.session.commit()
            
            # Log policy update
            AuditService.log_action(
                action_type=AuditActionType.PANEL_UPDATE,
                action_description=f"Updated retention policy for panel '{panel.name}'",
                user_id=current_user.id,
                resource_type='retention_policy',
                resource_id=policy.id,
                details={
                    'panel_id': panel_id,
                    'policy_id': policy.id,
                    'changes': list(data.keys())
                }
            )
            
            return jsonify({
                'message': 'Retention policy updated successfully',
                'policy': policy.to_dict()
            }), 200
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating retention policy: {e}")
            return jsonify({'error': 'Failed to update retention policy'}), 500


@main_bp.route('/api/user/panels/<int:panel_id>/cleanup', methods=['POST'])
@login_required
@limiter.limit("2 per hour")
def api_retention_cleanup(panel_id):
    """Manually run retention cleanup for a panel"""
    
    # Verify panel ownership
    panel = SavedPanel.query.filter_by(id=panel_id, owner_id=current_user.id).first()
    if not panel:
        return jsonify({'error': 'Panel not found or access denied'}), 404
    
    try:
        # Use version control service to apply retention
        vc_service = VersionControlService()
        vc_service.retention_policy.apply_retention(panel_id)
        
        # Update policy timestamp
        policy = PanelRetentionPolicy.query.filter_by(panel_id=panel_id).first()
        if policy:
            policy.update_cleanup_timestamp()
            db.session.commit()
        
        # Log cleanup operation
        AuditService.log_action(
            action_type=AuditActionType.PANEL_UPDATE,
            action_description=f"Manually ran retention cleanup for panel '{panel.name}'",
            user_id=current_user.id,
            resource_type='panel',
            resource_id=panel_id,
            details={
                'panel_id': panel_id,
                'triggered_by': 'manual',
                'user_id': current_user.id
            }
        )
        
        return jsonify({
            'success': True,
            'message': 'Retention cleanup completed successfully',
            'timestamp': datetime.datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error running retention cleanup: {e}")
        return jsonify({'error': 'Failed to run retention cleanup'}), 500


@main_bp.route('/api/user/panels/<int:panel_id>/versions/<int:version_id>/restore', methods=['POST'])
@login_required
@limiter.limit("3 per hour")
def api_restore_version(panel_id, version_id):
    """Restore a panel to a specific version
    
    Note: version_id in the URL can be either the database ID or version_number.
    The function will try both to maintain compatibility.
    """
    
    # Verify panel ownership
    panel = SavedPanel.query.filter_by(id=panel_id, owner_id=current_user.id).first()
    if not panel:
        logger.error(f"Panel {panel_id} not found or access denied for user {current_user.id}")
        return jsonify({'error': 'Panel not found or access denied'}), 404
    
    # Try to find version by ID first, then by version_number
    version = PanelVersion.query.filter_by(id=version_id, panel_id=panel_id).first()
    if not version:
        # Try finding by version_number instead
        version = PanelVersion.query.filter_by(version_number=version_id, panel_id=panel_id).first()
        if not version:
            logger.error(f"Version {version_id} not found for panel {panel_id}")
            return jsonify({'error': 'Version not found'}), 404
    
    try:
        logger.info(f"User {current_user.id} is restoring panel {panel_id} to version {version.id} (version_number: {version.version_number})")
        data = request.get_json() or {}
        create_backup = data.get('create_backup', True)
        
        # Use version control service to restore
        # IMPORTANT: Pass version.id (database ID) not version_id from URL
        vc_service = VersionControlService()
        restored_version = vc_service.restore_version(
            panel_id=panel_id,
            version_id=version.id,  # Use the database ID, not the URL parameter
            user_id=current_user.id,
            create_backup=create_backup
        )
        
        return jsonify({
            'success': True,
            'restored_version': restored_version.to_dict(),
            'message': f'Successfully restored to version {version.version_number}',
            'backup_created': create_backup
        }), 200
        
    except VersionControlError as e:
        logger.error(f"Version control error during restore: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error restoring version: {e}")
        return jsonify({'error': 'Failed to restore version'}), 500


# ============================================================================
# Genie Gene Registration
# ============================================================================

@main_bp.route('/panels/<int:panel_id>/add-to-genie')
@login_required
def panel_add_to_genie(panel_id):
    """
    GET /panels/<panel_id>/add-to-genie

    Renders a full-page wizard that lets the user look up an Ensembl ID
    for each gene in the panel and register all resolved genes in Genie.
    """
    panel = SavedPanel.query.filter_by(
        id=panel_id, owner_id=current_user.id
    ).filter(SavedPanel.status != PanelStatus.DELETED).first()
    if not panel:
        abort(404)

    genes = PanelGene.query.filter_by(panel_id=panel.id).order_by(PanelGene.gene_symbol).all()
    gene_list = [
        {
            'symbol': g.gene_symbol,
            'name': g.gene_name or '',
            'ensembl_id': g.ensembl_id or '',
        }
        for g in genes
    ]

    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_urlsafe(32)

    return render_template(
        'main/panel_genie_export.html',
        panel=panel,
        genes=gene_list,
    )


@main_bp.route('/api/user/panels/<int:panel_id>/add-to-genie', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
def api_panel_add_to_genie(panel_id):
    """
    POST /api/user/panels/<panel_id>/add-to-genie
    JSON body: {"genes": [{"gene_symbol": "BRCA1", "ensembl_id": "ENSG..."}]}

    Registers each supplied gene (by Ensembl ID) in Genie.
    Returns per-gene status.
    """
    panel = SavedPanel.query.filter_by(
        id=panel_id, owner_id=current_user.id
    ).filter(SavedPanel.status != PanelStatus.DELETED).first()
    if not panel:
        return jsonify({'error': 'Panel not found or access denied'}), 404

    data = request.get_json(silent=True) or {}
    genes = data.get('genes')
    if not isinstance(genes, list) or len(genes) == 0:
        return jsonify({'error': 'genes list is required'}), 400

    from ..litreview.genie_service import genie_service

    # Partition genes into those with/without an Ensembl ID
    skipped = []
    to_register = []  # {gene_symbol, ensembl_id}
    for gene in genes:
        ensembl_id  = (gene.get('ensembl_id')  or '').strip()
        gene_symbol = (gene.get('gene_symbol') or '').strip()
        if not ensembl_id:
            skipped.append({'gene_symbol': gene_symbol, 'ensembl_id': '',
                            'status': 'skipped', 'message': 'No Ensembl ID provided'})
        else:
            to_register.append({'gene_symbol': gene_symbol, 'ensembl_id': ensembl_id})

    results = list(skipped)

    if to_register:
        ensembl_ids = [g['ensembl_id'] for g in to_register]
        try:
            genie_service.create_genes_bulk(ensembl_ids)

            # Persist resolved Ensembl IDs back to PanelGene records where blank
            for g in to_register:
                pg = PanelGene.query.filter_by(
                    panel_id=panel.id, gene_symbol=g['gene_symbol']
                ).first()
                if pg and not pg.ensembl_id:
                    pg.ensembl_id = g['ensembl_id']

            results.extend({
                'gene_symbol': g['gene_symbol'],
                'ensembl_id': g['ensembl_id'],
                'status': 'registered',
            } for g in to_register)

        except Exception as exc:
            logger.error('Genie create_genes_bulk failed for panel %s: %s', panel_id, exc)
            results.extend({
                'gene_symbol': g['gene_symbol'],
                'ensembl_id': g['ensembl_id'],
                'status': 'error',
                'message': str(exc),
            } for g in to_register)

    db.session.commit()

    AuditService.log_action(
        action_type=AuditActionType.PANEL_DOWNLOAD,
        action_description=(
            f"Added {sum(1 for r in results if r['status'] == 'registered')} "
            f"gene(s) from panel '{panel.name}' to Genie"
        ),
        user_id=current_user.id,
        resource_id=panel.id,
        resource_type='panel',
        details={
            'panel_id': panel_id,
            'panel_name': panel.name,
            'gene_count': len(genes),
            'registered': sum(1 for r in results if r['status'] == 'registered'),
            'skipped': sum(1 for r in results if r['status'] == 'skipped'),
            'errors': sum(1 for r in results if r['status'] == 'error'),
        },
    )

    return jsonify({'results': results}), 200


@main_bp.route('/api/user/panels/<int:panel_id>/genie-status', methods=['GET'])
@login_required
@limiter.limit("60 per minute")
def api_panel_genie_status(panel_id):
    """
    GET /api/user/panels/<panel_id>/genie-status

    Returns Genie registration status for all genes in the panel that have
    an Ensembl ID stored.  Genes without an Ensembl ID are omitted.

    Response JSON:
        {
            "status": [
                {"ensembl_id": "ENSG...", "gene_symbol": "BRCA1", "exists": true},
                ...
            ]
        }
    """
    panel = SavedPanel.query.filter_by(
        id=panel_id, owner_id=current_user.id
    ).filter(SavedPanel.status != PanelStatus.DELETED).first()
    if not panel:
        return jsonify({'error': 'Panel not found or access denied'}), 404

    genes = PanelGene.query.filter_by(panel_id=panel.id).all()

    # Genes that already have a resolved Ensembl ID stored.
    id_to_symbol = {
        g.ensembl_id: g.gene_symbol
        for g in genes
        if g.ensembl_id and g.ensembl_id.strip()
    }

    # Genes whose Ensembl ID has not yet been resolved — look them up by symbol.
    unresolved_symbols = [
        g.gene_symbol for g in genes
        if (not g.ensembl_id or not g.ensembl_id.strip()) and g.gene_symbol
    ]

    from ..litreview.genie_service import genie_service

    if unresolved_symbols:
        try:
            resolved = genie_service.lookup_genes_bulk(unresolved_symbols)  # {symbol: ensembl_id}
            for symbol, eid in resolved.items():
                if eid and eid not in id_to_symbol:
                    id_to_symbol[eid] = symbol
        except Exception as exc:
            logger.warning('Genie bulk symbol lookup failed for panel %s: %s', panel_id, exc)

    if not id_to_symbol:
        return jsonify({'status': []}), 200

    try:
        check_results = genie_service.check_genes(list(id_to_symbol.keys()))
    except Exception as exc:
        logger.error('Genie check_genes failed for panel %s: %s', panel_id, exc)
        return jsonify({'error': 'Genie service unavailable'}), 502

    status = [
        {
            'ensembl_id': item['ensembl_id'],
            'gene_symbol': id_to_symbol.get(item['ensembl_id'], ''),
            'exists': item.get('exists', False),
        }
        for item in check_results
    ]

    return jsonify({'status': status}), 200


# ===========================
# GENE DETAIL PAGE
# ===========================

_ENSEMBL_ID_RE = re.compile(r'^ENSG\d{6,}$', re.IGNORECASE)


@main_bp.route('/genes/<ensembl_id>')
@login_required
def gene_detail_page(ensembl_id):
    """
    GET /genes/<ensembl_id>

    Render a detail page for a gene identified by Ensembl ID.
    Fetches annotation from Genie/Ensembl and shows whether the gene
    is already registered in Genie.  If not, prompts the user to add it.
    """
    if not _ENSEMBL_ID_RE.match(ensembl_id):
        abort(404)

    from ..litreview.genie_service import genie_service

    gene_info = None
    in_genie = False
    omim_id = None
    error = None

    try:
        gene_info = genie_service.get_gene_detail(ensembl_id)
    except Exception as exc:
        logger.warning('Genie get_gene_detail failed for %s: %s', ensembl_id, exc)
        error = 'Could not reach the Genie service. Please try again later.'

    if gene_info is not None:
        try:
            check = genie_service.check_genes([ensembl_id])
            in_genie = bool(check and check[0].get('exists'))
        except Exception as exc:
            logger.warning('Genie check_genes failed for %s: %s', ensembl_id, exc)

        if in_genie:
            try:
                omim_id = genie_service.get_omim_id(ensembl_id)
            except Exception as exc:
                logger.warning('Genie get_omim_id failed for %s: %s', ensembl_id, exc)

    return render_template(
        'main/gene_detail.html',
        ensembl_id=ensembl_id,
        gene_info=gene_info,
        in_genie=in_genie,
        omim_id=omim_id,
        error=error,
    )


@main_bp.route('/api/genes/<ensembl_id>/register', methods=['POST'])
@login_required
@limiter.limit('30 per minute')
def api_gene_register(ensembl_id):
    """
    POST /api/genes/<ensembl_id>/register

    Register a single gene in Genie by Ensembl ID.
    Idempotent: safe to call when the gene already exists.

    Response JSON:
        {
            "success": true,
            "ensembl_id": "ENSG...",
            "already_existed": false,
            "message": "Gene added to Genie successfully."
        }
    """
    if not _ENSEMBL_ID_RE.match(ensembl_id):
        return jsonify({'error': 'Invalid Ensembl ID format'}), 400

    from ..litreview.genie_service import genie_service

    try:
        result = genie_service.create_genes_bulk([ensembl_id])
        already_existed = bool(result and result[0].get('exists'))
        return jsonify({
            'success': True,
            'ensembl_id': ensembl_id,
            'already_existed': already_existed,
            'message': 'Gene is already in Genie.' if already_existed
                       else 'Gene added to Genie successfully.',
        }), 200
    except Exception as exc:
        logger.error('Genie register gene failed for %s: %s', ensembl_id, exc)
        return jsonify({'error': 'Genie service unavailable. Please try again later.'}), 502
